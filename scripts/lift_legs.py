"""Make short legs tall by stretching only the leg band (rows below the body bottom) vertically. Legs are plain tapered posts, so
this reads as taller legs. Usage: lift_legs(rgba, factor) -> rgba."""
import numpy as np
from PIL import Image


def lift_legs(im, factor, wide=0.55):
    a = np.array(im.getchannel('A')) > 40
    W = a.shape[1]
    rows = a.sum(1) / float(max(1, np.ptp(np.where(a.any(0))[0]) + 1))
    ys = np.where(a.any(1))[0]
    y0, y1 = ys.min(), ys.max()
    body_bottom = y0
    for y in range(y1, y0, -1):          # first row (from the bottom) that is "body wide"
        if rows[y] >= wide:
            body_bottom = y
            break
    legs = im.crop((0, body_bottom + 1, im.width, y1 + 1))
    body = im.crop((0, 0, im.width, body_bottom + 1))
    legs = legs.resize((legs.width, max(1, round(legs.height * factor))), Image.LANCZOS)
    out = Image.new('RGBA', (im.width, body.height + legs.height), (0, 0, 0, 0))
    out.alpha_composite(body, (0, 0))
    out.alpha_composite(legs, (0, body.height))
    return out, (y0, body_bottom, y1)
