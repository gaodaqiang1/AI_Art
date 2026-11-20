"""
Cut a generated picture out of its background (rembg / U2-Net), drop a soft ground shadow if one was caught,
and save a transparent PNG.
Usage: venv/Scripts/python.exe scripts/cutout.py in1.png in2.png ...   (writes output_25d/cutout/<name>_cut.png)
"""
import os
import sys
import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy import ndimage as ndi

OUT_DIR = 'I:/GODOT/AI_Art/output_25d/cutout/'


def drop_shadow(rgba):
    # a ground shadow is a grey, desaturated, semi-transparent blob below the character: remove low-saturation pixels that are
    # not fully opaque and sit in the lower part, then keep only the biggest connected piece
    arr = np.array(rgba).astype(np.float32)
    alpha = arr[..., 3] / 255.0
    rgb = arr[..., :3] / 255.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    soft = (alpha < 0.85) & (sat < 0.18) & (mx < 0.75)
    alpha = np.where(soft, 0.0, alpha)
    solid = alpha > 0.5
    lab, n = ndi.label(solid)
    if n > 1:
        sizes = ndi.sum(solid, lab, range(1, n + 1))
        keep = 1 + int(np.argmax(sizes))
        near = ndi.binary_dilation(lab == keep, iterations=3)
        alpha = np.where(near, alpha, 0.0)
    arr[..., 3] = alpha * 255.0
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    session = new_session('isnet-general-use')
    for path in sys.argv[1:]:
        im = Image.open(path).convert('RGB')
        cut = remove(im, session=session, alpha_matting=True, alpha_matting_foreground_threshold=235, alpha_matting_background_threshold=15, alpha_matting_erode_size=8)
        cut = drop_shadow(cut.convert('RGBA'))
        bbox = cut.getchannel('A').getbbox()
        cut = cut.crop(bbox)
        name = os.path.basename(path).replace('.png', '_cut.png')
        cut.save(OUT_DIR + name, optimize=True)
        print('cut', name, cut.size, flush=True)
    print('CUT_DONE', flush=True)


if __name__ == '__main__':
    main()
