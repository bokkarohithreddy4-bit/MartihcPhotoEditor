import os
from dotenv import load_dotenv
load_dotenv()
import json
import cv2
from pathlib import Path
from openai import OpenAI


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

MODEL_NAME = "google/gemma-3-12b-it"

try:
    import cloudinary
    import cloudinary.uploader


    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=False,
    )
except:
    print(" Cloudinary not available, using local paths")


def upload_to_cloudinary(local_path):
    try:
        res = cloudinary.uploader.upload(
            local_path,
            resource_type="image",
            use_filename=True,
            unique_filename=False,
            overwrite=True
        )
        return res.get("secure_url")
    except Exception as e:
        print(f"Upload error: {e}")
        return None


def analyze_image_axes(image_path, user_prompt=None):
    print("\nAnalyzing image for semantic axes...")

    img_url = upload_to_cloudinary(image_path)
    if not img_url:
        print(" Cloudinary upload failed, using fallback axes")
        return get_fallback_axes()

    print("Image uploaded successfully, requesting AI analysis...")

    goal_text = ""
    if user_prompt:
        goal_text = f"\nUSER GOAL: \"{user_prompt.strip()}\"\n" \
                    f"You MUST prioritize axes that help achieve THIS goal.\n"


    analysis_prompt = f"""
Analyze the given image AND the user's editing goal to determine the
TWO MOST RELEVANT semantic editing axes from the supported library.

{goal_text}

The chosen axes MUST:
- Address aspects of the image that are most transformable AND
- Move the image closer to the user's intended editing goal.
- Represent two *independent* visual dimensions
  (not overlapping concepts like Bright-Dark + High Key–Low Key).

You MUST choose the axes ONLY from the following VALID AXIS LIBRARY:

COLOR & TONE:
- Vibrant-Muted
- Cool-Warm
- Vintage-Modern

LIGHT & CONTRAST:
- Bright-Dark
- Dramatic-Flat
- High Key–Low Key
- Deep Blacks–Raised Blacks
- Matte-Glossy

MOOD & ATMOSPHERE:
- Gloomy-Happy
- Moody-Airy
- Calm-Energetic
- Dreamy-Crisp
- Ethereal-Realistic

TEXTURE & STYLE:
- Sharp-Soft
- Gritty-Clean
- Punchy-Faded
- Textured-Smooth

CINEMATIC LOOKS:
- Cinematic-Natural
- Cyberpunk-Organic
- Night-Day
- Noir-Colorful
- Neon-Subtle
- Golden Hour-Blue Hour


RULES FOR AXIS SELECTION:
- Select EXACTLY 2 axes.
- Do NOT invent or modify axis names.
- Do NOT pick two axes that describe the same dimension.
- The axes must explain how the image can be MOST EFFECTIVELY changed
  in service of the user's goal.
- Ensure "suitable_synonym_pair" strictly respects the Left (-1.0) vs Right (+1.0) direction.
- CRITICAL: For any axis named "A-B", the Left Pole (-1.0) MUST correspond to "A" and the Right Pole (+1.0) MUST correspond to "B".

FOR EACH AXIS RETURN:
- "name": axis name EXACTLY as listed above (copy-paste it)
- "left_pole": description for -1.0 end. For axis "A-B", this MUST describe "A".
- "right_pole": description for +1.0 end. For axis "A-B", this MUST describe "B".
- "current_position": always 0.0
- "description": why this axis is relevant to this image AND user's goal
- "left_synonym": A simple, creative word for the LEFT pole (first word of axis name)
- "right_synonym": A simple, creative word for the RIGHT pole (second word of axis name)

CRITICAL ORDERING RULE:
- Axis name format is always "LeftConcept-RightConcept"
- "Vibrant-Muted" means: left_pole=Vibrant, right_pole=Muted, left_synonym=Colorful, right_synonym=Faded
- "Gloomy-Happy" means: left_pole=Gloomy, right_pole=Happy, left_synonym=Dark, right_synonym=Cheerful
- NEVER reverse this. The FIRST word is ALWAYS the LEFT pole.

OUTPUT ONLY VALID JSON:
{{
  "axes": [
    {{
      "name": "AxisName",
      "left_pole": "...",
      "right_pole": "...",
      "current_position": 0.0,
      "description": "...",
      "left_synonym": "SimpleWord",
      "right_synonym": "SimpleWord"
    }}
  ]
}}
"""

    try:
        print("Sending request to AI model...")
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert photo analyst and color scientist. "
                               "You must output ONLY valid JSON and nothing else."
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {"type": "image_url", "image_url": {"url": img_url}}
                    ]
                }
            ],
            extra_headers={
                "HTTP-Referer": "https://google.com",
                "X-Title": "SemanticAnalyzer"
            }
        )

        text = resp.choices[0].message.content.strip()

        print(f"Received AI response ({len(text)} chars)")
        print(f"Response preview: {text[:150]}...")


        if text.startswith("```"):
            print("Removing markdown code blocks...")
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()
            print(f"Cleaned text preview: {text[:150]}...")

        result = None
        try:
            result = json.loads(text)
            print(" Direct JSON parse successful")
        except json.JSONDecodeError as e:
            print(f" Direct parse failed: {e}")
            print("Extracting JSON from text...")
            s = text.find("{")
            e = text.rfind("}") + 1
            if s == -1 or e == 0:
                print(f"No JSON object found. Full response:\n{text}")
                raise ValueError("No JSON object found in response")
            json_str = text[s:e]
            print(f"Extracted JSON preview: {json_str[:100]}...")
            result = json.loads(json_str)
            print(" Extracted JSON successfully")

        if 'axes' not in result:
            raise ValueError("Response missing 'axes' field")

        if len(result['axes']) != 2:
            print(f" Expected 2 axes, got {len(result['axes'])}, using fallback")
            return get_fallback_axes()

        for i, axis in enumerate(result['axes']):
            required_fields = ['name', 'left_pole', 'right_pole', 'current_position', 'description']
            for field in required_fields:
                if field not in axis:
                    print(f" Axis {i} missing '{field}', using fallback")
                    return get_fallback_axes()

        print(f" Successfully generated 2 custom axes: {[ax['name'] for ax in result['axes']]}")
        return result

    except Exception as e:
        print(f" Analysis error: {type(e).__name__}: {e}")
        print(" Using fallback axes instead")
        import traceback
        traceback.print_exc()
        return get_fallback_axes()


