"""prep_{o}{k}.png (o=5..9 furniture, k=0..4 colour) = confirmed lang_final lang_{o}0{k}0.png stretched to the legacy prep size
(legacy did exactly this stretch). Output: AI_Art/bg_work/prep_new/ (never overwrites the game)."""
import os
from PIL import Image
S = 'I:/GODOT/xwn/assets/legacy/images/'
F = 'I:/GODOT/AI_Art/output_api/lang_final/'
OUT = 'I:/GODOT/AI_Art/bg_work/prep_new/'
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(OUT + f)
n = 0
for o in range(5, 10):
    for k in range(5):
        size = Image.open(S + f'prep_{o}{k}.png').size
        src = Image.open(F + f'lang_{o}0{k}0.png').convert('RGBA')
        c = src.crop(src.getchannel('A').point(lambda v: 255 if v > 20 else 0).getbbox())
        c.resize(size, Image.LANCZOS).save(OUT + f'prep_{o}{k}.png', optimize=True)
        n += 1
print(n, 'written to', OUT)
