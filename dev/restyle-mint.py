#!/usr/bin/env python3
"""Mint pass: move the UI from blush/rose/plum/lilac to a fresh mint palette.

Rewrites literal colours in the theme stylesheets and the textile SVGs (never
game data, shoe colours or sock colours, which live in JS). Lightness is kept,
so contrast relationships survive:
  pink / rose / red (hue 300-360, 0-25)  -> mint (hue 156); darks -> deep green ink
  lilac / violet (hue 235-300)           -> aqua mint (hue 172)
Gold, neutrals and greys are left alone. Idempotent: nothing it writes is pink.
usage: python3 dev/restyle-mint.py
"""
import colorsys, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['layout.css', 'textile.css', 'atelier.css', 'dev/build-textiles.py',
         *[f'assets/ui/textile/{n}' for n in ('lace-trim.svg', 'bow.svg', 'rosette.svg', 'tulle.svg', 'tulle-fine.svg')]]
HEX = re.compile(r'#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b')
RGB = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+%?)\s*)?\)')


def remap(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    deg = h * 360
    if s < .07:
        return None
    if deg >= 300 or deg <= 25:
        if l < .45:                       # plum ink and deep rose -> deep green ink
            h2, s2, l2 = 164 / 360, min(.32, s * .9), l * .95
        elif l >= .9:                     # blush washes -> mint washes
            h2, s2, l2 = 156 / 360, min(.6, s * .85), l
        else:                             # rose accents -> mint accents, a touch deeper
            h2, s2, l2 = 156 / 360, min(.5, s * .8), l * .9
    elif 235 <= deg < 300:
        if l < .45:
            h2, s2, l2 = 168 / 360, min(.3, s * .8), l
        else:
            h2, s2, l2 = 172 / 360, min(.5, s * .75), l
    else:
        return None
    r2, g2, b2 = colorsys.hls_to_rgb(h2, l2, s2)
    return round(r2 * 255), round(g2 * 255), round(b2 * 255)


def sub_hex(m):
    v = m.group(1)
    if len(v) in (3, 4):
        v = ''.join(c * 2 for c in v)
    new = remap(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    if not new:
        return m.group(0)
    return '#%02x%02x%02x' % new + (v[6:8] if len(v) == 8 else '')


def sub_rgb(m):
    new = remap(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if not new:
        return m.group(0)
    a = m.group(4)
    return f'rgba({new[0]},{new[1]},{new[2]},{a})' if a is not None else f'rgb({new[0]},{new[1]},{new[2]})'


for rel in FILES:
    path = ROOT / rel
    text = path.read_text()
    out = RGB.sub(sub_rgb, HEX.sub(sub_hex, text))
    n = sum(1 for a, b in zip(HEX.findall(text), HEX.findall(out)) if a.lower() != b.lower())
    path.write_text(out)
    print(f'{rel}: {n} colours remapped')
