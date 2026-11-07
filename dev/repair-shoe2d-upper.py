#!/usr/bin/env python3
"""Close coverage gaps in the studio/Collection dye mattes (assets/shoe2d/*_upper)
and the fitting-room fallback dye mattes (assets/fitting2d/*_upper).

The product renderer tints <style>_base through <style>_upper. The matte
stopped a pixel or two short of the painted satin along strap edges, the
heel seat and heel tops, so a coloured shoe showed jagged white rims.

Per style, without changing any painting pixel or any other matte:
- neutral satin (spread <= 24, lum >= 105, green - blue <= 8) that touches
  the dye within 4 px (4-connected, through such pixels) and is not owned
  by binding/insole/sole gets dye alpha = 255 - that ownership;
- ornaments painted into the base (brooch crystals, pearls) are excluded:
  thick bright neutral regions outside the dye and their 2 px rim, plus
  sparkle points (bright local maxima).
Alpha is only raised. Baseline is the shipped matte at BASELINE, so reruns
are idempotent.  usage: python3 dev/repair-shoe2d-upper.py [--check]
"""
import importlib.util, io, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / 'assets/shoe2d'
spec = importlib.util.spec_from_file_location('rep', ROOT / 'dev/repair-worn-mask-coverage.py')
rep = importlib.util.module_from_spec(spec); spec.loader.exec_module(rep)
BASELINE = '9a14f27'
REACH = 4


def baseline(name, folder='shoe2d'):
    data = subprocess.check_output(['git', 'show', f'{BASELINE}:assets/{folder}/{name}.webp'], cwd=ROOT)
    return np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')).copy()


def repair(style, folder='shoe2d', painting='base', parts=('binding', 'insole', 'sole')):
    R = ROOT / 'assets' / folder
    P = np.asarray(Image.open(R / f'{style}_{painting}.webp').convert('RGBA')).astype(np.int32)
    U = baseline(f'{style}_upper', folder)
    own = np.zeros(P.shape[:2], np.int32)
    for part in parts:
        own = np.maximum(own, np.asarray(Image.open(R / f'{style}_{part}.webp').convert('RGBA'))[..., 3].astype(np.int32))
    r, g, b, a = (P[..., i] for i in range(4))
    lum = r * .299 + g * .587 + b * .114
    spread = np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))
    neutral = (a > 0) & (spread <= 24) & (lum >= 105) & (g - b <= 8)
    dyed = U[..., 3] >= 128
    thick = rep.thick_parts(neutral & ~dyed & (lum >= 170), 3)
    sparkle = (lum - rep.box_mean(lum, 2) > 45) & (lum > 200) & ~dyed
    ornament = rep.dilate(thick | sparkle, 2)
    allowed = neutral & ~ornament & (own < 255)
    if not parts:
        # The fallback set has no binding matte: pale collar piping and strap
        # edges along the skin stay as painted (10 px band from the legs).
        legs = np.asarray(Image.open(R / f'{style}_legs.webp').convert('RGBA'))[..., 3]
        if legs.shape == allowed.shape:
            allowed &= ~rep.dilate(legs >= 128, 10)
    fill = rep.geodesic(U[..., 3] >= 200, allowed & (U[..., 3] < 255 - own), REACH)
    # partial dye on satin touching solid dye
    fill |= allowed & rep.dilate(U[..., 3] >= 200, 1) & (U[..., 3] < 255 - own)
    want = np.where(fill, 255 - own, 0)
    raise_ = (want > U[..., 3]) & (U[..., 3] < 200)  # gaps only; authored partial dye kept
    U[raise_, 3] = want[raise_]
    U[raise_, 0] = U[raise_, 1] = U[raise_, 2] = 255
    return U, int(raise_.sum())


def main():
    for folder, painting, parts in (('shoe2d', 'base', ('binding', 'insole', 'sole')), ('fitting2d', 'shoe', ())):
        R = ROOT / 'assets' / folder
        for s in sorted(p.name[:-len('_upper.webp')] for p in R.glob('*_upper.webp')):
            U, n = repair(s, folder, painting, parts)
            print(f'{folder}/{s:14s} upper+{n:5d}px')
            if '--check' not in sys.argv:
                Image.fromarray(U, 'RGBA').save(R / f'{s}_upper.webp', lossless=True, quality=100, method=6, exact=True)


if __name__ == '__main__':
    main()
