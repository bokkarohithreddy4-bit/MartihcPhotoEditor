

import json


GOLDEN_HOUR_SUBTLE = {
    "keywords": ["golden hour", "warm", "sunset light", "warm tones", "golden"],
    "description": "Subtle golden hour warmth - natural looking",
    "parameters": {
        "adjust_temp_tint": {"temp": 35, "tint": 3},
        "adjust_exposure": {"value": 3},
        "adjust_contrast": {"value": 1.08},
        "adjust_highlights": {"value": -15},
        "adjust_shadows": {"value": 12},
        "adjust_whites": {"value": -5},
        "adjust_blacks": {"value": -3},
        "adjust_saturation": {"scale": 1.1},
        "adjust_vibrance": {"strength": 0.2},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.1, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.25, "lum_scale": 1.05},
            "yellow": {"hue_shift": 0, "sat_scale": 1.2, "lum_scale": 1.0},
            "green": {"hue_shift": 5, "sat_scale": 0.95, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0}
        }
    },
    "reasoning": "Golden hour: temp 30-40 for warmth, PROTECT highlights with negative values, lift shadows for detail, boost orange/yellow saturation moderately. Keep overall saturation under 1.15 for natural look."
}

GOLDEN_HOUR_DRAMATIC = {
    "keywords": ["dramatic golden", "intense sunset", "fiery", "strong golden hour"],
    "description": "More dramatic golden hour with stronger warmth",
    "parameters": {
        "adjust_temp_tint": {"temp": 50, "tint": 5},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.15},
        "adjust_highlights": {"value": -20},
        "adjust_shadows": {"value": 8},
        "adjust_whites": {"value": -10},
        "adjust_blacks": {"value": -8},
        "adjust_saturation": {"scale": 1.15},
        "adjust_vibrance": {"strength": 0.25},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.2, "lum_scale": 1.0},
            "orange": {"hue_shift": -3, "sat_scale": 1.35, "lum_scale": 1.08},
            "yellow": {"hue_shift": 0, "sat_scale": 1.25, "lum_scale": 1.0},
            "green": {"hue_shift": 8, "sat_scale": 0.9, "lum_scale": 0.98},
            "cyan": {"hue_shift": 0, "sat_scale": 0.85, "lum_scale": 0.95},
            "blue": {"hue_shift": 0, "sat_scale": 0.8, "lum_scale": 0.95},
            "purple": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0}
        }
    },
    "reasoning": "Dramatic golden hour: higher temp (50), more contrast, reduce blues/cyans to eliminate coolness, stronger orange boost. Still protect highlights!"
}

MORNING_LIGHT = {
    "keywords": ["morning", "sunrise", "early morning", "dawn", "soft morning", "morning glow"],
    "description": "Soft morning light with gentle warmth",
    "parameters": {
        "adjust_temp_tint": {"temp": 25, "tint": 0},
        "adjust_exposure": {"value": 5},
        "adjust_contrast": {"value": 1.05},
        "adjust_highlights": {"value": -10},
        "adjust_shadows": {"value": 20},
        "adjust_whites": {"value": 0},
        "adjust_blacks": {"value": 5},
        "adjust_saturation": {"scale": 1.08},
        "adjust_vibrance": {"strength": 0.18},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.05, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.15, "lum_scale": 1.03},
            "yellow": {"hue_shift": 0, "sat_scale": 1.12, "lum_scale": 1.02},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "Morning light is SOFTER than golden hour: moderate warmth (temp 25), heavily lifted shadows, raised blacks for soft/hazy feel, gentle saturation."
}

NIGHT_PRESET = {
    "keywords": ["night", "nighttime", "night scene", "dark night", "night look"],
    "description": "Night scene using style preset",
    "parameters": {
        "apply_style_preset": {"style": "night"}
    },
    "reasoning": "For night scenes, USE THE STYLE PRESET! It applies proper exposure, blue tones, and vignette."
}

NIGHT_DEEP = {
    "keywords": ["deep night", "very dark", "midnight", "pitch black", "ultra dark"],
    "description": "Very dark night scene",
    "parameters": {
        "apply_style_preset": {"style": "deep_night"}
    },
    "reasoning": "For very dark night scenes, use the deep_night preset."
}

NIGHT_BLUE_HOUR = {
    "keywords": ["blue hour", "twilight", "dusk", "pre-dawn"],
    "description": "Blue hour twilight",
    "parameters": {
        "apply_style_preset": {"style": "blue_hour"}
    },
    "reasoning": "For blue hour/twilight, use the blue_hour preset."
}

NIGHT_NATURAL = {
    "keywords": ["night manual", "evening", "after dark", "night city", "urban night"],
    "description": "Natural night scene - dark but with visible detail (manual control)",
    "parameters": {
        "adjust_temp_tint": {"temp": -8, "tint": 0},
        "adjust_exposure": {"value": -12},
        "adjust_contrast": {"value": 1.12},
        "adjust_highlights": {"value": 5},
        "adjust_shadows": {"value": -18},
        "adjust_whites": {"value": 8},
        "adjust_blacks": {"value": -15},
        "adjust_saturation": {"scale": 1.05},
        "adjust_vibrance": {"strength": 0.15}
    },
    "reasoning": "CRITICAL for night: temp should be only slightly cool (-5 to -15), NOT extreme blue! Reduce exposure (-10 to -15), deepen shadows and blacks."
}

BLUE_HOUR = {
    "keywords": ["blue hour", "twilight", "dusk", "pre-dawn", "cool evening"],
    "description": "Blue hour twilight - cool but natural",
    "parameters": {
        "adjust_temp_tint": {"temp": -25, "tint": -3},
        "adjust_exposure": {"value": -5},
        "adjust_contrast": {"value": 1.08},
        "adjust_highlights": {"value": 0},
        "adjust_shadows": {"value": 8},
        "adjust_whites": {"value": -5},
        "adjust_blacks": {"value": -8},
        "adjust_saturation": {"scale": 1.0},
        "adjust_vibrance": {"strength": 0.12},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.1, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.08, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.05, "lum_scale": 1.0}
        }
    },
    "reasoning": "Blue hour: moderate cool temp (-20 to -30), MUTED saturation (not boosted!), slight blue/cyan boost. Reduce warm tones."
}


