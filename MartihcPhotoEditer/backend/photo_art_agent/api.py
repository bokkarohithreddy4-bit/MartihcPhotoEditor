"""
PhotoArtAgent API - Modal Cloud Backend
========================================
A comprehensive photo editing API that uses AI vision models to edit images
based on natural language prompts, with iterative refinement capabilities.

Endpoints:
- POST /upload: Upload image + prompt, get session_id
- POST /generate/{session_id}: Start first iteration
- POST /iterate/{session_id}: Continue iterating
- POST /semantic/init/{session_id}: Initialize semantic editing mode
- POST /semantic/edit/{session_id}: Apply semantic edits
- GET /session/{session_id}: Get session info
"""

import os
import shutil
import uuid
import json
import cv2
import numpy as np
from typing import Dict, Optional, List, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import modal


image_volume = modal.Volume.from_name("photoart-images", create_if_missing=True)
session_state = modal.Dict.from_name("photoart-sessions", create_if_missing=True)

full_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "opencv-python-headless",
        "numpy",
        "torch",
        "openai",
        "cloudinary",
        "Pillow",
        "python-dotenv",
        "fastapi[standard]",
        "uvicorn",
        "python-multipart"
    )
    .add_local_dir(".", remote_path="/root/app")
)

# Initialize Modal app
app = modal.App("photoart-backend")


MOUNT_PATH = "/data"
VLM_PREVIEW_WIDTH = 212
MAX_ITERATIONS = 5


web_app = FastAPI(title="PhotoArtAgent API", version="2.0")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SemanticEditRequest(BaseModel):
    coordinates: Dict[str, float]
    base_filename: Optional[str] = None

class IterateRequest(BaseModel):
    base_filename: Optional[str] = None


def get_toolbox():
    """Get the toolbox with all available tools."""
    import sys
    sys.path.insert(0, "/root/app")
    import opencv_tools

    return {
        "adjust_exposure": opencv_tools.adjust_exposure,
        "adjust_contrast": opencv_tools.adjust_contrast,
        "adjust_highlights": opencv_tools.adjust_highlights,
        "adjust_shadows": opencv_tools.adjust_shadows,
        "adjust_whites": opencv_tools.adjust_whites,
        "adjust_blacks": opencv_tools.adjust_blacks,
        "adjust_temp_tint": opencv_tools.adjust_temp_tint,
        "adjust_saturation": opencv_tools.adjust_saturation,
        "adjust_vibrance": opencv_tools.adjust_vibrance,
        "adjust_color_mixer": opencv_tools.adjust_color_mixer,
        "apply_split_toning": opencv_tools.apply_split_toning,
        "apply_color_overlay": opencv_tools.apply_color_overlay,
        "apply_curves": opencv_tools.apply_curves,
        "apply_vignette": opencv_tools.apply_vignette,
        "apply_glow": opencv_tools.apply_glow,
        "apply_grain": opencv_tools.apply_grain,
        "apply_duotone": opencv_tools.apply_duotone,
        "apply_haze": opencv_tools.apply_haze,
        "apply_film_fade": opencv_tools.apply_film_fade,
        "apply_clarity": opencv_tools.apply_clarity,
        "apply_dehaze": opencv_tools.apply_dehaze,
        "apply_orton_effect": opencv_tools.apply_orton_effect,
        "apply_cross_process": opencv_tools.apply_cross_process,
        "apply_bleach_bypass": opencv_tools.apply_bleach_bypass,
        "apply_teal_and_orange": opencv_tools.apply_teal_and_orange,
        "apply_lut_color_grade": opencv_tools.apply_lut_color_grade,
        "apply_style_preset": opencv_tools.apply_style_preset,
    }


def make_vlm_preview(path: str, width: int = 224) -> Optional[str]:
    """Create a smaller preview image for VLM processing."""
    if not os.path.exists(path):
        print(f"⚠️ make_vlm_preview: Path not found {path}")
        return None

    img = cv2.imread(path)
    if img is None:
        print(f"⚠️ make_vlm_preview: Could not read image at {path}")
        return None

    h, w_img = img.shape[:2]

    if w_img <= width:
        preview = img
    else:
        scale = width / w_img
        preview = cv2.resize(img, (width, int(h * scale)), interpolation=cv2.INTER_AREA)

    root, ext = os.path.splitext(path)
    preview_path = f"{root}_vlm_preview{ext}"
    cv2.imwrite(preview_path, preview)
    return preview_path


