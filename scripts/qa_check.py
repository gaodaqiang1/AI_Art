"""Batch QA of generated pictures against the confirmed base pictures (lang_final).
Usage: python qa_check.py <glob-or-files...> [--csv out.csv]
Checks per file: aspect ratio vs base, silhouette IoU vs base (stretched), white fringe, content touching border, size.
Prints only a one-line verdict per file + the failing reasons, so a 450-file batch needs a glance at the FAIL lines only."""
import csv
import glob
import os
import sys
from PIL import Image
from artlib import base_for, cut_white, content, alpha_iou, fringe_ratio

IOU_MIN, AR_TOL, FRINGE_MAX, MARGIN = 0.80, 0.12, 0.10, 2


def check(path):
    name = os.path.basename(path)
    base = base_for(name)
    raw = Image.open(path)
    im = raw if raw.mode == 'RGBA' and raw.getchannel('A').getextrema()[0] < 250 else cut_white(raw)
    c, bb = content(im)
    why = []
    iou = ar_diff = None
    if base is not None:
        b, _ = content(base)
        ar_diff = abs(c.width / c.height - b.width / b.height) / (b.width / b.height)
        iou = alpha_iou(base, im)
        if ar_diff > AR_TOL:
            why.append('aspect %.0f%% off' % (ar_diff * 100))
        if iou < IOU_MIN:
            why.append('silhouette IoU %.2f' % iou)
    else:
        why.append('no base found')
    fr = fringe_ratio(im)
    if fr > FRINGE_MAX:
        why.append('white fringe %.0f%%' % (fr * 100))
    W, H = im.size
    if '_big' in name and (bb[0] <= MARGIN or bb[1] <= MARGIN or bb[2] >= W - MARGIN or bb[3] >= H - MARGIN):
        why.append('touches border')
    return {'file': name, 'iou': None if iou is None else round(iou, 3), 'aspect_off': None if ar_diff is None else round(ar_diff, 3),
            'fringe': round(fr, 3), 'verdict': 'FAIL' if why else 'ok', 'reasons': '; '.join(why)}


def main():
    args = sys.argv[1:]
    out = None
    if '--csv' in args:
        i = args.index('--csv')
        out = args[i + 1]
        args = args[:i] + args[i + 2:]
    files = []
    for a in args:
        files += sorted(glob.glob(a)) or [a]
    rows = [check(f) for f in files]
    for r in rows:
        print('%-4s %-34s IoU=%s aspectOff=%s fringe=%s %s' % (r['verdict'], r['file'], r['iou'], r['aspect_off'], r['fringe'], r['reasons']))
    bad = sum(r['verdict'] == 'FAIL' for r in rows)
    print('--- %d files, %d FAIL' % (len(rows), bad))
    if out:
        with open(out, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


if __name__ == '__main__':
    main()
