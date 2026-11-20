from PIL import Image
R = 'I:/GODOT/AI_Art/'
def load(p): return Image.open(R + p).convert('RGB').resize((760, 570))
s = Image.new('RGB', (1540, 1160), 'white')
s.paste(load('bg_work/out/lang_bg_2.png'), (0, 0)); s.paste(load('bg_work/out25/lang_bg_2.png'), (780, 0))
s.paste(load('bg_work/out/bg_star.png'), (0, 590)); s.paste(load('bg_work/out25/bg_star.png'), (780, 590))
s.save(R + 'output_api/_bg25_cmp.png')
