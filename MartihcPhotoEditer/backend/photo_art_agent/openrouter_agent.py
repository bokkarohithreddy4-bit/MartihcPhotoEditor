import os
from dotenv import load_dotenv
load_dotenv()
import json
import time
import urllib.parse
from pathlib import Path
from openai import OpenAI
import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    from edit_examples import get_example_prompt_addition, find_matching_examples
    HAS_EXAMPLES = True
except ImportError:
    HAS_EXAMPLES = False
    print("Warning: edit_examples.py not found, running without few-shot examples")

try:
    import cloudinary
    import cloudinary.uploader
except Exception as exc:
    raise RuntimeError("cloudinary SDK is required. Install with: pip install cloudinary") from exc

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


MODEL_NAME = "google/gemma-3-12b-it"

SAVE_PAYLOADS = True
PAYLOAD_DIR = "payloads_qwen_openrouter"
os.makedirs(PAYLOAD_DIR, exist_ok=True)


cloudinary.config(
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME"),
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY"),
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET"),
    secure=False,
)

CACHE_PATH = os.path.join(PAYLOAD_DIR, "cloudinary_cache.json")
if not os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, "w", encoding="utf8") as f:
        json.dump({}, f)

SYSTEM_PROMPT_FIRST = """You are PhotoArtAgent, an expert photo editor with access to BOTH basic adjustments AND creative effects.

═══════════════════════════════════════════════════════════════════════════════
AVAILABLE TOOLS - Use the RIGHT tool for the job!
═══════════════════════════════════════════════════════════════════════════════

【BASIC ADJUSTMENTS】 - For subtle, natural edits
• adjust_exposure: {"value": -30 to 30} - Brightness control
• adjust_contrast: {"value": 0.8 to 1.4} - Tonal contrast (1.0=neutral)
• adjust_highlights: {"value": -50 to 30} - Bright area control (NEGATIVE to recover)
• adjust_shadows: {"value": -40 to 50} - Dark area control (positive=lift)
• adjust_whites: {"value": -40 to 20} - White point
• adjust_blacks: {"value": -30 to 30} - Black point
• adjust_temp_tint: {"temp": -80 to 80, "tint": -30 to 30}
• adjust_saturation: {"scale": 0.0 to 1.8} - Color intensity (0=B&W)
• adjust_vibrance: {"strength": 0.0 to 1.0} - Boost muted colors
• adjust_color_mixer: Per-channel control

【CREATIVE EFFECTS】 - For dramatic/artistic looks!
• apply_duotone: {"dark_color": [B,G,R], "light_color": [B,G,R]}
• apply_split_toning: {"shadow_hue": 0-360, "shadow_sat": 0-0.5, "highlight_hue": 0-360, "highlight_sat": 0-0.5}
  → Hues: 0=red, 30=orange, 60=yellow, 120=green, 180=cyan, 220=blue, 280=purple
• apply_vignette: {"strength": 0.0-1.0, "radius": 0.4-0.95}
• apply_glow: {"intensity": 0.0-0.5, "radius": 15-51}
• apply_grain: {"amount": 0.0-0.3, "size": 1-3}
• apply_haze: {"amount": 0.0-0.4, "color": [B,G,R]}
• apply_curves: {"shadows": -50 to 50, "midtones": -50 to 50, "highlights": -50 to 50}
• apply_clarity: {"amount": -1.0 to 1.0} - Local contrast
• apply_film_fade: {"fade_amount": 0-1, "black_fade": 0-0.5} - Matte/faded look
• apply_bleach_bypass: {"intensity": 0-1} - Desaturated high contrast
• apply_teal_and_orange: {"intensity": 0-1} - Hollywood color grade
• apply_cross_process: {"intensity": 0-1} - Retro color shifts
• apply_orton_effect: {"blur_amount": 15-45, "blend": 0-0.5} - Dreamy glow

【STYLE PRESETS】 - One-click complete looks! USE THESE FOR SPECIFIC REQUESTS!
apply_style_preset: {"style": "name"}

NOIR STYLES:
• "noir" / "classic_noir" - High contrast B&W, deep shadows, film grain
• "neo_noir" - Modern noir with subtle color, like Sin City/Drive
• "dark_noir" - Extra dark and dramatic noir

NIGHT STYLES:
• "night" - Cool blue tones, dark, moody
• "deep_night" - Very dark night scene
• "blue_hour" - Twilight blue hour atmosphere
• "midnight" - Deep midnight blue

CYBERPUNK / NEON:
• "cyberpunk" - Neon pink/cyan, high contrast, glow
• "neon" - Electric saturated colors with glow
• "synthwave" - 80s retro synthwave aesthetic
• "blade_runner" - Blade Runner inspired, teal/orange, hazy

MOODY STYLES:
• "moody_blue" - Desaturated blue shadows, atmospheric
• "moody_dark" - Dark and moody with color
• "atmospheric" - Hazy, atmospheric feel
• "dramatic" - High contrast, strong vignette

VINTAGE / RETRO:
• "vintage_film" / "vintage" - Faded, warm, grainy film
• "retro_70s" - 70s film aesthetic
• "polaroid" - Instant polaroid look
• "kodachrome" - Classic Kodachrome film simulation

CINEMATIC:
• "cinematic_teal_orange" / "cinematic" - Hollywood teal/orange
• "blockbuster" - Modern blockbuster movie look
• "indie_film" - Muted indie film aesthetic

GOLDEN / WARM:
• "golden_hour" - Warm sunset golden light
• "morning_light" - Soft cool morning sun
• "sunrise" - Early sunrise pink/orange tones
• "sunset" - Dramatic warm sunset
• "warm_glow" - Soft warm dreamy glow
• "magic_hour" - Magical hour atmosphere

BLACK & WHITE:
• "black_and_white" - Clean B&W
• "high_contrast_bw" - Punchy B&W
• "film_noir_bw" - Classic film noir B&W
• "silver" - Bright silvery B&W

SPECIAL:
• "dream" - Dreamy, ethereal
• "ethereal" - Light, airy, magical
• "horror" - Horror movie aesthetic
• "western" - Western movie dusty look
• "underwater" - Underwater blue/green tint

═══════════════════════════════════════════════════════════════════════════════
WHEN USER ASKS FOR THESE → USE STYLE PRESETS!
═══════════════════════════════════════════════════════════════════════════════
• "noir" / "film noir" → {"style": "noir"} or {"style": "neo_noir"}
• "night" / "nighttime" / "dark" → {"style": "night"} or {"style": "deep_night"}
• "cyberpunk" / "neon" / "futuristic" → {"style": "cyberpunk"} or {"style": "neon"}
• "moody" / "blue mood" → {"style": "moody_blue"} or {"style": "moody_dark"}
• "vintage" / "retro" / "old film" → {"style": "vintage_film"} or {"style": "retro_70s"}
• "cinematic" / "movie look" → {"style": "cinematic"} or {"style": "blockbuster"}
• "golden hour" / "warm" / "sunset" → {"style": "golden_hour"} or {"style": "sunset"}
• "morning light" / "morning" / "sunrise" → {"style": "morning_light"} or {"style": "sunrise"}
• "black and white" / "B&W" → {"style": "noir"} or {"style": "black_and_white"}
• "dreamy" / "soft" → {"style": "dream"} or {"style": "ethereal"}
• "horror" / "scary" → {"style": "horror"}

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT - ALWAYS RETURN VALID JSON:
═══════════════════════════════════════════════════════════════════════════════

Use style presets for quick looks. Fine-tune with sliders if needed.

EXAMPLE - Noir request:
{
  "reason": "Applying noir film style - classic B&W with dramatic contrast",
  "parameters": {
    "apply_style_preset": {"style": "noir"},
    "adjust_contrast": {"value": 1.25}
  },
  "status": "in_progress"
}

EXAMPLE - Manual night edit:
{
  "reason": "Creating night scene with blue tones",
  "parameters": {
    "adjust_exposure": {"value": -25},
    "adjust_temp_tint": {"temp": -20, "tint": 0},
    "adjust_saturation": {"scale": 0.85},
    "apply_vignette": {"strength": 0.5, "radius": 0.7}
  },
  "status": "in_progress"
}

CRITICAL RULES:
1. Use apply_style_preset for complete looks (noir, night, cyberpunk, etc.)
2. Style presets already include grain, vignette, contrast - don't duplicate!
3. Keep grain amount under 0.05 (0.03 is subtle, 0.05 is noticeable)
4. Keep vignette strength under 0.6 (0.4 is subtle, 0.6 is strong)
5. Keep contrast under 1.3 (1.1 is subtle, 1.25 is strong)
6. Output ONLY valid JSON - no markdown, no text outside JSON
"""