BLACK_AND_WHITE_CLASSIC = {
    "keywords": ["black and white", "b&w", "bw", "monochrome", "grayscale", "black & white"],
    "description": "Classic B&W with good tonal range",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 3},
        "adjust_contrast": {"value": 1.15},
        "adjust_highlights": {"value": -8},
        "adjust_shadows": {"value": 10},
        "adjust_whites": {"value": 8},
        "adjust_blacks": {"value": -10},
        "adjust_saturation": {"scale": 0.0},
        "adjust_vibrance": {"strength": 0.0},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.05},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.08},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.1},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.95},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.9},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.8},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.9}
        }
    },
    "reasoning": "B&W MUST have saturation=0.0! Use color mixer LUMINANCE to control tones: darken blues (lum_scale 0.8) for dramatic skies, brighten yellows/oranges (lum_scale 1.1) for warm tones. Boost contrast."
}

BLACK_AND_WHITE_HIGH_CONTRAST = {
    "keywords": ["high contrast b&w", "dramatic black and white", "contrasty bw", "punchy monochrome"],
    "description": "High contrast dramatic B&W",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.35},
        "adjust_highlights": {"value": 8},
        "adjust_shadows": {"value": -25},
        "adjust_whites": {"value": 18},
        "adjust_blacks": {"value": -25},
        "adjust_saturation": {"scale": 0.0},
        "adjust_vibrance": {"strength": 0.0},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.1},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.1},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.15},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.85},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.75},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.65},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.8}
        }
    },
    "reasoning": "High contrast B&W: saturation=0, very high contrast (1.35), crushed blacks (-25), boosted whites, heavily darkened blues (lum_scale 0.65) for black skies."
}


DEEP_SHADOWS = {
    "keywords": ["deep shadows", "dark shadows", "moody shadows", "shadow", "darker shadows", "crush shadows"],
    "description": "Deepen shadows for dramatic depth",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.1},
        "adjust_highlights": {"value": 0},
        "adjust_shadows": {"value": -25},
        "adjust_whites": {"value": 0},
        "adjust_blacks": {"value": -18},
        "adjust_saturation": {"scale": 1.0},
        "adjust_vibrance": {"strength": 0.0},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "Deep shadows: NEGATIVE shadows value (-20 to -30), negative blacks (-15 to -20), slight contrast boost. Keep other values neutral."
}

LIFTED_SHADOWS = {
    "keywords": ["lift shadows", "open shadows", "brighten shadows", "shadow detail", "see into shadows"],
    "description": "Lift shadows to reveal detail",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.0},
        "adjust_highlights": {"value": -5},
        "adjust_shadows": {"value": 35},
        "adjust_whites": {"value": 0},
        "adjust_blacks": {"value": 12},
        "adjust_saturation": {"scale": 1.0},
        "adjust_vibrance": {"strength": 0.0},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "Lift shadows: POSITIVE shadows value (+30 to +40), raised blacks (+10 to +15), slight highlight reduction to balance."
}

HIGH_CONTRAST = {
    "keywords": ["high contrast", "contrasty", "punchy", "more contrast", "dramatic contrast"],
    "description": "High contrast with deep blacks and bright whites",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.25},
        "adjust_highlights": {"value": 5},
        "adjust_shadows": {"value": -12},
        "adjust_whites": {"value": 12},
        "adjust_blacks": {"value": -15},
        "adjust_saturation": {"scale": 1.05},
        "adjust_vibrance": {"strength": 0.1},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "High contrast: contrast value 1.2-1.3, boost whites (+10-15), crush blacks (-12 to -18), slight shadow reduction."
}

LOW_CONTRAST = {
    "keywords": ["low contrast", "soft", "flat", "matte", "faded"],
    "description": "Low contrast soft/matte look",
    "parameters": {
        "adjust_temp_tint": {"temp": 0, "tint": 0},
        "adjust_exposure": {"value": 3},
        "adjust_contrast": {"value": 0.85},
        "adjust_highlights": {"value": -12},
        "adjust_shadows": {"value": 25},
        "adjust_whites": {"value": -8},
        "adjust_blacks": {"value": 18},
        "adjust_saturation": {"scale": 0.95},
        "adjust_vibrance": {"strength": 0.1},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "Low contrast/matte: contrast 0.8-0.9, heavily lifted shadows (+20-30) and blacks (+15-20), reduced highlights/whites."
}



MOODY_DARK = {
    "keywords": ["moody", "dark moody", "atmospheric", "brooding", "dark"],
    "description": "Dark moody atmosphere",
    "parameters": {
        "adjust_temp_tint": {"temp": -5, "tint": 0},
        "adjust_exposure": {"value": -10},
        "adjust_contrast": {"value": 1.12},
        "adjust_highlights": {"value": -8},
        "adjust_shadows": {"value": -12},
        "adjust_whites": {"value": -5},
        "adjust_blacks": {"value": -15},
        "adjust_saturation": {"scale": 0.9},
        "adjust_vibrance": {"strength": 0.1},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 0.98},
            "orange": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 0.98},
            "yellow": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 0.98},
            "green": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 0.95},
            "cyan": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 0.98},
            "purple": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 0.98}
        }
    },
    "reasoning": "Moody: reduced exposure (-8 to -12), deep shadows/blacks, DESATURATED (0.85-0.95), slight cool tint, muted colors."
}

