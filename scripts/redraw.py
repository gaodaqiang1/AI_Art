"""
Redraw a picture as a 2.5D cartoon (free shape), keeping the colour that the game question depends on.
Usage: venv/Scripts/python.exe scripts/redraw.py --src lang_0030.png --subject puppy --colour blue --tag r1
The result is fitted onto a canvas of the ORIGINAL size (transparent background); the dominant colour is measured
and the picture is rejected and redrawn with a new seed when it is not clearly the requested colour.
"""
import argparse
import colorsys
import json
import os
import shutil
import time
import urllib.request
import uuid
import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = 'http://127.0.0.1:8188'
INPUT_DIR = os.path.join(ROOT, 'input_original')
OUTPUT_DIR = os.path.join(ROOT, 'output_25d')
COMFY_INPUT = os.path.join(ROOT, 'ComfyUI', 'input')
COMFY_OUTPUT = os.path.join(ROOT, 'ComfyUI', 'output')
SIZE = 1024

# colour name -> ((hue from, hue to) in degrees, minimum saturation, minimum share of the body that must be in range)
COLOURS = {'red': ((345, 15), 0.45, 0.55), 'orange': ((16, 40), 0.55, 0.55), 'green': ((90, 160), 0.35, 0.55), 'blue': ((195, 250), 0.35, 0.55), 'brown': ((15, 40), 0.15, 0.40)}
WORDS = {'red': 'bright red', 'orange': 'bright orange', 'green': 'bright green', 'blue': 'bright blue', 'brown': 'warm brown'}