def get_fallback_axes():
    return {
        "axes": [
            {
                "name": "Warm-Cool",
                "left_pole": "Warm, golden tones",
                "right_pole": "Cool, blue tones",
                "current_position": 0.0,
                "description": "Color temperature"
            },
            {
                "name": "Vibrant-Muted",
                "left_pole": "Rich, saturated colors",
                "right_pole": "Subtle, soft colors",
                "current_position": 0.0,
                "description": "Color intensity"
            },
        ]
    }


def convert_coordinates_to_params(axis_vals, axes_info):
    params = {
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
        }
    }

    for i, axis_val in enumerate(axis_vals):
        name = axes_info["axes"][i]["name"].lower()
        if "golden" in name or "blue" in name:
            if axis_val < 0:
                params["adjust_temp_tint"]["temp"] += 25 * abs(axis_val)
            else:
                params["adjust_temp_tint"]["temp"] -= 25 * axis_val
            continue

        if "deep blacks" in name or "raised blacks" in name:
            if axis_val < 0:
                params["adjust_blacks"]["value"] -= 35 * abs(axis_val)
                params["adjust_contrast"]["value"] *= 1 + 0.10 * abs(axis_val)
            else:
                params["adjust_blacks"]["value"] += 35 * axis_val
                params["adjust_shadows"]["value"] -= 15 * axis_val
            continue

        if "textured" in name or "smooth" in name:
            if axis_val < 0:
                params["adjust_contrast"]["value"] *= 1 + 0.25 * abs(axis_val)
                params["adjust_blacks"]["value"] -= 20 * abs(axis_val)
            else:
                params["adjust_shadows"]["value"] -= 20 * axis_val
                params["adjust_highlights"]["value"] -= 10 * axis_val
            continue

        if "calm" in name or "energetic" in name:
            if axis_val < 0:
                params["adjust_contrast"]["value"] *= 1 - 0.10 * abs(axis_val)
                params["adjust_temp_tint"]["temp"] -= 10 * abs(axis_val)
                params["adjust_saturation"]["scale"] *= 1 - 0.2 * abs(axis_val)
            else:
                params["adjust_exposure"]["value"] += 20 * axis_val
                params["adjust_saturation"]["scale"] *= 1 + 0.25 * axis_val
                params["adjust_contrast"]["value"] *= 1 + 0.10 * axis_val
            continue

        if "warm" in name and "cool" in name:
            params["adjust_temp_tint"]["temp"] += axis_val * 18
            continue

        if "vibrant" in name or "muted" in name:
            params["adjust_saturation"]["scale"] *= (1 - axis_val * 0.4)
            params["adjust_vibrance"]["strength"] += max(0, -axis_val * 0.7)
            continue

        if "bright" in name or "dark" in name:
            params["adjust_exposure"]["value"] += -axis_val * 30
            continue

        if "dramatic" in name or "flat" in name:
            params["adjust_contrast"]["value"] *= (1 - axis_val * 0.4)
            params["adjust_highlights"]["value"] += -axis_val * 20
            params["adjust_shadows"]["value"] -= axis_val * 20
            continue

        if "vintage" in name or "modern" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["adjust_contrast"]["value"] *= (1 - 0.20 * s)
                params["adjust_blacks"]["value"] += 25 * s
                params["adjust_whites"]["value"] -= 15 * s
                params["adjust_temp_tint"]["temp"] += 20 * s
                params["adjust_temp_tint"]["tint"] -= 10 * s
                params["adjust_saturation"]["scale"] *= (1 - 0.25 * s)
                params["adjust_vibrance"]["strength"] -= 0.2 * s
                params["adjust_color_mixer"]["blue"]["hue_shift"] = -10 * s
                params["adjust_color_mixer"]["green"]["hue_shift"] = -5 * s
                continue
            else:
                s = axis_val
                params["adjust_contrast"]["value"] *= (1 + 0.25 * s)
                params["adjust_blacks"]["value"] -= 25 * s
                params["adjust_whites"]["value"] += 20 * s
                params["adjust_temp_tint"]["temp"] -= 10 * s
                params["adjust_temp_tint"]["tint"] += 5 * s
                params["adjust_saturation"]["scale"] *= (1 + 0.25 * s)
                params["adjust_vibrance"]["strength"] += 0.25 * s
                params["adjust_color_mixer"]["blue"]["sat_scale"] = 1 + 0.2 * s
                params["adjust_color_mixer"]["green"]["sat_scale"] = 1 + 0.15 * s
                continue

        if "happy" in name or "gloomy" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["adjust_exposure"]["value"] -= 25 * s
                params["adjust_temp_tint"]["temp"] -= 20 * s
                params["adjust_saturation"]["scale"] *= (1 - 0.30 * s)
                params["adjust_highlights"]["value"] -= 20 * s
                params["adjust_blacks"]["value"] += 15 * s
                params["adjust_contrast"]["value"] *= (1 - 0.15 * s)
                continue
            else:
                s = axis_val
                params["adjust_exposure"]["value"] += 25 * s * 0.5
                params["adjust_temp_tint"]["temp"] += 25 * s * 0.5
                params["adjust_saturation"]["scale"] *= (1 + 0.35 * s)
                params["adjust_highlights"]["value"] += 20 * s * 0.5

                params["adjust_shadows"]["value"] += 10 * s * 0.5

                params["adjust_contrast"]["value"] *= (1 + 0.20 * s)
                continue

        if "sharp" in name or "soft" in name:
            if axis_val < 0:
                params["adjust_whites"]["value"] += 20 * abs(axis_val)
                params["adjust_blacks"]["value"] -= 20 * abs(axis_val)
                params["adjust_contrast"]["value"] *= 1 + 0.10 * abs(axis_val)
            else:
                params["adjust_highlights"]["value"] -= 15 * axis_val
                params["adjust_shadows"]["value"] -= 10 * axis_val
            continue

        if "ethereal" in name or "realistic" in name:
            if axis_val < 0:
                params["adjust_shadows"]["value"] -= 25 * abs(axis_val)
                params["adjust_highlights"]["value"] -= 25 * abs(axis_val)
                params["adjust_contrast"]["value"] *= 1 - 0.10 * abs(axis_val)
            else:
                params["adjust_contrast"]["value"] *= 1 + 0.10 * axis_val
                params["adjust_whites"]["value"] += 20 * axis_val
                params["adjust_blacks"]["value"] -= 20 * axis_val
            continue

        if "clean" in name or "gritty" in name:
            if axis_val < 0:
                params["adjust_blacks"]["value"] -= 30 * abs(axis_val)
                params["adjust_contrast"]["value"] *= 1 + 0.12 * abs(axis_val)
            else:
                params["adjust_saturation"]["scale"] *= 1 + 0.2 * axis_val
                params["adjust_contrast"]["value"] *= 1 - 0.122 * axis_val
            continue

        if "punchy" in name or "faded" in name:
            if axis_val < 0:
                params["adjust_contrast"]["value"] *= 1 + 0.15 * abs(axis_val)
                params["adjust_saturation"]["scale"] *= 1 + 0.25 * abs(axis_val)
            else:
                params["adjust_contrast"]["value"] *= 1 - 0.15 * axis_val
                params["adjust_shadows"]["value"] -= 30 * axis_val
            continue

        if "natural" in name or "artificial" in name:
            if axis_val < 0:
                strength = abs(axis_val)
                params["adjust_temp_tint"]["tint"] -= 20 * 0.3 * strength
                params["adjust_shadows"]["value"] -= 10 * 0.3 * strength
                params["adjust_highlights"]["value"] -= 15 * 0.3 * strength
                params["adjust_whites"]["value"] -= 10 * 0.3 * strength
                params["adjust_contrast"]["value"] *= (1 - 0.10 * 0.3 * strength)
                continue
            else:
                strength = axis_val
                params["adjust_temp_tint"]["tint"] += 30 * 0.3 * strength
                params["adjust_whites"]["value"] += 25 * 0.3 * strength
                params["adjust_contrast"]["value"] *= (1 + 0.20 * strength)
                params["adjust_shadows"]["value"] += 10 * 0.3 * strength
                params["adjust_highlights"]["value"] += 20 * 0.3 * strength
                continue

        if "dreamy" in name or "crisp" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["adjust_shadows"]["value"] -= 20 * s
                params["adjust_highlights"]["value"] -= 20 * s
                params["adjust_contrast"]["value"] *= (1 - 0.25 * s)
                params["adjust_saturation"]["scale"] *= (1 - 0.20 * s)
                params["adjust_temp_tint"]["temp"] += 10 * s
                continue
            else:
                s = axis_val
                params["adjust_contrast"]["value"] *= (1 + 0.35 * s)
                params["adjust_blacks"]["value"] -= 25 * s
                params["adjust_whites"]["value"] += 20 * s
                params["adjust_saturation"]["scale"] *= (1 + 0.20 * s)
                continue

        if "moody" in name or "airy" in name:
            if axis_val < 0:
                params["adjust_exposure"]["value"] -= 25 * abs(axis_val)
                params["adjust_temp_tint"]["temp"] -= 15 * abs(axis_val)
            else:
                params["adjust_exposure"]["value"] += 25 * axis_val
                params["adjust_saturation"]["scale"] *= 1 + 0.25 * axis_val
            continue

        if "high" in name and "key" in name:
            params["adjust_whites"]["value"] += -axis_val * 40
            params["adjust_blacks"]["value"] += axis_val * 40
            continue

        if "matte" in name or "glossy" in name:
            if axis_val < 0:
                params["adjust_shadows"]["value"] -= 15 * abs(axis_val)
                params["adjust_blacks"]["value"] += 20 * abs(axis_val)
            else:
                params["adjust_contrast"]["value"] *= 1 + 0.25 * axis_val
                params["adjust_whites"]["value"] += 15 * axis_val
            continue

        if "cinematic" in name or "natural" in name:

            if axis_val < 0:
                s = abs(axis_val)
                params["adjust_exposure"]["value"] += 10 * (-s)
                params["adjust_temp_tint"]["temp"] -= 10 * s
                params["adjust_temp_tint"]["tint"] += 5 * s
                params["adjust_contrast"]["value"] *= (1 - 0.15 * s)
                params["adjust_saturation"]["scale"] *= (1 + 0.05 * s)
                params["adjust_vibrance"]["strength"] *= (1 - 0.10 * s)
                params["adjust_blacks"]["value"] += 10 * s
                params["adjust_highlights"]["value"] -= 10 * s
                params["adjust_color_mixer"]["blue"]["hue_shift"] = 0
                params["adjust_color_mixer"]["yellow"]["hue_shift"] = 0
                continue
            else:
                s = axis_val
                params["adjust_exposure"]["value"] -= 15 * s
                params["adjust_temp_tint"]["temp"] -= 20 * s
                params["adjust_temp_tint"]["tint"] += 10 * s
                params["adjust_contrast"]["value"] *= (1 + 0.25 * s)
                params["adjust_blacks"]["value"] -= 25 * s
                params["adjust_highlights"]["value"] -= 10 * s
                params["adjust_saturation"]["scale"] *= (1 - 0.15 * s)
                params["adjust_vibrance"]["strength"] += 0.10 * s
                params["adjust_color_mixer"]["blue"]["hue_shift"] = -10 * s
                params["adjust_color_mixer"]["yellow"]["hue_shift"] = 10 * s
                params["adjust_color_mixer"]["blue"]["lum_scale"] = 1 - 0.10 * s
                params["adjust_color_mixer"]["yellow"]["lum_scale"] = 1 + 0.10 * s
                continue


        if "cyberpunk" in name or "organic" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["style_preset"] = "cyberpunk"
                params["apply_split_toning"] = {"shadow_hue": 280, "shadow_sat": 0.4 * s,
                                                "highlight_hue": 180, "highlight_sat": 0.3 * s}
                params["apply_vignette"] = {"strength": 0.6 * s, "radius": 0.7}
                params["apply_glow"] = {"intensity": 0.25 * s, "radius": 31}
                params["adjust_saturation"]["scale"] *= (1 + 0.4 * s)
                params["adjust_contrast"]["value"] *= (1 + 0.3 * s)
            else:
                s = axis_val
                params["adjust_temp_tint"]["temp"] += 15 * s
                params["adjust_saturation"]["scale"] *= (1 - 0.2 * s)
                params["adjust_vibrance"]["strength"] += 0.3 * s
            continue

        if "night" in name and "day" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["style_preset"] = "night"
                params["adjust_exposure"]["value"] -= 30 * s
                params["apply_split_toning"] = {"shadow_hue": 220, "shadow_sat": 0.5 * s,
                                                "highlight_hue": 200, "highlight_sat": 0.2 * s}
                params["apply_vignette"] = {"strength": 0.7 * s, "radius": 0.6}
                params["adjust_saturation"]["scale"] *= (1 - 0.2 * s)
            else:
                s = axis_val
                params["adjust_exposure"]["value"] += 20 * s
                params["adjust_temp_tint"]["temp"] += 15 * s
                params["apply_glow"] = {"intensity": 0.15 * s, "radius": 41}
            continue

        if "noir" in name or "colorful" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["style_preset"] = "noir"
                params["adjust_saturation"]["scale"] *= (1 - 0.8 * s)
                params["adjust_contrast"]["value"] *= (1 + 0.5 * s)
                params["apply_vignette"] = {"strength": 0.8 * s, "radius": 0.5}
                params["apply_grain"] = {"amount": 0.15 * s, "size": 1}
            else:
                s = axis_val
                params["adjust_saturation"]["scale"] *= (1 + 0.5 * s)
                params["adjust_vibrance"]["strength"] += 0.5 * s
            continue

        if "neon" in name or "subtle" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["style_preset"] = "neon"
                params["adjust_saturation"]["scale"] *= (1 + 0.6 * s)
                params["adjust_vibrance"]["strength"] += 0.6 * s
                params["adjust_contrast"]["value"] *= (1 + 0.25 * s)
                params["apply_glow"] = {"intensity": 0.35 * s, "radius": 25}
                params["apply_vignette"] = {"strength": 0.5 * s, "radius": 0.7}
            else:
                s = axis_val
                params["adjust_saturation"]["scale"] *= (1 - 0.3 * s)
                params["adjust_contrast"]["value"] *= (1 - 0.15 * s)
            continue

        if "golden" in name and "hour" in name:
            if axis_val < 0:
                s = abs(axis_val)
                params["style_preset"] = "golden_hour"
                params["apply_split_toning"] = {"shadow_hue": 30, "shadow_sat": 0.2 * s,
                                                "highlight_hue": 45, "highlight_sat": 0.4 * s}
                params["adjust_temp_tint"]["temp"] += 30 * s
                params["apply_glow"] = {"intensity": 0.2 * s, "radius": 41}
                params["apply_haze"] = {"amount": 0.08 * s, "color": (255, 220, 180)}
            else:
                s = axis_val
                params["apply_split_toning"] = {"shadow_hue": 220, "shadow_sat": 0.3 * s,
                                                "highlight_hue": 260, "highlight_sat": 0.2 * s}
                params["adjust_temp_tint"]["temp"] -= 25 * s
                params["adjust_exposure"]["value"] -= 15 * s
            continue

    params["adjust_exposure"]["value"] = max(-50, min(50, params["adjust_exposure"]["value"]))
    params["adjust_contrast"]["value"] = max(0.5, min(1.8, params["adjust_contrast"]["value"]))
    params["adjust_saturation"]["scale"] = max(0.4, min(1.7, params["adjust_saturation"]["scale"]))

    return params


