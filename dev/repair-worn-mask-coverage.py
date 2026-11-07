#!/usr/bin/env python3
"""Close coverage gaps in the worn fitting mattes (assets/worn/*_mask, *_sock).

The fitting room dyes the shoe through `<variant>_mask.webp` and lays socks
through `<variant>_sock.webp`. Both mattes stopped short of the painted
silhouette in places, with stair-stepped edges:

* Undyed white satin was left along the outer silhouette, under the collar
  piping and at the heel counter, so a coloured shoe showed jagged white
  fringes and specks (worst between the two collars and at the front throat).
* In frill/lace variants the green matting key of the painted sock was left
  uncovered at the sock edge, so a pale green/grey fringe showed between the
  sock and the shoe.

Repair, per variant, without changing any painting pixel:

1. Sock matte: green-key pixels within 3 px of solid sock coverage get sock
   alpha proportional to their key strength; RGB is the painting's luminance,
   the same encoding as the existing matte.
2. Dye matte: neutral satin pixels that no matte owns (dye, legs, sole/no-dye,
   sock, clear) and that are connected to the existing dye matte within
   16 px (4-connected, through such pixels only) are added. Alpha is the
   complement of the legs matte, so the shoe/skin seam keeps the leg
   matte's antialiasing. Ornaments (pearls, crystals, studs, hardware) are
   owned by the sole/no-dye matte or are not neutral satin, so they stay
   undyed; lining, piping, skin and soles are warm and are never selected.

Existing matte alpha is only ever raised, never lowered. The original mattes
are the baseline commit's files; rerunning is idempotent.

usage: python3 dev/repair-worn-mask-coverage.py [--check] [variant ...]
"""
import argparse
import io
import json
import subprocess
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORN = ROOT / 'assets/worn'
BASELINE = '9a14f27'
SPRITES = json.loads((WORN / 'worn.json').read_text())['sprites']
REACH = 16
SEAM = 2
SOCK_REACH = 8


