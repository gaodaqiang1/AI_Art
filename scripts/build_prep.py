"""Assemble the new prep_* set (25 furniture + 5 shadows) into bg_work/prep_final/ and write prep.json next to it.
Furniture: cut from white bg (enclosed white holes inside the object, e.g. between chair back bars, are made transparent too),
fitted into the legacy box (aspect kept, bottom aligned, same as under_zone checks). Shadows: soft elliptical contact shadow."""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import content
R = 'I:/GODOT/AI_Art/'
S = 'I:/GODOT/xwn/assets/legacy/images/'
OUT = R + 'bg_work/prep_final/'
os.makedirs(OUT, exist_ok=True)
rows = json.load(open('I:/GODOT/xwn/data/sqlite_content/prep.json', encoding='utf-8'))


def cut_holes(im, thresh=236, blur=1.0):
    """white (>=thresh) connected to the border -> transparent; also any enclosed white pocket larger than 40 px (real see-through holes)."""
    im = im.convert('RGB')
    a = np.array(im)
    white = a.min(2) >= thresh
    lab, n = ndi.label(white)
    keep = np.zeros_like(white)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    sizes = ndi.sum(white, lab, range(1, n + 1))
    for i in range(1, n + 1):
        if i in border or sizes[i - 1] >= 40:
            keep |= lab == i
    alpha = Image.fromarray(((~keep) * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(blur))
    o = im.convert('RGBA')
    o.putalpha(alpha)
    return o


def furniture(o, c):
    path = R + (f'output_api/longleg_sel/{o}.png' if c == 0 else f'output_api/longleg_col/{o}_c{c}_big.png')
    cut, _ = content(cut_holes(Image.open(path)))
    old = Image.open(S + f'prep_{o}{c}.png')
    k = min(old.width / cut.width, old.height / cut.height)
    nw, nh = round(cut.width * k), round(cut.height * k)
    out = Image.new('RGBA', old.size, (0, 0, 0, 0))
    out.alpha_composite(cut.resize((nw, nh), Image.LANCZOS), ((old.width - nw) // 2, old.height - nh))
    out.save(OUT + f'prep_{o}{c}.png', optimize=True)
    return cut.size, (nw, nh)


def shadow(o):
    old = Image.open(S + f'prep_{o}.png')
    w, h = old.size
    y, x = np.mgrid[0:h, 0:w]
    d = ((x - w / 2) / (w * .46)) ** 2 + ((y - h / 2) / (h * .40)) ** 2
    a = np.clip(1 - d, 0, 1) ** .8 * 90
    im = Image.new('RGBA', (w, h), (70, 110, 120, 0))
    im.putalpha(Image.fromarray(a.astype('uint8')).filter(ImageFilter.GaussianBlur(6)))
    im.save(OUT + f'prep_{o}.png', optimize=True)


if __name__ == '__main__':
    for o in range(5, 10):
        shadow(o)
        for c in range(5):
            furniture(o, c)
    print('furniture+shadows written:', len(os.listdir(OUT)))
