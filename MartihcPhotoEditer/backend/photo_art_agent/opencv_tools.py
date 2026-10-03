import cv2
import numpy as np
import torch

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
USE_GPU = torch.cuda.is_available()

if USE_GPU:
    print(f" GPU acceleration enabled: {torch.cuda.get_device_name(0)}")
else:
    print(" GPU not available, using CPU")

def _to_tensor(image):
    if USE_GPU:
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb).float() / 255.0
        return tensor.to(DEVICE).permute(2, 0, 1)
    return image

def _from_tensor(tensor_or_image):
    if USE_GPU and isinstance(tensor_or_image, torch.Tensor):
        img = tensor_or_image.permute(1, 2, 0).cpu().numpy()
        img = (img * 255.0).clip(0, 255).astype(np.uint8)
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return tensor_or_image


def adjust_exposure(image, value=0.0):

    if USE_GPU:
        tensor = _to_tensor(image)
        tensor = tensor + (value / 255.0)
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    return cv2.convertScaleAbs(image, alpha=1.0, beta=value)

def adjust_contrast(image, value=1.0):

    if USE_GPU:
        tensor = _to_tensor(image)
        tensor = (tensor - 0.5) * value + 0.5
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    return cv2.convertScaleAbs(image, alpha=value, beta=0)

def _adjust_masked(image, value, threshold, mode):
    if USE_GPU:
        tensor = _to_tensor(image)
        r, g, b = tensor[0], tensor[1], tensor[2]

        threshold_norm = threshold / 255.0
        if mode == 'highlight':
            mask = (r > threshold_norm).float()
        elif mode == 'shadow':
            mask = (r < threshold_norm).float()

        adjustment = (value / 255.0) * mask.unsqueeze(0)
        tensor = tensor + adjustment
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    else:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        if mode == 'highlight':
            mask = cv2.threshold(v, threshold, 255, cv2.THRESH_BINARY)[1]
        elif mode == 'shadow':
            mask = cv2.threshold(v, threshold, 255, cv2.THRESH_BINARY_INV)[1]
        v_float = v.astype(np.float32)
        v_float[mask > 0] += value
        v = np.clip(v_float, 0, 255).astype(np.uint8)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

def adjust_highlights(image, value=-10.0):

    return _adjust_masked(image, value, 200, 'highlight')


def adjust_shadows(image, value=10.0):

    return _adjust_masked(image, -value, 80, 'shadow')

def adjust_whites(image, value=0.0):

    return _adjust_masked(image, value, 230, 'highlight')

def adjust_blacks(image, value=0.0):
    return _adjust_masked(image, value, 40, 'shadow')



def adjust_temp_tint(image, temp=0.0, tint=0.0):

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b_ch = cv2.split(lab)


    b_adj = temp * 0.25
    b_float = b_ch.astype(np.float32) + b_adj
    b_ch = np.clip(b_float, 0, 255).astype(np.uint8)

    a_adj = tint * 0.20
    a_float = a.astype(np.float32) + a_adj
    a = np.clip(a_float, 0, 255).astype(np.uint8)

    final_lab = cv2.merge((l, a, b_ch))
    return cv2.cvtColor(final_lab, cv2.COLOR_LAB2BGR)

def adjust_saturation(image, scale=1.0):

    if USE_GPU:
        tensor = _to_tensor(image)
        r, g, b = tensor[0], tensor[1], tensor[2]
        gray = 0.299 * r + 0.587 * g + 0.114 * b
        r = gray + (r - gray) * scale
        g = gray + (g - gray) * scale
        b = gray + (b - gray) * scale
        tensor = torch.stack([r, g, b])
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    else:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s_float = s.astype(np.float32)
        s_float *= scale
        s = np.clip(s_float, 0, 255).astype(np.uint8)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

def adjust_vibrance(image, strength=0.5):
    if USE_GPU:
        tensor = _to_tensor(image)
        r, g, b = tensor[0], tensor[1], tensor[2]
        gray = 0.299 * r + 0.587 * g + 0.114 * b

        sat = torch.sqrt((r - gray)**2 + (g - gray)**2 + (b - gray)**2)
        sat_norm = sat / (torch.max(sat) + 1e-6)

        vibrance_mask = 1.0 - sat_norm

        scale = 1.0 + strength * vibrance_mask
        r = gray + (r - gray) * scale
        g = gray + (g - gray) * scale
        b = gray + (b - gray) * scale

        tensor = torch.stack([r, g, b])
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    else:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s_float = s.astype(np.float32) / 255.0
        vibrance_mask = 1.0 - s_float
        s_change = strength * vibrance_mask * s_float * 255.0
        s_new = s.astype(np.float32) + s_change
        s = np.clip(s_new, 0, 255).astype(np.uint8)
        final_hsv = cv2.merge((h, s, v))
        return cv2.cvtColor(final_hsv, cv2.COLOR_HSV2BGR)

