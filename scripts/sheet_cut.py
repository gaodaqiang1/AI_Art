import sys

from PIL import Image

# usage: sheet_cut.py out.png a_cut.png b_cut.png ...   (each cut-out on a cream background, same height)
out = sys.argv[1]
imgs = [Image.open(p).convert('RGBA') for p in sys.argv[2:]]
h = 440
scaled = [i.resize((int(i.width * h / i.height), h), Image.LANCZOS) for i in imgs]
w = sum(i.width for i in scaled) + 30 * (len(scaled) + 1)
sheet = Image.new('RGBA', (w, h + 60), (255, 246, 234, 255))
x = 30
for i in scaled:
    sheet.alpha_composite(i, (x, 30))
    x += i.width + 30
sheet.convert('RGB').save(out)
print('saved', out, sheet.size)
