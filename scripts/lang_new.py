"""Brand-new designs (text-to-image, no source image) for the language game objects.
Only the size anchor comes from the original: result is fitted inside the original pixel box.
Usage: python scripts/lang_new.py [object ids...]     ids 0..9 (0 = dog)
Output: output_api/lang_new/obj<k>_v<1..3>.png (RGBA, original pixel size) + _raw
Key is read from ../IMAGE_API_KEY and never printed.
"""
import base64
import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://cf.api.fan'
MODEL = 'gpt-image-2.5-flare'
KEY = open(os.path.join(os.path.dirname(ROOT), 'IMAGE_API_KEY'), encoding='utf-8').read().strip()
OUT = os.path.join(ROOT, 'output_api', 'lang_new')
SRC = os.path.join(ROOT, '..', 'xwn', 'assets', 'legacy', 'images')

# Three different design directions per object. Colours kept neutral/pastel so recolouring later is easy.
DESIGNS = {
    0: ['a fluffy golden retriever puppy running, side view, whole body with tail visible',
        'a round chubby corgi puppy running, side view, whole body with tail visible',
 'a small floppy-eared beagle puppy running, side view, whole body with tail visible'],
    1: ['a round ceramic teacup with a tiny heart pattern and a saucer, steam-free, side view',
        'a tall mug-style cup with a curly handle and a small saucer, three-quarter view',
        'a cute teacup shaped like a flower with a saucer, three-quarter view'],
    2: ['a classic round beach ball with six curved pastel stripes',
        'a polka-dot rubber ball with a star in the middle',
        'a soft round playground ball with two big colour halves and a thin white band'],
    3: ['a cute toy pedal car with big round wheels and a steering wheel, side three-quarter view',
        'a chubby toy bus-like ride-on car with a smiling front, side three-quarter view',
        'a small retro toy convertible with round fenders, side three-quarter view'],
    4: ['an open picture book lying flat with colourful page edges, three-quarter view',
 'an open storybook with a ribbon bookmark and rounded corners, three-quarter view',
        'an open hardcover book standing slightly upright on its spine, three-quarter view'],
    5: ['a round-corner wooden kids table with four chunky legs, three-quarter view',
        'a cute low table with a rounded top and thick tapered legs, three-quarter view',
        'a small square play table with wide rounded edges, three-quarter view'],
    6: ['a cute small kids chair with a rounded backrest and four chunky legs, three-quarter view',
        'a stool-like kids chair with a heart cut-out backrest, three-quarter view',
 'a plump cushioned kids chair with a rounded top backrest, three-quarter view'],
    7: ['a plump rounded two-seat sofa with two cushions, front three-quarter view',
 'a cosy armchair-sofa with big rounded arms and stubby legs, front three-quarter view',
 'a soft fabric loveseat with a tufted back and small round feet, front three-quarter view'],
    8: ['a playground slide with a curved smooth slide and a short ladder, side view',
 'a cute straight slide with a small platform and a short ladder with handles, side view',
        'a wavy playground slide with a rounded tower and steps, side view'],
    9: ['a cute child bed with rounded wooden posts, a pillow and a blanket, three-quarter view',
        'a small cot-style bed with a curved headboard, pillow and quilt, three-quarter view',
        'a cosy kids bed with a star-pattern blanket and a rounded footboard, three-quarter view'],
}
STYLE = ('soft cartoon children game asset, simple rounded shapes, thin darker-tone outline instead of black, '
         'gentle pastel colors, subtle flat shading, clean readable silhouette, single object, centered')
TAIL = (' Plain solid flat pure magenta (#FF00FF) background, no scenery, no ground, no shadow, no text, '
 'no characters, do not use magenta or pink-purple on the object itself. Style: ')


def canvas_for(w, h):
    r = w / h
    if r > 1.2:
        return (1536, 1024)
    if r < 0.83:
        return (1024, 1536)
    return (1024, 1024)


def is_mag(p):
    return p[0] > 150 and p[2] > 150 and p[1] < 120 and abs(p[0] - p[2]) < 90


def cut(im):
    """Remove magenta everywhere (also enclosed holes) and decontaminate edge pixels."""
    im = im.convert('RGB')
    w, h = im.size
    px = im.load()
    a = Image.new('L', (w, h), 255)
    ap = a.load()
    for y in range(h):
        for x in range(w):
            if is_mag(px[x, y]):
                ap[x, y] = 0
    a = a.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(1.0))
    o = im.convert('RGBA')
    o.putalpha(a)
    return o


def fit(o, w, h, m=4):
    box = o.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    o = o.crop(box)
    k = min((w - 2 * m) / o.width, (h - 2 * m) / o.height)
    o = o.resize((max(1, round(o.width * k)), max(1, round(o.height * k))), Image.LANCZOS)
    f = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    f.alpha_composite(o, ((w - o.width) // 2, (h - o.height) // 2))
    return f


def generate(prompt, cw, ch):
    r = requests.post(BASE + '/v1/images/generations',
        headers={'Authorization': 'Bearer ' + KEY},
        json={'model': MODEL, 'prompt': prompt, 'size': '%dx%d' % (cw, ch),
       'quality': 'medium', 'n': 1}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError('HTTP %d %s' % (r.status_code, r.text[:300]))
    d = r.json()['data'][0]
    raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
    return Image.open(io.BytesIO(raw)).convert('RGB')


def one(job):
    k, v, w, h = job
    cw, ch = canvas_for(w, h)
    prompt = 'Draw ' + DESIGNS[k][v] + '.' + TAIL + STYLE
    out = generate(prompt, cw, ch)
    os.makedirs(OUT, exist_ok=True)
    out.save(os.path.join(OUT, 'obj%d_v%d_raw.png' % (k, v + 1)))
    fit(cut(out), w, h).save(os.path.join(OUT, 'obj%d_v%d.png' % (k, v + 1)), optimize=True)
    return 'ok obj%d v%d' % (k, v + 1)


def main():
    ids = [int(a) for a in sys.argv[1:]] or list(DESIGNS)
    jobs = []
    for k in ids:
        w, h = Image.open(os.path.join(SRC, 'lang_%d000.png' % k)).size
        jobs += [(k, v, w, h) for v in range(3)]
    with ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(one, jobs):
            print(res)


if __name__ == '__main__':
    main()
