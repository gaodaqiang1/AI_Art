"""'prep' version of each confirmed furniture base (lang_final lang_{o}000): SAME design/colours/2.5D look, but with a big clear
open space UNDER it (the 'under' preposition game drops a picture there). Independent redraw, NOT stretched from the lang picture.
Usage: python gen_longleg.py <5|6|7|8|9> <variant>   -> output_api/longleg/<o>_v<variant>_big.png
5 table / 6 chair / 7 sofa / 8 slide / 9 bed"""
import base64
import io
import os
import sys
import requests
from PIL import Image

ROOT = 'I:/GODOT/AI_Art/'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()

KEEP = ("Redraw this exact piece of furniture with the SAME design, colours, materials, patterns, outline and glossy 2.5D look, "
        "same three-quarter viewing angle. ONLY change the underside as follows: ")
END = (" Nothing at all in the open gap: no drawers, no crossbars, no panels, no floor, no ground shadow, no cast shadow, no text. "
       "Style: polished 2.5D children's mobile-game icon, soft glossy highlights, smooth gradients, thin darker-tone coloured outline. "
       "Plain solid white background.")
SPEC = {
    5: "the tabletop stays the same; give it four sturdy tall legs at the four far corners, so the space under the tabletop is a wide, "
       "completely empty open gap about half of the picture height.",
    6: "the backrest and seat stay the same; four slim legs at the four corners with NO crossbars between them, so the space under the "
       "seat is a wide, completely empty open gap about 45% of the picture height.",
    7: "the sofa body (back, cushions, arms) stays the same and sits in the upper half of the picture; give it four TALL, LONG sturdy round "
       "wooden legs at the four far corners, each as long as the sofa body is tall, so the lower half of the picture is a wide, completely "
       "empty open gap between the legs with the white background visible through it.",
    8: "the slide chute and ladder stay the same; raise them on a tall open frame so the whole area under the sloping chute, between the "
       "ladder and the low end, is a big completely empty open space about 45% of the picture height; only thin supports at the extreme ends.",
    9: "the bed (mattress, blanket, pillow, headboard, footboard) stays the same and sits in the upper half of the picture; give it four "
       "TALL, LONG sturdy round wooden legs at the four far corners, each as long as the bed body is tall, so the lower half of the picture "
       "is a wide, completely empty open gap between the legs with the white background visible through it.",
}

o, v = int(sys.argv[1]), int(sys.argv[2])
src = Image.open(ROOT + f'output_api/lang_final/lang_{o}000.png').convert('RGBA')
w, h = src.size
cw, ch = (1536, 1024) if o != 6 else (1024, 1536)
fit_w, fit_h = (.62, .5) if o in (7, 9) else (.7, .6)
k = min(cw * fit_w / w, ch * fit_h / h)
nw, nh = round(w * k), round(h * k)
cv = Image.new('RGB', (cw, ch), 'white')
big = src.resize((nw, nh), Image.LANCZOS)
cv.paste(big, ((cw - nw) // 2, int(ch * .12)), big)
buf = io.BytesIO()
cv.save(buf, 'PNG')
buf.seek(0)
r = requests.post('https://cf.api.fan/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY},
                  files={'image': ('in.png', buf, 'image/png')},
                  data={'model': 'gpt-image-2.5-flare', 'prompt': KEEP + SPEC[o] + END, 'size': f'{cw}x{ch}', 'quality': 'medium', 'n': '1'},
                  timeout=300)
if r.status_code != 200:
    print('HTTP', r.status_code, r.text[:300])
    sys.exit(1)
d = r.json()['data'][0]
raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
os.makedirs(ROOT + 'output_api/longleg', exist_ok=True)
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'output_api/longleg/{o}_v{v}_big.png')
print('ok', o, v)
