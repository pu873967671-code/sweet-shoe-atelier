#!/usr/bin/env python3
"""Native Chromium dye-loss counts against each base's pre-edges mask.

Only dye masks vary between the three pages; current sock/leg repairs and
renderer stay identical. No shipping code is instrumented on disk.
"""
import base64
import functools
import hashlib
import http.server
import io
import json
import subprocess
import sys
import threading
from importlib import import_module
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dev'))
fix = import_module('fix-edges-dye')
check = import_module('edges-fix-check')
OUT = fix.OUT


def main():
    errors, rows = [], []
    originals = {}
    for group, bases in fix.GROUPS.items():
        for base in bases:
            for suffix in ['', '_frill', '_lace']:
                name = base + suffix + '_mask'
                originals[name] = subprocess.check_output(
                    ['git', 'show', f'{fix.ORIGINALS[group]}:assets/worn/{name}.webp'], cwd=ROOT)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(
        check.q.QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    renderer = (ROOT / 'js/worn-sprites.js').read_bytes().replace(
        b'A.WornSprites={has', b'A.__edgeTest={load,tinted};A.WornSprites={has')
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])

            def page(kind):
                p = browser.new_page()
                p.on('pageerror', lambda e: errors.append(str(e)))
                p.route('https://**/*', lambda r: r.abort())
                p.route('**/js/worn-sprites.js*', lambda r: r.fulfill(
                    body=renderer, content_type='application/javascript'))
                if kind != 'after':
                    def asset(r):
                        name = Path(r.request.url.split('?')[0]).stem
                        if name in originals:
                            data = originals[name] if kind == 'original' else (
                                OUT / f'{name}-before.webp').read_bytes()
                            r.fulfill(body=data, content_type='image/webp')
                        else:
                            r.continue_()
                    p.route('**/assets/worn/*.webp*', asset)
                p.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
                p.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
                p.evaluate('window.requestAnimationFrame=()=>0')
                return p

            pages = [page(k) for k in ['original', 'before', 'after']]
            for base in check.BASES:
                for case, outfit in enumerate(check.CASES):
                    name = base + ('_' + outfit['sock'] if outfit['sock'] in ['lace', 'frill'] else '')
                    mask = Image.open(io.BytesIO(originals[name + '_mask'])).convert('RGBA').getchannel('A')
                    protected = Image.open(OUT / f'{name}-trim-band.png').convert('L')
                    painting = Image.open(ROOT / f'assets/worn/{name}.webp').convert('RGBA')
                    # Ignore intentional piping/yarn and transparent source pixels.
                    body = ImageChops.multiply(mask.point(lambda v: 255 if v >= 64 else 0), ImageChops.invert(protected))
                    body = ImageChops.multiply(body, painting.getchannel('A').point(lambda v: 255 if v >= 128 else 0))
                    native = []
                    for p in pages:
                        result = p.evaluate('''async v=>{
                          const c=await SweetShoe.__edgeTest.tinted(
                            {heel:v.base,color:v.color,material:'satin',pattern:v.pattern,
                             strap:'none',decoration:'none',charm:'none'},
                            {sock:v.sock,color:v.colour});
                          return c.toDataURL().split(',')[1];
                        }''', dict(outfit, base=base))
                        native.append(Image.open(io.BytesIO(base64.b64decode(result))).convert('RGB'))
                    original, before, after = native
                    # A visible dye regression differs from the fully dyed baseline
                    # by >=8 RGB levels. This catches highlights and partial alpha,
                    # including motif gaps, rather than relying on a pink threshold.
                    def loss(image):
                        r, g, b = ImageChops.difference(image, original).split()
                        maximum = ImageChops.lighter(ImageChops.lighter(r, g), b)
                        return ImageChops.multiply(body, maximum.point(lambda v: 255 if v >= 8 else 0))
                    lost_before, lost_after = loss(before), loss(after)
                    count_before, count_after = lost_before.histogram()[255], lost_after.histogram()[255]
                    row = dict(base=base, case=case, outfit=outfit, body_pixels=body.histogram()[255],
                               rendered_loss_before=count_before, rendered_loss_after=count_after)
                    rows.append(row)
                    if count_after:
                        lost_after.save(OUT / f'{name}-rendered-residual.png')
                    assert count_after == 0, row
                print('PASS native rendered dye-loss', base, flush=True)
            assert not errors, errors
            report = dict(status='PASS', method='native RGB distance >=8 from pre-chunk dye masks, outside protected trim',
                          renderer_sha256=hashlib.sha256((ROOT / 'js/worn-sprites.js').read_bytes()).hexdigest(),
                          cases=rows, page_errors=errors)
            (OUT / 'rendered-regressions.json').write_text(json.dumps(report, indent=2) + '\n')
            browser.close()
            print('PASS all 45 native RGB comparisons, zero remaining dye loss and page errors', flush=True)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
