"""2.5D colour variants of the 10 lang bases. Input output_api/base25/<k>.png (RGB, white bg) -> output_api/col25/<k>_c<c>_big.png
Usage: python gen_colour25.py <k 0..9> <c 1..4>"""
import base64, io, os, sys, requests
from PIL import Image
ROOT = 'I:/GODOT/AI_Art/'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()
COL = {1: ('bright red (#E53935 family)', 'red'), 2: ('fresh green (#43A047 family)', 'green'), 3: ('sky blue (#1E88E5 family)', 'blue'), 4: ('vivid orange (#FB8C00 family)', 'orange')}
k, c = int(sys.argv[1]), int(sys.argv[2])
colour, name = COL[c]
PROMPT = (f"Recolor this exact game object so that it is clearly and predominantly {colour}. Use lighter and darker shades of that one hue for all parts "
          f"of the object (every part: for a dog its fur, ears and body; for a book its cover and pages edge; for a cup the cup and saucer; for a bed the blanket and frame), "
          f"so a child would call it 'the {name} one'. Keep IDENTICAL shape, design, proportions, pose, outline style, glossy 2.5D look, details, size and position. "
          f"Plain solid white background, no floor, no shadow, no text.")
src = Image.open(ROOT + f'output_api/base25/{k}.png').convert('RGB')
w, h = src.size
cw, ch = (1536, 1024) if w / h > 1.2 else (1024, 1536) if w / h < .83 else (1024, 1024)
s = min(cw * .85 / w, ch * .85 / h); nw, nh = round(w * s), round(h * s)
cv = Image.new('RGB', (cw, ch), 'white'); cv.paste(src.resize((nw, nh), Image.LANCZOS), ((cw - nw) // 2, (ch - nh) // 2))
buf = io.BytesIO(); cv.save(buf, 'PNG'); buf.seek(0)
r = requests.post('https://cf.api.fan/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY}, files={'image': ('in.png', buf, 'image/png')},
    data={'model': 'gpt-image-2.5-flare', 'prompt': PROMPT, 'size': f'{cw}x{ch}', 'quality': 'medium', 'n': '1'}, timeout=300)
if r.status_code != 200:
    print('HTTP', r.status_code, r.text[:200]); sys.exit(1)
d = r.json()['data'][0]
raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
os.makedirs(ROOT + 'output_api/col25', exist_ok=True)
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'output_api/col25/{k}_c{c}_big.png'); print('ok', k, c)