def adjust_color_mixer(
    image,
    red=None,
    orange=None,
    yellow=None,
    green=None,
    cyan=None,
    blue=None,
    purple=None
):

    params = {
        "red": red,
        "orange": orange,
        "yellow": yellow,
        "green": green,
        "cyan": cyan,
        "blue": blue,
        "purple": purple
    }

    if USE_GPU:
        tensor = _to_tensor(image)
        r, g, b = tensor[0], tensor[1], tensor[2]

        max_val = torch.max(torch.stack([r, g, b]), dim=0)[0]
        min_val = torch.min(torch.stack([r, g, b]), dim=0)[0]
        delta = max_val - min_val
        h = torch.zeros_like(r)
        mask_r = (max_val == r) & (delta != 0)
        mask_g = (max_val == g) & (delta != 0)
        mask_b = (max_val == b) & (delta != 0)
        h[mask_r] = (((g[mask_r] - b[mask_r]) / (delta[mask_r] + 1e-6)) % 6) / 6.0
        h[mask_g] = (((b[mask_g] - r[mask_g]) / (delta[mask_g] + 1e-6)) + 2) / 6.0
        h[mask_b] = (((r[mask_b] - g[mask_b]) / (delta[mask_b] + 1e-6)) + 4) / 6.0
        h = h * 180.0

        ranges = {
            'red': (h <= 10) | (h >= 170),
            'orange': (h >= 11) & (h <= 25),
            'yellow': (h >= 26) & (h <= 34),
            'green': (h >= 35) & (h <= 85),
            'cyan': (h >= 86) & (h <= 100),
            'blue': (h >= 101) & (h <= 130),
            'purple': (h >= 131) & (h <= 169)
        }

        for channel, cfg in params.items():
            if cfg is None:
                continue
            mask = ranges[channel]

            hue_shift = cfg.get("hue_shift", 0)
            sat_scale = cfg.get("sat_scale", 1.0)
            lum_scale = cfg.get("lum_scale", 1.0)

            hue_shift_norm = hue_shift / 180.0
            if hue_shift_norm != 0:
                angle = hue_shift_norm * 2 * 3.14159
                cos_a, sin_a = torch.cos(angle), torch.sin(angle)
                r_new = r * cos_a - g * sin_a
                g_new = r * sin_a + g * cos_a
                r = torch.where(mask, r_new, r)
                g = torch.where(mask, g_new, g)

            gray = 0.299 * r + 0.587 * g + 0.114 * b
            r = torch.where(mask, gray + (r - gray) * sat_scale * lum_scale, r)
            g = torch.where(mask, gray + (g - gray) * sat_scale * lum_scale, g)
            b = torch.where(mask, gray + (b - gray) * sat_scale * lum_scale, b)

        tensor = torch.stack([r, g, b])
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)

    hls = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    h, l, s = cv2.split(hls)

    ranges = {
        'red': (h <= 10) | (h >= 170),
        'orange': (h >= 11) & (h <= 25),
        'yellow': (h >= 26) & (h <= 34),
        'green': (h >= 35) & (h <= 85),
        'cyan': (h >= 86) & (h <= 100),
        'blue': (h >= 101) & (h <= 130),
        'purple': (h >= 131) & (h <= 169)
    }

    for channel, cfg in params.items():
        if cfg is None:
            continue
        mask = ranges[channel]

        hue_shift = cfg.get("hue_shift", 0)
        sat_scale = cfg.get("sat_scale", 1.0)
        lum_scale = cfg.get("lum_scale", 1.0)

        h_float = h.astype(np.float32)
        h_float[mask] = (h_float[mask] + hue_shift) % 180
        h = h_float.astype(np.uint8)

        s_float = s.astype(np.float32)
        s_float[mask] *= sat_scale
        s = np.clip(s_float, 0, 255).astype(np.uint8)

        l_float = l.astype(np.float32)
        l_float[mask] *= lum_scale
        l = np.clip(l_float, 0, 255).astype(np.uint8)

    final_hls = cv2.merge((h, l, s))
    return cv2.cvtColor(final_hls, cv2.COLOR_HLS2BGR)



