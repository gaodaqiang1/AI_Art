"""2.5D redraw of the 5 furniture bases with a guaranteed open 'under' space (zones measured by under_zone.py).
Input = confirmed lang_final base (style + composition anchor). Usage: python gen_furniture.py <objIdx 5..9> <variant 1..>
Output: output_api/furn/<obj>_v<variant>_big.png (white background)."""
import base64, io, os, sys, requests
from PIL import Image
ROOT = 'I:/GODOT/AI_Art/'
KEY = open('I:/GODOT/IMAGE_API_KEY', encoding='utf-8').read().strip()
STYLE = ("Style: 2.5D modern children's mobile-game cartoon, slight 3D volume, soft glossy highlights, smooth gradients, thin darker-tone coloured outline, "
         "keep the exact same colour scheme and cute rounded design language as the reference. Plain solid white background, no floor, no ground shadow, no text.")
HEAD = ("Redraw this reference piece of toy furniture. Keep the SAME style, colours, materials, side-on three-quarter viewing angle and the SAME overall "
        "width-to-height proportion of the whole picture (the object must fill the frame the same way). BUT change the structure as follows: ")
SPEC = {
 5: "a low kid's table: a thick rounded tabletop raised on four sturdy tapered legs placed at the far corners only; the legs are tall so that the space under the tabletop between the legs is a big clear open gap, about 55% of the total height, background visible through it; nothing between the legs.",
 6: "a kid's chair: seat raised on four tall slim legs placed at the corners only (front pair and back pair far apart), the open gap under the seat between the legs is clear and about 45% of the total height; no crossbars, no stretchers between the legs; backrest stays above the seat.",
 7: "a cute two-seat sofa lifted high on four tall slender wooden legs at the far left and far right ends only. The whole space under the sofa body must be a tall, wide, completely empty gap, about 40% of the total height, with the white background clearly visible through it; the sofa body (seat, arms, back) sits entirely in the upper 60% of the picture.",
 8: "a children's playground slide with a ladder; the slide chute is lifted on a tall open frame so there is a big clear open space underneath the sloping chute and between the ladder and the slide end, about 45% of the total height; only thin supports at the extreme ends.",
 9: "a cute kid's bed lifted high on four tall posts/legs at the four far corners only. The mattress, blanket, pillow and headboard sit in the upper 60% of the picture; the whole space under the bed frame is a tall, wide, completely empty gap, about 40% of the total height, white background clearly visible through it; no drawers, no storage, no side panels reaching down.",
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
os.makedirs(ROOT + 'output_api/furn', exist_ok=True)
Image.open(io.BytesIO(raw)).convert('RGB').save(ROOT + f'output_api/furn/{o}_v{v}_big.png'); print('ok', o, v)
