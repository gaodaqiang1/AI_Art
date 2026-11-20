import sys

from PIL import Image

# usage: compare_grid.py out.png orig1,new1 orig2,new2 ...   (top row originals, bottom row new pictures)
out = sys.argv[1]
pairs = [a.split(',') for a in sys.argv[2:]]
cell_h = 360
cell_w = 400
sheet = Image.new('RGBA', (cell_w * len(pairs) + 20, cell_h * 2 + 30), (255, 246, 234, 255))
for i, pair in enumerate(pairs):
    for row, path in enumerate(pair):
        im = Image.open(path).convert('RGBA')
        s = min((cell_w - 30) / im.width, (cell_h - 30) / im.height)
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        x = 20 + i * cell_w + (cell_w - 30 - im.width) // 2
        y = 15 + row * cell_h + (cell_h - 30 - im.height) // 2
        sheet.alpha_composite(im, (x, y))
sheet.convert('RGB').save(out)
print('saved', out, sheet.size)