SYSTEM_PROMPT_ITERATIVE = """You are PhotoArtAgent refining photo edits iteratively.

═══════════════════════════════════════════════════════════════════════════════
YOUR TASK: Compare the current edit to the user's goal and refine it.
═══════════════════════════════════════════════════════════════════════════════

AVAILABLE TOOLS:
【BASIC SLIDERS】
- adjust_exposure: {"value": -100 to 100} (darker < 0 < brighter)
- adjust_contrast: {"value": 0.5 to 1.5} (flat < 1.0 < punchy)
- adjust_highlights: {"value": -100 to 100} (recover/boost bright areas)
- adjust_shadows: {"value": -100 to 100} (lift/crush dark areas)
- adjust_whites: {"value": -100 to 100}
- adjust_blacks: {"value": -100 to 100}
- adjust_temp_tint: {"temp": -100 to 100, "tint": -100 to 100} (cool < 0 < warm)
- adjust_saturation: {"scale": 0.0 to 2.0} (B&W < 1.0 < vivid)
- adjust_vibrance: {"strength": -1.0 to 1.0}

【STYLE PRESETS】 (use for complete looks)
apply_style_preset: {"style": "noir"} - noir, night, cyberpunk, golden_hour, moody_blue, vintage, sunset, dream, horror, etc.

【CREATIVE TOOLS】
- apply_vignette: {"strength": 0.3, "radius": 0.7} (strength 0.2-0.5 is subtle)
- apply_grain: {"amount": 0.03, "size": 1} (KEEP UNDER 0.05!)
- apply_glow: {"intensity": 0.15, "radius": 21}

═══════════════════════════════════════════════════════════════════════════════
SAFE VALUE RANGES (to avoid ugly results):
═══════════════════════════════════════════════════════════════════════════════
• Grain amount: 0.02-0.05 (MAX 0.05, anything higher looks terrible)
• Vignette strength: 0.2-0.5 (MAX 0.6)
• Contrast: 1.05-1.25 (MAX 1.35)
• Saturation: 0.7-1.3 (don't go to extremes)
• Exposure: -30 to 20 (don't over-expose or crush)

═══════════════════════════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════════════════════════
{
  "reason": "What needs to change to get closer to goal",
  "parameters": {
    "adjust_exposure": {"value": 0},
    "adjust_contrast": {"value": 1.0},
    ... (include only parameters you want to adjust)
  },
  "status": "refined" or "satisfactory"
}

Output ONLY valid JSON. No markdown, no text outside the JSON.
"""


