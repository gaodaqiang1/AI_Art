"""
Six pixel-art looks of one subject, running, side view; each one is cut out and snapped to a clean pixel grid.
Usage: venv/Scripts/python.exe scripts/pixel6.py --subject puppy --seed 6000
Writes output_25d/hand10/<subject>_<n>.png (raw) and output_25d/hand10/cut/<subject>_<n>_cut.png plus a contact sheet.
"""
import argparse
import json
import os
import shutil
import time
import urllib.request
import uuid
import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = 'http://127.0.0.1:8188'
OUT_DIR = os.path.join(ROOT, 'output_25d', 'pixel6')
CUT_DIR = os.path.join(OUT_DIR, 'cut')
COMFY_OUTPUT = os.path.join(ROOT, 'ComfyUI', 'output')

COMMON = ", pixel art, running, side view, whole body visible with all four legs and the tail clearly visible, mid-stride, plain solid white background with no scenery and no ground shadow, centered, single character, child friendly, calm, no accessories, no collar, no text"
STYLES = [
    'pixel art, 16-bit retro game sprite, clean pixels, limited color palette, flat colors, dark outline, cute simple',
    'pixel art, 32-bit game sprite, soft pastel palette, one pixel dark outline, simple shading, cute round face',
    'chunky low resolution pixel art, 8-bit style, very few colors, bold dark outline, cute simplified dog',
    'pixel art sprite, soft rounded shapes, gentle two-tone shading, no outline, pastel colors, cute',
    'isometric style pixel art character, clean pixel clusters, soft palette, cute',
    'pixel art, Game Boy Advance style character sprite, bright clean colors, black outline, friendly',
]
NEGATIVE = 'text, watermark, logo, extra limbs, deformed, blurry, antialiased smooth gradient, photo, realistic, 3d render, scary, multiple characters, sitting, front view, facing camera, collar, bandana, scarf, clothes, accessories, floor, ground, cropped, partial body, scenery'


def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(COMFY + path, data=data, headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


def get(path):
    return json.load(urllib.request.urlopen(COMFY + path))


def node(class_type, **inputs):
    return {'class_type': class_type, 'inputs': inputs}


def graph(prompt, seed):
    g = {}
    g['1'] = node('CheckpointLoaderSimple', ckpt_name='sd_xl_base_1.0.safetensors')
    g['2'] = node('EmptyLatentImage', width=1024, height=1024, batch_size=1)
    g['4'] = node('CLIPTextEncode', text=prompt, clip=['1', 1])
    g['5'] = node('CLIPTextEncode', text=NEGATIVE, clip=['1', 1])
    g['13'] = node('KSampler', model=['1', 0], seed=seed, steps=30, cfg=7.0, sampler_name='dpmpp_2m', scheduler='karras', positive=['4', 0], negative=['5', 0], latent_image=['2', 0], denoise=1.0)
    g['14'] = node('VAEDecode', samples=['13', 0], vae=['1', 2])
    g['15'] = node('SaveImage', images=['14', 0], filename_prefix='hand10')
    return g


def wait_for(pid):
    while True:
        hist = get('/history/' + pid)
        if pid in hist:
            return hist[pid]
        time.sleep(1.0)


def drop_shadow(rgba):
    arr = np.array(rgba).astype(np.float32)
    alpha = arr[..., 3] / 255.0
    rgb = arr[..., :3] / 255.0
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    soft = (alpha < 0.85) & (sat < 0.18) & (mx < 0.75)
    alpha = np.where(soft, 0.0, alpha)
    solid = alpha > 0.5
    lab, n = ndi.label(solid)
    if n > 1:
        sizes = ndi.sum(solid, lab, range(1, n + 1))
        keep = 1 + int(np.argmax(sizes))
        near = ndi.binary_dilation(lab == keep, iterations=3)
        alpha = np.where(near, alpha, 0.0)
    arr[..., 3] = alpha * 255.0
    return Image.fromarray(arr.astype(np.uint8), 'RGBA')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', required=True)
    ap.add_argument('--colour', default='cream beige')
    ap.add_argument('--seed', type=int, default=5000)
    args = ap.parse_args()
    os.makedirs(CUT_DIR, exist_ok=True)
    session = new_session('isnet-general-use')
    cuts = []
    for i, style in enumerate(STYLES):
        prompt = 'a cute %s %s, %s%s' % (args.colour, args.subject, style, COMMON)
        payload = {'prompt': graph(prompt, args.seed + i * 13), 'client_id': str(uuid.uuid4())}
        pid = post('/prompt', payload)['prompt_id']
        t0 = time.time()
        entry = wait_for(pid)
        out = entry['outputs']['15']['images'][0]
        produced = os.path.join(COMFY_OUTPUT, out.get('subfolder', ''), out['filename'])
        raw = os.path.join(OUT_DIR, '%s_px%02d.png' % (args.subject, i + 1))
        shutil.copy2(produced, raw)
        cut = remove(Image.open(raw).convert('RGB'), session=session, alpha_matting=True, alpha_matting_foreground_threshold=235, alpha_matting_background_threshold=15, alpha_matting_erode_size=8)
        cut = drop_shadow(cut.convert('RGBA'))
        cut = cut.crop(cut.getchannel('A').getbbox())
        cp = os.path.join(CUT_DIR, '%s_px%02d_cut.png' % (args.subject, i + 1))
        cut.save(cp, optimize=True)
        cuts.append(cp)
        print('%02d done (%.0fs): %s' % (i + 1, time.time() - t0, style[:60]), flush=True)
    h = 360
    ims = [Image.open(p).convert('RGBA') for p in cuts]
    ims = [im.resize((int(im.width * h / im.height), h), Image.LANCZOS) for im in ims]
    cols = 5
    cell_w = max(im.width for im in ims) + 30
    sheet = Image.new('RGBA', (cell_w * cols + 30, (h + 70) * 2), (255, 246, 234, 255))
    for i, im in enumerate(ims):
        x = 30 + (i % cols) * cell_w + (cell_w - 30 - im.width) // 2
        y = 30 + (i // cols) * (h + 70)
        sheet.alpha_composite(im, (x, y))
    sheet.convert('RGB').save(os.path.join(OUT_DIR, '_sheet6_%s.png' % args.subject))
    print('SHEET_DONE', flush=True)


if __name__ == '__main__':
    main()
