import json
from PIL import Image
R = 'I:/GODOT/AI_Art/output_api/'
S = 'I:/GODOT/xwn/assets/legacy/images/'
rows = json.load(open('I:/GODOT/xwn/data/sqlite_content/lang.json', encoding='utf-8'))
FN = {(r['category0'], r['category1'], r['category2'], r['category3']): r['filename'] for r in rows}
picks = [(0, 0, 0, 0), (0, 0, 0, 2), (0, 1, 2, 1), (5, 0, 3, 2), (5, 2, 0, 1), (8, 0, 4, 1), (6, 1, 1, 2), (9, 0, 2, 2)]
sh = Image.new('RGB', (len(picks) * 330, 2 * 330), (200, 220, 200))
def put(d, f, x, y):
    im = Image.open(d + f).convert('RGBA')
    im.thumbnail((320, 320))
    sh.paste(im, (x * 330, y * 330), im)
[put(S, FN[p], i, 0) for i, p in enumerate(picks)]
[put(R + 'lang_final/', FN[p], i, 1) for i, p in enumerate(picks)]
sh.save(R + '_final_check.png')