NOIR = {
    "keywords": ["noir", "film noir", "detective", "shadowy", "mysterious", "classic noir"],
    "description": "Film noir style - use the noir style preset!",
    "parameters": {
        "apply_style_preset": {"style": "noir"}
    },
    "reasoning": "For noir style, USE THE STYLE PRESET! It applies proper B&W conversion, high contrast, vignette, and grain all at once."
}

NOIR_NEO = {
    "keywords": ["neo noir", "modern noir", "sin city", "drive", "color noir"],
    "description": "Neo-noir with subtle color accents",
    "parameters": {
        "apply_style_preset": {"style": "neo_noir"}
    },
    "reasoning": "Neo-noir: modern take with subtle color accents. Use the neo_noir preset."
}

NOIR_DARK = {
    "keywords": ["dark noir", "very dark", "extreme noir", "heavy shadows"],
    "description": "Extra dark noir style",
    "parameters": {
        "apply_style_preset": {"style": "dark_noir"}
    },
    "reasoning": "Dark noir: extra dark and moody. Use the dark_noir preset."
}

GLOOMY = {
    "keywords": ["gloomy", "overcast", "cloudy", "gray", "rainy", "dull", "muted"],
    "description": "Gloomy overcast weather look",
    "parameters": {
        "adjust_temp_tint": {"temp": -8, "tint": 0},
        "adjust_exposure": {"value": -5},
        "adjust_contrast": {"value": 0.95},
        "adjust_highlights": {"value": -10},
        "adjust_shadows": {"value": 5},
        "adjust_whites": {"value": -8},
        "adjust_blacks": {"value": 5},
        "adjust_saturation": {"scale": 0.8},
        "adjust_vibrance": {"strength": 0.05},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 0.85, "lum_scale": 0.98},
            "orange": {"hue_shift": 0, "sat_scale": 0.85, "lum_scale": 0.98},
            "yellow": {"hue_shift": 0, "sat_scale": 0.8, "lum_scale": 0.98},
            "green": {"hue_shift": 0, "sat_scale": 0.85, "lum_scale": 0.98},
            "cyan": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 0.95, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0}
        }
    },
    "reasoning": "Gloomy: cool temp (-5 to -10), LOW saturation (0.75-0.85), low contrast, muted all colors, reduced exposure."
}

CINEMATIC = {
    "keywords": ["cinematic", "movie", "film look", "hollywood", "teal orange", "blockbuster"],
    "description": "Classic teal-orange Hollywood color grading",
    "parameters": {
        "adjust_temp_tint": {"temp": 12, "tint": 0},
        "adjust_exposure": {"value": 0},
        "adjust_contrast": {"value": 1.12},
        "adjust_highlights": {"value": -8},
        "adjust_shadows": {"value": 5},
        "adjust_whites": {"value": 0},
        "adjust_blacks": {"value": -8},
        "adjust_saturation": {"scale": 1.05},
        "adjust_vibrance": {"strength": 0.15},
        "adjust_color_mixer": {
            "red": {"hue_shift": 5, "sat_scale": 1.08, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.2, "lum_scale": 1.02},
            "yellow": {"hue_shift": -5, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 12, "sat_scale": 0.85, "lum_scale": 0.98},
            "cyan": {"hue_shift": 0, "sat_scale": 1.25, "lum_scale": 1.0},
            "blue": {"hue_shift": -8, "sat_scale": 1.15, "lum_scale": 0.98},
            "purple": {"hue_shift": 0, "sat_scale": 0.9, "lum_scale": 1.0}
        }
    },
    "reasoning": "Teal-orange: boost orange (sat_scale 1.2), push greens toward teal (hue +10-15), boost cyan (sat_scale 1.25), shift blues toward teal (hue -8)."
}


VINTAGE = {
    "keywords": ["vintage", "retro", "old", "film", "analog", "nostalgic", "70s", "80s"],
    "description": "Vintage film look with faded blacks",
    "parameters": {
        "adjust_temp_tint": {"temp": 18, "tint": 5},
        "adjust_exposure": {"value": 3},
        "adjust_contrast": {"value": 0.92},
        "adjust_highlights": {"value": -10},
        "adjust_shadows": {"value": 18},
        "adjust_whites": {"value": -5},
        "adjust_blacks": {"value": 15},
        "adjust_saturation": {"scale": 0.92},
        "adjust_vibrance": {"strength": 0.12},
        "adjust_color_mixer": {
            "red": {"hue_shift": 3, "sat_scale": 1.05, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.1, "lum_scale": 1.0},
            "yellow": {"hue_shift": -5, "sat_scale": 1.05, "lum_scale": 1.02},
            "green": {"hue_shift": 8, "sat_scale": 0.9, "lum_scale": 1.0},
            "cyan": {"hue_shift": 5, "sat_scale": 0.9, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 0.85, "lum_scale": 1.0},
            "purple": {"hue_shift": -5, "sat_scale": 0.9, "lum_scale": 1.0}
        }
    },
    "reasoning": "Vintage: RAISED blacks (+12 to +18), low contrast (0.9), warm tint, muted saturation (0.9), greens shifted toward yellow."
}


VIBRANT = {
    "keywords": ["vibrant", "colorful", "saturated", "vivid", "pop", "bold colors"],
    "description": "Vibrant punchy colors",
    "parameters": {
        "adjust_temp_tint": {"temp": 5, "tint": 0},
        "adjust_exposure": {"value": 3},
        "adjust_contrast": {"value": 1.1},
        "adjust_highlights": {"value": -8},
        "adjust_shadows": {"value": 10},
        "adjust_whites": {"value": 3},
        "adjust_blacks": {"value": -5},
        "adjust_saturation": {"scale": 1.2},
        "adjust_vibrance": {"strength": 0.35},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.15, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.15, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.12, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.15, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.12, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.15, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.1, "lum_scale": 1.0}
        }
    },
    "reasoning": "Vibrant: saturation 1.15-1.25 (don't go higher!), high vibrance (0.3-0.4), boost all color channels equally."
}



