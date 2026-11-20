"""2.5D version of the 4 language backgrounds: bevelled frame, inset panels with inner shadow, glassy bubbles with rim light,
raised plates for bg_star. Same geometry as lang_bg_compose.py (divider x, hand box, circle centres). Output: bg_work/out25/"""
import os, sys, random
import numpy as np
from PIL import Image, ImageChops, ImageFilter
sys.argv = sys.argv[:1]
import lang_bg_compose as B
from lang_bg_compose import W, H, F, mask, fill, rrect, circle, clip, hexc, vgrad, inner_m, INNER, RAD, HAND, HAND_BOX, SPLIT

OUT = 'I:/GODOT/AI_Art/bg_work/out25'
os.makedirs(OUT, exist_ok=True)


def blur(m, r):
    return m.filter(ImageFilter.GaussianBlur(r * F))


def inner_shadow(img, region, dx, dy, r, color, alpha):
    """shadow falling INSIDE region from its own edge (inset look)"""
    off = ImageChops.offset(ImageChops.invert(region), dx * F, dy * F)
    sh = ImageChops.multiply(blur(off, r), region)
    fill(img, sh, color, alpha)


def drop_shadow(img, shape, dx, dy, r, color, alpha):
    fill(img, blur(ImageChops.offset(shape, dx * F, dy * F), r), color, alpha)


def frame25(base_top, base_bot, hi, lo):
    img = vgrad(base_top, base_bot)
    outer = mask(rrect((0, 0, 1024, 768), 56))
    # bevel on the outer border: light top/left rim, dark bottom/right rim
    lit = ImageChops.subtract(outer, ImageChops.offset(outer, 5 * F, 5 * F))
    fill(img, lit, hi, 0.9)
    dark = ImageChops.subtract(outer, ImageChops.offset(outer, -5 * F, -5 * F))
    fill(img, dark, lo, 0.55)
    # panel sits in a groove
    ring = mask(rrect((INNER[0] - 7, INNER[1] - 7, INNER[2] + 7, INNER[3] + 7), RAD + 7))
    fill(img, ring, lo, 0.9)
    groove_hi = ImageChops.subtract(mask(rrect((INNER[0] - 9, INNER[1] - 9, INNER[2] + 9, INNER[3] + 9), RAD + 9)), ring)
    fill(img, groove_hi, hi, 0.8)
    # tab
    tab = mask(rrect((-20, 358, 37, 410), 9))
    drop_shadow(img, tab, 2, 3, 3, lo, 0.6)
    fill(img, tab, lo)
    fill(img, mask(rrect((-20, 358, 37, 376), 8)), hi, 0.55)
    return img


def glass_bubbles(img, region, x_max, seed=3, tint='#8FD3DA'):
    rnd = random.Random(seed)
    for i in range(24):
        r = rnd.choice([16, 22, 30, 42, 60, 90, 120])
        cx, cy = rnd.uniform(0, x_max), rnd.uniform(0, 768)
        body = clip(mask(circle(cx, cy, r)), region)
        fill(img, body, hexc(tint) if i % 3 == 0 else (255, 255, 255), rnd.uniform(.10, .20))
        # rim light on the upper-left and soft shade on the lower-right, clipped to the bubble
        hi = ImageChops.subtract(body, ImageChops.offset(body, 3 * F, 3 * F)); fill(img, hi, (255, 255, 255), 0.55)
        lo = ImageChops.subtract(body, ImageChops.offset(body, -3 * F, -3 * F)); fill(img, lo, hexc('#5FB3BD'), 0.30)
        if r >= 30:
            fill(img, clip(mask(circle(cx - r * .35, cy - r * .38, r * .16)), region), (255, 255, 255), 0.65)


def paper_dots(img, region, x0, x1, seed=5):
    rnd = random.Random(seed)
    for _ in range(34):
        r = rnd.uniform(6, 18); cx, cy = rnd.uniform(x0, x1), rnd.uniform(30, 740)
        d = clip(mask(circle(cx, cy, r)), region)
        fill(img, d, hexc('#FFE3C2'), rnd.uniform(.45, .8))
        fill(img, ImageChops.subtract(d, ImageChops.offset(d, 2 * F, 2 * F)), (255, 255, 255), 0.6)


