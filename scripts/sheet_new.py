from PIL import Image

D = 'I:/GODOT/AI_Art/output_api/lang_new/'
S = 'I:/GODOT/xwn/assets/legacy/images/'
W, H = 260, 200
sh = Image.new('RGB', (W * 4, H * 10), (200, 220, 200))


def put(path, x, y):
    im = Image.open(path).convert('RGBA')
    im.thumbnail((W - 10, H - 10))
    sh.paste(im, (x * W, y * H), im)


for k in range(10):
    put(S + 'lang_%d000.png' % k, 0, k)
    for v in range(3):
        put(D + 'obj%d_v%d.png' % (k, v + 1), v + 1, k)
sh.save('I:/GODOT/AI_Art/output_api/_lang_new_sheet.png')
