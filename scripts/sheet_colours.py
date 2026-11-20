from PIL import Image

D = 'I:/GODOT/AI_Art/output_api/lang_new/'
F = 'I:/GODOT/AI_Art/output_api/final/dog_golden.png'
W, H = 230, 190
sh = Image.new('RGB', (W * 5, H * 10), (200, 220, 200))


def path(k, c):
    if c == 0:
        return F if k == 0 else D + 'obj%d_v1.png' % k
    return D + 'obj%d_c%d.png' % (k, c)


def put(k, c):
    im = Image.open(path(k, c)).convert('RGBA')
    im.thumbnail((W - 10, H - 10))
    sh.paste(im, (c * W, k * H), im)


[put(k, c) for k in range(10) for c in range(5)]
sh.save('I:/GODOT/AI_Art/output_api/_lang_colours_sheet.png')