NATURAL = {
    "keywords": ["natural", "clean", "realistic", "subtle", "balanced"],
    "description": "Natural subtle enhancement",
    "parameters": {
        "adjust_temp_tint": {"temp": 2, "tint": 0},
        "adjust_exposure": {"value": 2},
        "adjust_contrast": {"value": 1.03},
        "adjust_highlights": {"value": -5},
        "adjust_shadows": {"value": 8},
        "adjust_whites": {"value": 2},
        "adjust_blacks": {"value": -2},
        "adjust_saturation": {"scale": 1.03},
        "adjust_vibrance": {"strength": 0.1},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "green": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "cyan": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "blue": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0},
            "purple": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.0}
        }
    },
    "reasoning": "Natural: ALL adjustments minimal! Contrast 1.0-1.05, saturation 1.0-1.05, tiny shadow lift. Less is more."
}

BRIGHT_AIRY = {
    "keywords": ["bright", "airy", "light", "fresh", "high key", "luminous"],
    "description": "Bright airy high-key look",
    "parameters": {
        "adjust_temp_tint": {"temp": 8, "tint": 0},
        "adjust_exposure": {"value": 12},
        "adjust_contrast": {"value": 0.95},
        "adjust_highlights": {"value": -15},
        "adjust_shadows": {"value": 30},
        "adjust_whites": {"value": 5},
        "adjust_blacks": {"value": 15},
        "adjust_saturation": {"scale": 1.0},
        "adjust_vibrance": {"strength": 0.15},
        "adjust_color_mixer": {
            "red": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.03},
            "orange": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.03},
            "yellow": {"hue_shift": 0, "sat_scale": 1.0, "lum_scale": 1.05},
            "green": {"hue_shift": 0, "sat_scale": 0.98, "lum_scale": 1.03},
            "cyan": {"hue_shift": 0, "sat_scale": 0.98, "lum_scale": 1.03},
            "blue": {"hue_shift": 0, "sat_scale": 0.98, "lum_scale": 1.03},
            "purple": {"hue_shift": 0, "sat_scale": 0.98, "lum_scale": 1.03}
        }
    },
    "reasoning": "Bright/airy: high exposure (+10-15), heavily lifted shadows (+25-35) and blacks (+12-18), LOW contrast (0.9-0.95)."
}

CYBERPUNK = {
    "keywords": ["cyberpunk", "neon", "futuristic", "synthwave", "blade runner"],
    "description": "Cyberpunk with pink/cyan accents",
    "parameters": {
        "apply_style_preset": {"style": "cyberpunk"},
        "adjust_exposure": {"value": -5},
        "adjust_contrast": {"value": 1.15}
    },
    "reasoning": "CYBERPUNK: USE apply_style_preset with style='cyberpunk' for the quickest result. This applies neon pink/cyan split toning, glow, high saturation, and vignette automatically."
}



DUOTONE_CLASSIC = {
    "keywords": ["duotone", "two tone", "two-tone", "dual tone", "duo tone"],
    "description": "Classic duotone effect - maps darks to one color, lights to another",
    "parameters": {
        "apply_duotone": {
            "dark_color": [20, 0, 80],
            "light_color": [255, 200, 100]
        },
        "adjust_contrast": {"value": 1.1}
    },
    "reasoning": "DUOTONE: Use apply_duotone tool! dark_color for shadows (e.g. deep purple [20,0,80]), light_color for highlights (e.g. warm cream [255,200,100]). This is a CREATIVE EFFECT tool, NOT achievable with basic adjustments."
}

DUOTONE_TEAL_ORANGE = {
    "keywords": ["teal orange duotone", "teal and orange", "orange teal duotone"],
    "description": "Hollywood teal-orange duotone",
    "parameters": {
        "apply_duotone": {
            "dark_color": [0, 80, 80],
            "light_color": [255, 140, 50]
        },
        "adjust_contrast": {"value": 1.15}
    },
    "reasoning": "Teal-orange duotone: dark_color = teal [0,80,80], light_color = orange [255,140,50]. Creates cinematic color separation."
}

DUOTONE_BLUE_GOLD = {
    "keywords": ["blue gold duotone", "blue and gold", "navy gold"],
    "description": "Elegant blue-gold duotone",
    "parameters": {
        "apply_duotone": {
            "dark_color": [15, 30, 80],
            "light_color": [255, 210, 100]
        }
    },
    "reasoning": "Blue-gold duotone: shadows to deep navy blue, highlights to warm gold. Elegant and classic."
}

DUOTONE_SEPIA = {
    "keywords": ["sepia duotone", "sepia", "antique", "old photo duotone"],
    "description": "Sepia/antique duotone effect",
    "parameters": {
        "apply_duotone": {
            "dark_color": [30, 20, 10],
            "light_color": [255, 230, 180]
        },
        "adjust_contrast": {"value": 1.05}
    },
    "reasoning": "Sepia duotone: dark brown shadows [30,20,10], cream highlights [255,230,180]. Classic antique look."
}

DUOTONE_COOL = {
    "keywords": ["cool duotone", "blue duotone", "cold duotone", "icy duotone"],
    "description": "Cool/icy duotone effect",
    "parameters": {
        "apply_duotone": {
            "dark_color": [10, 20, 60],
            "light_color": [200, 220, 255]
        }
    },
    "reasoning": "Cool duotone: deep blue-black shadows, icy blue-white highlights. Creates cold, icy atmosphere."
}


SPLIT_TONE_TEAL_ORANGE = {
    "keywords": ["split tone", "split toning", "color grading split"],
    "description": "Split toning - different colors in shadows vs highlights",
    "parameters": {
        "apply_split_toning": {
            "shadow_color": [30, 80, 100],
            "highlight_color": [255, 180, 100],
            "balance": 0.5
        },
        "adjust_contrast": {"value": 1.08}
    },
    "reasoning": "SPLIT TONING: Use apply_split_toning! shadow_color tints shadows, highlight_color tints highlights, balance (0-1) controls crossover. Different from duotone - preserves more original tones."
}