def lang25(n):
    sp = SPLIT[n]
    img = frame25(hexc('#D3C2F2'), hexc('#B49FE0'), hexc('#F6EEFF'), hexc('#8F7BC2'))
    left = clip(inner_m, mask(lambda d, k: d.rectangle([0, 0, sp * k, 768 * k], fill=255)))
    right = clip(inner_m, mask(lambda d, k: d.rectangle([sp * k, 0, 1024 * k, 768 * k], fill=255)))
    img.paste(vgrad(hexc('#DDF6F8'), hexc('#A9E1E8')), (0, 0), left)
    glass_bubbles(img, left, 560)
    img.paste(vgrad(hexc('#FFF9EF'), hexc('#FFEBD2')), (0, 0), right)
    paper_dots(img, right, sp + 20, 1000)
    if n == 3:
        xs = np.arange(W); ramp = np.clip((xs - 1880) / 132, 0, 1) * 140
        img.paste(Image.new('RGB', (W, H), (255, 253, 247)), (0, 0), clip(Image.fromarray(np.tile(ramp[None, :], (H, 1)).astype(np.uint8)), right))
    # both panels are inset into the frame
    inner_shadow(img, left, 3, 4, 7, hexc('#4C97A3'), 0.55)
    inner_shadow(img, right, 3, 4, 7, hexc('#B79B72'), 0.50)
    # raised ridge as divider
    ridge = clip(mask(lambda d, k: d.rectangle([(sp - 3) * k, 17 * k, (sp + 12) * k, 751 * k], fill=255)), inner_m)
    drop_shadow(img, ridge, 5, 0, 5, hexc('#7A6544'), 0.50)
    fill(img, ridge, hexc('#F3EBDD'))
    fill(img, clip(mask(lambda d, k: d.rectangle([(sp - 3) * k, 17 * k, (sp + 2) * k, 751 * k], fill=255)), inner_m), (255, 255, 255))
    fill(img, clip(mask(lambda d, k: d.rectangle([(sp + 8) * k, 17 * k, (sp + 12) * k, 751 * k], fill=255)), inner_m), hexc('#CDBB9B'))
    # hand with a soft contact shadow, clipped to the left panel
    x0h, x1h, y0h, y1h = HAND_BOX[n]
    hw = round((x1h - x0h) * F * 1.01); hh = round(HAND.height * hw / HAND.width)
    hand = HAND.resize((hw, hh), Image.LANCZOS); top = round((y0h + y1h) / 2 * F - hh / 2)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.alpha_composite(hand, (x0h * F, top))
    ha = ImageChops.multiply(lay.getchannel('A'), left)
    drop_shadow(img, ha, 4, 12, 9, hexc('#3E8E9A'), 0.45)
    img.paste(lay.convert('RGB'), (0, 0), ha)
    return img


def star25():
    img = frame25(hexc('#8ED6DB'), hexc('#5FB3BD'), hexc('#E2F8F9'), hexc('#3E8E9A'))
    base = vgrad(hexc('#C6EFE8'), hexc('#9AD9D6'))
    yy, xx = np.mgrid[0:H, 0:W]; d = np.hypot((xx - 1028) / 1400, (yy - 850) / 1000)
    base.paste(Image.new('RGB', (W, H), hexc('#EBFBF4')), (0, 0), Image.fromarray((np.clip(1 - d, 0, 1) ** 1.6 * 150).astype('uint8')))
    img.paste(base, (0, 0), inner_m)
    glass_bubbles(img, inner_m, 1024, seed=11, tint='#7CC9CC')
    inner_shadow(img, inner_m, 3, 4, 8, hexc('#2F7C86'), 0.55)
    C = (514, 421, 170); S = [(485, 134, 90), (796, 282, 90), (217, 299, 90), (783, 588, 90), (260, 597, 90)]

    def conns(width):
        def fn(dr, k):
            for (x, y, r) in S: dr.line([C[0] * k, C[1] * k, x * k, y * k], fill=255, width=int(width * k))
        return mask(fn)
    cm = conns(24)
    drop_shadow(img, cm, 0, 8, 6, hexc('#2F7C86'), 0.40); fill(img, cm, hexc('#7CC6C0')); fill(img, conns(17), hexc('#F6FFF6'))
    for (x, y, r) in [C] + S:
        plate = mask(circle(x, y, r + 4))
        drop_shadow(img, plate, 0, 14, 9, hexc('#2F7C86'), 0.45)           # raised plate casts a shadow
        fill(img, plate, hexc('#6FBDB6'))                                     # rim
        side = mask(circle(x, y + 7, r + 1)); fill(img, side, hexc('#A9DAD0'))  # plate thickness (lower side)
        top = mask(circle(x, y, r)); fill(img, top, hexc('#FFFEF3'))
        # dish: soft inner shade at the top edge + glossy highlight arc
        fill(img, ImageChops.subtract(top, ImageChops.offset(top, 0, 9 * F)), hexc('#D6EBDD'), 0.9)
        fill(img, clip(mask(circle(x - r * .28, y - r * .42, r * .34)), top), (255, 255, 255), 0.55)
    return img


if __name__ == '__main__':
    for n in (1, 2, 3):
        lang25(n).save(f'{OUT}/lang_bg_{n}.png', optimize=True); print('lang_bg', n)
    star25().save(f'{OUT}/bg_star.png', optimize=True); print('bg_star')
