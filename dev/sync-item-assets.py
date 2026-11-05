#!/usr/bin/env python3
"""Refresh the optional local artwork catalog after new item WebPs arrive. No build needed to play."""
import json
from PIL import Image
from pathlib import Path
root = Path(__file__).resolve().parents[1]
names = sorted(p.stem for p in (root / 'assets/items').glob('*.webp'))
bounds = {}
for name in names:
    im = Image.open(root / 'assets/items' / (name + '.webp')).convert('RGBA')
    box = im.getchannel('A').point(lambda a: 255 if a > 20 else 0).getbbox()
    if box:
        x, y, right, bottom = box
        bounds[name] = [round(v, 5) for v in (im.width / max(right-x, bottom-y), (im.width/2-(x+right)/2)/im.width, (im.height/2-(y+bottom)/2)/im.height)]
(root / 'js/item-assets.js').write_text("'use strict';\n// Optional artwork present at catalog refresh; absent files use the CSS miniatures.\n(function(A){ A.ITEM_ASSETS = " + json.dumps(names) + "; A.ITEM_BOUNDS = " + json.dumps(bounds) + "; })(globalThis.SweetShoe = globalThis.SweetShoe || {});\n")
print(f'Cataloged {len(names)} local item assets.')