SPLIT_TONE_WARM_COOL = {
    "keywords": ["warm shadows cool highlights", "cool shadows warm highlights"],
    "description": "Warm/cool split tone",
    "parameters": {
        "apply_split_toning": {
            "shadow_color": [60, 40, 80],
            "highlight_color": [255, 230, 180],
            "balance": 0.4
        }
    },
    "reasoning": "Warm/cool split: purple-ish shadows, warm cream highlights. Classic portrait split tone."
}



STYLE_CYBERPUNK = {
    "keywords": ["cyberpunk style", "neon style", "futuristic style", "blade runner style"],
    "description": "Cyberpunk style preset with neon pink/cyan",
    "parameters": {
        "apply_style_preset": {"style": "cyberpunk"}
    },
    "reasoning": "CYBERPUNK STYLE: Use apply_style_preset with style='cyberpunk'. Applies neon pink/cyan color grading automatically."
}

STYLE_VINTAGE = {
    "keywords": ["vintage style", "retro style", "70s style", "film style preset"],
    "description": "Vintage film style preset",
    "parameters": {
        "apply_style_preset": {"style": "vintage_film"}
    },
    "reasoning": "VINTAGE STYLE: Use apply_style_preset with style='vintage_film'. Applies faded film look automatically."
}

STYLE_NOIR = {
    "keywords": ["noir style", "film noir style", "detective style", "make it noir", "noir"],
    "description": "Film noir style preset - classic dramatic B&W look",
    "parameters": {
        "apply_style_preset": {"style": "noir"},
        "adjust_exposure": {"value": -8},
        "adjust_contrast": {"value": 12},
        "adjust_highlights": {"value": -10},
        "adjust_shadows": {"value": 5},
        "adjust_whites": {"value": 5},
        "adjust_blacks": {"value": -8},
        "adjust_temperature": {"value": -10},
        "adjust_tint": {"value": 0},
        "adjust_vibrance": {"value": -20},
        "adjust_saturation": {"value": -15},
        "adjust_clarity": {"value": 15},
        "adjust_dehaze": {"value": 5},
        "adjust_texture": {"value": 8},
        "adjust_sharpness": {"value": 15},
        "adjust_noise_reduction": {"value": 10},
        "adjust_color_noise_reduction": {"value": 10},
        "adjust_shadow_hue": {"value": 0},
        "adjust_highlight_hue": {"value": 0},
        "adjust_shadow_saturation": {"value": 0},
        "adjust_highlight_saturation": {"value": 0},
        "adjust_hue_red": {"value": 0},
        "adjust_hue_orange": {"value": 0},
        "adjust_hue_yellow": {"value": 0},
        "adjust_hue_green": {"value": 0},
        "adjust_hue_aqua": {"value": 0},
        "adjust_hue_blue": {"value": 0},
        "adjust_hue_purple": {"value": 0},
        "adjust_hue_magenta": {"value": 0},
        "adjust_saturation_red": {"value": -20},
        "adjust_saturation_blue": {"value": -15},
        "adjust_luminance_red": {"value": -5},
        "adjust_luminance_blue": {"value": -10}
    },
    "reasoning": "NOIR STYLE: Use apply_style_preset with style='noir'. Applies balanced high-contrast dramatic B&W-ish look. Preset uses contrast 1.25, saturation 0.25, grain 0.03, vignette 0.6 - all carefully balanced values."
}

STYLE_SUNSET = {
    "keywords": ["sunset style", "warm style preset", "golden style"],
    "description": "Sunset warm style preset",
    "parameters": {
        "apply_style_preset": {"style": "sunset"}
    },
    "reasoning": "SUNSET STYLE: Use apply_style_preset with style='sunset'. Applies warm golden tones automatically."
}


STYLE_MOODY_BLUE = {
    "keywords": ["moody blue", "blue mood", "cool mood", "blue tones", "moody"],
    "description": "Moody blue atmospheric style",
    "parameters": {
        "apply_style_preset": {"style": "moody_blue"}
    },
    "reasoning": "MOODY BLUE: Use apply_style_preset with style='moody_blue'. Desaturated blue shadows, atmospheric."
}

STYLE_NIGHT = {
    "keywords": ["night style", "night preset", "night look", "dark night"],
    "description": "Night scene style preset",
    "parameters": {
        "apply_style_preset": {"style": "night"}
    },
    "reasoning": "NIGHT STYLE: Use apply_style_preset with style='night'. Cool blue tones, dark, moody."
}

STYLE_DEEP_NIGHT = {
    "keywords": ["deep night", "very dark night", "midnight", "ultra dark"],
    "description": "Very dark night style",
    "parameters": {
        "apply_style_preset": {"style": "deep_night"}
    },
    "reasoning": "DEEP NIGHT: Use apply_style_preset with style='deep_night'. Very dark with strong blue shadows."
}

STYLE_SYNTHWAVE = {
    "keywords": ["synthwave", "80s", "retro wave", "outrun", "vaporwave"],
    "description": "80s synthwave retro aesthetic",
    "parameters": {
        "apply_style_preset": {"style": "synthwave"}
    },
    "reasoning": "SYNTHWAVE: Use apply_style_preset with style='synthwave'. 80s aesthetic with pink/purple."
}

STYLE_BLADE_RUNNER = {
    "keywords": ["blade runner", "sci-fi", "dystopian", "futuristic city"],
    "description": "Blade Runner 2049 inspired look",
    "parameters": {
        "apply_style_preset": {"style": "blade_runner"}
    },
    "reasoning": "BLADE RUNNER: Use apply_style_preset with style='blade_runner'. Hazy teal/orange sci-fi look."
}

