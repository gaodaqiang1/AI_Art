import json
import os
from PIL import Image

os.chdir('I:/GODOT/xwn')
O = 'I:/GODOT/AI_Art/output_api/'
rows = json.load(open('data/sqlite_content/lang.json', encoding='utf-8'))
t = {(r['category0'], r['category1'], r['category2'], r['category3']): r for r in rows}


def size_of(k):
    return (t[k]['width'], t[k]['height'])


for o in (0, 5):
    print('obj', o)
    print(' sizes', [[size_of((o, s, 0, n)) for n in range(3)] for s in range(3)])
    print(' colours', [size_of((o, 0, c, 0)) for c in range(5)])


def tile(sh, k, x, y, W, H):
    im = Image.open('assets/legacy/images/' + t[k]['filename']).convert('RGBA')
    im.thumbnail((W - 8, H - 8))
    sh.paste(im, (x * W, y * H), im)


def paste(keys, name, W=260, H=170):
    sh = Image.new('RGB', (W * len(keys[0]), H * len(keys)), (200, 220, 200))
    cells = [(x, y, k) for y, row in enumerate(keys) for x, k in enumerate(row)]
    [tile(sh, k, x, y, W, H) for x, y, k in cells]
    sh.save(O + name)


paste([[(5, s, 0, n) for n in range(3)] for s in range(3)], '_t_sizes.png')
paste([[(o, 0, c, 0) for c in range(5)] for o in (0, 5, 2)], '_t_colours.png')