def baseline(name):
    """Matte as shipped before this repair (idempotent reruns)."""
    rel = f'assets/worn/{name}.webp'
    try:
        data = subprocess.check_output(['git', 'show', f'{BASELINE}:{rel}'], cwd=ROOT, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        path = WORN / f'{name}.webp'
        return np.asarray(Image.open(path).convert('RGBA')).copy() if path.exists() else None
    return np.asarray(Image.open(io.BytesIO(data)).convert('RGBA')).copy()


def current(name):
    path = WORN / f'{name}.webp'
    return np.asarray(Image.open(path).convert('RGBA')).copy() if path.exists() else None


def aligned(arr, dx, dy, shape):
    out = np.zeros(shape[:2] + (4,), np.uint8)
    if arr is None:
        return out
    h, w = arr.shape[:2]
    H, W = shape[:2]
    ys, xs, ye, xe = max(0, dy), max(0, dx), min(H, dy + h), min(W, dx + w)
    out[ys:ye, xs:xe] = arr[ys - dy:ye - dy, xs - dx:xe - dx]
    return out


def dilate(mask, radius):
    out = mask.copy()
    for _ in range(radius):
        grown = out.copy()
        grown[1:] |= out[:-1]; grown[:-1] |= out[1:]
        grown[:, 1:] |= out[:, :-1]; grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def geodesic(seed, allowed, reach):
    H, W = seed.shape
    dist = np.full((H, W), -1, np.int32)
    queue = deque()
    ys, xs = np.nonzero(seed & dilate(allowed, 1))
    for y, x in zip(ys, xs):
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < H and 0 <= xx < W and allowed[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = 1
                queue.append((yy, xx))
    while queue:
        y, x = queue.popleft()
        d = dist[y, x]
        if d >= reach:
            continue
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < H and 0 <= xx < W and allowed[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = d + 1
                queue.append((yy, xx))
    return dist > 0


def erode(mask, radius):
    return ~dilate(~mask, radius)


def soften_sole(base):
    """Fit the no-dye matte (collar piping, welt, sole, heel) to the painting.

    The shipped matte is binary and overreaches: blobs of shaded satin next to
    the piping and along the welt stayed undyed (grey/white patches on a
    coloured shoe), and its edge was a pixel staircase.

    Away from the collar the separating feature is cream content, green minus
    blue: soles, welts and lining are >= 14, satin (lit or shaded) is <= 9.
    1. Release: no-dye pixels that are neutral satin and connect to the dye
       matte within 10 px through such pixels become dyeable. Pearls, crystals
       and the heel outline do not touch the dye through satin, so they stay.
    2. Antialias: within 2 px of the remaining boundary, alpha ramps with
       cream content from 8 (dyed) to 15 (kept).
    The style's measured collar piping band keeps the authored matte: pale
    piping can be as neutral as satin, so colour must not decide there.
    Skin is excluded via the legs matte.
    """
    sole = baseline(f'{base}_sole')
    dye = baseline(f'{base}_mask')[..., 3]
    painting = np.asarray(Image.open(WORN / f'{base}.webp').convert('RGBA')).astype(np.int32)
    legs = current(f'{base}_legs')[..., 3].astype(np.int32)
    r, g, b, a = (painting[..., i] for i in range(4))
    cream = g - b
    lum = r * .299 + g * .587 + b * .114
    solid = sole[..., 3] >= 128
    satin = solid & (cream <= CREAM_LO + 1) & (r - b <= 26) & (lum >= 150) & (a > 200) & (legs < 128)
    # Collar: the measured piping band of this style (none for unpiped styles).
    collar = piping_zone(painting, legs, dye >= 128, base in SPLIT_BASES, piping_width(base))
    if base in SPLIT_BASES:
        # Strap styles carry small rhinestones along every strap, all near the
        # skin: keep the authored matte within 16 px of the skin there.
        collar = dilate(legs >= 128, COLLAR) & ~(legs >= 128) & (a > 0)
    # Ornaments (pearls, crystals, clear heels) are thick bright neutral parts
    # of the authored matte; their shaded rims stay with them.
    spread = np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))
    core = thick_parts(solid & (spread <= 24) & (lum >= 150), THICK)
    ornament = dilate(core, 3)
    release = geodesic((dye >= 128) & ~solid, satin & ~collar & ~dilate(core, ORNAMENT_MARGIN), RELEASE)
    original = sole[..., 3].copy()
    sole[release, 3] = 0
    solid = sole[..., 3] >= 128
    soft = np.rint(np.clip((cream - CREAM_LO) / (CREAM_HI - CREAM_LO), 0, 1) * 255).astype(np.int32)
    # Inside the boundary the ramp may lower coverage; outside it only raises
    # it. Neither applies in the collar zone (see above).
    inner = solid & ~erode(solid, BAND) & (a > 0) & (legs < 128) & ~collar & ~ornament
    outer = dilate(solid, OUTER) & ~solid & (a > 0) & (legs < 128) & ~collar & ~ornament
    sole[inner, 3] = soft[inner]
    sole[outer, 3] = np.maximum(sole[outer, 3], soft[outer])
    band = inner | outer
    touched = release | band
    sole[touched, 0] = sole[touched, 1] = sole[touched, 2] = 255
    return sole, int((sole[..., 3] != original).sum())


BAND, OUTER, CREAM_LO, CREAM_HI, RELEASE = 2, 4, 8, 15, 10
COLLAR, PIPING, STITCH = 16, 10, 14
SPLIT_BASES = {'crystalsandal'}
THICK = 3
ORNAMENT_MARGIN = 8


def box_mean(values, radius):
    """Mean over a (2r+1)^2 window, edge-clamped."""
    pad = np.pad(values.astype(np.float64), radius, mode='edge')
    acc = np.cumsum(np.cumsum(pad, 0), 1)
    acc = np.pad(acc, ((1, 0), (1, 0)))
    k = 2 * radius + 1
    total = acc[k:, k:] - acc[:-k, k:] - acc[k:, :-k] + acc[:-k, :-k]
    return total / (k * k)


def thick_parts(mask, radius):
    """Connected parts of mask (8-connected) that survive erosion by radius."""
    core = erode(mask, radius)
    if not core.any():
        return np.zeros_like(mask)
    H, W = mask.shape
    out = np.zeros_like(mask)
    queue = deque(zip(*np.nonzero(core)))
    for y, x in queue:
        out[y, x] = True
    while queue:
        y, x = queue.popleft()
        for yy in (y - 1, y, y + 1):
            for xx in (x - 1, x, x + 1):
                if 0 <= yy < H and 0 <= xx < W and mask[yy, xx] and not out[yy, xx]:
                    out[yy, xx] = True
                    queue.append((yy, xx))
    return out


def distances(seed, allowed, reach):
    """4-connected geodesic distance from seed through allowed (-1: unreached)."""
    H, W = seed.shape
    dist = np.full((H, W), -1, np.int32)
    queue = deque()
    ys, xs = np.nonzero(seed & dilate(allowed, 1))
    for y, x in zip(ys, xs):
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < H and 0 <= xx < W and allowed[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = 1
                queue.append((yy, xx))
    while queue:
        y, x = queue.popleft()
        d = dist[y, x]
        if d >= reach:
            continue
        for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= yy < H and 0 <= xx < W and allowed[yy, xx] and dist[yy, xx] < 0:
                dist[yy, xx] = d + 1
                queue.append((yy, xx))
    return dist


_WIDTHS = {}


def piping_width(base):
    """Measured collar piping width for a style, 0 when it has none.

    Cream share (green - blue >= 12) per distance from the skin; piping shows
    as a band at 3-9 px. Styles whose band peaks below 15% (stiletto9, bow
    mule, bow sling, crystal sandal) have no piping to protect. The width is
    where the share falls below half its peak, plus 2 px for antialiasing.
    """
    if base not in _WIDTHS:
        painting = np.asarray(Image.open(WORN / f'{base}.webp').convert('RGBA')).astype(np.int32)
        legs = current(f'{base}_legs')[..., 3]
        skin, a = legs >= 128, painting[..., 3]
        d = distances(skin, ~skin & (a > 0), 16)
        r, g, b = painting[..., 0], painting[..., 1], painting[..., 2]
        cream = (g - b >= 12) & (r - b <= 45) & (a > 200)
        share = [float(cream[d == k].mean()) if (d == k).any() else 0. for k in range(1, 15)]
        peak = max(share[2:8])
        width = 0
        if peak >= .15:
            width = max(k + 1 for k in range(2, 14) if share[k] >= peak / 2) + 2
        _WIDTHS[base] = width
    return _WIDTHS[base]


def piping_zone(painting, legs, dye, split=False, width=PIPING):
    """Collar piping, protected by geometry because pale piping is often in no
    matte and can be as neutral as satin.

    Piping is fenced off from the shoe body by a dark stitch line. A pixel near
    the skin is piping when, without crossing a stitch pixel, it is closer to
    the skin than to the dyed body (or the body cannot reach it at all). Strap
    and sling rims touch the dyed strap directly, so they split at the middle
    and their outer half is dyed.
    The split is used only for styles without collar piping (SPLIT_BASES):
    elsewhere the stitch line has gaps at the throat corner through which the
    dye would leak into the piping, so any skin-reachable pixel stays piping.
    """
    r, g, b, a = (painting[..., i] for i in range(4))
    lum = r * .299 + g * .587 + b * .114
    skin = legs >= 128
    collar = dilate(skin, COLLAR) & ~skin & (a > 0)
    stitch = collar & (lum < box_mean(lum, 2) - STITCH)
    open_ = collar & ~stitch & ~dye
    if width <= 0:
        return np.zeros_like(skin)
    from_skin = distances(skin, open_, width - 1)
    from_dye = distances(dye, open_, COLLAR)
    near = from_skin > 0
    keep = near & ((from_dye < 0) | (from_skin < from_dye)) if split else near
    return keep | (stitch & dilate(near, 1))


def repair(variant):
    base = variant.split('_')[0]
    painting = np.asarray(Image.open(WORN / f'{variant}.webp').convert('RGBA')).astype(np.int32)
    shape = painting.shape
    dx, dy = SPRITES[base]['x'] - SPRITES[variant]['x'], SPRITES[base]['y'] - SPRITES[variant]['y']
    dye = baseline(f'{variant}_mask')
    sock = baseline(f'{variant}_sock')
    legs = aligned(current(f'{base}_legs'), dx, dy, shape)[..., 3].astype(np.int32)
    sole = aligned(current(f'{base}_sole'), dx, dy, shape)[..., 3].astype(np.int32)
    clear = current(f'{variant}_clear')[..., 3].astype(np.int32)
    r, g, b, a = (painting[..., i] for i in range(4))
    lum = np.clip(np.rint(r * .299 + g * .587 + b * .114), 0, 255).astype(np.uint8)

    sock_added = 0
    if sock is not None:
        key = np.clip((g - np.maximum(r, b) - 2) / 10.0, 0, 1)
        keyed = np.where((a > 0) & (legs < 128) & (clear < 128), np.rint(key * 255), 0).astype(np.int32)
        for _ in range(4):  # grow from the updated edge until stable
            want = np.where(dilate(sock[..., 3] >= 128, SOCK_REACH), keyed, 0)
            raise_ = want > sock[..., 3]
            if not raise_.any():
                break
            sock_added += int((raise_ & (sock[..., 3] < 128) & (want >= 128)).sum())
            sock[raise_, 3] = want[raise_]
            sock[raise_, 0] = sock[raise_, 1] = sock[raise_, 2] = lum[raise_]

    sock_alpha = sock[..., 3].astype(np.int32) if sock is not None else np.zeros(shape[:2], np.int32)
    spread = np.maximum(r, np.maximum(g, b)) - np.minimum(r, np.minimum(g, b))
    # Ornaments: thick neutral-white parts of the authored no-dye matte
    # (pearls, crystals). Their antialiased outline must stay undyed too.
    sole0_solid = aligned(baseline(f'{base}_sole'), dx, dy, shape)[..., 3] >= 128
    ornament = dilate(thick_parts(sole0_solid & (spread <= 24) & (lum >= 150), THICK), 3)
    satin = (a > 0) & (spread <= 24) & (lum >= 105) & ~ornament & ~piping_zone(painting, legs, dye[..., 3] >= 128, base in SPLIT_BASES, piping_width(base))
    # Pixels whose no-dye coverage this repair lowered (see soften_sole)
    # need dye underneath, whatever their tint, or the released
    # share of the pixel shows the undyed painting. The runtime removes dye in
    # proportion to the no-dye alpha, which gives the antialiased edge.
    sole0 = aligned(baseline(f'{base}_sole'), dx, dy, shape)[..., 3].astype(np.int32)
    softened = (a > 0) & (sole < sole0) & ~ornament
    owned = (dye[..., 3] >= 128) | (legs >= 128) | (sole >= 255) | (sock_alpha >= 128) | (clear >= 128)
    fill = geodesic(dye[..., 3] >= 128, (satin | softened) & ~owned, REACH)
    alpha = np.where(fill, 255 - legs, 0)
    # Seam pixels: the legs/sock matte is partial (antialiased skin or cloth
    # mixed with satin) and nothing else owns the rest, so the raw painting
    # showed as a light line along the throat and collar. The dye takes the
    # complement of that coverage, next to the existing (or newly filled) dye.
    cover = np.maximum(legs, sock_alpha)
    seam = (dilate((dye[..., 3] >= 128) | fill, SEAM) & (a > 0) & (cover > 0) & (cover < 255)
            & ((sole == 0) | softened) & (clear < 128) & ~ornament)
    alpha = np.where(seam, np.maximum(alpha, 255 - cover), alpha)
    # Pinholes: partially opaque dye on satin inside the dyed area left faint
    # white specks. Satin that touches solid dye and that nothing else owns
    # takes full coverage (less any legs/sock share).
    inside = (satin & dilate((dye[..., 3] >= 250) | fill, 1) & (legs < 128) & ((sole == 0) | softened)
              & (sock_alpha < 128) & (clear < 128))
    alpha = np.where(inside, np.maximum(alpha, 255 - cover), alpha)
    # Closing: satin within 2 px of solid dye whose total coverage (dye,
    # no-dye, skin, sock) still leaves the painting visible gets the missing
    # share. Ornament cores and piping stay excluded; ornament margins are
    # allowed here because a strap's rim can sit within 3 px of a rhinestone.
    core = thick_parts(sole0_solid & (spread <= 24) & (lum >= 150), THICK)
    gap = 255 - np.maximum(legs, sock_alpha) - sole
    open_satin = ((a > 200) & (spread <= 24) & (lum >= 105) & ~core & ~dilate(core, 1)
                  & ~piping_zone(painting, legs, dye[..., 3] >= 128, base in SPLIT_BASES, piping_width(base))
                  & (clear < 128) & (gap > 0))
    for _ in range(8):  # repeat until stable: newly solid pixels close their neighbours
        closing = open_satin & dilate(np.maximum(dye[..., 3], alpha) >= 200, 2) & (alpha < gap)
        if not closing.any():
            break
        alpha = np.where(closing, np.maximum(alpha, gap), alpha)
    raise_ = alpha > dye[..., 3]
    dye[raise_, 3] = alpha[raise_]
    dye[raise_, 0] = dye[raise_, 1] = dye[raise_, 2] = 255
    return dye, sock, int(raise_.sum()), sock_added


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('variants', nargs='*')
    parser.add_argument('--check', action='store_true', help='report only; do not write files')
    args = parser.parse_args()
    names = args.variants or sorted(SPRITES)
    for base in sorted({n.split('_')[0] for n in names}):
        sole, changed = soften_sole(base)
        print(f'{base + "_sole":22s} edge {changed:5d}px')
        if not args.check:
            Image.fromarray(sole, 'RGBA').save(WORN / f'{base}_sole.webp', lossless=True, quality=100, method=6, exact=True)
    for variant in names:
        dye, sock, filled, sock_added = repair(variant)
        line = f'{variant:22s} dye+{filled:5d}px'
        if sock is not None:
            line += f'  sock+{sock_added:4d}px'
        print(line)
        if args.check:
            continue
        Image.fromarray(dye, 'RGBA').save(WORN / f'{variant}_mask.webp', lossless=True, quality=100, method=6, exact=True)
        if sock is not None:
            Image.fromarray(sock, 'RGBA').save(WORN / f'{variant}_sock.webp', lossless=True, quality=100, method=6, exact=True)


if __name__ == '__main__':
    main()
