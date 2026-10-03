import cv2
import os
import shutil
import json
from pathlib import Path
import openrouter_agent
import opencv_tools
import torch
import time

if torch.cuda.is_available():
    print(f" GPU available: {torch.cuda.get_device_name(0)}")
else:
    print(" Running on CPU (GPU not available)")

USER_PROMPT = '''make it noir'''
USER_PROMPT_COPY=USER_PROMPT

INPUT_IMAGE_PATH = "images/kid.jpg"
OUTPUT_DIR = "images/output"
MAX_ITERATIONS = 5
VLM_PREVIEW_WIDTH = 256


direct_mode = input(" Enter Semantic Editor directly? (y/n): ").strip().lower()

if direct_mode == "y":
    try:
        import semantic_editor

        print("\n Launching Semantic Editor...")
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        final_semantic = semantic_editor.interactive_semantic_editor(
            final_image_path=INPUT_IMAGE_PATH,
            output_dir=OUTPUT_DIR,prompt=USER_PROMPT_COPY,
        )

        print(f"\n Final semantic output: {final_semantic}")
        print("\n Processing complete.")
        exit(0)

    except Exception as e:
        print(" Failed to launch Semantic Editor:", e)
        exit(1)



TOOLBOX = {
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

if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

original_copy_path = os.path.join(OUTPUT_DIR, "00_original.jpg")
shutil.copy(INPUT_IMAGE_PATH, original_copy_path)
original_image = cv2.imread(original_copy_path)

if original_image is None:
    raise RuntimeError(f"Could not read original image at {original_copy_path}")


def make_vlm_preview(path, width=224):
    img = cv2.imread(path)
    if img is None:
        raise RuntimeError(f"Could not read image at {path}")
    h, w = img.shape[:2]
    if w <= width:
        preview = img
    else:
        scale = width / w
        preview = cv2.resize(img, (width, int(h * scale)), interpolation=cv2.INTER_AREA)
    root, ext = os.path.splitext(path)
    preview_path = f"{root}_preview{ext}"
    cv2.imwrite(preview_path, preview)
    return preview_path


vlm_preview_path = make_vlm_preview(original_copy_path, width=VLM_PREVIEW_WIDTH)

history = []


def clamp(value, mn, mx):
    try:
        return max(mn, min(mx, float(value)))
    except:
        return mn


def clamp_params(params):
    def _c(val, mn, mx):
        try:
            return max(mn, min(mx, float(val)))
        except:
            return mn

    mixer = params.get("adjust_color_mixer", {})
    new_mixer = {}
    for ch in ["red", "orange", "yellow", "green", "cyan", "blue", "purple"]:
        cfg = mixer.get(ch, {})
        if not isinstance(cfg, dict):
            cfg = {}

        hue = int(_c(cfg.get("hue_shift", 0), -20, 20))   
        sat = _c(cfg.get("sat_scale", 1.0), 0.5, 1.8)     
        lum = _c(cfg.get("lum_scale", 1.0), 0.7, 1.3)     
        new_mixer[ch] = {"hue_shift": hue, "sat_scale": sat, "lum_scale": lum}
    params["adjust_color_mixer"] = new_mixer


    if "adjust_exposure" in params:
        exp = params["adjust_exposure"]
        val = exp.get("value", 0.0) if isinstance(exp, dict) else exp
        params["adjust_exposure"] = {"value": _c(val, -35, 15)}  
    else:
        params["adjust_exposure"] = {"value": 0.0}

    if "adjust_contrast" in params:
        con = params["adjust_contrast"]
        val = con.get("value", 1.0) if isinstance(con, dict) else con
        params["adjust_contrast"] = {"value": _c(val, 0.85, 1.35)}  
    else:
        params["adjust_contrast"] = {"value": 1.0}

    if "adjust_highlights" in params:
        hl = params["adjust_highlights"]
        val = hl.get("value", 0.0) if isinstance(hl, dict) else hl
        params["adjust_highlights"] = {"value": _c(val, -35, 10)} 
    else:
        params["adjust_highlights"] = {"value": 0.0}

    if "adjust_shadows" in params:
        sh = params["adjust_shadows"]
        val = sh.get("value", 0.0) if isinstance(sh, dict) else sh
        params["adjust_shadows"] = {"value": _c(val, -25, 35)}  
    else:
        params["adjust_shadows"] = {"value": 0.0}

    if "adjust_whites" in params:
        wh = params["adjust_whites"]
        val = wh.get("value", 0.0) if isinstance(wh, dict) else wh
        params["adjust_whites"] = {"value": _c(val, -25, 8)}  
    else:
        params["adjust_whites"] = {"value": 0.0}

    if "adjust_blacks" in params:
        bl = params["adjust_blacks"]
        val = bl.get("value", 0.0) if isinstance(bl, dict) else bl
        params["adjust_blacks"] = {"value": _c(val, -20, 15)}
    else:
        params["adjust_blacks"] = {"value": 0.0}

    if "adjust_temp_tint" in params:
        tt = params["adjust_temp_tint"]
        if isinstance(tt, dict):
            t_val = _c(tt.get("temp", 0.0), -70, 70)  
            tint_val = _c(tt.get("tint", 0.0), -25, 25)
            params["adjust_temp_tint"] = {"temp": t_val, "tint": tint_val}
        else:
            params["adjust_temp_tint"] = {"temp": 0.0, "tint": 0.0}
    else:
        params["adjust_temp_tint"] = {"temp": 0.0, "tint": 0.0}

    if "adjust_saturation" in params:
        sat = params["adjust_saturation"]
        val = sat.get("scale", 1.0) if isinstance(sat, dict) else sat
        params["adjust_saturation"] = {"scale": _c(val, 0.6, 1.4)}
    else:
        params["adjust_saturation"] = {"scale": 1.0}

    if "adjust_vibrance" in params:
        vib = params["adjust_vibrance"]
        val = vib.get("strength", 0.0) if isinstance(vib, dict) else vib
        params["adjust_vibrance"] = {"strength": _c(val, 0.0, 0.8)}
    else:
        params["adjust_vibrance"] = {"strength": 0.0}

    return params


def rgb_to_hue(rgb):
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


def normalize_tool_params(tool_name, tool_params):

    if isinstance(tool_params, str):
        if tool_name == "apply_style_preset":
            return {"style": tool_params}
        elif tool_name == "apply_grain":
            try:
                return {"amount": float(tool_params)}
            except:
                return {"amount": 0.1}
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
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.1
        amount = float(amount)
        if amount > 1.0:
            amount = amount / 100.0  
        size = normalized.get("size", 1)
        amount = min(0.1, amount)
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
        strength = normalized.get("strength") or normalized.get("amount") or normalized.get("intensity") or 0.5
        radius = normalized.get("radius") or normalized.get("feather") or normalized.get("feathers") or normalized.get("size") or 0.8
        strength = float(strength)
        if strength > 1.0:
            strength = strength / 100.0  
        radius = float(radius)
        if radius > 1.0:
            radius = radius / 100.0

            radius = radius / 100.0
        strength = min(0.6, strength)
        radius = min(0.9, max(0.4, radius))
        return {"strength": strength, "radius": radius}


    if tool_name == "apply_glow":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.3
        radius = normalized.get("radius") or normalized.get("size") or 21
        intensity = min(0.35, float(intensity))
        radius = int(radius)
        if radius % 2 == 0:
            radius += 1
        return {"intensity": float(intensity), "radius": radius}


    if tool_name == "apply_split_toning":
        result = {
            "shadow_hue": 220,
            "shadow_sat": 0.3,
            "highlight_hue": 40,
            "highlight_sat": 0.2
        }

        if "shadow_color" in normalized:
            color = normalized["shadow_color"]
            if isinstance(color, list) and len(color) >= 3:
                result["shadow_hue"] = rgb_to_hue(color)
                result["shadow_sat"] = 0.4  

        if "highlight_color" in normalized:
            color = normalized["highlight_color"]
            if isinstance(color, list) and len(color) >= 3:
                result["highlight_hue"] = rgb_to_hue(color)
                result["highlight_sat"] = 0.4

        if "shadow_hue" in normalized:
            result["shadow_hue"] = float(normalized["shadow_hue"])
        if "shadows_hue" in normalized:
            result["shadow_hue"] = float(normalized["shadows_hue"])
        if "shadow_h" in normalized:
            result["shadow_hue"] = float(normalized["shadow_h"])

        if "highlight_hue" in normalized:
            result["highlight_hue"] = float(normalized["highlight_hue"])
        if "highlights_hue" in normalized:
            result["highlight_hue"] = float(normalized["highlights_hue"])
        if "highlight_h" in normalized:
            result["highlight_hue"] = float(normalized["highlight_h"])

        if "shadow_sat" in normalized:
            result["shadow_sat"] = float(normalized["shadow_sat"])
        if "shadow_saturation" in normalized:
            result["shadow_sat"] = float(normalized["shadow_saturation"])
        if "shadows_sat" in normalized:
            result["shadow_sat"] = float(normalized["shadows_sat"])
        if "shadow_s" in normalized:
            result["shadow_sat"] = float(normalized["shadow_s"])

        if "highlight_sat" in normalized:
            result["highlight_sat"] = float(normalized["highlight_sat"])
        if "highlight_saturation" in normalized:
            result["highlight_sat"] = float(normalized["highlight_saturation"])
        if "highlights_sat" in normalized:
            result["highlight_sat"] = float(normalized["highlights_sat"])
        if "highlight_s" in normalized:
            result["highlight_sat"] = float(normalized["highlight_s"])

        if "shadows" in normalized and isinstance(normalized["shadows"], dict):
            sh = normalized["shadows"]
            if "hue" in sh:
                result["shadow_hue"] = float(sh["hue"])
            if "sat" in sh or "saturation" in sh:
                result["shadow_sat"] = float(sh.get("sat") or sh.get("saturation"))
            if "color" in sh and isinstance(sh["color"], list):
                result["shadow_hue"] = rgb_to_hue(sh["color"])

        if "highlights" in normalized and isinstance(normalized["highlights"], dict):
            hl = normalized["highlights"]
            if "hue" in hl:
                result["highlight_hue"] = float(hl["hue"])
            if "sat" in hl or "saturation" in hl:
                result["highlight_sat"] = float(hl.get("sat") or hl.get("saturation"))
            if "color" in hl and isinstance(hl["color"], list):
                result["highlight_hue"] = rgb_to_hue(hl["color"])

        return result


    if tool_name == "apply_duotone":
        dark = normalized.get("dark_color") or normalized.get("shadow_color") or normalized.get("color1") or normalized.get("dark") or [20, 0, 80]
        light = normalized.get("light_color") or normalized.get("highlight_color") or normalized.get("color2") or normalized.get("light") or [255, 200, 100]

        if isinstance(dark, list):
            dark = tuple(dark[:3])
        if isinstance(light, list):
            light = tuple(light[:3])

        return {"dark_color": dark, "light_color": light}


    if tool_name == "apply_haze":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.2
        color = normalized.get("color") or [200, 180, 160]
        if isinstance(color, list):
            color = tuple(color[:3])
        return {"amount": float(amount), "color": color}

    if tool_name == "apply_color_overlay":
        color = normalized.get("color") or [255, 100, 50]
        opacity = normalized.get("opacity") or normalized.get("amount") or normalized.get("strength") or 0.2
        blend = normalized.get("blend_mode") or normalized.get("mode") or normalized.get("blend") or "overlay"
        if isinstance(color, list):
            color = tuple(color[:3])
        return {"color": color, "opacity": float(opacity), "blend_mode": str(blend)}



    if tool_name == "apply_film_fade":
        fade = normalized.get("fade_amount") or normalized.get("amount") or normalized.get("fade") or 0.3
        black = normalized.get("black_fade") or normalized.get("black") or normalized.get("matte") or 0.15
        return {"fade_amount": float(fade), "black_fade": float(black)}

    if tool_name == "apply_clarity":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.5
        return {"amount": float(amount)}

    if tool_name == "apply_dehaze":
        amount = normalized.get("amount") or normalized.get("strength") or normalized.get("intensity") or 0.5
        return {"amount": float(amount)}

    if tool_name == "apply_orton_effect":
        blur = normalized.get("blur_amount") or normalized.get("blur") or normalized.get("radius") or 25
        blend = normalized.get("blend") or normalized.get("amount") or normalized.get("strength") or 0.3
        blur = int(blur)
        if blur % 2 == 0:
            blur += 1
        return {"blur_amount": blur, "blend": float(blend)}

    if tool_name == "apply_cross_process":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.5
        return {"intensity": float(intensity)}

    if tool_name == "apply_bleach_bypass":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.5
        return {"intensity": float(intensity)}

    if tool_name == "apply_teal_and_orange":
        intensity = normalized.get("intensity") or normalized.get("amount") or normalized.get("strength") or 0.5
        return {"intensity": float(intensity)}

    if tool_name == "apply_lut_color_grade":
        style = normalized.get("style") or normalized.get("lut") or normalized.get("name") or "neutral"
        return {"style": str(style)}

    return normalized


def apply_panel_to_original(orig_img, panel):

    img = orig_img.copy()
    params = clamp_params(panel)


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
        if tool_name in TOOLBOX:
            tool_func = TOOLBOX[tool_name]
            tool_params = params.get(tool_name, {})
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
        if tool_name in params and tool_name in TOOLBOX:
            tool_func = TOOLBOX[tool_name]
            raw_params = params[tool_name]

            tool_params = normalize_tool_params(tool_name, raw_params)

            if tool_name == "apply_style_preset":
                style = tool_params.get("style", "")
                if not style or style == "none":
                    continue

            if not tool_params:
                continue

            try:
                print(f"   Applying {tool_name}: {tool_params}")
                img = tool_func(img, **tool_params)
            except Exception as e:
                print(f"   ERROR applying {tool_name}: {e}")

    return img



print(f" PhotoArtAgent Starting")
print(f" Goal: '{USER_PROMPT.strip()}'")
print(f" Input: {INPUT_IMAGE_PATH}")
print(f" Output: {OUTPUT_DIR}")

final_out = None

for i in range(1, MAX_ITERATIONS + 1):
    print(f" ITERATION {i}/{MAX_ITERATIONS}")
    start_time = time.time()

    try:
        response_json = openrouter_agent.get_next_step(
            USER_PROMPT,
            vlm_preview_path,
            history,
            iteration=i,
            is_first=(i == 1)
        )
    except Exception as e:
        print(f" ERROR calling agent: {e}")
        break

    if not isinstance(response_json, dict):
        print(" Agent response not a dict, aborting.")
        break

    with open(os.path.join(OUTPUT_DIR, f"response_{i:02d}.json"), "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=2)

    status = response_json.get("status", "in_progress")
    params = response_json.get("parameters")
    reason = response_json.get("reason", "No reason provided")

    print(f" Status: {status}")
    print(f" Reason: {reason}")

    if params is None:
        print(" Agent missing parameters → neutral panel used.")
        params = clamp_params({})
    else:
        basic_tools = [k for k in params.keys() if k.startswith("adjust_")]
        creative_tools = [k for k in params.keys() if k.startswith("apply_")]
        print(f" Basic tools: {len(basic_tools)} | Creative tools: {creative_tools if creative_tools else 'none'}")


        for ct in creative_tools:
            print(f"   → {ct}: {params[ct]}")

    if i == 1:
        base_image = original_image
    else:
        prev_path = os.path.join(OUTPUT_DIR, f"{i-1:02d}_final.jpg")
        if os.path.exists(prev_path):
            base_image = cv2.imread(prev_path)
            print(f" Building on iteration {i-1}")
        else:
            base_image = original_image
            print(f" Warning: Previous iteration not found, using original")

    current_image = apply_panel_to_original(base_image, params)

    out_path = os.path.join(OUTPUT_DIR, f"{i:02d}_final.jpg")
    cv2.imwrite(out_path, current_image)
    print(f" Saved: {out_path}")

    latest_preview = make_vlm_preview(out_path, width=VLM_PREVIEW_WIDTH)

    history.append({
        "parameters": params,
        "image_path": latest_preview,
        "reason": response_json.get("reason", "")
    })

    final_out = out_path

    end_time = time.time()
    print(f"  Iteration time: {end_time - start_time:.2f}s")

    if i < MAX_ITERATIONS:
        print(f"\n CHECKPOINT:")
        user_input = input(f"   Are you satisfied with iteration {i}? (y/n): ").strip().lower()

        if user_input == "y":
            print(" Human approved, stopping early.")
            break
    else:
        print("\n Reached maximum iterations")


print(" MAIN ITERATIONS COMPLETE")
print(f" Final image: {final_out}")
print(f" Output folder: {OUTPUT_DIR}")

print("\n SEMANTIC EDITOR MODE")
print("Edit your photo using intuitive semantic axes like:")
print("  • Warm-Cool (color temperature)")
print("  • Vibrant-Muted (color intensity)")
print("  • Dramatic-Soft (contrast & mood)")
print("  • Happy-Gloomy (overall atmosphere)")
semantic_choice = input("\n Enter Semantic Editor? (y/n): ").strip().lower()

if semantic_choice == 'y':
    try:
        import semantic_editor

        print("\n Available images in output directory:")
        images = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith((".jpg",".png",".jpeg"))]

        for idx, img in enumerate(images, 1):
            print(f"  {idx}. {img}")

        choice = input("\n Enter the number of the image you want to edit: ").strip()

        try:
            choice_idx = int(choice) - 1
            if choice_idx < 0 or choice_idx >= len(images):
                raise ValueError
            selected_image = os.path.join(OUTPUT_DIR, images[choice_idx])
        except:
            print("️ Invalid selection. Defaulting to final image.")
            selected_image = final_out

        print(f"\n Launching semantic editor with: {selected_image}")

        final_semantic = semantic_editor.interactive_semantic_editor(
            final_image_path=selected_image,
            output_dir=OUTPUT_DIR,prompt=USER_PROMPT_COPY
        )

        print(f"\n Final semantic output: {final_semantic}")

    except Exception as e:
        print(f" Semantic editor error: {e}")


        print(f"\n Final semantic output: {final_semantic}")

    except ImportError:
        print("semantic_editor.py not found.")
    except Exception as e:
        print(f" Semantic editor error: {e}")

else:
    print("⏭ Skipping semantic editor")


print(" ALL PROCESSING COMPLETE")
print(f" All outputs saved to: {OUTPUT_DIR}")
print(f" Final image: {final_out}")
