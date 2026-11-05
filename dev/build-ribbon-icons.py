#!/usr/bin/env python3
"""Export authored SVG ribbon icons to local transparent 256px WebPs.
Native mint/candy SVG gradients match assets/decor/mint_flowers*.svg. No image
service or bitmap painting is used; editable sources live beside this helper.
Requires existing Playwright/Chromium and Pillow used by the QA suite.
"""
from io import BytesIO
import json
import re
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
metadata = ROOT / 'js/item-assets.js'
catalog = metadata.read_text()
pattern = r'A.ITEM_BOUNDS = (.*?); '
bounds = json.loads(re.search(pattern, catalog).group(1))
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 768, 'height': 768}, device_scale_factor=1)
    for tier in (1, 2, 6):
        source = ROOT / f'dev/item-sources/rib{tier}.svg'
        svg = source.read_text().replace('width="256" height="256"', 'width="768" height="768"', 1)
        page.set_content('<style>html,body{margin:0;background:transparent;overflow:hidden}</style>' + svg)
        image = Image.open(BytesIO(page.screenshot(omit_background=True))).convert('RGBA')
        image = image.resize((256, 256), Image.Resampling.LANCZOS)
        assert image.getchannel('A').getbbox(), tier
        image.save(ROOT / f'assets/items/m_rib{tier}.webp', lossless=True, method=6)
        box = image.getchannel('A').point(lambda a: 255 if a > 20 else 0).getbbox()
        x, y, right, bottom = box
        assert min(x, y) > 1 and max(right, bottom) < 255, (tier, box)
        bounds[f'm_rib{tier}'] = [round(v, 5) for v in (256 / max(right-x, bottom-y), (128-(x+right)/2)/256, (128-(y+bottom)/2)/256)]
        print(f'Exported rib{tier}: {box}')
    browser.close()

# Refresh only the three authored entries; preserve other accepted icon framing.
metadata.write_text(re.sub(pattern, lambda m: 'A.ITEM_BOUNDS = ' + json.dumps(bounds) + '; ', catalog))
