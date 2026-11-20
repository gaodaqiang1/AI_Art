"""Compose the 4 language-game backgrounds (lang_bg_1/2/3 + bg_star) in the soft pastel style.
Geometry (frame, divider x, hand box, star-circle centres) is copied from the legacy 1024x768 art; output is 2048x1536.
Usage: python lang_bg_compose.py [outdir]   (default AI_Art/bg_work/out)"""
import os
import sys
import random
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

W, H, F = 2048, 1536, 2          # final size, factor vs legacy 1x coordinates
SS = 2                            # extra supersample for masks
OUT = sys.argv[1] if len(sys.argv) > 1 else 'I:/GODOT/AI_Art/bg_work/out'
os.makedirs(OUT, exist_ok=True)


def hexc(s):
    return tuple(int(s[i:i + 2], 16) for i in (1, 3, 5))


def mask(fn):
    m = Image.new('L', (W * SS, H * SS), 0)
    d = ImageDraw.Draw(m)
    fn(d, F * SS)
    return m.resize((W, H), Image.LANCZOS)


def fill(img, m, color, alpha=1.0):
    layer = Image.new('RGB', (W, H), color)
    if alpha < 1:
        m = m.point(lambda v: int(v * alpha))
    img.paste(layer, (0, 0), m)


def rrect(box, r):
    return lambda d, k: d.rounded_rectangle([box[0] * k, box[1] * k, box[2] * k, box[3] * k], r * k, fill=255)


def circle(cx, cy, r):
    return lambda d, k: d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=255)


def clip(m, region):
    return ImageChops.multiply(m, region)


INNER = (17, 17, 1007, 751)
RAD = 42
inner_m = mask(rrect(INNER, RAD))


def frame(base, hi, lo, tab_col):
    img = Image.new('RGB', (W, H), base)
    ring = mask(rrect((INNER[0] - 6, INNER[1] - 6, INNER[2] + 6, INNER[3] + 6), RAD + 6))
    fill(img, ring, lo)
    outer_hi = mask(rrect((4, 4, 1020, 764), 52))
    inner_hi = mask(rrect((9, 9, 1015, 759), 47))
    fill(img, ImageChops.subtract(outer_hi, inner_hi), hi, 0.55)
    fill(img, mask(rrect((-20, 358, 37, 410), 9)), tab_col)      # tab on the left edge (legacy y 358-410)
    fill(img, mask(rrect((-20, 358, 37, 372), 7)), hi, 0.35)
    return img


def bubbles(img, region, x_max, seed=3):
    rnd = random.Random(seed)
    for i in range(26):
        r = rnd.choice([14, 20, 28, 40, 60, 90, 130])
        cx = rnd.uniform(0, x_max)
        cy = rnd.uniform(0, 768)
        if i % 3:
            col, a = (255, 255, 255), rnd.uniform(.18, .34)
        else:
            col, a = hexc('#8FD3DA'), rnd.uniform(.14, .24)
        fill(img, clip(mask(circle(cx, cy, r)), region), col, a)


def cream_dots(img, region, x0, x1, seed=5, col='#FFEAD0'):
    rnd = random.Random(seed)
    for _ in range(46):
        r = rnd.uniform(5, 16)
        cx = rnd.uniform(x0, x1)
        cy = rnd.uniform(30, 740)
        fill(img, clip(mask(circle(cx, cy, r)), region), hexc(col), rnd.uniform(.35, .7))


def vgrad(top, bot):
    a = np.linspace(0, 1, H)[:, None, None]
    t = np.array(top, float)[None, None, :]
    b = np.array(bot, float)[None, None, :]
    arr = (t * (1 - a) + b * a) * np.ones((H, W, 1))
    return Image.fromarray(arr.astype('uint8'))


