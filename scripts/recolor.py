"""
Recolour one cut-out picture into the game colours WITHOUT redrawing it, so it stays the same character.
Only pixels that carry the body colour change; white (patches, eye whites) and dark ink (outline, eyes, nose) stay.
Usage: venv/Scripts/python.exe scripts/recolor.py in_cut.png out_dir prefix
"""
import colorsys
import os
import sys
import numpy as np
from PIL import Image

# target colour -> (hue in degrees, body saturation, body brightness). Brightness and saturation are set absolutely:
# the old body is almost white, so scaling it could never give a strong red / green / blue.
TARGETS = {'red': (0, 0.88, 0.80), 'green': (125, 0.85, 0.66), 'blue': (214, 0.88, 0.84), 'orange': (27, 0.92, 0.98), 'brown': (26, 0.62, 0.50)}
SHADE_GAIN = 2.6   # how strongly the old light and shade differences are kept (old body values sit in a narrow 0.75-0.97 band)


def to_hsv(rgb):
    flat = rgb.reshape(-1, 3)
    hsv = np.array([colorsys.rgb_to_hsv(p[0], p[1], p[2]) for p in flat], np.float32)
    return hsv.reshape(rgb.shape)


def to_rgb(h, s, v):
    trip = zip(h.reshape(-1), s.reshape(-1), v.reshape(-1))
    out = np.array([colorsys.hsv_to_rgb(x, y, z) for x, y, z in trip], np.float32)
    return out.reshape(h.shape + (3,))


def recolor(img, hue_deg, sat_scale, val_scale):
    arr = np.array(img.convert('RGBA')).astype(np.float32) / 255.0
    rgb = arr[..., :3]
    hsv = to_hsv(rgb)
    h = hsv[..., 0]
    s = hsv[..., 1]
    v = hsv[..., 2]
    # weight 0 for white and for dark ink, 1 for body colour, smooth in between
    weight = np.clip((s - 0.10) / 0.12, 0.0, 1.0) * np.clip((v - 0.35) / 0.15, 0.0, 1.0)
    body = weight > 0.5
    median_v = float(np.median(v[body])) if body.any() else 0.9
    # new brightness: the target brightness plus the old light/shade difference, amplified (so the form stays visible)
    target_v = np.clip(val_scale + (v - median_v) * SHADE_GAIN, 0.0, 1.0)
    # new saturation: the target, a little lower where the old picture was bright highlight
    target_s = np.clip(sat_scale - np.clip(v - median_v, 0.0, 1.0) * 1.5, 0.0, 1.0)
    target_h = np.full_like(h, hue_deg / 360.0)
    new_h = h * (1.0 - weight) + target_h * weight
    new_s = s * (1.0 - weight) + target_s * weight
    new_v = v * (1.0 - weight) + target_v * weight
    out = to_rgb(new_h, new_s, new_v)
    res = np.dstack([out, arr[..., 3]])
    return Image.fromarray((res * 255.0 + 0.5).astype(np.uint8), 'RGBA')


def main():
    src, out_dir, prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(src)
    for name, params in TARGETS.items():
        r = recolor(img, params[0], params[1], params[2])
        path = os.path.join(out_dir, '%s_%s.png' % (prefix, name))
        r.save(path, optimize=True)
        print('saved', path, flush=True)
    print('RECOLOR_DONE', flush=True)


if __name__ == '__main__':
    main()
