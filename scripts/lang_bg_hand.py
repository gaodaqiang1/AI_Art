"""Redraw the teacher's hand used in lang_bg_1/2/3 in the new soft style (paid API). Output: bg_work/hand_new_<n>.png"""
import base64, io, os, sys, requests
from PIL import Image
ROOT = 'I:/GODOT/AI_Art/'
BASE = 'https://cf.api.fan'; MODEL = 'gpt-image-2.5-flare'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()
PROMPT = ("Redraw this exact hand as a polished children's mobile game asset. Keep the SAME pose: a friendly open palm facing up "
 "with relaxed fingers, seen from the side, coming in from the LEFT edge of the picture where the forearm is cut off by the frame edge "
 "(the arm continues beyond the left edge, no cuff, no sleeve, no wrist end). Keep the same size and position in the frame. "
 "Plain solid white background, no scenery, no shadow, no text. Style: soft cartoon, simple rounded shapes, thin darker warm-brown outline "
 "instead of black, gentle peach skin tone with a slightly darker peach shading side, subtle flat shading, soft glossy highlight. Calm and child friendly.")
src = Image.open(ROOT + 'bg_work/hand_src.png').convert('RGB')
cw, ch = 1536, 1024
k = min(cw * 0.8 / src.width * 1.0, ch * 0.8 / src.height)
nw, nh = round(src.width * k), round(src.height * k)
canvas = Image.new('RGB', (cw, ch), 'white'); y0 = (ch - nh) // 2
canvas.paste(src.resize((nw, nh), Image.LANCZOS), (0, y0))
buf = io.BytesIO(); canvas.save(buf, 'PNG'); buf.seek(0)
n = sys.argv[1]
r = requests.post(BASE + '/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY}, files={'image': ('in.png', buf, 'image/png')},
    data={'model': MODEL, 'prompt': PROMPT, 'size': f'{cw}x{ch}', 'quality': 'medium', 'n': '1'}, timeout=300)
if r.status_code != 200: print('HTTP', r.status_code, r.text[:400]); sys.exit(1)
d = r.json()['data'][0]
raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'bg_work/hand_new_{n}.png'); print('ok', nw, nh, k)