def clamp(value: float, mn: float, mx: float) -> float:
    """Clamp a value to a range."""
    try:
        return max(mn, min(mx, float(value)))
    except:
        return mn


def rgb_to_hue(rgb: List[int]) -> float:
    """Convert RGB color [R,G,B] to hue (0-360)."""
    if not rgb or len(rgb) < 3:
        return 0
    r, g, b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c
    if diff == 0:
        return 0
    if max_c == r:
        hue = 60 * ((g - b) / diff % 6)
    elif max_c == g:
        hue = 60 * ((b - r) / diff + 2)
    else:
        hue = 60 * ((r - g) / diff + 4)
    return hue if hue >= 0 else hue + 360


def clamp_params(params: Dict) -> Dict:
    """
    Clamp parameters to balanced, safe ranges.
    Key insight: Brightness controls need to be CONSERVATIVE to avoid washing out!
    Color controls (temp, saturation) can be more aggressive.
    """
    def _c(val, mn, mx):
        try:
            return max(mn, min(mx, float(val)))
        except:
            return mn

    result = params.copy()

    mixer = result.get("adjust_color_mixer", {})
    new_mixer = {}
    for ch in ["red", "orange", "yellow", "green", "cyan", "blue", "purple"]:
        cfg = mixer.get(ch, {})
        if not isinstance(cfg, dict):
            cfg = {}
        hue = int(_c(cfg.get("hue_shift", 0), -20, 20))
        sat = _c(cfg.get("sat_scale", 1.0), 0.5, 1.8)
        lum = _c(cfg.get("lum_scale", 1.0), 0.7, 1.3)
        new_mixer[ch] = {"hue_shift": hue, "sat_scale": sat, "lum_scale": lum}
    result["adjust_color_mixer"] = new_mixer

    if "adjust_exposure" in result:
        exp = result["adjust_exposure"]
        val = exp.get("value", 0.0) if isinstance(exp, dict) else exp
        result["adjust_exposure"] = {"value": _c(val, -35, 15)}
    else:
        result["adjust_exposure"] = {"value": 0.0}

    if "adjust_contrast" in result:
        con = result["adjust_contrast"]
        val = con.get("value", 1.0) if isinstance(con, dict) else con
        result["adjust_contrast"] = {"value": _c(val, 0.85, 1.35)}
    else:
        result["adjust_contrast"] = {"value": 1.0}

    if "adjust_highlights" in result:
        hl = result["adjust_highlights"]
        val = hl.get("value", 0.0) if isinstance(hl, dict) else hl
        result["adjust_highlights"] = {"value": _c(val, -35, 10)}
    else:
        result["adjust_highlights"] = {"value": 0.0}

    if "adjust_shadows" in result:
        sh = result["adjust_shadows"]
        val = sh.get("value", 0.0) if isinstance(sh, dict) else sh
        result["adjust_shadows"] = {"value": _c(val, -25, 35)}
    else:
        result["adjust_shadows"] = {"value": 0.0}

    if "adjust_whites" in result:
        wh = result["adjust_whites"]
        val = wh.get("value", 0.0) if isinstance(wh, dict) else wh
        result["adjust_whites"] = {"value": _c(val, -25, 8)}
    else:
        result["adjust_whites"] = {"value": 0.0}

    if "adjust_blacks" in result:
        bl = result["adjust_blacks"]
        val = bl.get("value", 0.0) if isinstance(bl, dict) else bl
        result["adjust_blacks"] = {"value": _c(val, -20, 15)}
    else:
        result["adjust_blacks"] = {"value": 0.0}

    if "adjust_temp_tint" in result:
        tt = result["adjust_temp_tint"]
        if isinstance(tt, dict):
            t_val = _c(tt.get("temp", 0.0), -70, 70)
            tint_val = _c(tt.get("tint", 0.0), -25, 25)
            result["adjust_temp_tint"] = {"temp": t_val, "tint": tint_val}
        else:
            result["adjust_temp_tint"] = {"temp": 0.0, "tint": 0.0}
    else:
        result["adjust_temp_tint"] = {"temp": 0.0, "tint": 0.0}

    if "adjust_saturation" in result:
        sat = result["adjust_saturation"]
        val = sat.get("scale", 1.0) if isinstance(sat, dict) else sat
        result["adjust_saturation"] = {"scale": _c(val, 0.0, 1.4)}
    else:
        result["adjust_saturation"] = {"scale": 1.0}

    if "adjust_vibrance" in result:
        vib = result["adjust_vibrance"]
        val = vib.get("strength", 0.0) if isinstance(vib, dict) else vib
        result["adjust_vibrance"] = {"strength": _c(val, 0.0, 0.8)}
    else:
        result["adjust_vibrance"] = {"strength": 0.0}

    return result


