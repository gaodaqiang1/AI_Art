import os
from PIL import Image, ImageFilter
from collections import deque
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.makedirs('output_api/final', exist_ok=True)
W, H, M = 205, 187, 5   # game frame size, margin

def is_white(p): return min(p) >= 225
def is_mag(p): return p[0] > 190 and p[2] > 190 and p[1] < 110

def cut(im, test):
    im = im.convert('RGB'); w, h = im.size; px = im.load()
    bg = Image.new('L', (w, h), 0); b = bg.load(); seen = set()
    q = deque([(x, y) for x in range(w) for y in (0, h-1)] + [(x, y) for y in range(h) for x in (0, w-1)])
    while q:
        x, y = q.popleft()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h) or not test(px[x, y]): continue
        seen.add((x, y)); b[x, y] = 255
        q.extend(((x+1, y), (x-1, y), (x, y+1), (x, y-1)))
    a = bg.point(lambda v: 255-v).filter(ImageFilter.GaussianBlur(1.5))
    o = im.convert('RGBA'); o.putalpha(a); return o

def fit(o):
    o = o.crop(o.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
    k = min((W-2*M)/o.width, (H-2*M)/o.height)
    o = o.resize((max(1, round(o.width*k)), max(1, round(o.height*k))), Image.LANCZOS)
    f = Image.new('RGBA', (W, H), (0, 0, 0, 0)); f.alpha_composite(o, ((W-o.width)//2, (H-o.height)//2)); return f

names = ['golden', 'choco', 'black', 'cream', 'red', 'gray']
ims = []
for n in names:
    f = 'output_api/lang_0000_golden_s1_big.png' if n == 'golden' else f'output_api/_golden_base_{n}_s1_big.png'
    o = fit(cut(Image.open(f), is_mag if n == 'cream' else is_white))
    o.save(f'output_api/final/dog_{n}.png', optimize=True)
    o.save(f'output_api/final/dog_{n}.webp', 'WEBP', quality=80, method=6)
    ims.append(o); print(n, os.path.getsize(f'output_api/final/dog_{n}.png'), os.path.getsize(f'output_api/final/dog_{n}.webp'))
s = Image.new('RGBA', (sum(i.width+10 for i in ims), H), (120, 170, 120, 255)); x = 0
for n in names:
    s.alpha_composite(Image.open(f'output_api/final/dog_{n}.webp').convert('RGBA'), (x, 0)); x += W+10
s.save('output_api/final/_sheet_colors.png')
