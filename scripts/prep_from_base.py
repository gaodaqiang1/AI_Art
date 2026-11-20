"""Build prep_X0 furniture from the CONFIRMED lang_final base pictures (2.5D redraw), stretched to the legacy prep_* size
(legacy stretched lang_* base to prep_* size). Usage: python prep_from_base.py"""
import json
from collections import deque
from PIL import Image, ImageFilter
R = 'I:/GODOT/AI_Art/'
SZ = {o: Image.open(f'I:/GODOT/xwn/assets/legacy/images/prep_{o}0.png').size for o in range(5, 10)}

def cut(im):
    im = im.convert('RGB'); w, h = im.size; px = im.load(); seen = set()
    bg = Image.new('L', (w, h), 0); b = bg.load()
    q = deque([(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or min(px[x, y]) < 232: continue
        seen.add((x, y)); b[x, y] = 255
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    a = bg.point(lambda v: 255 - v).filter(ImageFilter.GaussianBlur(1.2))
    o = im.convert('RGBA'); o.putalpha(a); return o

for o in range(5, 10):
    c = cut(Image.open(R + f'output_api/lang_{o}000_fin25d_s3_big.png'))
    c = c.crop(c.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    c.resize(SZ[o], Image.LANCZOS).save(R + f'bg_work/prep_new/prep_{o}0.png', optimize=True)
    print(o, c.size, '->', SZ[o])