def normalize_tool_params(tool_name: str, tool_params: Any) -> Dict:
    """
    Normalize AI's various parameter formats to what our functions expect.
    The AI can send params in MANY different formats - we handle them ALL here.
    """
    if isinstance(tool_params, str):
        if tool_name == "apply_style_preset":
            return {"style": tool_params}
        elif tool_name == "apply_grain":
            try:
                return {"amount": float(tool_params)}
            except:
                return {"amount": 0.03}
        else:
            return {}

    if tool_params is None:
        return {}

    if isinstance(tool_params, list):
        if tool_name == "apply_curves":
            try:
                shadows = (tool_params[0][1] - 0) * 2
                midtones = (tool_params[2][1] - 128) / 2
                highlights = (tool_params[4][1] - 255) * 2
                return {"shadows": shadows, "midtones": midtones, "highlights": highlights}
            except:
                return {"shadows": 0, "midtones": 0, "highlights": 0}
        return {}

    if not isinstance(tool_params, dict):
        return {}

    normalized = tool_params.copy()

    if tool_name == "apply_style_preset":
        if "preset" in normalized and "style" not in normalized:
            normalized["style"] = normalized.pop("preset")
        if "name" in normalized and "style" not in normalized:
            normalized["style"] = normalized.pop("name")
        return {"style": normalized.get("style", "none")}

    if tool_name == "apply_grain":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.03
        amount = float(amount)
        if amount > 1.0:
            amount = amount / 100.0
        size = normalized.get("size", 1)
        amount = min(0.08, amount)  # SAFETY CAP
        return {"amount": amount, "size": int(min(2, max(1, size)))}

    if tool_name == "apply_curves":
        if "points" in normalized:
            points = normalized["points"]
            if isinstance(points, list) and len(points) >= 5:
                try:
                    return {
                        "shadows": (points[0][1] - 0) * 2,
                        "midtones": (points[2][1] - 128) / 2,
                        "highlights": (points[4][1] - 255) * 2
                    }
                except:
                    pass
        return {
            "shadows": normalized.get("shadows", 0),
            "midtones": normalized.get("midtones", 0),
            "highlights": normalized.get("highlights", 0)
        }

    if tool_name == "apply_vignette":
        strength = normalized.get("strength") or normalized.get("amount") or normalized.get("intensity") or 0.4
        radius = normalized.get("radius") or normalized.get("feather") or normalized.get("feathers") or normalized.get("size") or 0.75
        strength = float(strength)
        if strength > 1.0:
            strength = strength / 100.0
        radius = float(radius)
        if radius > 1.0:
            radius = radius / 100.0
        strength = min(0.6, strength)  # SAFETY CAP
        radius = min(0.9, max(0.4, radius))
        return {"strength": strength, "radius": radius}

    if tool_name == "apply_glow":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.2
        radius = normalized.get("radius") or normalized.get("size") or 21
        intensity = min(0.35, float(intensity))
        radius = int(radius)
        if radius % 2 == 0:
            radius += 1
        return {"intensity": float(intensity), "radius": radius}

    if tool_name == "apply_split_toning":
        result = {
            "shadow_hue": 220,
            "shadow_sat": 0.25,
            "highlight_hue": 40,
            "highlight_sat": 0.2
        }

        if "shadow_color" in normalized:
            color = normalized["shadow_color"]
            if isinstance(color, list) and len(color) >= 3:
                result["shadow_hue"] = rgb_to_hue(color)
                result["shadow_sat"] = 0.3

        if "highlight_color" in normalized:
            color = normalized["highlight_color"]
            if isinstance(color, list) and len(color) >= 3:
                result["highlight_hue"] = rgb_to_hue(color)
                result["highlight_sat"] = 0.3

        for key in ["shadow_hue", "shadows_hue", "shadow_h"]:
            if key in normalized:
                result["shadow_hue"] = float(normalized[key])
                break

        for key in ["highlight_hue", "highlights_hue", "highlight_h"]:
            if key in normalized:
                result["highlight_hue"] = float(normalized[key])
                break

        for key in ["shadow_sat", "shadow_saturation", "shadows_sat", "shadow_s"]:
            if key in normalized:
                result["shadow_sat"] = float(normalized[key])
                break

        for key in ["highlight_sat", "highlight_saturation", "highlights_sat", "highlight_s"]:
            if key in normalized:
                result["highlight_sat"] = float(normalized[key])
                break

        if "shadows" in normalized and isinstance(normalized["shadows"], dict):
            sh = normalized["shadows"]
            if "hue" in sh:
                result["shadow_hue"] = float(sh["hue"])
            if "sat" in sh or "saturation" in sh:
                result["shadow_sat"] = float(sh.get("sat") or sh.get("saturation"))

        if "highlights" in normalized and isinstance(normalized["highlights"], dict):
            hl = normalized["highlights"]
            if "hue" in hl:
                result["highlight_hue"] = float(hl["hue"])
            if "sat" in hl or "saturation" in hl:
                result["highlight_sat"] = float(hl.get("sat") or hl.get("saturation"))

        return result

    if tool_name == "apply_duotone":
        dark = normalized.get("dark_color") or normalized.get("shadow_color") or normalized.get("color1") or [20, 0, 80]
        light = normalized.get("light_color") or normalized.get("highlight_color") or normalized.get("color2") or [255, 200, 100]
        if isinstance(dark, list):
            dark = tuple(dark[:3])
        if isinstance(light, list):
            light = tuple(light[:3])
        return {"dark_color": dark, "light_color": light}

    if tool_name == "apply_haze":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.15
        color = normalized.get("color") or [200, 180, 160]
        if isinstance(color, list):
            color = tuple(color[:3])
        return {"amount": float(amount), "color": color}

    if tool_name == "apply_film_fade":
        fade = normalized.get("fade_amount") or normalized.get("amount") or normalized.get("fade") or 0.25
        black = normalized.get("black_fade") or normalized.get("black") or normalized.get("matte") or 0.1
        return {"fade_amount": float(fade), "black_fade": float(black)}

    if tool_name == "apply_clarity":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.3
        return {"amount": float(amount)}

    if tool_name == "apply_dehaze":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.4
        return {"amount": float(amount)}

    if tool_name == "apply_orton_effect":
        blur = normalized.get("blur_amount") or normalized.get("blur") or normalized.get("radius") or 25
        blend = normalized.get("blend") or normalized.get("amount") or normalized.get("strength") or 0.25
        blur = int(blur)
        if blur % 2 == 0:
            blur += 1
        return {"blur_amount": blur, "blend": float(blend)}

    if tool_name == "apply_cross_process":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.4
        return {"intensity": float(intensity)}

    if tool_name == "apply_bleach_bypass":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.4
        return {"intensity": float(intensity)}

    if tool_name == "apply_teal_and_orange":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.5
        return {"intensity": float(intensity)}

    if tool_name == "apply_lut_color_grade":
        style = normalized.get("style") or normalized.get("lut") or normalized.get("name") or "neutral"
        return {"style": str(style)}

    return normalized