def _neutral_block(reason="Neutral parameters returned"):
    return {
        "reason": reason,
        "tools_to_use": [
            "adjust_exposure", "adjust_contrast", "adjust_highlights", "adjust_shadows",
            "adjust_whites", "adjust_blacks", "adjust_temp_tint", "adjust_saturation",
            "adjust_vibrance", "adjust_color_mixer", "apply_style_preset"
        ],
        "parameters": {
            "adjust_exposure": {"value": 0.0},
            "adjust_contrast": {"value": 1.0},
            "adjust_highlights": {"value": 0.0},
            "adjust_shadows": {"value": 0.0},
            "adjust_whites": {"value": 0.0},
            "adjust_blacks": {"value": 0.0},
            "adjust_temp_tint": {"temp": 0.0, "tint": 0.0},
            "adjust_saturation": {"scale": 1.0},
            "adjust_vibrance": {"strength": 0.0},
            "adjust_color_mixer": {
                "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
                "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            },
            "apply_style_preset": {"style": "none"}
        },
        "status": "in_progress"
    }


def _ensure_full_parameters(parsed):
    if "parameters" not in parsed:
        parsed["parameters"] = {}

    params = parsed["parameters"]

    defaults = {
        "adjust_exposure": {"value": 0.0},
        "adjust_contrast": {"value": 1.0},
        "adjust_highlights": {"value": 0.0},
        "adjust_shadows": {"value": 0.0},
        "adjust_whites": {"value": 0.0},
        "adjust_blacks": {"value": 0.0},
        "adjust_temp_tint": {"temp": 0.0, "tint": 0.0},
        "adjust_saturation": {"scale": 1.0},
        "adjust_vibrance": {"strength": 0.0},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
        },
        "apply_style_preset": {"style": "none"}
    }

    for key, default_val in defaults.items():
        if key not in params:
            params[key] = default_val

    if "tools_to_use" not in parsed:
        parsed["tools_to_use"] = list(defaults.keys())

    return parsed


