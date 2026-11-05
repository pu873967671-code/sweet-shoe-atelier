#!/usr/bin/env python3
"""WebKit skin-tone acceptance; writes only dev/qa-out, never qa/."""
import base64
import functools
import http.server
import io
import json
import os
from pathlib import Path
import subprocess
import threading

from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dev/qa-out'
OUT.mkdir(exist_ok=True)
HEELS = ['studpump', 'crystalsandal', 'ballet', 'kitten']
SOCKS = ['none', 'sheer', 'fishnet', 'frill', 'lace', 'opaque']
BASELINE = '71f4e22b'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


RENDER = """async ([heel,sock,skin])=>{
 const c=document.createElement('canvas');c.width=780;c.height=390;
 const d={heel,color:'pink',material:'satin',pattern:'none',strap:'none',decoration:'none',charm:'none'};
 await SweetShoe.Fitting2D.render(c,d,{sock,color:'black',...(skin?{skin}:{})},'salon',true);
 if(c.dataset.renderer!=='worn-sprite')throw Error('Unexpected fallback '+heel+' '+sock);
 const o=document.createElement('canvas');o.width=c.width;o.height=c.height;
 const p=o.getContext('2d');p.fillStyle='#e9e2d6';p.fillRect(0,0,o.width,o.height);p.drawImage(c,0,0);
 return {url:o.toDataURL(),pose:c.dataset.pairLayout,contacts:c.dataset.shadowContacts};
}"""


def frame(page, heel, sock, skin=None):
    result = page.evaluate(RENDER, [heel, sock, skin])
    im = Image.open(io.BytesIO(base64.b64decode(result.pop('url').split(',')[1]))).convert('RGB')
    return im, result


def main():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors, frames, defaults = [], {}, {}
    previous = subprocess.check_output(['git', 'show', BASELINE + ':js/worn-sprites.js'], cwd=ROOT).decode()
    with sync_playwright() as pw:
        browser = pw.webkit.launch(env={k: v for k, v in os.environ.items() if 'proxy' not in k.lower()})
        page = browser.new_page(viewport={'width': 780, 'height': 390})
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('response', lambda r: errors.append(f'{r.status} {r.url}') if r.status >= 400 else None)
        page.route('https://**', lambda r: r.fulfill(status=200, body=''))
        page.add_init_script("window.CrazyGames={SDK:{environment:'disabled',init:async()=>{}}}")
        page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
        page.wait_for_function('window.SweetShoe?.WornSprites&&SweetShoe.Fitting2D')
        for sock in SOCKS:
            for heel in HEELS:
                fair, fair_meta = frame(page, heel, sock)
                brown, brown_meta = frame(page, heel, sock, '#8a5a3c')
                assert fair_meta == brown_meta, (heel, sock, 'geometry changed')
                assert ImageChops.difference(fair, brown).getbbox() is not None or sock == 'opaque', (heel, sock, 'tone absent')
                # A cached tinted pair must never contaminate a later fair pair.
                again, _ = frame(page, heel, sock)
                assert ImageChops.difference(fair, again).getbbox() is None, (heel, sock, 'cache contamination')
                defaults[heel, sock] = fair
                frames[heel, sock] = brown
                print('PASS', heel, sock, flush=True)
        assert page.evaluate('SweetShoe.WornSprites.info().cacheEntries<=SweetShoe.WornSprites.info().cacheLimit')
        # Compare un-tinted output to the committed renderer, in the same engine.
        page.route('**/js/worn-sprites.js', lambda r: r.fulfill(body=previous, content_type='application/javascript'))
        page.reload()
        page.wait_for_function('window.SweetShoe?.WornSprites&&SweetShoe.Fitting2D')
        for (heel, sock), fair in defaults.items():
            original, _ = frame(page, heel, sock)
            assert ImageChops.difference(fair, original).getbbox() is None, (heel, sock, 'default changed')
        browser.close()
    server.shutdown()
    assert not errors, errors
    rows = [('none', '#8a5a3c'), ('sheer', '#8a5a3c'), ('fishnet', '#8a5a3c'), ('frill', '#8a5a3c'), ('none', 'default / no tint')]
    sheet = Image.new('RGB', (780 * 4, 430 * len(rows)), '#e9e2d6')
    draw = ImageDraw.Draw(sheet)
    for row, (sock, label) in enumerate(rows):
        for col, heel in enumerate(HEELS):
            im = defaults[heel, sock] if row == 4 else frames[heel, sock]
            sheet.paste(im, (col * 780, row * 430 + 35))
            draw.text((col * 780 + 16, row * 430 + 12), f'{heel} | {sock} | {label} | WebKit 780x390', fill='#39291f')
    sheet.save(OUT / 'skin_sheet.jpg', quality=92)
    (OUT / 'skin-report.json').write_text(json.dumps({'engine': 'WebKit', 'viewport': '780x390', 'tinted_cases': 24, 'default_pixel_exact_cases': 24, 'cache_isolation': True, 'geometry_unchanged': True, 'errors': errors}, indent=2) + '\n')
    print('PASS: 24 tinted/default cases, exact incumbent default output, cache isolation, unchanged geometry, no console errors; dev/qa-out/skin_sheet.jpg')


if __name__ == '__main__':
    main()
