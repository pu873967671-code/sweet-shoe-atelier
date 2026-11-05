#!/usr/bin/env python3
"""Rebuild reviewed q95 package art from pristine originals in a separate tree.

Example: python3 dev/optimize-package-art.py --source /tmp/original-assets --output /tmp/rebuilt-assets
Both trees contain shoe2d/ and fitting2d/. Never encode the already compressed output.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageChops

NAMES = (
    'shoe2d/bootie_base.webp', 'shoe2d/platform_base.webp',
    'shoe2d/loafer_base.webp', 'shoe2d/ballet_base.webp',
    'shoe2d/bowsling_base.webp', 'shoe2d/crystalpump_base.webp',
    'shoe2d/maryjane_base.webp', 'shoe2d/studpump_base.webp',
    'fitting2d/bootie_shoe.webp', 'fitting2d/bowmule_shoe.webp',
)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if source == output or source in output.parents or output in source.parents:
        parser.error('source and output trees must be separate')
    for name in NAMES:
        original = source / name
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        image = Image.open(original).convert('RGBA')
        image.save(target, format='WEBP', quality=95, method=4, exact=True)
        with Image.open(target) as encoded:
            encoded = encoded.convert('RGBA')
            if image.size != encoded.size or ImageChops.difference(
                image.getchannel('A'), encoded.getchannel('A')
            ).getbbox() is not None:
                raise RuntimeError('dimensions or alpha changed: ' + name)
        print(f'{name}: {original.stat().st_size} -> {target.stat().st_size} bytes')

if __name__ == '__main__':
    main()