def apply_panel_to_image(image: np.ndarray, params: Dict, toolbox: Dict) -> np.ndarray:
    """
    Apply editing parameters to an image.
    Only applies tools that are explicitly in the params.
    """
    img = image.copy()
    clamped_params = clamp_params(params)

    safe_tools = [
        "adjust_exposure",
        "adjust_contrast",
        "adjust_highlights",
        "adjust_shadows",
        "adjust_whites",
        "adjust_blacks",
        "adjust_temp_tint",
        "adjust_saturation",
        "adjust_vibrance",
        "adjust_color_mixer"
    ]

    for tool_name in safe_tools:
        if tool_name in toolbox:
            tool_func = toolbox[tool_name]
            tool_params = clamped_params.get(tool_name, {})
            try:
                img = tool_func(img, **tool_params)
            except Exception as e:
                print(f"ERROR applying {tool_name}: {e}")

    advanced_tools = [
        "apply_split_toning",
        "apply_color_overlay",
        "apply_curves",
        "apply_vignette",
        "apply_glow",
        "apply_grain",
        "apply_duotone",
        "apply_haze",
        "apply_film_fade",
        "apply_clarity",
        "apply_dehaze",
        "apply_orton_effect",
        "apply_cross_process",
        "apply_bleach_bypass",
        "apply_teal_and_orange",
        "apply_lut_color_grade",
        "apply_style_preset"
    ]

    for tool_name in advanced_tools:
        if tool_name in params and tool_name in toolbox:
            tool_func = toolbox[tool_name]
            raw_params = params[tool_name]
            tool_params = normalize_tool_params(tool_name, raw_params)

            if tool_name == "apply_style_preset":
                style = tool_params.get("style", "")
                if not style or style == "none":
                    continue

            if not tool_params:
                continue

            try:
                print(f"  ✓ Applying {tool_name}: {tool_params}")
                img = tool_func(img, **tool_params)
            except Exception as e:
                print(f"  ✗ ERROR applying {tool_name}: {e}")

    return img



