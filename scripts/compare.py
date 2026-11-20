import sys

from PIL import Image

# usage: compare.py out.png a.png b.png [c.png ...]  (every image is shown on the same cream background)
out = sys.argv[1]
imgs = [Image.open(p).convert('RGBA') for p in sys.argv[2:]]
h = 640
scaled = []
for im in imgs:
    scaled.append(im.resize((int(im.width * h / im.height), h), Image.LANCZOS))
w = sum(i.width for i in scaled) + 20 * (len(scaled) + 1)
sheet = Image.new('RGBA', (w, h + 40), (255, 246, 234, 255))
x = 20
for im in scaled:
    sheet.alpha_composite(im, (x, 20))
    x += im.width + 20
sheet.convert('RGB').save(out)
print('saved', out, sheet.size)