STYLE_BLOCKBUSTER = {
    "keywords": ["blockbuster", "hollywood", "action movie", "movie look"],
    "description": "Hollywood blockbuster color grade",
    "parameters": {
        "apply_style_preset": {"style": "blockbuster"}
    },
    "reasoning": "BLOCKBUSTER: Use apply_style_preset with style='blockbuster'. Modern Hollywood color grade."
}

STYLE_INDIE = {
    "keywords": ["indie film", "indie", "art film", "independent film"],
    "description": "Indie film aesthetic",
    "parameters": {
        "apply_style_preset": {"style": "indie_film"}
    },
    "reasoning": "INDIE FILM: Use apply_style_preset with style='indie_film'. Muted, natural, grainy."
}

STYLE_GOLDEN_HOUR = {
    "keywords": ["golden hour preset", "golden light", "magic hour"],
    "description": "Golden hour style preset",
    "parameters": {
        "apply_style_preset": {"style": "golden_hour"}
    },
    "reasoning": "GOLDEN HOUR: Use apply_style_preset with style='golden_hour'. Warm orange/gold with glow."
}

STYLE_DREAM = {
    "keywords": ["dream", "dreamy", "dreamlike", "fantasy"],
    "description": "Dreamy ethereal style",
    "parameters": {
        "apply_style_preset": {"style": "dream"}
    },
    "reasoning": "DREAM: Use apply_style_preset with style='dream'. Ethereal, soft, magical look."
}

STYLE_ETHEREAL = {
    "keywords": ["ethereal", "angelic", "heavenly", "light airy magical"],
    "description": "Light ethereal magical style",
    "parameters": {
        "apply_style_preset": {"style": "ethereal"}
    },
    "reasoning": "ETHEREAL: Use apply_style_preset with style='ethereal'. Light, airy, magical atmosphere."
}

STYLE_HORROR = {
    "keywords": ["horror", "scary", "creepy", "dark horror", "terrifying"],
    "description": "Horror movie aesthetic",
    "parameters": {
        "apply_style_preset": {"style": "horror"}
    },
    "reasoning": "HORROR: Use apply_style_preset with style='horror'. Dark, desaturated, greenish, scary."
}

STYLE_WESTERN = {
    "keywords": ["western", "wild west", "dusty", "desert", "cowboy"],
    "description": "Western movie style",
    "parameters": {
        "apply_style_preset": {"style": "western"}
    },
    "reasoning": "WESTERN: Use apply_style_preset with style='western'. Warm, dusty, faded look."
}

STYLE_POLAROID = {
    "keywords": ["polaroid", "instant", "instant film", "instax"],
    "description": "Polaroid instant film look",
    "parameters": {
        "apply_style_preset": {"style": "polaroid"}
    },
    "reasoning": "POLAROID: Use apply_style_preset with style='polaroid'. Faded with cyan shadows."
}

STYLE_KODACHROME = {
    "keywords": ["kodachrome", "kodak", "classic film", "film stock"],
    "description": "Kodachrome film simulation",
    "parameters": {
        "apply_style_preset": {"style": "kodachrome"}
    },
    "reasoning": "KODACHROME: Use apply_style_preset with style='kodachrome'. Classic saturated film look."
}

STYLE_RETRO_70S = {
    "keywords": ["70s", "seventies", "retro", "disco", "groovy"],
    "description": "1970s retro aesthetic",
    "parameters": {
        "apply_style_preset": {"style": "retro_70s"}
    },
    "reasoning": "70s RETRO: Use apply_style_preset with style='retro_70s'. Faded, warm, cross-processed."
}


VIGNETTE_SUBTLE = {
    "keywords": ["vignette", "edge darkening", "corner darkening", "subtle vignette"],
    "description": "Subtle vignette to draw attention to center",
    "parameters": {
        "apply_vignette": {
            "strength": 0.25,
            "radius": 0.85
        }
    },
    "reasoning": "VIGNETTE: Use apply_vignette! strength controls darkness (0-0.7 MAX), radius controls size (0-1). Subtle values: strength 0.2-0.3, radius 0.8-0.9."
}

VIGNETTE_DRAMATIC = {
    "keywords": ["strong vignette", "dramatic vignette", "heavy vignette"],
    "description": "Dramatic vignette - still balanced",
    "parameters": {
        "apply_vignette": {
            "strength": 0.5,
            "radius": 0.7
        }
    },
    "reasoning": "Dramatic vignette: strength 0.4-0.6 MAX, radius 0.6-0.75. NEVER exceed 0.7 strength - makes image too dark!"
}


GLOW_SOFT = {
    "keywords": ["glow", "bloom", "soft glow", "dreamy glow", "ethereal"],
    "description": "Soft glow/bloom effect",
    "parameters": {
        "apply_glow": {
            "intensity": 0.3,
            "radius": 25
        }
    },
    "reasoning": "GLOW: Use apply_glow! intensity controls strength (0-1), radius controls blur amount. Soft: intensity 0.2-0.4, radius 20-30."
}

GLOW_DREAMY = {
    "keywords": ["dreamy", "soft dreamy", "fairytale", "fantasy glow"],
    "description": "Dreamy fantasy glow effect",
    "parameters": {
        "apply_glow": {
            "intensity": 0.5,
            "radius": 40
        },
        "adjust_highlights": {"value": 5}
    },
    "reasoning": "Dreamy glow: higher intensity (0.4-0.6), larger radius (35-50). Creates soft fantasy atmosphere."
}


GRAIN_SUBTLE = {
    "keywords": ["grain", "film grain", "noise", "texture", "subtle grain"],
    "description": "Subtle film grain for analog feel",
    "parameters": {
        "apply_grain": {
            "intensity": 0.02,
            "size": 1.0
        }
    },
    "reasoning": "GRAIN: Use apply_grain! intensity controls visibility (0-0.08 MAX), size controls grain size. Subtle: 0.02-0.03 intensity. NEVER go above 0.08!"
}

