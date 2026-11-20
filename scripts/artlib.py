"""Shared helpers for the AI_Art pipeline: white-background cutout, alpha IoU, base/candidate lookup."""
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

ROOT = 'I:/GODOT/AI_Art/'
BASE_DIR = ROOT + 'output_api/lang_final/'


def cut_white(im, thresh=232, blur=1.2):
    """Flood-fill the white background from the border, return RGBA with soft alpha."""
    im = im.convert('RGB')
    a = np.array(im)
    white = a.min(2) >= thresh
    h, w = white.shape
    bg = np.zeros((h, w), bool)
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or bg[y, x] or not white[y, x]:
            continue
        bg[y, x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    alpha = Image.fromarray((~bg * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(blur))
    o = im.convert('RGBA')
    o.putalpha(alpha)
    return o


def content(im):
    """Crop RGBA to its visible content; returns (cropped, bbox)."""
    bb = im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    return im.crop(bb), bb


def alpha_iou(a, b):
    """IoU of the silhouettes after stretching b's content box to a's content box size."""
    ac, _ = content(a)
    bc, _ = content(b)
    bc = bc.resize(ac.size, Image.BILINEAR)
    x = np.array(ac.getchannel('A')) > 20
    y = np.array(bc.getchannel('A')) > 20
    return float((x & y).sum()) / max(1.0, float((x | y).sum()))


def fringe_ratio(im):
    """Share of mostly-opaque edge pixels (alpha 128-250) that are still near-white = a white halo left by a bad cutout.
    (Semi-transparent edge pixels of a cutout from white are always whitish, so they are NOT counted.)"""
    a = np.array(im.convert('RGBA')).astype(int)
    edge = (a[..., 3] > 128) & (a[..., 3] < 250)
    if edge.sum() == 0:
        return 0.0
    return float((edge & (a[..., :3].min(2) > 235)).sum()) / float(edge.sum())


def base_for(name):
    """'lang_7000_xxx.png' / 'lang_7000.png' -> confirmed base 'lang_7000.png'; 'prep_X0*.png' -> 'lang_X000.png'. RGBA or None."""
    stem = name.rsplit('.', 1)[0].split('_')
    if len(stem) < 2 or not stem[1].isdigit():
        return None
    key = stem[1]
    if stem[0] == 'prep':
        key = key[0] + '000'
    try:
        return Image.open(BASE_DIR + f'lang_{key}.png').convert('RGBA')
    except FileNotFoundError:
        return None