def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(COMFY + path, data=data, headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


def get(path):
    return json.load(urllib.request.urlopen(COMFY + path))


def node(class_type, **inputs):
    return {'class_type': class_type, 'inputs': inputs}


def build_graph(image_name, prompt, negative, denoise, seed):
    g = {}
    g['1'] = node('CheckpointLoaderSimple', ckpt_name='sd_xl_base_1.0.safetensors')
    g['2'] = node('LoadImage', image=image_name)
    g['4'] = node('CLIPTextEncode', text=prompt, clip=['1', 1])
    g['5'] = node('CLIPTextEncode', text=negative, clip=['1', 1])
    g['12'] = node('VAEEncode', pixels=['2', 0], vae=['1', 2])
    g['13'] = node('KSampler', model=['1', 0], seed=seed, steps=30, cfg=7.0, sampler_name='dpmpp_2m', scheduler='karras', positive=['4', 0], negative=['5', 0], latent_image=['12', 0], denoise=denoise)
    g['14'] = node('VAEDecode', samples=['13', 0], vae=['1', 2])
    g['15'] = node('SaveImage', images=['14', 0], filename_prefix='redraw')
    return g


def hue_share(rgb, mask, colour):
    hue_range, smin, need = COLOURS[colour]
    h0, h1 = hue_range
    pix = rgb[mask]
    if len(pix) == 0:
        return 0.0, need
    hsv = np.array([colorsys.rgb_to_hsv(p[0], p[1], p[2]) for p in pix[::7]])
    hue = hsv[:, 0] * 360.0
    sat = hsv[:, 1]
    val = hsv[:, 2]
    colourful = (sat >= smin) & (val >= 0.25)
    if h0 <= h1:
        in_range = (hue >= h0) & (hue <= h1)
    else:
        in_range = (hue >= h0) | (hue <= h1)
    share = float((in_range & colourful).sum()) / max(1, len(hue))
    return share, need


def fit_to_canvas(img_rgba, size):
    W, H = size
    bbox = img_rgba.getchannel('A').getbbox()
    obj = img_rgba.crop(bbox)
    scale = min(W * 0.96 / obj.width, H * 0.96 / obj.height)
    obj = obj.resize((max(1, int(obj.width * scale)), max(1, int(obj.height * scale))), Image.LANCZOS)
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(obj, ((W - obj.width) // 2, H - obj.height - int(H * 0.02)))
    return canvas


def cut_out(rgb_img):
    # the picture sits on a plain white background: everything that is not that white is the object
    arr = np.array(rgb_img.convert('RGB')).astype(np.float32) / 255.0
    dist = np.sqrt(((arr - 1.0) ** 2).sum(axis=2))
    alpha = np.clip((dist - 0.08) / 0.12, 0.0, 1.0)
    a_img = Image.fromarray((alpha * 255).astype(np.uint8), 'L').filter(ImageFilter.MedianFilter(5))
    rgba = rgb_img.convert('RGBA')
    rgba.putalpha(a_img)
    return rgba, np.array(a_img) > 128


def wait_for(pid):
    while True:
        hist = get('/history/' + pid)
        if pid in hist:
            return hist[pid]
        time.sleep(1.0)


def generate(padded, prompt, negative, denoise, seed):
    payload = {'prompt': build_graph(padded, prompt, negative, denoise, seed), 'client_id': str(uuid.uuid4())}
    pid = post('/prompt', payload)['prompt_id']
    entry = wait_for(pid)
    status = entry.get('status', dict())
    if status.get('status_str') == 'error':
        raise RuntimeError(json.dumps(status)[:600])
    out = entry['outputs']['15']['images'][0]
    return os.path.join(COMFY_OUTPUT, out.get('subfolder', ''), out['filename'])


def pad_to_square(src_path, dst_path):
    im = Image.open(src_path).convert('RGBA')
    scale = (SIZE * 0.86) / max(im.size)
    small = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255))
    canvas.alpha_composite(small, ((SIZE - small.width) // 2, (SIZE - small.height) // 2))
    canvas.convert('RGB').save(dst_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--subject', required=True)
    ap.add_argument('--colour', required=True, choices=sorted(COLOURS))
    ap.add_argument('--denoise', type=float, default=0.82)
    ap.add_argument('--tag', default='r1')
    ap.add_argument('--tries', type=int, default=6)
    args = ap.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    src = os.path.join(INPUT_DIR, args.src)
    orig = Image.open(src).convert('RGBA')
    padded = 'pad_' + args.src
    pad_to_square(src, os.path.join(COMFY_INPUT, padded))
    word = WORDS[args.colour]
    prompt = 'a cute %s %s, entirely %s colored body, simple friendly cartoon character, soft rounded 3D plush toy look, smooth soft shading, matte, gentle studio lighting, calm child friendly, solid plain white background, centered, full body, mobile game asset' % (word, args.subject, word)
    negative = 'text, watermark, extra limbs, deformed, noisy texture, pattern, spots, harsh shadows, high contrast, glossy, black outline, dark background, realistic photo, multicolored, two colors, other colors'
    best = None
    for k in range(args.tries):
        seed = 1000 + k * 77
        t0 = time.time()
        produced = generate(padded, prompt, negative, args.denoise, seed)
        raw = os.path.join(OUTPUT_DIR, '_raw_%s_%s_s%d.png' % (args.src[:-4], args.tag, seed))
        shutil.copy2(produced, raw)
        rgba, mask = cut_out(Image.open(raw))
        rgb = np.array(rgba.convert('RGB')).astype(np.float32) / 255.0
        share, need = hue_share(rgb, mask, args.colour)
        print('try %d seed %d: %s share %.2f (need >= %.2f)  %.0fs' % (k + 1, seed, args.colour, share, need, time.time() - t0), flush=True)
        if best is None or share > best[0]:
            best = (share, rgba)
        if share >= need:
            break
    share, rgba = best
    final = fit_to_canvas(rgba, orig.size)
    dst = os.path.join(OUTPUT_DIR, args.src.replace('.png', '_%s.png' % args.tag))
    final.save(dst, optimize=True)
    print('SAVED', os.path.basename(dst), final.size, 'colour share %.2f' % share, 'original size', orig.size, flush=True)


if __name__ == '__main__':
    main()
