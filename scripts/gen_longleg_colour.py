"""Recolour the chosen long-leg furniture (output_api/longleg_sel/<o>.png, white bg) into colour variants 1 red / 2 green / 3 blue / 4 orange,
using the SAME colour words the confirmed lang_final used. Usage: python gen_longleg_colour.py <o> <c>  -> output_api/longleg_col/<o>_c<c>_big.png"""
import base64, io, os, sys, requests
from PIL import Image
ROOT = 'I:/GODOT/AI_Art/'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()
COL = {1: ('bright red (#E53935 family)', 'red'), 2: ('fresh green (#43A047 family)', 'green'), 3: ('sky blue (#1E88E5 family)', 'blue'), 4: ('vivid orange (#FB8C00 family)', 'orange')}
o, c = int(sys.argv[1]), int(sys.argv[2])
colour, name = COL[c]
PROMPT = (f"Recolor this exact piece of furniture so that it is clearly and predominantly {colour}. Use lighter and darker shades of that one hue for all "
          f"parts (for the bed the blanket, headboard and footboard too; for the chair the backrest and seat too), so a child would call it 'the {name} one'. "
          f"Keep IDENTICAL shape, design, proportions, outline style, glossy 2.5D look, details, size and position, including the big empty open gap under it. "
          f"Plain solid white background, no floor, no shadow, no text.")
src = Image.open(ROOT + f'output_api/longleg_sel/{o}.png').convert('RGB')
w, h = src.size
cw, ch = (1536, 1024) if w / h > 1.2 else (1024, 1536) if w / h < .83 else (1024, 1024)
k = min(cw * .85 / w, ch * .85 / h); nw, nh = round(w * k), round(h * k)
cv = Image.new('RGB', (cw, ch), 'white'); cv.paste(src.resize((nw, nh), Image.LANCZOS), ((cw - nw) // 2, (ch - nh) // 2))
buf = io.BytesIO(); cv.save(buf, 'PNG'); buf.seek(0)
r = requests.post('https://cf.api.fan/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY}, files={'image': ('in.png', buf, 'image/png')},
    data={'model': 'gpt-image-2.5-flare', 'prompt': PROMPT, 'size': f'{cw}x{ch}', 'quality': 'medium', 'n': '1'}, timeout=300)
if r.status_code != 200:
    print('HTTP', r.status_code, r.text[:300]); sys.exit(1)
d = r.json()['data'][0]
raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
os.makedirs(ROOT + 'output_api/longleg_col', exist_ok=True)
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'output_api/longleg_col/{o}_c{c}_big.png'); print('ok', o, c)
