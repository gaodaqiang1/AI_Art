"""Game-logic check for the 'under' preposition (dp_spatialprep.gd): where the dragged picture lands (target) and how much of that
rectangle is covered by the stationary furniture. Pieces are compared at game scale (prep size * 2).
Usage: python under_zone.py [piece_dir]   (default: legacy game folder)"""
import sys
import numpy as np
from PIL import Image
S = 'I:/GODOT/xwn/assets/legacy/images/'
OBJ = {5: [[204, 988], [666, 986], [900, 374], [94, 482], [490, 480], [330, 1220]],
       6: [[436, 982], [578, 950], [924, 350], [410, 188], [556, 518], [330, 1220]],
       7: [[260, 838], [792, 854], [978, 380], [218, 438], [565, 624], [588, 1204]],
       8: [[192, 886], [666, 808], [1104, 468], [174, 328], [770, 176], [462, 1212]],
       9: [[180, 950], [822, 945], [800, 340], [120, 423], [580, 600], [465, 1225]]}
BASKET = (326, 226); DISP_X = [.55, .51, .5, .5, .5]; DISP_Y = [.01, .2, .1, .1, .2]; SIZE_DY = [0.0, .15, -.15]
DSF = 0.7
NOUN = {0: 'dog', 1: 'cup', 2: 'ball', 3: 'car', 4: 'book'}


def zones(o):
    """all (noun,size) landing rectangles for 'under' (basket index 1), in 2048x1536 canvas coords."""
    out = {}
    for n in range(5):
        for s in range(3):
            w, h = Image.open(S + f'lang_{n}{s}00.png').size
            bw, bh = w * 2 * DSF, h * 2 * DSF
            tx = OBJ[o][1][0] + DISP_X[n] * BASKET[0]
            ty = OBJ[o][1][1] + (DISP_Y[n] + SIZE_DY[s]) * BASKET[1]
            out[(n, s)] = (tx - bw / 2, ty - bh / 2, tx + bw / 2, ty + bh / 2)
    return out


def coverage(piece, o, rect):
    px, py = OBJ[o][3]
    a = np.array(piece.resize((piece.width * 2, piece.height * 2), Image.BILINEAR).getchannel('A')) > 40
    x0, y0, x1, y1 = [int(round(v)) for v in rect]
    sub = np.zeros((y1 - y0, x1 - x0), bool)
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            ax, ay = xx - px, yy - py
            if 0 <= ax < a.shape[1] and 0 <= ay < a.shape[0]:
                sub[yy - y0, xx - x0] = a[ay, ax]
    return float(sub.mean())


def report(piece_dir, tag):
    print('==', tag)
    for o, name in ((5, 'table'), (6, 'chair'), (7, 'sofa'), (8, 'slide'), (9, 'bed')):
        p = Image.open(piece_dir + f'prep_{o}0.png').convert('RGBA')
        z = zones(o)
        cov = {k: coverage(p, o, r) for k, r in z.items()}
        ball = [cov[(2, s)] for s in range(3)]
        print('%-6s covered by furniture: ball(S/M/L)=%s  worst over all nouns=%.0f%% (%s)' % (
            name, '/'.join('%.0f%%' % (v * 100) for v in ball), max(cov.values()) * 100, NOUN[max(cov, key=cov.get)[0]]))


if __name__ == '__main__':
    report(S, 'LEGACY prep (flat, hollow underneath)')
    report(sys.argv[1] if len(sys.argv) > 1 else 'I:/GODOT/AI_Art/bg_work/prep_new/', 'CURRENT prep_new (= lang_final stretched)')
