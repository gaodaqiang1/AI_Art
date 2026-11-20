"""
Batch image-to-image through a running ComfyUI (http://127.0.0.1:8188).
Usage: venv/Scripts/python.exe scripts/run_batch.py [--only lang_0000.png] [--denoise 0.65] [--tag v3]
Reads input_original/*.png, writes output_25d/<name>_<tag>.png. Nothing in the game project is touched.
"""
import argparse
import json
import os
import shutil
import time
import urllib.request
import uuid
from PIL import Image
from postprocess import finish, same_geometry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = 'http://127.0.0.1:8188'
INPUT_DIR = os.path.join(ROOT, 'input_original')
OUTPUT_DIR = os.path.join(ROOT, 'output_25d')
COMFY_INPUT = os.path.join(ROOT, 'ComfyUI', 'input')
COMFY_OUTPUT = os.path.join(ROOT, 'ComfyUI', 'output')
SIZE = 1024

PROMPT = 'soft pastel plush toy, cute simple 3D cartoon, smooth rounded shapes, very soft studio lighting, gentle shading, matte fabric surface, calm and friendly, child friendly, no outlines, solid plain white background, mobile game asset'
NEGATIVE = 'text, watermark, logo, extra objects, extra limbs, deformed, blurry, noisy texture, pattern, harsh shadows, high contrast, glossy, shiny, specular highlight, oversaturated, dark background, realistic photo, black outline, sketch, 2d'


def post(path, payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(COMFY + path, data=data, headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


def get(path):
    return json.load(urllib.request.urlopen(COMFY + path))


def node(class_type, **inputs):
    return {'class_type': class_type, 'inputs': inputs}


def add_style(g, style_name):
    g['9'] = node('LoadImage', image=style_name)
    g['10'] = node('IPAdapterUnifiedLoader', model=['1', 0], preset='PLUS (high strength)')
    g['11'] = node('IPAdapterAdvanced', model=['10', 0], ipadapter=['10', 1], image=['9', 0], weight=0.7, weight_type='style transfer', combine_embeds='concat', start_at=0.0, end_at=1.0, embeds_scaling='V only')


def build_graph(image_name, denoise, seed, style_name, ctrl_strength):
    g = {}
    g['1'] = node('CheckpointLoaderSimple', ckpt_name='sd_xl_base_1.0.safetensors')
    g['2'] = node('LoadImage', image=image_name)
    g['3'] = node('ImageScale', image=['2', 0], upscale_method='lanczos', width=SIZE, height=SIZE, crop='disabled')
    g['4'] = node('CLIPTextEncode', text=PROMPT, clip=['1', 1])
    g['5'] = node('CLIPTextEncode', text=NEGATIVE, clip=['1', 1])
    g['6'] = node('LineArtPreprocessor', image=['3', 0], coarse='disable', resolution=SIZE)
    g['7'] = node('ControlNetLoader', control_net_name='controlnet-union-sdxl-promax.safetensors')
    g['8'] = node('ControlNetApplyAdvanced', positive=['4', 0], negative=['5', 0], control_net=['7', 0], image=['6', 0], strength=ctrl_strength, start_percent=0.0, end_percent=0.8, vae=['1', 2])
    model_ref = ['1', 0]
    if style_name:
        add_style(g, style_name)
        model_ref = ['11', 0]
    g['12'] = node('VAEEncode', pixels=['3', 0], vae=['1', 2])
    g['13'] = node('KSampler', model=model_ref, seed=seed, steps=28, cfg=6.5, sampler_name='dpmpp_2m', scheduler='karras', positive=['8', 0], negative=['8', 1], latent_image=['12', 0], denoise=denoise)
    g['14'] = node('VAEDecode', samples=['13', 0], vae=['1', 2])
    g['15'] = node('SaveImage', images=['14', 0], filename_prefix='batch')
    return g


def pad_to_square(src_path, dst_path):
    im = Image.open(src_path).convert('RGBA')
    scale = (SIZE * 0.86) / max(im.size)
    nw = int(im.width * scale)
    nh = int(im.height * scale)
    small = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (SIZE, SIZE), (255, 255, 255, 255))
    x = (SIZE - nw) // 2
    y = (SIZE - nh) // 2
    canvas.alpha_composite(small, (x, y))
    canvas.convert('RGB').save(dst_path)
    return (x, y, x + nw, y + nh)


def wait_for(pid):
    while True:
        hist = get('/history/' + pid)
        if pid in hist:
            return hist[pid]
        time.sleep(1.0)


def run_one(src_path, denoise, seed, style_path, ctrl_strength):
    name = os.path.basename(src_path)
    os.makedirs(COMFY_INPUT, exist_ok=True)
    padded = 'pad_' + name
    box = pad_to_square(src_path, os.path.join(COMFY_INPUT, padded))
    style_name = None
    if style_path:
        style_name = 'style_' + os.path.basename(style_path)
        shutil.copy2(style_path, os.path.join(COMFY_INPUT, style_name))
    graph = build_graph(padded, denoise, seed, style_name, ctrl_strength)
    pid = post('/prompt', {'prompt': graph, 'client_id': str(uuid.uuid4())})['prompt_id']
    t0 = time.time()
    entry = wait_for(pid)
    status = entry.get('status', dict())
    if status.get('status_str') == 'error':
        raise RuntimeError(json.dumps(status)[:600])
    out = entry['outputs']['15']['images'][0]
    produced = os.path.join(COMFY_OUTPUT, out.get('subfolder', ''), out['filename'])
    return produced, time.time() - t0, box


def process(f, args):
    try:
        produced, secs, box = run_one(os.path.join(INPUT_DIR, f), args.denoise, args.seed, args.style, args.control)
    except Exception as e:
        print('FAILED', f, str(e)[:400], flush=True)
        return
    dst = os.path.join(OUTPUT_DIR, f.replace('.png', '_%s.png' % args.tag))
    raw = os.path.join(OUTPUT_DIR, '_raw_' + os.path.basename(dst))
    shutil.copy2(produced, raw)
    finish(os.path.join(INPUT_DIR, f), raw, dst, box)
    print('%s -> %s  (%.0f s)  %s' % (f, os.path.basename(dst), secs, same_geometry(os.path.join(INPUT_DIR, f), dst)), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--denoise', type=float, default=0.65)
    ap.add_argument('--control', type=float, default=0.9)
    ap.add_argument('--seed', type=int, default=12345)
    ap.add_argument('--style', default='')
    ap.add_argument('--tag', default='v3')
    args = ap.parse_args()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = sorted(f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.png'))
    if args.only:
        files = [f for f in files if f == args.only]
    for f in files:
        process(f, args)


if __name__ == '__main__':
    main()
