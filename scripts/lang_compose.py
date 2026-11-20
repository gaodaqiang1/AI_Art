"""Compose all 450 lang_XXXX.png from the chosen base/colour images, following ORIGINAL canvas, size ratio and copy layout.
file name: lang_<obj><size><colour><count>.png  (category0..3)
Output: output_api/lang_final/lang_XXXX.png  (+ .webp copies in lang_final_webp/)
"""
import json
import os

from PIL import Image

R = 'I:/GODOT/AI_Art/output_api/'
ND = R + 'lang_new/'
L = json.load(open(R + 'lang_layout.json'))
ROWS = json.load(open('I:/GODOT/xwn/data/sqlite_content/lang.json', encoding='utf-8'))
FN = {(r['category0'], r['category1'], r['category2'], r['category3']): r['filename'] for r in ROWS}
OUT = R + 'lang_final/'
OUTW = R + 'lang_final_webp/'
os.makedirs(OUT, exist_ok=True)
os.makedirs(OUTW, exist_ok=True)


def src(o, c):
    if c == 0:
        return R + 'final/dog_golden.png' if o == 0 else ND + 'obj%d_v1.png' % o
    return ND + 'obj%d_c%d.png' % (o, c)


def trimmed(o, c):
    im = Image.open(src(o, c)).convert('RGBA')
    return im.crop(im.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())


def compose(o, s, c, n, obj):
    e = L['%d_%d_%d' % (o, s, n)]
    cw, ch = e['canvas']
    x0, y0, x1, y1 = e['content']
    sc = min((x1 - x0) / obj.width, (y1 - y0) / obj.height)
    nw, nh = max(1, round(obj.width * sc)), max(1, round(obj.height * sc))
    piece = obj.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (cw, ch), (0, 0, 0, 0))
    # copies hold the top-left of the ORIGINAL single's content box at each position; scale to the new piece
    ow, oh = x1 - x0, y1 - y0
    [canvas.alpha_composite(piece, (px + (ow - nw) // 2, py + (oh - nh) // 2)) for px, py in e['copies']]
    return canvas


def save(name, im):
    im.save(OUT + name, optimize=True)
    im.save(OUTW + name.replace('.png', '.webp'), 'WEBP', quality=80, method=6)


def do(o, c):
    obj = trimmed(o, c)
    return [save(FN[(o, s, c, n)], compose(o, s, c, n, obj)) for s in range(3) for n in range(3)]


[do(o, c) for o in range(10) for c in range(5)]
print(len(os.listdir(OUT)), 'png', len(os.listdir(OUTW)), 'webp')
png = sum(os.path.getsize(OUT + f) for f in os.listdir(OUT))
web = sum(os.path.getsize(OUTW + f) for f in os.listdir(OUTW))
print('PNG %.1fMB  WEBP %.1fMB' % (png / 1e6, web / 1e6))
