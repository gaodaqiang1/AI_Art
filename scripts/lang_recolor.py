"""Make the 4 colour variants (1 red, 2 green, 3 blue, 4 orange) of each chosen base object via /v1/images/edits.
Base: object 0 = output_api/final/dog_golden.png, others = output_api/lang_new/obj<k>_v1.png
Output: output_api/lang_new/obj<k>_c<1..4>.png (RGBA, original single-image pixel size)
Key is read from ../IMAGE_API_KEY and never printed.
"""
import base64
import io
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lang_new as LN

ROOT = LN.ROOT
OUT = LN.OUT
COLOURS = {
    1: 'bright red (#E53935 family)',
    2: 'fresh green (#43A047 family)',
    3: 'sky blue (#1E88E5 family)',
    4: 'vivid orange (#FB8C00 family)',
}
PROMPT = ("Recolor this exact game object so that it is clearly and predominantly {colour}. Use lighter and darker "
          "shades of that one hue for all parts of the object, so a child would call it 'the {name} one'. Keep "
          "IDENTICAL shape, design, outline style, details, size and position. Plain solid flat pure magenta "
          "(#FF00FF) background, do not use magenta on the object, no text.")
NAMES = {1: 'red', 2: 'green', 3: 'blue', 4: 'orange'}


def base_path(k):
    if k == 0:
        return os.path.join(ROOT, 'output_api', 'final', 'dog_golden.png')
    return os.path.join(OUT, 'obj%d_v1.png' % k)


def edit(canvas, cw, ch, prompt):
    buf = io.BytesIO()
    canvas.save(buf, 'PNG')
    buf.seek(0)
    r = requests.post(LN.BASE + '/v1/images/edits', headers={'Authorization': 'Bearer ' + LN.KEY},
            files={'image': ('in.png', buf, 'image/png')},
            data={'model': LN.MODEL, 'prompt': prompt, 'size': '%dx%d' % (cw, ch),
                   'quality': 'medium', 'n': '1'}, timeout=300)
    if r.status_code != 200:
        raise RuntimeError('HTTP %d %s' % (r.status_code, r.text[:300]))
    d = r.json()['data'][0]
    raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
    return Image.open(io.BytesIO(raw)).convert('RGB')


def one(job):
    k, c = job
    base = Image.open(base_path(k)).convert('RGBA')
    w, h = base.size
    cw, ch = LN.canvas_for(w, h)
    bb = base.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox()
    obj = base.crop(bb)
    s = min(cw * 0.8 / obj.width, ch * 0.8 / obj.height)
    obj = obj.resize((round(obj.width * s), round(obj.height * s)), Image.LANCZOS)
    canvas = Image.new('RGB', (cw, ch), (255, 0, 255))
    canvas.paste(obj, ((cw - obj.width) // 2, (ch - obj.height) // 2), obj)
    out = edit(canvas, cw, ch, PROMPT.format(colour=COLOURS[c], name=NAMES[c]))
    out.save(os.path.join(OUT, 'obj%d_c%d_raw.png' % (k, c)))
    LN.fit(LN.cut(out), w, h).save(os.path.join(OUT, 'obj%d_c%d.png' % (k, c)), optimize=True)
    return 'ok obj%d c%d' % (k, c)


def main():
    ids = [int(a) for a in sys.argv[1:]] or list(range(10))
    jobs = [(k, c) for k in ids for c in COLOURS]
    with ThreadPoolExecutor(max_workers=6) as ex:
        print('\n'.join(ex.map(one, jobs)))


if __name__ == '__main__':
    main()
