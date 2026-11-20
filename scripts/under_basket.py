"""Where should the 'under' basket (plate, idx 1) sit so it is in the open space under the furniture, not on the legs?
Scale-invariant: works in fractions of the furniture box. Plate = 326x226 at game scale; furniture = prep_NK size * 2.
Search plate centres in the lower part of the box, pick the one with the least furniture inside the plate rectangle (shrunk 15%),
with a mild pull toward the legacy position. Prints fractions per furniture + colours spread, writes under_basket.json."""
import json, sys
import numpy as np
from PIL import Image
S = 'I:/GODOT/xwn/assets/legacy/images/'
P = 'I:/GODOT/AI_Art/bg_work/prep_final/'
OBJ = {5: [[204, 988], [666, 986], [900, 374], [94, 482], [490, 480], [330, 1220]], 6: [[436, 982], [578, 950], [924, 350], [410, 188], [556, 518], [330, 1220]],
       7: [[260, 838], [792, 854], [978, 380], [218, 438], [565, 624], [588, 1204]], 8: [[192, 886], [666, 808], [1104, 468], [174, 328], [770, 176], [462, 1212]],
       9: [[180, 950], [822, 945], [800, 340], [120, 423], [580, 600], [465, 1225]]}
BW, BH = 326, 226
STEP = 4


def best(piece_path, o, shrink=.85, pull=0.15):
    im = Image.open(piece_path).convert('RGBA')
    w, h = im.width * 2, im.height * 2                      # game scale (ssf = 1)
    a = np.array(im.resize((w // STEP, h // STEP), Image.BILINEAR).getchannel('A')) > 40
    ii = np.pad(a.cumsum(0).cumsum(1), ((1, 0), (1, 0))).astype(np.float64)
    pw, ph = int(BW * shrink / STEP), int(BH * shrink / STEP)
    ox, oy = OBJ[o][3]
    lx, ly = (OBJ[o][1][0] + BW / 2 - ox) / w, (OBJ[o][1][1] + BH / 2 - oy) / h   # legacy plate centre as fraction of the box
    res = None
    H, W = a.shape
    for cy in range(int(H * .45), H - ph // 2):
        for cx in range(pw // 2, W - pw // 2):
            y0, y1, x0, x1 = cy - ph // 2, cy + ph // 2, cx - pw // 2, cx + pw // 2
            occ = (ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0]) / (pw * ph)
            d = np.hypot((cx / W - lx) * 1.0, (cy / H - ly) * 1.6)
            score = occ + pull * d
            if res is None or score < res[0]:
                res = (score, cx / W, cy / H, occ)
    legacy_occ = None
    cx, cy = int(lx * W), int(ly * H)
    y0, y1, x0, x1 = max(0, cy - ph // 2), min(H, cy + ph // 2), max(0, cx - pw // 2), min(W, cx + pw // 2)
    legacy_occ = a[y0:y1, x0:x1].mean() if y1 > y0 and x1 > x0 else 1.0
    return res[1], res[2], res[3], (lx, ly), legacy_occ


if __name__ == '__main__':
    out = {}
    for o, name in ((5, 'table'), (6, 'chair'), (7, 'sofa'), (8, 'slide'), (9, 'bed')):
        rows = [best(P + f'prep_{o}{c}.png', o) for c in range(5)]
        fx, fy, occ, (lx, ly), locc = rows[0]
        spread = (max(r[0] for r in rows) - min(r[0] for r in rows), max(r[1] for r in rows) - min(r[1] for r in rows))
        print('%-6s legacy centre=(%.2f,%.2f) furniture-in-plate=%.0f%%  ->  new centre=(%.2f,%.2f) furniture-in-plate=%.0f%%  | colour spread dx=%.2f dy=%.2f'
              % (name, lx, ly, locc * 100, fx, fy, occ * 100, spread[0], spread[1]))
        out[str(o)] = [round(fx, 3), round(fy, 3)]
    json.dump(out, open('I:/GODOT/AI_Art/bg_work/under_basket.json', 'w'))
    print(out)