@web_app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "PhotoArtAgent API",
        "version": "2.0",
        "description": "AI-powered photo editing with iterative refinement",
        "endpoints": {
            "upload": "POST /upload (file + prompt) - Upload image and set editing goal",
            "generate": "POST /generate/{session_id} - Start first iteration",
            "iterate": "POST /iterate/{session_id} - Continue iterating (optional: base_filename)",
            "session": "GET /session/{session_id} - Get session info",
            "semantic_init": "POST /semantic/init/{session_id} - Analyze semantic axes",
            "semantic_edit": "POST /semantic/edit/{session_id} - Apply semantic edits"
        },  
        "style_presets": [
            "noir", "neo_noir", "dark_noir",
            "night", "deep_night", "blue_hour", "midnight",
            "cyberpunk", "neon", "synthwave", "blade_runner",
            "moody_blue", "moody_dark", "atmospheric", "dramatic",
            "vintage_film", "vintage", "retro_70s", "polaroid", "kodachrome",
            "cinematic_teal_orange", "cinematic", "blockbuster", "indie_film",
            "golden_hour", "morning_light", "sunrise", "sunset", "warm_glow", "magic_hour",
            "black_and_white", "high_contrast_bw", "film_noir_bw", "silver",
            "dream", "ethereal", "horror", "western", "underwater"
        ]
    }


@web_app.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    """Upload an image and set the editing goal."""
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(MOUNT_PATH, session_id)
    os.makedirs(session_dir, exist_ok=True)

    file_path = os.path.join(session_dir, "original.jpg")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if not prompt or len(prompt.strip()) == 0:
        raise HTTPException(400, "Prompt cannot be empty")

    session_state[session_id] = {
        "original_path": file_path,
        "current_path": file_path,
        "history": [],
        "iteration_count": 0,
        "prompt": prompt.strip(),
        "semantic_axes": None,
        "output_base": session_dir
    }

    image_volume.commit()

    return {
        "session_id": session_id,
        "message": "Upload successful",
        "prompt": prompt.strip(),
        "image_path": file_path
    }


