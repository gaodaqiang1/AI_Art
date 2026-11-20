"""Compose all 450 lang_XXXX.png in the 2.5D style from output_api/base25 (c0) + col25 (c1..4), following the ORIGINAL canvas, size
ratio and copy layout (lang_layout.json). Output: output_api/lang_final25/ (png) and lang_final25_webp/. Never touches the game."""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from artlib import cut_white, content
R = 'I:/GODOT/AI_Art/output_api/'
L = json.load(open(R + 'lang_layout.json'))
ROWS = json.load(open('I:/GODOT/xwn/data/sqlite_content/lang.json', encoding='utf-8'))
FN = {(r['category0'], r['category1'], r['category2'], r['category3']): (r['filename'], r['width'], r['height']) for r in ROWS}
OUT, OUTW = R + 'lang_final25/', R + 'lang_final25_webp/'
os.makedirs(OUT, exist_ok=True); os.makedirs(OUTW, exist_ok=True)


def trimmed(k, c):
    p = R + (f'base25/{k}.png' if c == 0 else f'col25/{k}_c{c}_big.png')
    return content(cut_white(Image.open(p)))[0]


def compose(o, s, n, obj, W, H):
    e = L['%d_%d_%d' % (o, s, n)]
    cw, ch = e['canvas']; x0, y0, x1, y1 = e['content']
    sc = min((x1 - x0) / obj.width, (y1 - y0) / obj.height)
    nw, nh = max(1, round(obj.width * sc)), max(1, round(obj.height * sc))
    piece = obj.resize((nw, nh), Image.LANCZOS)
    cv = Image.new('RGBA', (cw, ch), (0, 0, 0, 0)); ow, oh = x1 - x0, y1 - y0
    for px, py in e['copies']:
        cv.alpha_composite(piece, (px + (ow - nw) // 2, py + (oh - nh) // 2))
    if cv.size != (W, H):
        cv = cv.resize((W, H), Image.LANCZOS)      # json size is the game's truth (1-3 px rounding in the layout file)
    return cv


n = 0
for o in range(10):
    for c in range(5):
        obj = trimmed(o, c)
        for s in range(3):
            for k in range(3):
                name, W, H = FN[(o, s, c, k)]
                im = compose(o, s, k, obj, W, H)
                im.save(OUT + name, optimize=True)
                im.save(OUTW + name.replace('.png', '.webp'), 'WEBP', quality=82, method=6)
                n += 1
print(n, 'files; PNG %.1fMB WEBP %.1fMB' % (sum(os.path.getsize(OUT + f) for f in os.listdir(OUT)) / 1e6, sum(os.path.getsize(OUTW + f) for f in os.listdir(OUTW)) / 1e6))
