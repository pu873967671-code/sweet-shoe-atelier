#!/usr/bin/env python3
"""Build hosiery light fields for all twenty paintings from registered leg masks; never edit source art.

R: normalized horizontal distance to each leg silhouette (edge=255).
G: left/front-lit sheen following independently traced front/rear centrelines.
B: soft toe/heel reinforcement, confined to the exposed foot at the shoe mouth.
Only Pillow is needed. Run --verify to check byte-exact reproducibility.
"""
import argparse
import io
import math
from pathlib import Path
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
import json
LANDMARKS = json.loads((ROOT / 'dev/hose-landmarks.json').read_text())
BASES = tuple(base for base in LANDMARKS if not base.startswith('_'))


def smooth(values, radius=8):
    # A short weighted convolution avoids quantizing the mask centreline.
    weights = [(d, math.exp(-d*d/(2*radius*radius))) for d in range(-3*radius, 3*radius+1)]
    return [sum(values[min(len(values)-1, max(0, y+d))]*k for d, k in weights)/sum(k for _, k in weights)
            for y in range(len(values))]


def build(base):
    mask = Image.open(ROOT / f'assets/worn/{base}_legs.webp').convert('RGBA')
    w, h = mask.size
    px = mask.load()
    out = Image.new('RGBA', mask.size)
    dst = out.load()
    for front in (False, True):
        rows = []
        for y in range(h):
            xs = [x for x in range(w) if px[x, y][3] >= 128 and (px[x, y][0] >= 207) == front]
            rows.append((min(xs), max(xs)) if xs else None)
        valid = [y for y, row in enumerate(rows) if row]
        first, last = valid[0], valid[-1]
        # Extend over occluded rows only for tracing; never paint outside the mask.
        filled, previous = [], rows[first]
        for row in rows:
            previous = row or previous
            filled.append(previous)
        centres = smooth([(lo+hi)/2 for lo, hi in filled])
        widths = smooth([max(4, hi-lo) for lo, hi in filled])
        for y in valid:
            lo, hi = rows[y]
            half = max(2, (hi-lo)/2)
            centre = (lo+hi)/2
            cy, width = centres[y], widths[y]
            foot_y = last - h*.045
            for x in range(lo, hi+1):
                r, g, b, a = px[x, y]
                if a == 0 or (r >= 207) != front:
                    continue
                edge = min(1, abs(x-centre)/half)**1.65
                # Slightly left of centre matches the original painted light.
                band = math.exp(-((x-(cy-width*.10))/(width*.24))**2)
                shin = .68*math.exp(-((y-h*.43)/(h*.34))**4)
                knee = .25*math.exp(-((y-LANDMARKS[base]['knee'][int(front)]+25)/(h*.075))**2)
                instep = .30*math.exp(-((y-(last-h*.075))/(h*.045))**2)
                sheen = min(1, band*(shin+knee+instep))
                foot = math.exp(-((y-foot_y)/(h*.052))**2)
                # The shoes point left: distal toe on left, heel on right.
                across = (x-lo)/max(1, hi-lo)
                reinforce = foot*max(.85*math.exp(-((across-.13)/.23)**2),
                                     .65*math.exp(-((across-.88)/.21)**2))
                dst[x, y] = (round(255*edge), round(255*sheen), round(255*reinforce), a)
    # The mask's exact alpha/registration is retained; filtering RGB alone avoids halos.
    channels = out.split()
    out = Image.merge('RGBA', (channels[0], channels[1].filter(ImageFilter.GaussianBlur(1.2)),
                               channels[2].filter(ImageFilter.GaussianBlur(1.2)), mask.getchannel('A')))
    stream = io.BytesIO()
    out.save(stream, 'WEBP', lossless=True, exact=True, method=6)
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    for base in BASES:
        path = ROOT / f'assets/worn/{base}_hose.webp'
        data = build(base)
        if args.verify:
            assert path.read_bytes() == data, f'{base}: map differs from rebuild'
        else:
            path.write_bytes(data)
        print(f'{base}: {len(data)} bytes; {"verified" if args.verify else "built"}')


if __name__ == '__main__':
    main()
