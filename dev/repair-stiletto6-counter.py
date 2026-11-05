#!/usr/bin/env python3
"""Remove the two extraction teeth from the 6cm pump's counter dye mask.

The immutable shoe painting already has a rounded cream collar. Its semantic
upper mask accidentally crossed that collar twice. This source-only repair
removes dye coverage along the original piping; it never edits the painting,
adds alpha, or touches another shoe style.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'dev/stiletto6-fit/stiletto6_upper-original.webp'
TARGET = ROOT / 'assets/shoe2d/stiletto6_upper.webp'
# Outer edge of the original cream piping, in the product's native camera.
# The return has one rounded apex, rather than the extracted mask's W shape.
TRACE = [(800, 193), (810, 170), (820, 147), (825, 137), (830, 129),
         (835, 122), (840, 115), (845, 108), (850, 102), (855, 97),
         (860, 94), (865, 94), (870, 94), (875, 94), (880, 96),
         (885, 100), (890, 105), (895, 109)]


def main():
    if not SOURCE.exists():
        raise SystemExit('Missing pristine source: ' + str(SOURCE))
    original = np.array(Image.open(SOURCE).convert('RGBA'))
    result = original.copy()
    x = np.arange(825, 896)
    points = np.asarray(TRACE, dtype=float)
    edge = PchipInterpolator(points[:, 0], points[:, 1])(x)
    coverage = np.clip((np.arange(result.shape[0])[:, None] - edge + .75) / 1.5, 0, 1)
    result[:, x, 3] = np.rint(result[:, x, 3] * coverage).astype('uint8')
    assert np.all(result[:, :, 3] <= original[:, :, 3])
    assert np.array_equal(result[:, :, :3], original[:, :, :3])
    changed = np.any(result != original, axis=2)
    yy, xx = np.where(changed)
    Image.fromarray(result).save(TARGET, lossless=True, exact=True, method=6)
    decoded = np.array(Image.open(TARGET).convert('RGBA'))
    assert np.array_equal(result, decoded), 'Mask must retain every untouched byte'
    print(json.dumps({'target': str(TARGET.relative_to(ROOT)),
                      'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                      'changed_pixels': int(changed.sum()),
                      'changed_bounds': [int(xx.min()), int(yy.min()), int(xx.max()) + 1, int(yy.max()) + 1],
                      'painting_unchanged': True, 'alpha_additions': 0}, indent=2))


if __name__ == '__main__':
    main()
