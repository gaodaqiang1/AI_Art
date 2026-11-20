import json

L = json.load(open('I:/GODOT/AI_Art/output_api/lang_layout.json'))


def cw(o, s):
    b = L['%d_%d_0' % (o, s)]['content']
    return b[2] - b[0], b[3] - b[1]


def show(o):
    w0, h0 = cw(o, 0)
    r = [(round(cw(o, s)[0] / w0, 3), round(cw(o, s)[1] / h0, 3)) for s in (1, 2)]
    c = [L['%d_%d_0' % (o, s)]['canvas'] for s in range(3)]
    print(o, 'content s0', (w0, h0), 'ratio s1,s2', r, 'canvas', c)


[show(o) for o in range(10)]
