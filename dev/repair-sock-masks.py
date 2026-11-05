#!/usr/bin/env python3
"""Rebuild the 17 failed worn sock mattes from their registered green painting.

Like the good baked masks (9392063f), RGB is source luminance and alpha is
sock coverage. No source pixels are moved or repainted. Small green differences
at the painted boundary provide the soft matte; neutral hardware and warm skin
are excluded. Baseline is pinned so rebuilding is idempotent.
"""
import io
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
BASELINE = 'f376f42b'
NAMES = [f'{heel}_{variant}' for heel in ['stiletto6', 'slingback', 'pearlpump',
    'bowsling', 'crystalpump', 'studpump', 'bowmule', 'luciteheel']
    for variant in ['lace', 'frill']] + ['kitten_frill']
OUT = ROOT / 'dev/qa-out/sock-repair'


def original(path):
    return Image.open(io.BytesIO(subprocess.check_output(
        ['git', 'show', f'{BASELINE}:{path}'], cwd=ROOT))).convert('RGBA')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in NAMES:
        path = f'assets/worn/{name}_sock.webp'
        dye_path = f'assets/worn/{name}_mask.webp'
        sprite = Image.open(ROOT / f'assets/worn/{name}.webp').convert('RGBA')
        before, dye = original(path), original(dye_path)
        after = before.copy()
        assert sprite.size == before.size == dye.size
        # Keep the two sock bodies and their nearby lace/cuff antialiasing.
        # Isolated green codec reflections on transparent heels are not yarn.
        source_pixels = list(sprite.getdata())
        pending = {i for i, (r, g, b, a) in enumerate(source_pixels)
                   if a and min(g-r, g-b) > 2}
        core = Image.new('L', sprite.size)
        keep = []
        w = sprite.width
        while pending:
            first = pending.pop()
            component, stack = [first], [first]
            while stack:
                i = stack.pop()
                for j in (i-w, i+w, i-1 if i % w else -1,
                          i+1 if i % w != w-1 else -1):
                    if j in pending:
                        pending.remove(j)
                        component.append(j)
                        stack.append(j)
            if len(component) >= 150:
                keep.extend(component)
        core_pixels = bytearray(sprite.width*sprite.height)
        for i in keep:
            core_pixels[i] = 255
        core.frombytes(bytes(core_pixels))
        nearby = list(core.filter(ImageFilter.MaxFilter(7)).getdata())
        pixels, dyes, changed = [], [], 0
        for i, ((r, g, b, a), old, shoe) in enumerate(zip(source_pixels, before.getdata(), dye.getdata())):
            # Painted yarn is green; skin, ivory satin and hardware are not.
            # A narrow colour transition retains the authored antialias edge.
            coverage = max(0., min(1., (min(g-r, g-b)-2)/8)) if a and nearby[i] else 0
            if coverage:
                shade = round(.299*r + .587*g + .114*b)
                pixels.append((shade, shade, shade, round(a*coverage)))
                alpha = round(shoe[3]*(1-coverage))
                dyes.append((*shoe[:3], alpha))
                changed += alpha != shoe[3]
            else:
                pixels.append(old)
                dyes.append(shoe)
        after.putdata(pixels)
        after.save(ROOT/path, lossless=True, exact=True)
        dye.putdata(dyes)
        if changed:
            dye.save(ROOT/dye_path, lossless=True, exact=True)
        # Round-trip format and every protected mask pixel must be exact.
        assert Image.open(ROOT/path).convert('RGBA').tobytes() == after.tobytes()
        assert Image.open(ROOT/dye_path).convert('RGBA').tobytes() == dye.tobytes()
        count = lambda im: sum(a >= 128 for a in im.getchannel('A').getdata())
        row = {'file': name+'_sock.webp', 'before': count(before), 'after': count(after),
               'shoe_mask_pixels_changed': changed, 'size': list(sprite.size)}
        assert row['after'] > 30000, row
        rows.append(row)
    (OUT/'pixels.json').write_text(json.dumps({'baseline': BASELINE, 'files': rows}, indent=2)+'\n')
    print('| Mask | Before alpha >=128 | After alpha >=128 |')
    print('|---|---:|---:|')
    for row in rows:
        print(f"| {row['file']} | {row['before']} | {row['after']} |")


if __name__ == '__main__':
    main()
