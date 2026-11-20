"""Extract layout (canvas size, content box, copy positions) of every lang variant from the ORIGINAL images.
Verifies by re-rendering the original single at the found positions and comparing alpha IoU.
Output: output_api/lang_layout.json
"""
import json

import cv2
import numpy as np
from PIL import Image

S = 'I:/GODOT/xwn/assets/legacy/images/'
rows = json.load(open('I:/GODOT/xwn/data/sqlite_content/lang.json', encoding='utf-8'))
T = {(r['category0'], r['category1'], r['category2'], r['category3']): r['filename'] for r in rows}


def load(o, s, n):
    return Image.open(S + T[(o, s, 0, n)]).convert('RGBA')


def bbox(im):
    return im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()


def over_white(im):
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return np.array(bg.convert('RGB')).astype(np.float32)


def find_copies(single, big, n):
    bb = bbox(single)
    tpl = single.crop(bb)
    t = np.array(tpl).astype(np.float32)
    mask = np.dstack([(t[:, :, 3] > 20).astype(np.float32)] * 3)
    tpl_rgb = over_white(tpl)
    res = cv2.matchTemplate(over_white(big), tpl_rgb, cv2.TM_SQDIFF, mask=mask)
    res = res / max(1.0, float(mask.sum()))
    w, h = tpl.size
    rx, ry = max(3, int(w * 0.12)), max(3, int(h * 0.12))
    found = []
    for _ in range(n):
        y, x = np.unravel_index(int(np.argmin(res)), res.shape)
        found.append((int(x), int(y), float(res[y, x])))
        res[max(0, y - ry):y + ry + 1, max(0, x - rx):x + rx + 1] = np.inf
    return bb, found


def render(single, bb, big_size, positions):
    tpl = single.crop(bb)
    canvas = Image.new('RGBA', big_size, (0, 0, 0, 0))
    for x, y in positions:
        canvas.alpha_composite(tpl, (x, y))
    return canvas


def iou(a, b):
    x = np.array(a.getchannel('A')) > 20
    y = np.array(b.getchannel('A')) > 20
    return float((x & y).sum()) / max(1, float((x | y).sum()))



def do_variant(o, s, n, single, bb):
    big = load(o, s, n)
    bb2, found = find_copies(single, big, n + 1)
    order = sorted(found, key=lambda f: -f[2])
    pos = [(f[0], f[1]) for f in order]
    q = iou(big, render(single, bb2, big.size, pos))
    entry = {'canvas': list(big.size), 'content': list(bb2), 'copies': [list(p) for p in pos], 'iou': round(q, 3)}
    return '%d_%d_%d' % (o, s, n), entry, (q, o, s, n)


def do_size(o, s):
    single = load(o, s, 0)
    bb = bbox(single)
    out = [('%d_%d_0' % (o, s), {'canvas': list(single.size), 'content': list(bb), 'copies': [[bb[0], bb[1]]]}, None)]
    out += [do_variant(o, s, n, single, bb) for n in (1, 2)]
    return out


results = [r for o in range(10) for s in range(3) for r in do_size(o, s)]
layout = {k: e for k, e, _ in results}
worst = sorted(w for _, _, w in results if w)
print('lowest IoU:', [(round(q, 3), o, s, n) for q, o, s, n in worst[:12]])
print('mean IoU:', round(sum(w[0] for w in worst) / len(worst), 3))
json.dump(layout, open('I:/GODOT/AI_Art/output_api/lang_layout.json', 'w'))
