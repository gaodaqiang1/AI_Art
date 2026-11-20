import json
import os
from PIL import Image

os.chdir('I:/GODOT/xwn')
rows = json.load(open('data/sqlite_content/lang.json', encoding='utf-8'))
t = {(r['category0'], r['category1'], r['category2'], r['category3']): r for r in rows}


def dims(o, s):
    return [(t[(o, s, 0, n)]['width'], t[(o, s, 0, n)]['height']) for n in range(3)]


[print(o, s, dims(o, s)) for o in range(10) for s in range(3)]

W, H = 340, 300
sh = Image.new('RGB', (W * 3, H * 10), (200, 220, 200))


def tile(k, x, y):
    im = Image.open('assets/legacy/images/' + t[k]['filename']).convert('RGBA')
    im.thumbnail((W - 8, H - 8))
    sh.paste(im, (x * W, y * H), im)


[tile((o, 0, 0, n), n, o) for o in range(10) for n in range(3)]
sh.save('I:/GODOT/AI_Art/output_api/_orig_counts.png')
