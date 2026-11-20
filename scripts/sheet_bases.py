from PIL import Image
import os
D = 'I:/GODOT/AI_Art/output_api/lang_base/'
S = 'I:/GODOT/xwn/assets/legacy/images/'
sh = Image.new('RGB', (230 * 5, 400 * 1 + 400), (200, 220, 200))
def put(k, x, y, src):
    p = (S + 'lang_%d000.png' % k) if src else (D + 'obj%d.png' % k)
    if k == 0 and not src:
        p = 'I:/GODOT/AI_Art/output_api/final/dog_golden.png'
    if not os.path.exists(p):
        return
    im = Image.open(p).convert('RGBA')
    im.thumbnail((220, 190))
    sh.paste(im, (x * 230, y * 200), im)
cells = [(k, k % 5, k // 5, False) for k in range(10)] + [(k, k % 5, 2 + k // 5, True) for k in range(10)]
[put(*c[:3], c[3]) for c in cells]
sh.save('I:/GODOT/AI_Art/output_api/_lang_bases_sheet.png')
