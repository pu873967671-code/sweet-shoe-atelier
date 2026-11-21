#!/usr/bin/env python3
"""Pass 1 restyle: move the UI palette from mint/green to lilac, blush and plum.

Rewrites literal colours in style.css and index.html only (never game data or
shoe/sock colours in JS). Greens and teals (hue 95-205) are remapped by
lightness, keeping alpha and relative lightness so contrast is preserved:
  L >= .90   -> pearl lilac  (hue 262, low saturation)   page and card washes
  .62-.90    -> lilac        (hue 258)                   borders, chips, tracks
  < .62      -> plum ink     (hue 322, muted)            text, icons, dark fills
Run once on the pre-restyle files; it is idempotent on already-remapped files
because nothing it writes is green.  usage: python3 dev/restyle-palette.py
"""
import colorsys, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r'#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b')
RGB = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+%?)\s*)?\)')


def remap(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    deg = h * 360
    if not (95 <= deg <= 205) or s < .06:
        return None
    if l >= .9:
        h2, s2 = 262 / 360, min(.55, s * .8)
    elif l >= .62:
        h2, s2 = 258 / 360, min(.5, s * .75)
    else:
        h2, s2 = 322 / 360, min(.24, s * .55)
        l = l * .96
    r2, g2, b2 = colorsys.hls_to_rgb(h2, l, s2)
    return round(r2 * 255), round(g2 * 255), round(b2 * 255)


def sub_hex(m):
    v = m.group(1)
    if len(v) in (3, 4):
        v = ''.join(c * 2 for c in v)
    r, g, b = int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)
    new = remap(r, g, b)
    if not new:
        return m.group(0)
    return '#%02x%02x%02x' % new + (v[6:8] if len(v) == 8 else '')


def sub_rgb(m):
    r, g, b, a = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
    new = remap(r, g, b)
    if not new:
        return m.group(0)
    return f'rgba({new[0]},{new[1]},{new[2]},{a})' if a is not None else f'rgb({new[0]},{new[1]},{new[2]})'


def main():
    for rel in ['style.css', 'index.html']:
        path = ROOT / rel
        text = path.read_text()
        out = RGB.sub(sub_rgb, HEX.sub(sub_hex, text))
        changed = sum(1 for a, b in zip(HEX.findall(text), HEX.findall(out)) if a.lower() != b.lower())
        path.write_text(out)
        print(f'{rel}: {changed} colours remapped')


if __name__ == '__main__':
    sys.exit(main())