def _load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf8") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def _upload_to_cloudinary(local_path):
    cache = _load_cache()
    lp = str(Path(local_path).resolve()).replace("\\", "/")

    import hashlib
    with open(lp, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()

    cache_key = f"{lp}::{md5}"

    if cache_key in cache:
        return cache[cache_key]

    try:
        res = cloudinary.uploader.upload(
            lp,
            resource_type="image",
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        secure_url = res.get("secure_url")
        if secure_url:
            cache[cache_key] = secure_url
            _save_cache(cache)
            return secure_url
        else:
            raise RuntimeError("Cloudinary upload missing secure_url")
    except Exception:
        return None


def get_analysis(user_prompt, image_path):
    prompt = f"""User goal: "{user_prompt}"

Analyze image and describe editing strategy:
1. Exposure/contrast approach
2. Shadow/highlight treatment
3. Color temperature direction
4. Saturation/vibrance plan
5. Critical areas to preserve
6. Risks to avoid

Output: Plain language strategy (no parameters)."""

    img_url = _upload_to_cloudinary(image_path)
    messages = [
        {"role": "system", "content": "You are an expert photo editing strategist."},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": img_url}}
        ]}
    ]

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        extra_headers={"HTTP-Referer": "https://google.com", "X-Title": "Planner"}
    )
    return resp.choices[0].message.content.strip()