def apply_split_toning(image, shadow_hue=220, shadow_sat=0.3, highlight_hue=40, highlight_sat=0.2):

    if USE_GPU:
        tensor = _to_tensor(image)
        r, g, b = tensor[0], tensor[1], tensor[2]
        luminance = 0.299 * r + 0.587 * g + 0.114 * b

        shadow_mask = torch.clamp(1.0 - luminance * 2, 0, 1)
        highlight_mask = torch.clamp(luminance * 2 - 1, 0, 1)

        def hue_to_rgb(hue):
            h = (hue % 360) / 60.0
            x = 1 - abs(h % 2 - 1)
            if h < 1: return (1, x, 0)
            elif h < 2: return (x, 1, 0)
            elif h < 3: return (0, 1, x)
            elif h < 4: return (0, x, 1)
            elif h < 5: return (x, 0, 1)
            else: return (1, 0, x)

        sr, sg, sb = hue_to_rgb(shadow_hue)
        hr, hg, hb = hue_to_rgb(highlight_hue)

        r = r + (sr - 0.5) * shadow_mask * shadow_sat
        g = g + (sg - 0.5) * shadow_mask * shadow_sat
        b = b + (sb - 0.5) * shadow_mask * shadow_sat

        r = r + (hr - 0.5) * highlight_mask * highlight_sat
        g = g + (hg - 0.5) * highlight_mask * highlight_sat
        b = b + (hb - 0.5) * highlight_mask * highlight_sat

        tensor = torch.stack([r, g, b])
        tensor = torch.clamp(tensor, 0, 1)
        return _from_tensor(tensor)
    else:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
        l, a, b_ch = cv2.split(lab)
        l_norm = l / 255.0

        shadow_mask = np.clip(1.0 - l_norm * 2, 0, 1)
        highlight_mask = np.clip(l_norm * 2 - 1, 0, 1)

        def hue_to_ab(hue):

            rad = np.radians(hue)
            a_shift = np.sin(rad) * 40
            b_shift = np.cos(rad) * 40
            return a_shift, b_shift

        s_a, s_b = hue_to_ab(shadow_hue)
        a = a + shadow_mask * s_a * shadow_sat
        b_ch = b_ch + shadow_mask * s_b * shadow_sat

        h_a, h_b = hue_to_ab(highlight_hue)
        a = a + highlight_mask * h_a * highlight_sat
        b_ch = b_ch + highlight_mask * h_b * highlight_sat

        a = np.clip(a, 0, 255).astype(np.uint8)
        b_ch = np.clip(b_ch, 0, 255).astype(np.uint8)
        l = l.astype(np.uint8)

        final_lab = cv2.merge((l, a, b_ch))
        return cv2.cvtColor(final_lab, cv2.COLOR_LAB2BGR)


def apply_color_overlay(image, color=(255, 100, 50), opacity=0.2, blend_mode="overlay"):

    overlay = np.full_like(image, color, dtype=np.float32)
    base = image.astype(np.float32) / 255.0
    overlay = overlay / 255.0

    if blend_mode == "overlay":
        result = np.where(base < 0.5,
                         2 * base * overlay,
                         1 - 2 * (1 - base) * (1 - overlay))
    elif blend_mode == "multiply":
        result = base * overlay
    elif blend_mode == "screen":
        result = 1 - (1 - base) * (1 - overlay)
    elif blend_mode == "soft_light":
        result = np.where(overlay < 0.5,
                         base - (1 - 2 * overlay) * base * (1 - base),
                         base + (2 * overlay - 1) * (np.sqrt(base) - base))
    else:
        result = base

    blended = base * (1 - opacity) + result * opacity
    return (np.clip(blended, 0, 1) * 255).astype(np.uint8)


def apply_curves(image, shadows=0, midtones=0, highlights=0, points=None, curve=None):

    lut = np.arange(256, dtype=np.float32)

    shadow_curve = 1 + shadows / 200.0
    lut = lut + (shadows / 2.0) * np.exp(-lut / 64.0)

    lut = np.clip(lut, 0.001, 255)

    gamma = 1.0 - midtones / 200.0
    gamma = max(0.2, min(5.0, gamma))
    lut = 255 * np.power(lut / 255.0, gamma)

    lut = lut + (highlights / 2.0) * (1 - np.exp(-(lut - 192) / 64.0)) * (lut > 128)

    lut = np.clip(lut, 0, 255).astype(np.uint8)
    return cv2.LUT(image, lut)



