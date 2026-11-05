#!/usr/bin/env python3
"""Install the approved fb4f9728 candidates with strictly local, lossless edits.

The approved commit also holds the original decoded artwork, so reruns do not
apply the alpha cut twice. No source painting is transformed or resampled.
"""
import argparse
import hashlib
import io
import json
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dev/qa-out/rear_heel'
APPROVED = 'fb4f9728'
BOXES = {'flat': (302, 641, 343, 698), 'loafer': (337, 640, 378, 697)}
REFS = json.loads(re.search(r'const SPRITES=(.*?);',
                          (ROOT / 'js/worn-sprites.js').read_text()).group(1))


def original(path):
    data = subprocess.check_output(['git', 'show', f'{APPROVED}:{path}'], cwd=ROOT)
    return np.array(Image.open(io.BytesIO(data)).convert('RGBA'))


def read(path):
    return np.array(Image.open(ROOT / path).convert('RGBA'))


def aligned(base, key, pixels):
    """Register with integer translation only, including differently sized variants."""
    ref, dst = REFS[base], REFS[key]
    canvas = Image.new('RGBA', (dst['w'], dst['h']))
    canvas.paste(Image.fromarray(pixels), (ref['x']-dst['x'], ref['y']-dst['y']))
    return np.array(canvas)


def local(base, key):
    x0, y0, x1, y1 = BOXES[base]
    dx, dy = REFS[base]['x']-REFS[key]['x'], REFS[base]['y']-REFS[key]['y']
    mask = np.zeros((REFS[key]['h'], REFS[key]['w']), dtype=bool)
    mask[y0+dy:y1+dy, x0+dx:x1+dx] = True
    return mask


def sole(base, sprites, masks, legs):
    """Existing build-worn-sole-masks.py algorithm, computed for one base only."""
    ref = REFS[base]
    protection = Image.new('L', (ref['w'], ref['h']))
    for key, src in sprites.items():
        rgb = src.astype(np.int16)
        warm = ((rgb[:, :, 0]-rgb[:, :, 2] >= 24)
                & (rgb[:, :, 1]-rgb[:, :, 2] >= 10)
                & (rgb[:, :, 0] >= rgb[:, :, 1]) & (rgb[:, :, 3] > 0)
                & (masks[key][:, :, 3] > 16))
        m = Image.fromarray(np.uint8(warm)*255)
        m.paste(0, (0, 0, m.width, round(src.shape[0]*.58)))
        registered = Image.new('L', protection.size)
        registered.paste(m, (REFS[key]['x']-ref['x'], REFS[key]['y']-ref['y']))
        protection = ImageChops.lighter(protection, registered)
    protection = protection.filter(ImageFilter.MaxFilter(3))
    protection = ImageChops.subtract(protection,
        Image.fromarray(legs[:, :, 3]).point(lambda a: 255 if a else 0))
    return np.array(protection)


def sock_join(before, shade, candidate, skin, region):
    """Local clone-brush repair of the old counter contact, without a warp.

    The supplied coverage matte contains near-zero ringing over brown lining.
    Re-composite its genuine knit edge over v2 instead of treating every alpha
    value as opaque cloth. Sample neighbouring solid yarn to remove the old
    lining colour mixed into that antialias fringe. Solid knit stays exact.
    """
    shade = shade.copy()
    ink = before.copy()
    a = shade[:, :, 3].copy()
    rgb = before[:, :, :3].astype(np.int16)
    green = rgb[:, :, 1] - np.maximum(rgb[:, :, 0], rgb[:, :, 2])
    a[region & ((a <= 24) | ((green <= 0) & (a < 255)))] = 0
    solid = (shade[:, :, 3] == 255) & (green > 1)
    ys, xs = np.where(region & (a > 0) & (a < 255))
    for y, x in zip(ys, xs):
        y0, y1 = max(0, y-6), min(a.shape[0], y+7)
        x0, x1 = max(0, x-6), min(a.shape[1], x+7)
        yy, xx = np.where(solid[y0:y1, x0:x1])
        assert len(xx), ('No neighbouring knit for local brush', x, y)
        nearest = np.argmin((yy+y0-y)**2 + (xx+x0-x)**2)
        sy, sx = yy[nearest]+y0, xx[nearest]+x0
        ink[y, x, :3] = before[sy, sx, :3]
        shade[y, x, :3] = shade[sy, sx, :3]
    ink[:, :, 3] = a
    # The bare candidate's restored ankle fringe is replaced by the sock's
    # own painted contour, so no pink bare-skin halo can peek through the knit.
    underlay = candidate.copy()
    underlay[region & (skin[:, :, 3] > 0), 3] = 0
    painted = np.array(Image.alpha_composite(Image.fromarray(underlay), Image.fromarray(ink)))
    after = before.copy()
    after[region] = painted[region]
    # Exact preservation of the authored, opaque yarn, including its texture.
    opaque = region & (a == 255)
    after[opaque] = before[opaque]
    shade[region, 3] = a[region]
    return after, shade, opaque


