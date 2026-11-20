"""Contact sheet that keeps every picture's real aspect ratio (never squashes), with filename labels.
Usage: python sheet.py out.png file1 file2 ... [--cols 5] [--cell 360] [--bg white|teal] [--pair]
--pair: files are given as base,new,base,new ... and each pair is drawn on top of each other."""
import os
import sys
from PIL import Image, ImageDraw


def main():
    a = sys.argv[1:]
    out = a.pop(0)
    opt = {'--cols': 5, '--cell': 360}
    bg = 'white'
    pair = False
    files = []
    i = 0
    while i < len(a):
        if a[i] in opt:
            opt[a[i]] = int(a[i + 1]); i += 2
        elif a[i] == '--bg':
            bg = a[i + 1]; i += 2
        elif a[i] == '--pair':
            pair = True; i += 1
        else:
            files.append(a[i]); i += 1
    cols, cell = opt['--cols'], opt['--cell']
    color = {'white': (255, 255, 255), 'teal': (150, 230, 225)}.get(bg, (255, 255, 255))
    items = [files[i:i + 2] for i in range(0, len(files), 2)] if pair else [[f] for f in files]
    rows = (len(items) + cols - 1) // cols
    h = cell * (2 if pair else 1) + 22
    sheet = Image.new('RGB', (cols * cell, rows * h), color)
    d = ImageDraw.Draw(sheet)
    for n, grp in enumerate(items):
        for k, f in enumerate(grp):
            im = Image.open(f).convert('RGBA')
            im.thumbnail((cell - 12, cell - 12))
            x, y = (n % cols) * cell + 6, (n // cols) * h + k * cell + 4
            sheet.paste(im, (x, y), im)
        d.text(((n % cols) * cell + 6, (n // cols) * h + h - 16), os.path.basename(grp[-1])[:40], fill=(90, 70, 50))
    sheet.save(out)
    print('saved', out, sheet.size)


if __name__ == '__main__':
    main()