GRAIN_VINTAGE = {
    "keywords": ["heavy grain", "old film grain", "vintage grain", "grainy"],
    "description": "Heavy vintage film grain - still subtle",
    "parameters": {
        "apply_grain": {
            "intensity": 0.05,
            "size": 1.2
        }
    },
    "reasoning": "Heavy grain: intensity 0.04-0.06 MAX, size 1.0-1.5. NEVER exceed 0.08 intensity - causes posterization!"
}



HAZE_SOFT = {
    "keywords": ["haze", "atmospheric haze", "foggy", "misty", "soft haze"],
    "description": "Soft atmospheric haze",
    "parameters": {
        "apply_haze": {
            "intensity": 0.2,
            "color": [220, 220, 230]
        }
    },
    "reasoning": "HAZE: Use apply_haze! intensity controls strength (0-1), color is the haze tint. Soft: 0.15-0.25, neutral gray-blue."
}

HAZE_WARM = {
    "keywords": ["warm haze", "golden haze", "morning haze", "dusty"],
    "description": "Warm golden haze effect",
    "parameters": {
        "apply_haze": {
            "intensity": 0.25,
            "color": [255, 240, 200]
        }
    },
    "reasoning": "Warm haze: intensity 0.2-0.3, warm golden color [255,240,200]. Creates dusty morning atmosphere."
}



CURVES_FADE = {
    "keywords": ["fade", "faded blacks", "lifted blacks curves", "matte look curves"],
    "description": "Faded/lifted blacks using curves",
    "parameters": {
        "apply_curves": {
            "points": [[0, 30], [64, 80], [128, 128], [192, 180], [255, 240]]
        }
    },
    "reasoning": "CURVES for fade: Use apply_curves with points array. Lifted blacks: start at [0,30] not [0,0]. Creates matte/faded look."
}

CURVES_S_CONTRAST = {
    "keywords": ["s curve", "s-curve contrast", "curves contrast"],
    "description": "Classic S-curve for contrast boost",
    "parameters": {
        "apply_curves": {
            "points": [[0, 0], [64, 50], [128, 128], [192, 206], [255, 255]]
        }
    },
    "reasoning": "S-curve: shadows pulled down [64,50], highlights lifted [192,206]. Creates smooth contrast increase."
}



DREAMY_PORTRAIT = {
    "keywords": ["dreamy portrait", "soft portrait", "ethereal portrait"],
    "description": "Dreamy portrait with glow and vignette",
    "parameters": {
        "adjust_temp_tint": {"temp": 8, "tint": 3},
        "adjust_contrast": {"value": 0.95},
        "adjust_highlights": {"value": -10},
        "adjust_shadows": {"value": 15},
        "apply_glow": {"intensity": 0.35, "radius": 30},
        "apply_vignette": {"strength": 0.25, "radius": 0.85}
    },
    "reasoning": "Dreamy portrait: combine soft glow, subtle vignette, low contrast, lifted shadows. Creates ethereal look."
}

VINTAGE_FILM = {
    "keywords": ["film look", "analog look", "35mm look", "vintage film complete"],
    "description": "Complete vintage film look with grain and curves",
    "parameters": {
        "adjust_temp_tint": {"temp": 15, "tint": 5},
        "adjust_contrast": {"value": 0.95},
        "adjust_saturation": {"scale": 0.92},
        "apply_grain": {"intensity": 0.03, "size": 1.1},
        "apply_curves": {"points": [[0, 20], [64, 75], [128, 128], [192, 185], [255, 245]]},
        "apply_vignette": {"strength": 0.25, "radius": 0.8}
    },
    "reasoning": "Complete vintage film: grain 0.03 (subtle!) + faded blacks curves + vignette + warm tint + desaturation. NEVER exceed grain 0.05!"
}

CINEMATIC_COLOR_GRADE = {
    "keywords": ["cinematic color grade", "movie color grade", "hollywood grade"],
    "description": "Full cinematic color grading with split toning",
    "parameters": {
        "apply_split_toning": {
            "shadow_color": [30, 70, 90],
            "highlight_color": [255, 190, 120],
            "balance": 0.45
        },
        "adjust_contrast": {"value": 1.12},
        "adjust_highlights": {"value": -8},
        "adjust_shadows": {"value": 5},
        "apply_vignette": {"strength": 0.2, "radius": 0.85}
    },
    "reasoning": "Cinematic grade: split toning (teal shadows, orange highlights) + contrast + subtle vignette. Hollywood look."
}

MOODY_NIGHT = {
    "keywords": ["moody night", "dark night", "atmospheric night", "night mood"],
    "description": "Moody night with cool split toning and vignette",
    "parameters": {
        "adjust_temp_tint": {"temp": -12, "tint": 0},
        "adjust_exposure": {"value": -10},
        "adjust_contrast": {"value": 1.15},
        "adjust_shadows": {"value": -15},
        "adjust_blacks": {"value": -12},
        "apply_split_toning": {
            "shadow_color": [20, 40, 80],
            "highlight_color": [180, 160, 140],
            "balance": 0.3
        },
        "apply_vignette": {"strength": 0.4, "radius": 0.7}
    },
    "reasoning": "Moody night: cool temp + deep shadows + blue shadow split toning + strong vignette. Atmospheric darkness."
}


