"""Paid image API redraw, keeps the original size anchor.
Usage: python scripts/api_redraw.py --src input_original/lang_0000.png --style 1 [--quality medium]
Key is read from ../IMAGE_API_KEY (never printed). Output: output_api/<name>_s<style>.png (same pixel size as source)
"""
import argparse, base64, io, os, sys, requests
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://cf.api.fan'
MODEL = 'gpt-image-2.5-flare'
KEY = open(os.path.join(os.path.dirname(ROOT), 'IMAGE_API_KEY'), encoding='utf-8').read().strip()

COMMON = ("Redraw this exact game sprite as a polished children's mobile game asset. Keep the SAME subject, pose, "
   "proportions, silhouette and viewing angle, and keep it filling the same area of the frame. Plain solid white "
          "background, no scenery, no ground shadow, no text. Child friendly, calm, clean readable shape. Style: ")
STYLES = {
 1: "soft cartoon, simple rounded shapes, thin darker-tone outline instead of black, gentle pastel colors, subtle flat shading",
 2: "children's book gouache illustration, soft brush texture, warm pastel palette, no outline",
 3: "2.5D modern cartoon, slight 3D volume, soft glossy highlights, clean rim light, smooth gradients, thin colored outline",
 4: "flat vector sticker style, thick clean white border, bold flat colors, minimal shading",
 5: "clay / plasticine 3D render look, soft studio light, rounded chunky forms, pastel colors",
}

NEWTPL = ("Use this image ONLY as a guide for canvas placement, size, running side-view pose direction and overall framing. "
 "Draw a COMPLETELY DIFFERENT, new character instead (do not copy the original dog's face, ears, colors or markings): {subject}. "
 "Same mid-stride running pose, same size and position in frame, whole body visible. Plain solid white background, no scenery, no ground shadow, no text, no collar or accessories. Child friendly, cute, clean readable shape. Style: ")

RECOLOR = ("Redraw this exact same puppy with IDENTICAL shape, face, ears, pose, outline, size and position, changing ONLY the fur color to: {subject}. Keep eyes, nose, tongue and shading style the same. Plain solid flat BGCOLOR background, no text. Style: ")

def canvas_for(w, h):
    r = w / h
    return (1536, 1024) if r > 1.2 else (1024, 1536) if r < 0.83 else (1024, 1024)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True); ap.add_argument('--style', type=int, required=True)
    ap.add_argument('--quality', default='medium'); ap.add_argument('--subject', default=''); ap.add_argument('--tag', default=''); ap.add_argument('--recolor', action='store_true'); ap.add_argument('--bg', default='white')
    a = ap.parse_args()
    src = Image.open(os.path.join(ROOT, a.src)).convert('RGBA')
    w, h = src.size
    cw, ch = canvas_for(w, h)
    k = min(cw * 0.8 / w, ch * 0.8 / h)          # same margin for every asset
    nw, nh = round(w * k), round(h * k)
    x0, y0 = (cw - nw) // 2, (ch - nh) // 2
    canvas = Image.new('RGB', (cw, ch), 'white' if a.bg=='white' else 'magenta')
    big = src.resize((nw, nh), Image.LANCZOS)
    canvas.paste(big, (x0, y0), big)
    buf = io.BytesIO(); canvas.save(buf, 'PNG'); buf.seek(0)
    r = requests.post(BASE + '/v1/images/edits', headers={'Authorization': 'Bearer ' + KEY},
        files={'image': ('in.png', buf, 'image/png')},
        data={'model': MODEL, 'prompt': ((RECOLOR if a.recolor else NEWTPL).format(subject=a.subject).replace('BGCOLOR', a.bg) if a.subject else COMMON) + STYLES[a.style], 'size': f'{cw}x{ch}', 'quality': a.quality, 'n': '1'}, timeout=300)
    if r.status_code != 200:
        print('HTTP', r.status_code, r.text[:500]); sys.exit(1)
    d = r.json()['data'][0]
    raw = base64.b64decode(d['b64_json']) if d.get('b64_json') else requests.get(d['url']).content
    out = Image.open(io.BytesIO(raw)).convert('RGB').resize((cw, ch), Image.LANCZOS)
    name = os.path.splitext(os.path.basename(a.src))[0]
    od = os.path.join(ROOT, 'output_api'); os.makedirs(od, exist_ok=True)
    out.save(os.path.join(od, f'{name}{a.tag}_s{a.style}_big.png'))         # full-res for viewing
    out.crop((x0, y0, x0 + nw, y0 + nh)).resize((w, h), Image.LANCZOS).save(os.path.join(od, f'{name}{a.tag}_s{a.style}.png'))
    print('ok', name, a.style, (w, h))
main()
