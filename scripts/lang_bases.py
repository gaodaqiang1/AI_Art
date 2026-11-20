"""Generate one base image per lang-game object (style s1), cut to transparent, fit to the original game size.
Usage: python scripts/lang_bases.py [object ids...]   (default: 1..9; object 0 = golden dog already done)
Key is read from ../IMAGE_API_KEY and never printed.
Output: output_api/lang_base/obj<k>.png (RGBA, same pixel size as the original lang_<k>000.png) and obj<k>_raw.png
"""
import base64
import io
import os
import sys
from collections import deque

import requests
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://cf.api.fan'
MODEL = 'gpt-image-2.5-flare'
KEY = open(os.path.join(os.path.dirname(ROOT), 'IMAGE_API_KEY'), encoding='utf-8').read().strip()
OUT = os.path.join(ROOT, 'output_api', 'lang_base')
SRC = os.path.join(ROOT, '..', 'xwn', 'assets', 'legacy', 'images')

NAMES = {
    1: 'a teacup on a saucer',
    2: 'a beach ball with colourful wedges',
    3: 'a toy pedal car for children',
    4: 'an open picture book',
    5: 'a wooden table with four legs',
    6: "a small child's chair",
    7: 'a two-seat sofa',
    8: 'a playground slide with a ladder',
    9: 'a child bed with a blue blanket and a pillow',
}
STYLE = ('soft cartoon, simple rounded shapes, thin darker-tone outline instead of black, '
         'gentle pastel colors, subtle flat shading')
PROMPT = ("Redraw this game object ({name}) as a polished children's mobile game asset. Keep the SAME object, "
   "viewing angle, proportions, silhouette and main colour family, filling the same area of the frame. "
          "Plain solid flat pure magenta (#FF00FF) background, no scenery, no ground shadow, no text. "
          "Child friendly, calm, clean readable shape. Style: " + STYLE)


def canvas_for(w, h):
    r = w / h
    if r > 1.2:
        return (1536, 1024)
    if r < 0.83:
        return (1024, 1536)
    return (1024, 1024)


def is_mag(p):
    return p[0] > 170 and p[2] > 170 and p[1] < p[0] - 60 and p[1] < p[2] - 60


def cut(im):
    im = im.convert('RGB')
    w, h = im.size
    px = im.load()
    bg = Image.new('L', (w, h), 0)
    b = bg.load()
    seen = set()
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not is_mag(px[x, y]):
            continue
        seen.add((x, y))
        b[x, y] = 255
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    a = bg.point(lambda v: 255 - v).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    o = im.convert('RGBA')
    o.putalpha(a)
    return o


def fit(o, w, h, m=4):
    o = o.crop(o.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    k = min((w - 2 * m) / o.width, (h - 2 * m) / o.height)
    o = o.resize((max(1, round(o.width * k)), max(1, round(o.height * k))), Image.LANCZOS)
    f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    f.alpha_composite(o, ((w - o.width) // 2, (h - o.height) // 2))
    return f


def call_api(canvas, cw, ch, prompt):
    buf = io.BytesIO()
    canvas.save(buf, 'PNG')
    buf.seek(0)
    r = requests.post(BASE + '/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY},
        files={'image': ('in.png', buf, 'image/png')},
        data={'model': MODEL, 'prompt': prompt, 'size': '%dx%d' % (cw, ch),
           'quality': 'medium', 'n': '1'}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError('HTTP %d %s' % (r.status_code, r.text[:300]))
    d = r.json()['data'][0]
    raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
    return Image.open(io.BytesIO(raw)).convert('RGB')


def make(k):
    src = Image.open(os.path.join(SRC, 'lang_%d000.png' % k)).convert('RGBA')
    w, h = src.size
    cw, ch = canvas_for(w, h)
    s = min(cw * 0.8 / w, ch * 0.8 / h)
    nw, nh = round(w * s), round(h * s)
    canvas = Image.new('RGB', (cw, ch), (255, 0, 255))
    big = src.resize((nw, nh), Image.LANCZOS)
    canvas.paste(big, ((cw - nw) // 2, (ch - nh) // 2), big)
    out = call_api(canvas, cw, ch, PROMPT.format(name=NAMES[k]))
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, 'obj%d_raw.png' % k))
    fit(cut(out), w, h).save(os.path.join(OUT, 'obj%d.png' % k), optimize=True)
    print('ok obj', k, (w, h))


if __name__ == '__main__':
    ids = [int(a) for a in sys.argv[1:]] or list(NAMES)
    for i in ids:
        make(i)
