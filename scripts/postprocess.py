"""
Post-processing for the AI pictures. The game logic is untouched, so geometry must not change:
  - colours come from the ORIGINAL picture (colours are teaching content); the AI only supplies light and shade
  - the alpha channel is the original one, so silhouette, canvas size and anchor are identical
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from skimage import color

SHADE_FROM_AI = 0.7    # share of the lightness that comes from the AI picture (rest from the original)


def blur_norm(channel, weight, sigma):
    num = ndi.gaussian_filter(channel * weight, sigma)
    den = ndi.gaussian_filter(weight, sigma)
    return num / np.maximum(den, 1e-4)


def finish(original_path, generated_path, out_path, box):
    orig = Image.open(original_path).convert('RGBA')
    W, H = orig.size
    gen = Image.open(generated_path).convert('RGB').crop(box).resize((W, H), Image.LANCZOS)
    o = np.array(orig).astype(np.float32)
    alpha = o[..., 3] / 255.0
    rgb_o = o[..., :3] / 255.0
    inside = alpha > 0.5
    dist = ndi.distance_transform_edt(inside)
    band = max(3.0, 0.035 * min(W, H))
    lum = 0.299 * rgb_o[..., 0] + 0.587 * rgb_o[..., 1] + 0.114 * rgb_o[..., 2]
    # the thick black outline of the old art (very dark pixels in a band along the silhouette edge)
    outline = inside & (dist < band) & (lum < 0.2)
    good = (inside & ~outline).astype(np.float32)
    flat = np.zeros_like(rgb_o)
    for c in range(3):
        flat[..., c] = blur_norm(rgb_o[..., c], good, band)
    flat = np.where(outline[..., None], flat, rgb_o)
    lab_o = color.rgb2lab(flat)
    lab_g = color.rgb2lab(np.array(gen).astype(np.float32) / 255.0)
    # near the silhouette the AI picture is mixed with its background: take lightness from further inside
    core = np.clip(dist / 3.0, 0.0, 1.0)
    l_ext = blur_norm(lab_g[..., 0], (dist >= 3).astype(np.float32), band)
    l_gen = core * lab_g[..., 0] + (1.0 - core) * l_ext
    lightness = SHADE_FROM_AI * l_gen + (1.0 - SHADE_FROM_AI) * lab_o[..., 0]
    keep = inside & ~outline
    lightness = lightness + (lab_o[..., 0][keep].mean() - lightness[keep].mean())
    lightness = np.clip(lightness, 0.0, 100.0)
    lab = np.dstack([lightness, lab_o[..., 1], lab_o[..., 2]])
    rgb = np.clip(color.lab2rgb(lab), 0.0, 1.0)
    out = np.dstack([rgb, alpha])
    img = Image.fromarray((out * 255.0 + 0.5).astype(np.uint8), 'RGBA')
    img.save(out_path, optimize=True)
    return img.size


def same_geometry(original_path, new_path):
    a = Image.open(original_path).convert('RGBA')
    b = Image.open(new_path).convert('RGBA')
    if a.size != b.size:
        return 'SIZE DIFFERS %s vs %s' % (a.size, b.size)
    da = np.abs(np.array(a)[..., 3].astype(int) - np.array(b)[..., 3].astype(int)).max()
    return 'OK same size %s, alpha max diff %d' % (a.size, da)