@web_app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session."""
    if session_id not in session_state:
        raise HTTPException(404, "Session not found")

    sess = dict(session_state[session_id])

    return {
        "session_id": session_id,
        "prompt": sess.get("prompt"),
        "iteration_count": sess.get("iteration_count", 0),
        "max_iterations": MAX_ITERATIONS,
        "has_semantic_axes": sess.get("semantic_axes") is not None,
        "current_image": f"/images/{session_id}/{os.path.basename(sess['current_path'])}",
        "history": [
            {
                "iteration": idx + 1,
                "reason": h.get("reason", "")[:200],
                "image": f"/images/{session_id}/{os.path.basename(h.get('image_path', ''))}"
            }
            for idx, h in enumerate(sess.get("history", []))
        ]
    }


@web_app.post("/generate/{session_id}")
async def start_generation(session_id: str):
    """Start the first iteration of editing."""
    if session_id not in session_state:
        raise HTTPException(404, "Session not found")

    sess = dict(session_state[session_id])

    if not sess.get("prompt"):
        raise HTTPException(400, "No prompt found for this session")

    sess["iteration_count"] = 0
    sess["history"] = []
    sess["current_path"] = sess["original_path"]
    session_state[session_id] = sess

    return await run_iteration_logic(session_id)


@web_app.post("/iterate/{session_id}")
async def iterate(session_id: str, base_filename: Optional[str] = Form(None)):
    """Continue iterating on the current edit."""
    if session_id not in session_state:
        raise HTTPException(404, "Session not found")

    sess = dict(session_state[session_id])

    if base_filename:
        new_path = os.path.join(sess["output_base"], base_filename)
        if not os.path.exists(new_path):
            raise HTTPException(400, f"Base image not found: {base_filename}")
        sess["current_path"] = new_path
        session_state[session_id] = sess

    if sess["iteration_count"] >= MAX_ITERATIONS:
        filename = os.path.basename(sess["current_path"])
        return {
            "status": "done",
            "message": "Max iterations reached",
            "image_url": f"/images/{session_id}/{filename}",
            "iteration": sess["iteration_count"]
        }

    return await run_iteration_logic(session_id)


async def run_iteration_logic(session_id: str):
    """Core iteration logic - calls AI and applies edits."""
    import sys
    sys.path.insert(0, "/root/app")
    import openrouter_agent

    try:
        from edit_examples import find_matching_examples, get_example_prompt_addition
        HAS_EXAMPLES = True
    except ImportError:
        HAS_EXAMPLES = False

    sess = dict(session_state[session_id])
    current_iter = sess["iteration_count"] + 1
    is_first = (current_iter == 1)

    print(f"\n{'='*60}")
    print(f"🎨 Session: {session_id[:8]}...")
    print(f"📸 Iteration: {current_iter}/{MAX_ITERATIONS}")
    print(f"💬 Prompt: {sess['prompt']}")
    print(f"{'='*60}")

    preview_path = make_vlm_preview(sess["original_path"], width=VLM_PREVIEW_WIDTH)
    vlm_path = preview_path if preview_path else sess["original_path"]

    response_json = openrouter_agent.get_next_step(
        sess["prompt"],
        vlm_path,
        sess["history"],
        iteration=current_iter,
        is_first=is_first
    )

    params = response_json.get("parameters", {})
    reason = response_json.get("reason", "")
    status = response_json.get("status", "in_progress")

    basic_tools = [k for k in params.keys() if k.startswith("adjust_")]
    creative_tools = [k for k in params.keys() if k.startswith("apply_")]
    print(f"📊 Basic tools: {len(basic_tools)} | Creative tools: {creative_tools if creative_tools else 'none'}")

    if is_first:
        base_image = cv2.imread(sess["original_path"])
    else:
        prev_path = sess["current_path"]
        if os.path.exists(prev_path):
            base_image = cv2.imread(prev_path)
            print(f"🔄 Building on previous iteration")
        else:
            base_image = cv2.imread(sess["original_path"])
            print(f"⚠️ Previous not found, using original")

    if base_image is None:
        raise HTTPException(500, "Failed to read image for editing")

    toolbox = get_toolbox()
    new_image = apply_panel_to_image(base_image, params, toolbox)

    filename = f"{current_iter:02d}_final.jpg"
    save_path = os.path.join(sess["output_base"], filename)
    cv2.imwrite(save_path, new_image)
    image_volume.commit()

    result_preview = make_vlm_preview(save_path, width=VLM_PREVIEW_WIDTH)
    result_preview_path = result_preview if result_preview else save_path

    sess["iteration_count"] = current_iter
    sess["current_path"] = save_path
    sess["history"].append({
        "parameters": params,
        "image_path": result_preview_path,
        "reason": reason
    })
    session_state[session_id] = sess

    return {
        "status": "success",
        "iteration": current_iter,
        "reason": reason,
        "image_url": f"/images/{session_id}/{filename}",
        "parameters": params,
        "ai_status": status,
        "can_continue": current_iter < MAX_ITERATIONS and status != "satisfactory"
    }


@web_app.post("/semantic/init/{session_id}")
async def semantic_init(session_id: str):
    """Initialize semantic editing mode by analyzing the image for editing axes."""
    if session_id not in session_state:
        raise HTTPException(404, "Session not found")

    import sys
    sys.path.insert(0, "/root/app")
    import semantic_editor

    sess = dict(session_state[session_id])

    print(f"\n🎨 Analyzing image for semantic axes...")
    print(f"Session: {session_id[:8]}...")

    axes_info = semantic_editor.analyze_image_axes(
        sess["current_path"],
        user_prompt=sess.get("prompt", None)
    )

    sess["semantic_axes"] = axes_info
    session_state[session_id] = sess

    return axes_info


@web_app.post("/semantic/edit/{session_id}")
async def semantic_edit(session_id: str, request: SemanticEditRequest):
    """Apply semantic edits based on axis coordinates."""
    if session_id not in session_state:
        raise HTTPException(404, "Session not found")

    import sys
    sys.path.insert(0, "/root/app")
    import semantic_editor

    sess = dict(session_state[session_id])
    if not sess["semantic_axes"]:
        raise HTTPException(400, "Semantic mode not initialized. Call /semantic/init first.")

    base_image_path = sess["current_path"]
    if request.base_filename:
        user_path = os.path.join(sess["output_base"], request.base_filename)
        if not os.path.exists(user_path):
            raise HTTPException(400, f"Semantic base image not found: {request.base_filename}")
        base_image_path = user_path

    axis_vals = []
    for axis in sess["semantic_axes"]["axes"]:
        axis_vals.append(request.coordinates.get(axis["name"], 0.0))

    print(f"\n🎨 Applying semantic edit...")
    print(f"Session: {session_id[:8]}...")
    print(f"Coordinates: {request.coordinates}")

    params = semantic_editor.convert_coordinates_to_params(axis_vals, sess["semantic_axes"])

    filename = f"semantic_{uuid.uuid4().hex[:6]}.jpg"
    out_path = os.path.join(sess["output_base"], filename)

    semantic_editor.apply_params_to_image(base_image_path, params, out_path)
    image_volume.commit()

    return {
        "image_url": f"/images/{session_id}/{filename}",
        "used_params": params,
        "base_image_used": os.path.basename(base_image_path)
    }



@app.function(
    image=full_image,
    secrets=[
        modal.Secret.from_name("openrouter-api"),
        modal.Secret.from_name("cloudinary-secret"),
    ],
    volumes={MOUNT_PATH: image_volume},
    timeout=600,
    gpu="T4",
    cpu=4.0,
    memory=8192,
    allow_concurrent_inputs=10,
    min_containers=0,
)
@modal.asgi_app()
def fastapi_app():
    os.makedirs(MOUNT_PATH, exist_ok=True)

    if os.path.exists(MOUNT_PATH):
        web_app.mount("/images", StaticFiles(directory=MOUNT_PATH), name="images")

    return web_app



if __name__ == "__main__":
    import uvicorn

    os.makedirs("./data", exist_ok=True)
    MOUNT_PATH = "./data"

    uvicorn.run(web_app, host="0.0.0.0", port=8000)