def load_hand():
    im = Image.open('I:/GODOT/AI_Art/bg_work/hand_new_1.png').convert('RGB')
    a = np.array(im).astype(int)
    h, w = a.shape[:2]
    white = a.min(2) >= 235
    bg = np.zeros((h, w), bool)
    q = deque([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + [(w - 1, y) for y in range(h)])
    while q:
        x, y = q.popleft()
        if not (0 <= x < w and 0 <= y < h) or bg[y, x] or not white[y, x]:
            continue
        bg[y, x] = True
        q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    alpha = Image.fromarray((~bg * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.2))
    o = im.convert('RGBA')
    o.putalpha(alpha)
    return o.crop(o.getchannel('A').point(lambda v: 255 if v > 30 else 0).getbbox())


HAND = load_hand()
HAND_BOX = {1: (17, 473, 428, 591), 2: (17, 373, 430, 555), 3: (17, 260, 440, 530)}   # legacy skin bbox
SPLIT = {1: 513, 2: 383, 3: 272}


def lang_bg(n):
    sp = SPLIT[n]
    img = frame(hexc('#C9B6EC'), hexc('#F1E8FF'), hexc('#A894D6'), hexc('#A894D6'))
    left_region = clip(inner_m, mask(lambda d, k: d.rectangle([0, 0, sp * k, 768 * k], fill=255)))
    right_region = clip(inner_m, mask(lambda d, k: d.rectangle([sp * k, 0, 1024 * k, 768 * k], fill=255)))
    img.paste(vgrad(hexc('#D4F2F5'), hexc('#B5E4EA')), (0, 0), left_region)
    bubbles(img, left_region, 560)
    img.paste(vgrad(hexc('#FFF7EB'), hexc('#FFEFD9')), (0, 0), right_region)
    cream_dots(img, right_region, sp + 20, 1000)
    if n == 3:   # legacy bg3 has a lighter strip at the far right
        xs = np.arange(W)
        ramp = np.clip((xs - 1880) / (2012 - 1880), 0, 1) * 150
        a = np.tile(ramp[None, :], (H, 1)).astype(np.uint8)
        img.paste(Image.new('RGB', (W, H), (255, 252, 244)), (0, 0), clip(Image.fromarray(a), right_region))
    # divider: white line + soft shadow on the right
    sh = np.zeros((H, W), np.uint8)
    x0 = sp * F
    span = 13 * F
    for i in range(span):
        sh[:, x0 + 10 * F + i] = int(70 * (1 - i / span) ** 2)
    img.paste(Image.new('RGB', (W, H), hexc('#C9B79A')), (0, 0), clip(Image.fromarray(sh), right_region))
    line = mask(lambda d, k: d.rectangle([sp * k, 17 * k, (sp + 9) * k, 751 * k], fill=255))
    fill(img, clip(line, inner_m), (255, 255, 255))
    # hand, clipped to the left panel (arm is cut at the panel edge like the legacy art)
    x0h, x1h, y0h, y1h = HAND_BOX[n]
    hw = round((x1h - x0h) * F * 1.01)
    hh = round(HAND.height * hw / HAND.width)
    hand = HAND.resize((hw, hh), Image.LANCZOS)
    top = round((y0h + y1h) / 2 * F - hh / 2)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay.alpha_composite(hand, (x0h * F, top))
    la = ImageChops.multiply(lay.getchannel('A'), left_region)
    img.paste(lay.convert('RGB'), (0, 0), la)
    return img


def star_bg():
    img = frame(hexc('#86CBD4'), hexc('#D8F3F5'), hexc('#5FAEB9'), hexc('#5FAEB9'))
    base = vgrad(hexc('#BFEAE3'), hexc('#A6DDD9'))
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.hypot((xx - 1028) / 1400, (yy - 850) / 1000)
    glow = (np.clip(1 - d, 0, 1) ** 1.6 * 150).astype('uint8')
    base.paste(Image.new('RGB', (W, H), hexc('#E8FAF3')), (0, 0), Image.fromarray(glow))
    img.paste(base, (0, 0), inner_m)
    rnd = random.Random(11)
    for i in range(22):
        r = rnd.choice([40, 60, 90, 120, 160])
        cx = rnd.uniform(0, 1024)
        cy = rnd.uniform(0, 768)
        if i % 2:
            col, a = (255, 255, 255), rnd.uniform(.14, .26)
        else:
            col, a = hexc('#7CC9CC'), rnd.uniform(.14, .22)
        fill(img, clip(mask(circle(cx, cy, r)), inner_m), col, a)
    # hub (centres/radii copied from legacy bg_star)
    C = (514, 421, 170)
    S = [(485, 134, 90), (796, 282, 90), (217, 299, 90), (783, 588, 90), (260, 597, 90)]
    pale, edge, shade = hexc('#FFFDF2'), hexc('#8CCFC8'), hexc('#CFEBDD')

    def conns(width):
        def fn(d, k):
            for (x, y, r) in S:
                d.line([C[0] * k, C[1] * k, x * k, y * k], fill=255, width=int(width * k))
        return mask(fn)
    cm = conns(21)
    fill(img, ImageChops.offset(cm, 0, 6 * F), hexc('#5DB5B5'), 0.30)
    fill(img, cm, edge)
    fill(img, conns(15), pale)
    for (x, y, r) in [C] + S:
        fill(img, ImageChops.offset(mask(circle(x, y, r + 2)), 0, 8 * F), hexc('#5DB5B5'), 0.30)
        fill(img, mask(circle(x, y, r + 3)), edge)
        fill(img, mask(circle(x, y, r)), pale)
        ring = ImageChops.subtract(mask(circle(x, y, r)), mask(circle(x, y - 5, r)))
        fill(img, ring, shade, 0.9)
    return img


if __name__ == '__main__':
    for n in (1, 2, 3):
        lang_bg(n).save(f'{OUT}/lang_bg_{n}.png', optimize=True)
        print('lang_bg', n)
    star_bg().save(f'{OUT}/bg_star.png', optimize=True)
    print('bg_star')
