"""
Free text-to-image: make several different cartoon styles of one subject so you can pick a style.
Usage: venv/Scripts/python.exe scripts/styles.py --subject puppy --tag s
Writes output_25d/styles/<subject>_<n>.png (1024, white background) and a contact sheet.
"""
import argparse
import json
import os
import shutil
import time
import urllib.request
import uuid
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMFY = 'http://127.0.0.1:8188'
OUT_DIR = os.path.join(ROOT, 'output_25d', 'styles')
COMFY_OUTPUT = os.path.join(ROOT, 'ComfyUI', 'output')

COMMON = ", running, side view, whole body visible with all four legs and the tail clearly visible, mid-stride dynamic pose, plain solid white background with no scenery and no paper texture, centered, single character, child friendly, calm, no accessories, no collar, no clothes, no text, mobile game asset"
STYLES = ['children book hand drawn illustration, soft crayon texture, simple rounded shapes, clean clear edges, gentle pastel colors', 'colored pencil drawing, soft shading, simple cute cartoon, clean outline, gentle pastel colors', 'gouache painting, flat soft brush strokes, simple shapes, clean edges, warm pastel colors', 'hand drawn cartoon with soft thick marker lines and flat pastel coloring, very simple, clean clear edges', 'soft pastel chalk drawing, smooth blended shading, simple rounded cute shapes, clean clear silhouette']
NEGATIVE = 'text, watermark, logo, extra limbs, deformed, noisy, harsh shadows, high contrast, dark background, realistic photo, scary, multiple characters, black outline, sitting, standing still, front view, facing camera, collar, bandana, scarf, bell, pendant, clothes, accessories, ground shadow, floor, cropped, partial body'


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
    g['15'] = node('SaveImage', images=['14', 0], filename_prefix='style')
    return g


def wait_for(pid):
    while True:
        hist = get('/history/' + pid)
        if pid in hist:
            return hist[pid]
        time.sleep(1.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', required=True)
    ap.add_argument('--colour', default='cream beige')
    ap.add_argument('--seed', type=int, default=2024)
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    made = []
    for i, style in enumerate(STYLES):
        prompt = 'a cute %s %s, %s%s' % (args.colour, args.subject, style, COMMON)
        payload = {'prompt': graph(prompt, args.seed + i), 'client_id': str(uuid.uuid4())}
        pid = post('/prompt', payload)['prompt_id']
        t0 = time.time()
        entry = wait_for(pid)
        out = entry['outputs']['15']['images'][0]
        produced = os.path.join(COMFY_OUTPUT, out.get('subfolder', ''), out['filename'])
        dst = os.path.join(OUT_DIR, '%s_hand_%d.png' % (args.subject, i + 1))
        shutil.copy2(produced, dst)
        made.append(dst)
        print('style %d done (%.0fs): %s' % (i + 1, time.time() - t0, style[:50]), flush=True)
    sheet = Image.new('RGB', (512 * len(made), 512), (255, 255, 255))
    for i, p in enumerate(made):
        sheet.paste(Image.open(p).convert('RGB').resize((512, 512), Image.LANCZOS), (i * 512, 0))
    sheet.save(os.path.join(OUT_DIR, '_sheet_%s_hand.png' % args.subject))
    print('SHEET_DONE', flush=True)


if __name__ == '__main__':
    main()
