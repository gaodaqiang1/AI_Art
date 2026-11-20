"""2.5D redraw of the 5 furniture bases with a guaranteed open 'under' space (zones measured by under_zone.py).
Input = confirmed lang_final base (style + composition anchor). Usage: python gen_furniture.py <objIdx 5..9> <variant 1..>
Output: output_api/furn2/<obj>_v<variant>_big.png (white background)."""
import base64, io, os, sys, requests
from PIL import Image
ROOT = 'I:/GODOT/AI_Art/'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()
STYLE = ("Style: polished 2.5D children's mobile-game icon, clearly 3D-looking volume: soft glossy top highlights, bright lit top surfaces and darker shaded "
         "side faces, smooth gradients, rounded chunky forms, thin darker-tone coloured outline, slightly isometric three-quarter view from above. "
         "Plain solid white background, absolutely no floor, no ground shadow, no cast shadow, no text.")
HEAD = ("Use the reference only for the object type, colour palette and cute design language; redraw it freshly in a much stronger 2.5D look. The structure "
        "MUST follow these rules: ")
SPEC = {
 5: "a kid's wooden table, warm light-wood tabletop with a visible thick edge, standing on four thick rounded tapered legs at the four far corners. Under the tabletop there is a big, completely empty, clear gap (about 55% of the whole height); no shelves, no crossbars.",
 6: "a kid's chair with a yellow backrest and a light-blue seat, raised on four slim tapered wooden legs at the four corners, no crossbars or stretchers between the legs, the gap under the seat is large and empty (about 45% of the height).",
 7: "a compact two-seat sofa, the sofa body is LOW and FLAT-ish and sits entirely in the TOP 45% of the picture (back cushions, seat cushions, rounded arms). It stands on four thick chunky round wooden legs at the far corners that are TALL, so the bottom 55% of the picture is an empty wide open gap between the legs with the white background visible through it. Cream colour.",
 8: "a children's playground slide with ladder in yellow slide, blue ladder and teal handrails. The slide chute and ladder are raised on a tall open frame so the whole area under the slope between the ladder and the low end is a big empty open space (about 45% of the height); no walls or panels underneath.",
 9: "a kid's bed with wooden frame, blue starry blanket, cream pillow. The bed body (mattress, blanket, pillow, short headboard and footboard) is LOW and sits entirely in the TOP 45% of the picture. It stands on four thick chunky wooden posts at the four far corners that are TALL, so the bottom 55% of the picture is an empty wide open gap with the white background visible through it. No drawers, no side panels reaching down.",
}
o, v = int(sys.argv[1]), int(sys.argv[2])
src = Image.open(ROOT + f'output_api/lang_final/lang_{o}000.png').convert('RGBA')
w, h = src.size
r = w / h
cw, ch = (1536, 1024) if r > 1.2 else (1024, 1536) if r < 0.83 else (1024, 1024)
k = min(cw * .8 / w, ch * .8 / h)
nw, nh = round(w * k), round(h * k)
cv = Image.new('RGB', (cw, ch), 'white'); big = src.resize((nw, nh), Image.LANCZOS); cv.paste(big, ((cw - nw) // 2, (ch - nh) // 2), big)
buf = io.BytesIO(); cv.save(buf, 'PNG'); buf.seek(0)
rr = requests.post('https://cf.api.fan/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY}, files={'image': ('in.png', buf, 'image/png')},
    data={'model': 'gpt-image-2.5-flare', 'prompt': HEAD + SPEC[o] + ' ' + STYLE, 'size': f'{cw}x{ch}', 'quality': 'medium', 'n': '1'}, timeout=300)
if rr.status_code != 200:
    print('HTTP', rr.status_code, rr.text[:300]); sys.exit(1)
d = rr.json()['data'][0]
raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
os.makedirs(ROOT + 'output_api/furn2', exist_ok=True)
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'output_api/furn2/{o}_v{v}_big.png'); print('ok', o, v)