def apply_vignette(image, strength=0.5, radius=0.8):

    rows, cols = image.shape[:2]
    center_x, center_y = cols / 2, rows / 2
    max_dist = np.sqrt(center_x**2 + center_y**2)

    Y, X = np.ogrid[:rows, :cols]
    dist = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    dist_norm = dist / max_dist

    vignette = 1 - strength * np.clip((dist_norm - radius) / (1 - radius), 0, 1) ** 2
    vignette = vignette[:, :, np.newaxis]

    result = image.astype(np.float32) * vignette
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_glow(image, intensity=0.3, radius=21):

    if radius % 2 == 0:
        radius += 1

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, highlights = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    glow = cv2.GaussianBlur(image, (radius, radius), 0)
    glow_mask = cv2.GaussianBlur(highlights, (radius, radius), 0)
    glow_mask = glow_mask[:, :, np.newaxis] / 255.0

    base = image.astype(np.float32) / 255.0
    glow = glow.astype(np.float32) / 255.0

    result = 1 - (1 - base) * (1 - glow * glow_mask * intensity)
    return (np.clip(result, 0, 1) * 255).astype(np.uint8)


def apply_grain(image, amount=0.03, size=1, strength=None, intensity=None):

    if strength is not None:
        amount = strength
    if intensity is not None:
        amount = intensity

    amount = float(amount)
    if amount > 1.0:
        amount = amount / 100.0
    amount = min(amount, 0.08)

    size = max(1, min(2, int(size)))

    rows, cols = image.shape[:2]
    grain = np.random.normal(0, 1, (rows // size, cols // size))
    grain = cv2.resize(grain, (cols, rows), interpolation=cv2.INTER_LINEAR)
    grain = grain[:, :, np.newaxis] * amount * 40

    result = image.astype(np.float32) + grain
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_duotone(image, dark_color=(20, 0, 80), light_color=(255, 200, 100)):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0

    result = np.zeros_like(image, dtype=np.float32)
    for i in range(3):
        result[:, :, i] = dark_color[i] * (1 - gray) + light_color[i] * gray

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_haze(image, amount=0.2, color=(200, 180, 160)):

    haze = np.full_like(image, color, dtype=np.float32)
    result = image.astype(np.float32) * (1 - amount) + haze * amount
    return np.clip(result, 0, 255).astype(np.uint8)


def apply_film_fade(image, fade_amount=0.3, black_fade=0.15):

    result = image.astype(np.float32)

    black_lift = black_fade * 255
    result = result + black_lift

    highlight_compress = 1.0 - (fade_amount * 0.3)
    result = result * highlight_compress + (255 * (1 - highlight_compress) * 0.5)

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_clarity(image, amount=0.5):

    blur = cv2.GaussianBlur(image, (0, 0), 10)

    if amount >= 0:
        result = cv2.addWeighted(image, 1 + amount, blur, -amount, 0)
    else:
        result = cv2.addWeighted(image, 1 + amount, blur, -amount, 0)

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_dehaze(image, amount=0.5):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0 + amount * 2, tileGridSize=(8, 8))
    l = clahe.apply(l)

    result = cv2.merge([l, a, b])
    return cv2.cvtColor(result, cv2.COLOR_LAB2BGR)


def apply_orton_effect(image, blur_amount=25, blend=0.3):

    if blur_amount % 2 == 0:
        blur_amount += 1

    bright = cv2.convertScaleAbs(image, alpha=1.3, beta=20)
    blur = cv2.GaussianBlur(bright, (blur_amount, blur_amount), 0)

    base = image.astype(np.float32) / 255.0
    overlay = blur.astype(np.float32) / 255.0
    multiplied = base * overlay * 1.5

    result = base * (1 - blend) + multiplied * blend
    return (np.clip(result, 0, 1) * 255).astype(np.uint8)


def apply_cross_process(image, intensity=0.5):

    result = image.astype(np.float32)
    b, g, r = cv2.split(result)

    b = b * (1 - intensity * 0.2) + intensity * 40
    g = g * (1 + intensity * 0.1)
    r = np.where(r > 128, r + intensity * 30, r - intensity * 20)

    result = cv2.merge([
        np.clip(b, 0, 255).astype(np.uint8),
        np.clip(g, 0, 255).astype(np.uint8),
        np.clip(r, 0, 255).astype(np.uint8)
    ])
    return result


def apply_bleach_bypass(image, intensity=0.5):

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    desat = cv2.addWeighted(image, 1 - intensity * 0.6, gray_bgr, intensity * 0.6, 0)

    contrast_boost = 1.0 + intensity * 0.4
    result = cv2.convertScaleAbs(desat, alpha=contrast_boost, beta=-intensity * 20)

    return result


def apply_teal_and_orange(image, intensity=0.5):

    result = image.astype(np.float32)
    b, g, r = cv2.split(result)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    shadow_mask = np.clip(1.0 - gray * 2, 0, 1)
    highlight_mask = np.clip(gray * 2 - 1, 0, 1)

    b = b + shadow_mask * intensity * 40
    g = g + shadow_mask * intensity * 20
    r = r - shadow_mask * intensity * 20

    r = r + highlight_mask * intensity * 35
    g = g + highlight_mask * intensity * 15
    b = b - highlight_mask * intensity * 30

    result = cv2.merge([
        np.clip(b, 0, 255).astype(np.uint8),
        np.clip(g, 0, 255).astype(np.uint8),
        np.clip(r, 0, 255).astype(np.uint8)
    ])
    return result


def apply_lut_color_grade(image, style="neutral"):

    if style == "neutral":
        return image

    result = image.astype(np.float32)
    b, g, r = cv2.split(result)

    if style == "warm_contrast":
        r = r * 1.1 + 5
        g = g * 1.02
        b = b * 0.95 - 5
        result = cv2.merge([np.clip(b, 0, 255), np.clip(g, 0, 255), np.clip(r, 0, 255)])
        result = adjust_contrast(result.astype(np.uint8), value=1.15)

    elif style == "cool_matte":
        b = b * 1.08 + 10
        g = g * 1.02 + 5
        r = r * 0.95
        result = cv2.merge([np.clip(b, 0, 255), np.clip(g, 0, 255), np.clip(r, 0, 255)])
        result = apply_film_fade(result.astype(np.uint8), fade_amount=0.2, black_fade=0.1)

    elif style == "vibrant_pop":
        result = adjust_saturation(image, scale=1.3)
        result = adjust_vibrance(result, strength=0.4)
        result = apply_clarity(result, amount=0.3)

    elif style == "film_emulation":
        result = apply_film_fade(image, fade_amount=0.25, black_fade=0.08)
        result = apply_split_toning(result, shadow_hue=220, shadow_sat=0.15,
                                   highlight_hue=45, highlight_sat=0.12)
        result = apply_grain(result, amount=0.08, size=1)

    elif style == "faded_pastel":
        result = adjust_exposure(image, value=15)
        result = adjust_contrast(result, value=0.85)
        result = adjust_saturation(result, scale=0.75)
        result = apply_film_fade(result, fade_amount=0.35, black_fade=0.2)

    return result.astype(np.uint8) if isinstance(result, np.ndarray) else result



def apply_style_preset(image, style="none"):

    if style == "none" or not style:
        return image

    result = image.copy()
    style = style.lower().replace("-", "_").replace(" ", "_")

    if style in ["noir", "classic_noir"]:
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_contrast(result, value=1.25)
        result = apply_curves(result, shadows=-15, midtones=5, highlights=10)
        result = apply_vignette(result, strength=0.45, radius=0.6)
        result = apply_grain(result, amount=0.03, size=1)

    elif style == "neo_noir":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        mask = gray.astype(np.float32) / 255.0
        mask = np.clip(mask * 2 - 0.5, 0, 1)[:, :, np.newaxis]
        result = (gray_bgr.astype(np.float32) * (1 - mask * 0.3) +
                  result.astype(np.float32) * mask * 0.3).astype(np.uint8)
        result = adjust_contrast(result, value=1.3)
        result = apply_split_toning(result, shadow_hue=240, shadow_sat=0.15,
                                   highlight_hue=350, highlight_sat=0.1)
        result = apply_vignette(result, strength=0.5, radius=0.6)

    elif style == "dark_noir":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_exposure(result, value=-20)
        result = adjust_contrast(result, value=1.35)
        result = apply_curves(result, shadows=-20, midtones=0, highlights=10)
        result = apply_vignette(result, strength=0.6, radius=0.5)
        result = apply_grain(result, amount=0.04, size=1)

    elif style == "night":
        result = adjust_exposure(result, value=-20)
        result = apply_split_toning(result, shadow_hue=220, shadow_sat=0.35,
                                   highlight_hue=200, highlight_sat=0.15)
        result = adjust_contrast(result, value=1.15)
        result = adjust_saturation(result, scale=0.85)
        result = apply_vignette(result, strength=0.5, radius=0.65)

    elif style == "deep_night":
        result = adjust_exposure(result, value=-35)
        result = apply_split_toning(result, shadow_hue=230, shadow_sat=0.4,
                                   highlight_hue=210, highlight_sat=0.2)
        result = adjust_contrast(result, value=1.2)
        result = adjust_saturation(result, scale=0.7)
        result = apply_vignette(result, strength=0.6, radius=0.55)
        result = apply_grain(result, amount=0.025, size=1)

    elif style == "blue_hour":
        result = adjust_exposure(result, value=-12)
        result = apply_split_toning(result, shadow_hue=235, shadow_sat=0.35,
                                   highlight_hue=280, highlight_sat=0.15)
        result = adjust_temp_tint(result, temp=-20, tint=3)
        result = adjust_saturation(result, scale=0.9)
        result = apply_haze(result, amount=0.05, color=(200, 180, 220))

    elif style == "midnight":
        result = adjust_exposure(result, value=-30)
        result = apply_split_toning(result, shadow_hue=240, shadow_sat=0.45,
                                   highlight_hue=220, highlight_sat=0.2)
        result = adjust_contrast(result, value=1.25)
        result = adjust_saturation(result, scale=0.6)
        result = apply_vignette(result, strength=0.6, radius=0.5)

    elif style == "cyberpunk":
        result = apply_split_toning(result, shadow_hue=280, shadow_sat=0.3,
                                   highlight_hue=180, highlight_sat=0.25)
        result = apply_color_overlay(result, color=(255, 0, 120), opacity=0.08, blend_mode="screen")
        result = adjust_contrast(result, value=1.2)
        result = adjust_saturation(result, scale=1.25)
        result = apply_vignette(result, strength=0.4, radius=0.7)
        result = apply_glow(result, intensity=0.2, radius=25)

    elif style == "neon":
        result = adjust_saturation(result, scale=1.4)
        result = adjust_vibrance(result, strength=0.4)
        result = adjust_contrast(result, value=1.2)
        result = apply_glow(result, intensity=0.25, radius=25)
        result = apply_vignette(result, strength=0.4, radius=0.7)

    elif style == "synthwave":
        result = apply_split_toning(result, shadow_hue=270, shadow_sat=0.35,
                                   highlight_hue=320, highlight_sat=0.25)
        result = apply_color_overlay(result, color=(255, 50, 150), opacity=0.1, blend_mode="screen")
        result = adjust_contrast(result, value=1.15)
        result = adjust_saturation(result, scale=1.3)
        result = apply_glow(result, intensity=0.2, radius=31)
        result = apply_grain(result, amount=0.025, size=1)

    elif style == "blade_runner":
        result = apply_teal_and_orange(result, intensity=0.4)
        result = apply_haze(result, amount=0.08, color=(180, 160, 140))
        result = adjust_contrast(result, value=1.15)
        result = apply_split_toning(result, shadow_hue=190, shadow_sat=0.2,
                                   highlight_hue=35, highlight_sat=0.25)
        result = apply_vignette(result, strength=0.4, radius=0.7)
        result = apply_glow(result, intensity=0.12, radius=21)

    elif style == "moody_blue":
        result = apply_split_toning(result, shadow_hue=215, shadow_sat=0.35,
                                   highlight_hue=225, highlight_sat=0.15)
        result = adjust_saturation(result, scale=0.75)
        result = adjust_exposure(result, value=-12)
        result = adjust_contrast(result, value=1.1)
        result = apply_haze(result, amount=0.06, color=(180, 190, 220))
        result = apply_vignette(result, strength=0.4, radius=0.7)

    elif style == "moody_dark":
        result = adjust_exposure(result, value=-18)
        result = adjust_contrast(result, value=1.2)
        result = adjust_saturation(result, scale=0.8)
        result = apply_curves(result, shadows=-15, midtones=-5, highlights=0)
        result = apply_vignette(result, strength=0.5, radius=0.6)

    elif style == "atmospheric":
        result = adjust_exposure(result, value=-8)
        result = apply_haze(result, amount=0.1, color=(190, 185, 200))
        result = apply_split_toning(result, shadow_hue=220, shadow_sat=0.2,
                                   highlight_hue=45, highlight_sat=0.1)
        result = adjust_contrast(result, value=0.95)
        result = adjust_saturation(result, scale=0.88)

    elif style == "dramatic":
        result = adjust_contrast(result, value=1.25)
        result = apply_curves(result, shadows=-15, midtones=8, highlights=10)
        result = adjust_saturation(result, scale=1.1)
        result = apply_vignette(result, strength=0.5, radius=0.6)
        result = apply_clarity(result, amount=0.25)

    elif style in ["vintage_film", "vintage"]:
        result = apply_film_fade(result, fade_amount=0.15, black_fade=0.08)
        result = apply_split_toning(result, shadow_hue=35, shadow_sat=0.18,
                                   highlight_hue=50, highlight_sat=0.12)
        result = adjust_saturation(result, scale=0.88)
        result = adjust_contrast(result, value=0.95)
        result = apply_grain(result, amount=0.025, size=1)
        result = apply_vignette(result, strength=0.35, radius=0.75)

    elif style == "retro_70s":
        result = apply_cross_process(result, intensity=0.25)
        result = apply_film_fade(result, fade_amount=0.2, black_fade=0.1)
        result = apply_split_toning(result, shadow_hue=30, shadow_sat=0.2,
                                   highlight_hue=55, highlight_sat=0.18)
        result = adjust_saturation(result, scale=0.9)
        result = apply_grain(result, amount=0.03, size=1)
        result = apply_vignette(result, strength=0.4, radius=0.7)

    elif style == "polaroid":
        result = apply_film_fade(result, fade_amount=0.15, black_fade=0.08)
        result = apply_split_toning(result, shadow_hue=45, shadow_sat=0.15,
                                   highlight_hue=180, highlight_sat=0.08)
        result = adjust_contrast(result, value=1.02)
        result = adjust_saturation(result, scale=0.9)
        b, g, r = cv2.split(result.astype(np.float32))
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        shadow_mask = np.clip(1 - gray * 2, 0, 1)
        b = b + shadow_mask * 10
        g = g + shadow_mask * 6
        result = cv2.merge([np.clip(b, 0, 255).astype(np.uint8),
                           np.clip(g, 0, 255).astype(np.uint8),
                           np.clip(r, 0, 255).astype(np.uint8)])
        result = apply_vignette(result, strength=0.3, radius=0.8)

    elif style == "kodachrome":
        result = adjust_saturation(result, scale=1.15)
        result = adjust_contrast(result, value=1.1)
        result = apply_split_toning(result, shadow_hue=220, shadow_sat=0.1,
                                   highlight_hue=40, highlight_sat=0.15)
        b, g, r = cv2.split(result.astype(np.float32))
        r = r * 1.05
        result = cv2.merge([b.astype(np.uint8), g.astype(np.uint8),
                           np.clip(r, 0, 255).astype(np.uint8)])
        result = apply_grain(result, amount=0.02, size=1)

    elif style in ["cinematic_teal_orange", "cinematic"]:
        result = apply_teal_and_orange(result, intensity=0.4)
        result = adjust_contrast(result, value=1.12)
        result = apply_curves(result, shadows=-8, midtones=0, highlights=5)
        result = apply_vignette(result, strength=0.35, radius=0.72)
        result = apply_film_fade(result, fade_amount=0.08, black_fade=0.04)

    elif style == "blockbuster":
        result = apply_teal_and_orange(result, intensity=0.45)
        result = adjust_contrast(result, value=1.18)
        result = adjust_saturation(result, scale=1.08)
        result = apply_vignette(result, strength=0.38, radius=0.7)
        result = apply_glow(result, intensity=0.1, radius=21)

    elif style == "indie_film":
        result = adjust_saturation(result, scale=0.88)
        result = apply_film_fade(result, fade_amount=0.12, black_fade=0.06)
        result = apply_split_toning(result, shadow_hue=200, shadow_sat=0.12,
                                   highlight_hue=45, highlight_sat=0.08)
        result = adjust_contrast(result, value=1.03)
        result = apply_grain(result, amount=0.025, size=1)

    elif style == "golden_hour":
        result = apply_split_toning(result, shadow_hue=30, shadow_sat=0.12,
                                   highlight_hue=50, highlight_sat=0.2)
        result = adjust_temp_tint(result, temp=20, tint=4)
        result = adjust_saturation(result, scale=1.1)
        result = apply_glow(result, intensity=0.1, radius=31)
        result = apply_haze(result, amount=0.03, color=(255, 240, 210))

    elif style == "morning_light":
        result = adjust_temp_tint(result, temp=12, tint=2)
        result = adjust_exposure(result, value=8)
        result = apply_split_toning(result, shadow_hue=220, shadow_sat=0.06,
                                   highlight_hue=45, highlight_sat=0.15)
        result = adjust_saturation(result, scale=1.05)
        result = apply_glow(result, intensity=0.08, radius=25)
        result = apply_haze(result, amount=0.02, color=(255, 248, 240))

    elif style == "sunrise":
        result = apply_split_toning(result, shadow_hue=250, shadow_sat=0.1,
                                   highlight_hue=35, highlight_sat=0.22)
        result = adjust_temp_tint(result, temp=18, tint=6)
        result = adjust_saturation(result, scale=1.12)
        result = apply_glow(result, intensity=0.12, radius=31)

    elif style == "sunset":
        result = apply_split_toning(result, shadow_hue=285, shadow_sat=0.12,
                                   highlight_hue=28, highlight_sat=0.28)
        result = adjust_temp_tint(result, temp=25, tint=10)
        result = adjust_saturation(result, scale=1.2)
        result = adjust_vibrance(result, strength=0.3)
        result = apply_glow(result, intensity=0.12, radius=31)

    elif style == "warm_glow":
        result = adjust_temp_tint(result, temp=22, tint=4)
        result = adjust_saturation(result, scale=1.08)
        result = apply_orton_effect(result, blur_amount=25, blend=0.18)
        result = apply_split_toning(result, shadow_hue=35, shadow_sat=0.1,
                                   highlight_hue=50, highlight_sat=0.15)

    elif style == "magic_hour":
        result = apply_split_toning(result, shadow_hue=280, shadow_sat=0.08,
                                   highlight_hue=40, highlight_sat=0.25)
        result = adjust_temp_tint(result, temp=20, tint=8)
        result = adjust_saturation(result, scale=1.12)
        result = apply_orton_effect(result, blur_amount=21, blend=0.15)
        result = apply_haze(result, amount=0.04, color=(255, 235, 210))

    elif style == "black_and_white":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_contrast(result, value=1.1)

    elif style == "high_contrast_bw":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_contrast(result, value=1.3)
        result = apply_curves(result, shadows=-15, midtones=8, highlights=12)

    elif style == "film_noir_bw":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_contrast(result, value=1.35)
        result = apply_curves(result, shadows=-18, midtones=5, highlights=15)
        result = apply_vignette(result, strength=0.55, radius=0.55)
        result = apply_grain(result, amount=0.035, size=1)

    elif style == "silver":
        gray = cv2.cvtColor(result, cv2.COLOR_BGR2GRAY)
        result = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        result = adjust_exposure(result, value=8)
        result = adjust_contrast(result, value=1.15)
        result = apply_curves(result, shadows=8, midtones=5, highlights=0)

    elif style == "dream":
        result = apply_orton_effect(result, blur_amount=25, blend=0.22)
        result = adjust_saturation(result, scale=0.92)
        result = apply_split_toning(result, shadow_hue=260, shadow_sat=0.12,
                                   highlight_hue=50, highlight_sat=0.1)
        result = apply_haze(result, amount=0.08, color=(220, 210, 230))
        result = apply_glow(result, intensity=0.18, radius=35)

    elif style == "ethereal":
        result = adjust_exposure(result, value=15)
        result = adjust_contrast(result, value=0.9)
        result = adjust_saturation(result, scale=0.85)
        result = apply_orton_effect(result, blur_amount=21, blend=0.2)
        result = apply_haze(result, amount=0.1, color=(240, 235, 250))
        result = apply_glow(result, intensity=0.22, radius=41)

    elif style == "horror":
        result = adjust_exposure(result, value=-15)
        result = adjust_saturation(result, scale=0.7)
        result = apply_split_toning(result, shadow_hue=160, shadow_sat=0.25,
                                   highlight_hue=40, highlight_sat=0.1)
        result = adjust_contrast(result, value=1.2)
        result = apply_vignette(result, strength=0.6, radius=0.5)
        result = apply_grain(result, amount=0.03, size=1)

    elif style == "western":
        result = apply_split_toning(result, shadow_hue=35, shadow_sat=0.22,
                                   highlight_hue=45, highlight_sat=0.18)
        result = adjust_temp_tint(result, temp=20, tint=6)
        result = adjust_saturation(result, scale=0.92)
        result = apply_haze(result, amount=0.08, color=(220, 200, 170))
        result = apply_film_fade(result, fade_amount=0.12, black_fade=0.06)
        result = apply_vignette(result, strength=0.35, radius=0.75)

    elif style == "underwater":
        result = apply_split_toning(result, shadow_hue=195, shadow_sat=0.35,
                                   highlight_hue=180, highlight_sat=0.3)
        result = adjust_temp_tint(result, temp=-30, tint=-10)
        result = adjust_saturation(result, scale=0.85)
        result = apply_haze(result, amount=0.18, color=(180, 200, 180))
        result = adjust_contrast(result, value=0.9)

    return result