def get_next_step(user_prompt, original_image_path, history, iteration=1, is_first=True):
    print(f"\n Iteration {iteration} - Preparing API call...")

    def to_image_url(p):
        p = str(Path(p).resolve()).replace("\\", "/")
        url = _upload_to_cloudinary(p)
        return url or p

    compact_history = []
    for idx, entry in enumerate(history[-3:], start=max(1, len(history) - 2)):
        compact_history.append({
            "iter": f"{idx:02d}",
            "reason": entry.get("reason", "")[:100],
            "params": {
                k: v for k, v in entry.get("parameters", {}).items()
            }
        })

    examples_text = ""
    if HAS_EXAMPLES and is_first:
        examples = find_matching_examples(user_prompt, max_examples=2)
        if examples:
            print(f" Found {len(examples)} matching examples for few-shot learning")
            examples_text = get_example_prompt_addition(user_prompt)

    if is_first:
        prompt_text = f"Goal: {user_prompt.strip()}\n\n{examples_text}\nAnalyze original image and output initial parameters."
    else:
        prompt_text = f"Goal: {user_prompt.strip()}\n\nPrevious: {json.dumps(compact_history)}\n\nCompare latest result to goal. Output refined parameters."

    print(f" Prompt size: {len(prompt_text)} chars")
    content = [{"type": "text", "text": prompt_text}]

    if is_first:
        orig_url = to_image_url(original_image_path)
        if not (orig_url and orig_url.startswith("http")):
            return _neutral_block("Cloudinary upload failed")

        content.append({"type": "image_url", "image_url": {"url": orig_url}})
        print(f" Images sent: 1 (original only)")

    else:
        orig_url = to_image_url(original_image_path)
        if not (orig_url and orig_url.startswith("http")):
            return _neutral_block("Cloudinary upload failed")

        content.append({"type": "image_url", "image_url": {"url": orig_url}})

        count = 1
        for entry in history:
            ip = entry.get("image_path")
            if ip:
                url = to_image_url(ip)
                if url and url.startswith("http"):
                    content.append({"type": "image_url", "image_url": {"url": url}})
                    count += 1

        print(f" Images sent: {count} (original + {count - 1} previous previews)")

    if SAVE_PAYLOADS:
        ts = int(time.time())
        with open(f"{PAYLOAD_DIR}/payload_{ts}.json", "w") as f:
            json.dump({"iteration": iteration, "prompt": prompt_text, "num_images": len(content) - 1}, f, indent=2)

    try:
        system_prompt = SYSTEM_PROMPT_FIRST if is_first else SYSTEM_PROMPT_ITERATIVE

        print(f" Calling OpenRouter API (system prompt: {len(system_prompt)} chars)...")

        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            extra_headers={
                "HTTP-Referer": "https://google.com",
                "X-Title": "PhotoArtAgent"
            }
        )
        print(f" API call successful")
    except Exception as e:
        print(f"API call failed: {e}")
        return _neutral_block(f"API failed: {e}")

    try:
        raw = resp.choices[0].message.content
        if isinstance(raw, str):
            text = raw.strip()
        elif isinstance(raw, list):
            text = "\n".join([b.get("text", "") for b in raw if b.get("type") == "text"]).strip()
        else:
            return _neutral_block("Unexpected content format")
    except Exception:
        return _neutral_block("Invalid response structure")

    if SAVE_PAYLOADS:
        ts = int(time.time())
        with open(f"{PAYLOAD_DIR}/response_{ts}.txt", "w", encoding="utf-8") as f:
            f.write(text)

    try:
        parsed = json.loads(text)
        print("✓ JSON parsed successfully")

        if "params" in parsed and "parameters" not in parsed:
            print(" Converting 'params' → 'parameters'")
            parsed["parameters"] = parsed.pop("params")

        parsed = _ensure_full_parameters(parsed)
        print(f" Parameters filled: {len(parsed.get('parameters', {}))} tools")

        return parsed

    except json.JSONDecodeError:
        try:
            s = text.find("{")
            e = text.rfind("}") + 1
            if s >= 0 and e > s:
                parsed = json.loads(text[s:e])
                print(" Extracted JSON from text")

                if "params" in parsed and "parameters" not in parsed:
                    parsed["parameters"] = parsed.pop("params")

                parsed = _ensure_full_parameters(parsed)
                return parsed
        except:
            pass

        return _neutral_block("JSON parse failed")
    except Exception as e:
        print(f" Parse error: {e}")
        return _neutral_block(f"Parse error: {e}")



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--orig", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--history", default=None)
    args = parser.parse_args()

    hist = []
    if args.history and os.path.exists(args.history):
        hist = json.load(open(args.history))

    out = get_next_step(args.prompt, args.orig, hist, iteration=len(hist) + 1, is_first=len(hist) == 0)
    print(json.dumps(out, indent=2))