ALL_EXAMPLES = [
    GOLDEN_HOUR_SUBTLE,
    GOLDEN_HOUR_DRAMATIC,
    MORNING_LIGHT,
    NIGHT_PRESET,
    NIGHT_DEEP,
    NIGHT_BLUE_HOUR,
    NIGHT_NATURAL,
    BLUE_HOUR,
    BLACK_AND_WHITE_CLASSIC,
    BLACK_AND_WHITE_HIGH_CONTRAST,
    DEEP_SHADOWS,
    LIFTED_SHADOWS,
    HIGH_CONTRAST,
    LOW_CONTRAST,
    MOODY_DARK,
    NOIR,
    NOIR_NEO,
    NOIR_DARK,
    GLOOMY,
    CINEMATIC,
    VINTAGE,
    VIBRANT,
    NATURAL,
    BRIGHT_AIRY,
    CYBERPUNK,
    DUOTONE_CLASSIC,
    DUOTONE_TEAL_ORANGE,
    DUOTONE_BLUE_GOLD,
    DUOTONE_SEPIA,
    DUOTONE_COOL,
    SPLIT_TONE_TEAL_ORANGE,
    SPLIT_TONE_WARM_COOL,
    STYLE_CYBERPUNK,
    STYLE_VINTAGE,
    STYLE_NOIR,
    STYLE_SUNSET,
    STYLE_MOODY_BLUE,
    STYLE_NIGHT,
    STYLE_DEEP_NIGHT,
    STYLE_SYNTHWAVE,
    STYLE_BLADE_RUNNER,
    STYLE_BLOCKBUSTER,
    STYLE_INDIE,
    STYLE_GOLDEN_HOUR,
    STYLE_DREAM,
    STYLE_ETHEREAL,
    STYLE_HORROR,
    STYLE_WESTERN,
    STYLE_POLAROID,
    STYLE_KODACHROME,
    STYLE_RETRO_70S,
    VIGNETTE_SUBTLE,
    VIGNETTE_DRAMATIC,
    GLOW_SOFT,
    GLOW_DREAMY,
    GRAIN_SUBTLE,
    GRAIN_VINTAGE,
    HAZE_SOFT,
    HAZE_WARM,
    CURVES_FADE,
    CURVES_S_CONTRAST,
    DREAMY_PORTRAIT,
    VINTAGE_FILM,
    CINEMATIC_COLOR_GRADE,
    MOODY_NIGHT,
]


def find_matching_examples(user_prompt: str, max_examples: int = 2) -> list:
    user_lower = user_prompt.lower()
    scored = []

    for example in ALL_EXAMPLES:
        keywords = example["keywords"]
        score = 0

        for kw in keywords:
            if kw.lower() in user_lower:
                score += 15
            for word in kw.lower().split():
                if len(word) > 2 and word in user_lower:
                    score += 3

        if score > 0:
            scored.append((score, example))

    scored.sort(key=lambda x: -x[0])
    return [ex for _, ex in scored[:max_examples]]


def format_examples_for_prompt(examples: list) -> str:
    if not examples:
        return ""

    lines = ["\n=== EXPERT REFERENCE EXAMPLES (COPY THESE VALUES!) ==="]
    lines.append("These examples are professionally tuned. USE SIMILAR VALUES!\n")

    for i, ex in enumerate(examples, 1):
        lines.append(f"EXAMPLE {i}: {ex['description']}")
        lines.append(f"KEY INSIGHT: {ex['reasoning']}")
        lines.append("EXACT Parameters to use as reference:")
        lines.append(json.dumps(ex['parameters'], indent=2))
        lines.append("")

    lines.append("=== CRITICAL RULES ===")
    lines.append("1. For NIGHT: temp = -5 to -15 ONLY (NOT -50!), saturation <= 1.1")
    lines.append("2. For B&W: saturation MUST be exactly 0.0")
    lines.append("3. For GOLDEN HOUR: temp = 30-50, saturation 1.1-1.15")
    lines.append("4. NEVER use saturation > 1.3 - it looks unnatural")
    lines.append("5. PROTECT highlights with negative values (-10 to -20)")
    lines.append("")
    lines.append("=== CREATIVE EFFECTS - USE THE RIGHT TOOL! ===")
    lines.append("6. For DUOTONE: USE apply_duotone, NOT color mixer!")
    lines.append("7. For SPLIT TONING: USE apply_split_toning for shadow/highlight color separation")
    lines.append("8. For STYLE PRESETS: USE apply_style_preset (cyberpunk, vintage, noir, sunset, etc.)")
    lines.append("9. For VIGNETTE: USE apply_vignette - strength 0.2-0.5 MAX, NEVER above 0.7!")
    lines.append("10. For GLOW/BLOOM: USE apply_glow (intensity 0.1-0.3, radius 15-35)")
    lines.append("11. For GRAIN: USE apply_grain - intensity 0.02-0.05 MAX, NEVER above 0.08!")
    lines.append("12. For HAZE/FOG: USE apply_haze (intensity 0.1-0.25, color [R,G,B])")
    lines.append("13. For CURVES: USE apply_curves (points array)")
    lines.append("")
    lines.append("=== ABSOLUTE LIMITS (WILL BE CLAMPED) ===")
    lines.append("- contrast: 0.8 to 1.35 (1.25 is punchy, 1.35 is dramatic MAX)")
    lines.append("- grain intensity: 0.02-0.05 natural, 0.08 absolute MAX")
    lines.append("- vignette strength: 0.2-0.4 subtle, 0.7 absolute MAX")
    lines.append("- exposure: -35 to +15")
    lines.append("=== END EXAMPLES ===\n")

    return "\n".join(lines)


def get_example_prompt_addition(user_prompt: str) -> str:
    examples = find_matching_examples(user_prompt, max_examples=2)
    return format_examples_for_prompt(examples)


if __name__ == "__main__":
    test_prompts = [
        "Make it look like golden hour",
        "Convert to black and white",
        "Make it night time",
        "Add deeper shadows",
        "Make it moody and dark",
    ]

    for prompt in test_prompts:
        print(f"\n{'='*60}")
        print(f"PROMPT: {prompt}")
        examples = find_matching_examples(prompt)
        for ex in examples:
            print(f"  -> {ex['description']}")
            print(f"     Temp: {ex['parameters']['adjust_temp_tint']['temp']}, Sat: {ex['parameters']['adjust_saturation']['scale']}")