def apply_params_to_image(image_path, params, output_path):
    from opencv_tools import (
        adjust_exposure, adjust_contrast, adjust_highlights,
        adjust_shadows, adjust_whites, adjust_blacks,
        adjust_temp_tint, adjust_saturation, adjust_vibrance,
        adjust_color_mixer,
        apply_split_toning, apply_color_overlay, apply_curves,
        apply_vignette, apply_glow, apply_grain, apply_duotone,
        apply_haze, apply_style_preset
    )

    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Cannot read {image_path}")

    if "style_preset" in params:
        img = apply_style_preset(img, style=params["style_preset"])

    img = adjust_exposure(img, **params.get("adjust_exposure", {}))
    img = adjust_contrast(img, **params.get("adjust_contrast", {}))
    img = adjust_highlights(img, **params.get("adjust_highlights", {}))
    img = adjust_shadows(img, **params.get("adjust_shadows", {}))
    img = adjust_whites(img, **params.get("adjust_whites", {}))
    img = adjust_blacks(img, **params.get("adjust_blacks", {}))
    img = adjust_temp_tint(img, **params.get("adjust_temp_tint", {}))
    img = adjust_saturation(img, **params.get("adjust_saturation", {}))
    img = adjust_vibrance(img, **params.get("adjust_vibrance", {}))
    img = adjust_color_mixer(img, **params.get("adjust_color_mixer", {}))

    if "apply_split_toning" in params:
        img = apply_split_toning(img, **params["apply_split_toning"])
    if "apply_color_overlay" in params:
        img = apply_color_overlay(img, **params["apply_color_overlay"])
    if "apply_curves" in params:
        img = apply_curves(img, **params["apply_curves"])

    if "apply_vignette" in params:
        img = apply_vignette(img, **params["apply_vignette"])
    if "apply_glow" in params:
        img = apply_glow(img, **params["apply_glow"])
    if "apply_grain" in params:
        img = apply_grain(img, **params["apply_grain"])
    if "apply_duotone" in params:
        img = apply_duotone(img, **params["apply_duotone"])
    if "apply_haze" in params:
        img = apply_haze(img, **params["apply_haze"])

    cv2.imwrite(output_path, img)
    return output_path