def build(policy):
    expected, stats = {}, {}
    for base in BOXES:
        old = original(f'assets/worn/{base}.webp')
        candidate_path = f'dev/qa-out/rear_heel/{base}_candidate.png'
        candidate_bytes = (ROOT / candidate_path).read_bytes()
        assert candidate_bytes == subprocess.check_output(
            ['git', 'show', f'{APPROVED}:{candidate_path}'], cwd=ROOT), 'Approval changed'
        new = read(candidate_path)
        assert new.shape == old.shape
        assert np.array_equal(old[~local(base, base)], new[~local(base, base)])
        changed = np.any(old != new, axis=2)
        sprites, masks = {}, {}
        for suffix in ['', '_frill', '_lace']:
            key = base + suffix
            path = f'assets/worn/{key}.webp'
            before = original(path)
            after = before.copy()
            old_aligned, new_aligned = aligned(base, key, old), aligned(base, key, new)
            change_aligned = np.any(old_aligned != new_aligned, axis=2) & local(base, key)
            same = np.all(before == old_aligned, axis=2)
            allowed = local(base, key)
            sock = None
            if suffix:
                sock = original(f'assets/worn/{key}_sock.webp')[:, :, 3]
                allowed &= (same if policy == 'exact' else sock == 0)
                # Even equality must never grant permission to touch yarn.
                allowed &= sock == 0
            after[allowed & change_aligned] = new_aligned[allowed & change_aligned]
            opaque_sock = None
            if sock is not None and policy == 'mask':
                sockpath = f'assets/worn/{key}_sock.webp'
                after, shade, opaque_sock = sock_join(
                    before, original(sockpath), new_aligned,
                    aligned(base, key, original(f'assets/worn/{base}_legs.webp')), change_aligned)
                assert np.array_equal(after[sock == 255], before[sock == 255]), key
                assert np.array_equal(shade[sock == 255], original(sockpath)[sock == 255]), key
                expected[sockpath] = shade
                allowed = local(base, key) & (shade[:, :, 3] < 255)
            elif sock is not None:
                assert np.array_equal(after[sock > 0], before[sock > 0])
            expected[path] = after
            sprites[key] = after
            maskpath = f'assets/worn/{key}_mask.webp'
            mask = original(maskpath)
            # Dye coverage follows the new silhouette. Keep all unaffected
            # authored coverage and RGB, including original partial fringes.
            alpha = np.minimum(mask[:, :, 3], after[:, :, 3])
            mask[allowed, 3] = alpha[allowed]
            expected[maskpath] = mask
            masks[key] = mask
            stats[key] = {'changed_pixels': int(np.any(before != after, axis=2).sum()),
                          'matching_base_pixels_in_patch': int((same & change_aligned).sum()),
                          'sock_pixels_unchanged': sock is None or np.array_equal(after[sock > 0], before[sock > 0]),
                          'opaque_sock_pixels_unchanged': opaque_sock is None or np.array_equal(after[opaque_sock], before[opaque_sock]),
                          'local_sock_edge_repaint_pixels': 0 if sock is None else int(np.count_nonzero((sock > 0) & np.any(before != after, axis=2))),
                          'sock_policy': policy if suffix else None}
        path = f'assets/worn/{base}_legs.webp'
        legs = original(path)
        region = local(base, base)
        # Preserve the front/back luminance map, and trim only lost silhouette.
        alpha = np.minimum(legs[:, :, 3], new[:, :, 3])
        legs[region, 3] = alpha[region]
        # Newly painted cream wall/piping is footwear, never exposed skin.
        painted = np.any(old[:, :, :3] != new[:, :, :3], axis=2) & changed
        legs[painted & (legs[:, :, 3] < 255), 3] = 0
        expected[path] = legs
        path = f'assets/worn/{base}_sole.webp'
        protection = original(path)
        new_protection = sole(base, sprites, masks, legs)
        # This matte is shared by every registered sock variant. A yarn-covered
        # pixel may retain the old contour, so clip against their union rather
        # than deleting protection still needed by that variant.
        coverage = new[:, :, 3].copy()
        for key, sprite in sprites.items():
            registered = Image.new('RGBA', (REFS[base]['w'], REFS[base]['h']))
            registered.paste(Image.fromarray(sprite),
                (REFS[key]['x']-REFS[base]['x'], REFS[key]['y']-REFS[base]['y']))
            coverage = np.maximum(coverage, np.array(registered)[:, :, 3])
        # Recompute source-derived protection locally. Removed pixels cannot
        # remain protected; every pixel outside the approved box stays exact.
        protection[region, 3] = np.minimum(new_protection, coverage)[region]
        expected[path] = protection
    return expected, stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--sock-policy', choices=['exact', 'mask'], default='exact')
    args = parser.parse_args()
    expected, stats = build(args.sock_policy)
    report = {'status': 'PASS', 'approved_commit': APPROVED, 'variants': stats, 'files': {}}
    for path, pixels in expected.items():
        before = original(path)
        base = Path(path).stem.split('_')[0]
        key = Path(path).stem.replace('_mask', '').replace('_sock', '')
        if key not in REFS:
            key = base
        outside = ~local(base, key)
        assert np.array_equal(pixels[outside], before[outside]), path
        if not args.verify:
            if np.array_equal(pixels, before):
                (ROOT / path).write_bytes(subprocess.check_output(
                    ['git', 'show', f'{APPROVED}:{path}'], cwd=ROOT))
            else:
                Image.fromarray(pixels).save(ROOT / path, lossless=True, exact=True, method=6)
        decoded = read(path)
        assert np.array_equal(decoded, pixels), f'{path}: lossless pixel mismatch'
        assert np.array_equal(decoded[outside], before[outside]), path
        report['files'][path] = {'changed_pixels': int(np.any(before != decoded, axis=2).sum()),
                                 'outside_patch_pixel_exact': True,
                                 'size': [decoded.shape[1], decoded.shape[0]],
                                 'sha256': hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
    # Every unrelated flat/loafer file remains exact; sock edge repairs are local.
    for base in BOXES:
        for p in (ROOT / 'assets/worn').glob(base+'*.webp'):
            path = str(p.relative_to(ROOT))
            if path not in expected:
                assert np.array_equal(read(path), original(path)), path
    (OUT / 'applied-pixels.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