def interactive_semantic_editor(final_image_path, output_dir,prompt=None):

    print(" SEMANTIC EDITOR MODE (2 AXES)")
    print("Edit your photo using intuitive semantic axes")
    print("Each axis ranges from -1.0 to +1.0")

    axes_info = analyze_image_axes(final_image_path,user_prompt=prompt)

    axes_file = os.path.join(output_dir, "semantic_axes.json")
    with open(axes_file, "w", encoding="utf-8") as f:
        json.dump(axes_info, f, indent=2)
    print(f"\n Axes info saved: {axes_file}")

    print("\nSEMANTIC AXES:")
    for i, axis in enumerate(axes_info['axes'], 1):
        print(f"\n{i}. {axis['name']}")
        print(f"   Left  (-1.0): {axis['left_pole']}")
        print(f"   Right (+1.0): {axis['right_pole']}")
        print(f"   Current: {axis['current_position']:.2f}")
        print(f"   Description: {axis['description']}")

    iteration = 1
    base_image = final_image_path
    last_output = final_image_path

    while True:
        print(f"SEMANTIC EDIT #{iteration}")
        print(f"Base image: {os.path.basename(base_image)}")

        try:
            print(f"\nEnter coordinates (or 'q' to quit, 'r' to reset):")

            axis_vals = []

            for i, axis in enumerate(axes_info['axes']):
                val_input = input(f"  {axis['name']} [-1.0 to 1.0]: ").strip().lower()

                if val_input == 'q':
                    print("\nExiting semantic editor")
                    print(f"Last semantic output: {last_output}")
                    print(f"Total variations created: {iteration - 1}")
                    return last_output

                if val_input == 'r':
                    axis_vals = [0.0, 0.0, 0.0, 0.0]
                    print(" Reset to neutral (0.0, 0.0, 0.0, 0.0)")
                    break

                try:
                    val = float(val_input)
                    val = max(-1.0, min(1.0, val))
                    axis_vals.append(val)
                except ValueError:
                    print(f"Invalid input, using 0.0 for {axis['name']}")
                    axis_vals.append(0.0)

            print(f"\n Coordinates: ({', '.join(f'{v:.2f}' for v in axis_vals)})")

            print(" Converting coordinates to edit parameters...")
            params = convert_coordinates_to_params(axis_vals, axes_info)

            print(f"Applying edits to base image (absolute changes)...")
            output_path = os.path.join(output_dir, f"semantic_{iteration:02d}.jpg")
            apply_params_to_image(base_image, params, output_path)

            print(f"Saved: {output_path}")

            param_file = os.path.join(output_dir, f"semantic_{iteration:02d}_params.json")
            coords_dict = {axes_info['axes'][i]['name']: axis_vals[i] for i in range(2)}

            with open(param_file, "w", encoding="utf-8") as f:
                json.dump({
                    "iteration": iteration,
                    "base_image": os.path.basename(base_image),
                    "coordinates": coords_dict,
                    "parameters": params
                }, f, indent=2)
            print(f" Parameters saved: {param_file}")

            last_output = output_path
            iteration += 1

            cont = input(" Continue editing? (y/n): ").strip().lower()
            if cont != 'y':
                print("\n Exiting semantic editor")
                break

        except Exception as e:
            print(f" Error: {e}")
            import traceback
            traceback.print_exc()

    print(f" Last semantic output: {last_output}")
    print(f" Total variations created: {iteration - 1}")

    return last_output


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        output_dir = "images/output"
        os.makedirs(output_dir, exist_ok=True)
        interactive_semantic_editor(test_image, output_dir)
    else:
        print("Usage: python semantic_editor.py <image_path>")
