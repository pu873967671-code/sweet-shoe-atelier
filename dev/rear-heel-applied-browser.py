#!/usr/bin/env python3
"""Runtime acceptance and native 2x crops; writes only dev/qa-out/rear_heel/."""
import base64
import functools
import http.server
import io
import json
import re
import subprocess
import threading
from pathlib import Path

from PIL import Image, ImageDraw
import numpy as np
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dev/qa-out/rear_heel'


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def main():
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    errors, results, captures = [], [], []
    refs = json.loads(re.search(r'const SPRITES=(.*?);',
                               (ROOT / 'js/worn-sprites.js').read_text()).group(1))
    sheet = Image.new('RGB', (1280, 720), '#f5efe9')
    pen = ImageDraw.Draw(sheet)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('https://**/*', lambda route: route.abort())
            page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
            page.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
            baseline = browser.new_page()
            baseline.route('https://**/*', lambda route: route.abort())

            def original_asset(route):
                from urllib.parse import urlparse
                path = urlparse(route.request.url).path.lstrip('/')
                if Path(path).stem.split('_')[0] in ['flat', 'loafer']:
                    route.fulfill(body=subprocess.check_output(
                        ['git', 'show', f'fb4f9728:{path}'], cwd=ROOT), content_type='image/webp')
                else:
                    route.continue_()

            baseline.route('**/assets/worn/*.webp*', original_asset)
            baseline.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
            baseline.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
            # Every base still loads through the actual fitting integration.
            cases = [(key, 'none', 390, 844) for key in refs if '_' not in key]
            cases += [(heel, sock, w, h) for heel in ['flat', 'loafer']
                      for sock in ['none', 'frill', 'lace', 'sheer', 'opaque', 'fishnet']
                      for w, h in [(390, 844), (1920, 1080)]]
            for heel, sock, w, h in cases:
                result = page.evaluate('''async v=>{
                  const c=document.createElement('canvas');c.width=v.w;c.height=v.h;
                  await SweetShoe.Fitting2D.render(c,{heel:v.heel,color:'pink',material:'satin',
                    pattern:'flowers',strap:'none',decoration:'none',charm:'none'},
                    {sock:v.sock,color:'cream',skin:'#8a5a3c'},'salon',true);
                  return {...c.dataset};
                }''', {'heel': heel, 'sock': sock, 'w': w, 'h': h})
                assert result['renderer'] == 'worn-sprite' and result['fallback'] == 'false', result
                assert result['sock'] == sock and result['pattern'] == 'flowers', result
                results.append({'heel': heel, 'sock': sock, 'size': [w, h], 'renderer': result['renderer']})
            for row, heel in enumerate(['flat', 'loafer']):
                for col, sock in enumerate(['none', 'frill', 'lace', 'sheer']):
                    render = '''async ({heel,sock})=>{
                      const c=document.createElement('canvas');c.width=1220;c.height=1000;
                      await SweetShoe.Fitting2D.render(c,{heel,color:'pink',material:'satin',
                        pattern:'flowers',strap:'none',decoration:'none',charm:'none'},
                        {sock,color:'cream',skin:'#8a5a3c'},'salon',true);
                      return {png:c.toDataURL().split(',')[1],layout:JSON.parse(c.dataset.pairLayout)};
                    }'''
                    result = page.evaluate(render, {'heel': heel, 'sock': sock})
                    raw = base64.b64decode(result['png'])
                    name = f'applied-{heel}-{sock}.png'
                    (OUT / name).write_bytes(raw)
                    im = Image.open(io.BytesIO(raw)).convert('RGBA')
                    g = result['layout']
                    assert g['scale'] == 1, g
                    dx, dy = (0, 0) if heel == 'flat' else (35, -1)
                    before = baseline.evaluate(render, {'heel': heel, 'sock': sock})
                    old = np.array(Image.open(io.BytesIO(base64.b64decode(before['png']))).convert('RGBA'))
                    changed = np.any(old != np.array(im), axis=2)
                    # Short socks/bare skin only interpolate nearby pixels.
                    # Sheer hosiery also derives its existing soft edge from
                    # an 18px blur of the sprite, so its local halo is wider.
                    x0, y0 = round(g['x'])+302+dx, round(g['y'])+641+dy
                    halo = 36 if sock == 'sheer' else 3
                    changed[y0-halo:y0+57+halo, x0-halo:x0+41+halo] = False
                    assert not changed.any(), (heel, sock, 'render changed outside local patch')
                    x, y = round(g['x'])+260+dx, round(g['y'])+610+dy
                    crop = im.crop((x, y, x+150, y+150)).resize((300, 300), Image.Resampling.NEAREST)
                    sheet.paste(crop, (col*320+10, row*360+46), crop)
                    pen.text((col*320+10, row*360+12), f'{heel} / {sock} / 2x', fill='#382b28')
                    pen.text((col*320+10, row*360+28), 'flowers / bridal skin / cream socks', fill='#382b28')
                    captures.append(name)
            # The four repaired short-sock joins must also tint cleanly at
            # dark and pale colours, using the same actual fitting path.
            colours = Image.new('RGB', (960, 1280), '#f5efe9')
            colour_pen = ImageDraw.Draw(colours)
            colour_cases = []
            for row, (heel, sock) in enumerate([
                    ('flat', 'frill'), ('flat', 'lace'),
                    ('loafer', 'frill'), ('loafer', 'lace')]):
                for col, colour in enumerate(['black', 'white', 'pink']):
                    result = page.evaluate('''async v=>{
                      const c=document.createElement('canvas');c.width=1220;c.height=1000;
                      await SweetShoe.Fitting2D.render(c,{heel:v.heel,color:'pink',material:'satin',
                        pattern:'flowers',strap:'none',decoration:'none',charm:'none'},
                        {sock:v.sock,color:v.colour,skin:'#8a5a3c'},'salon',true);
                      return {png:c.toDataURL().split(',')[1],data:{...c.dataset},
                        layout:JSON.parse(c.dataset.pairLayout)};
                    }''', {'heel': heel, 'sock': sock, 'colour': colour})
                    assert result['data']['renderer'] == 'worn-sprite'
                    assert result['data']['fallback'] == 'false'
                    im = Image.open(io.BytesIO(base64.b64decode(result['png']))).convert('RGBA')
                    g = result['layout']
                    dx, dy = (0, 0) if heel == 'flat' else (35, -1)
                    x, y = round(g['x'])+270+dx, round(g['y'])+610+dy
                    crop = im.crop((x, y, x+150, y+140)).resize((300, 280), Image.Resampling.NEAREST)
                    colours.paste(crop, (col*320+10, row*320+30), crop)
                    colour_pen.text((col*320+10, row*320+10), f'{heel} / {sock} / {colour} / 2x', fill='#382b28')
                    colour_cases.append({'heel': heel, 'sock': sock, 'colour': colour})
            colours.save(OUT / 'applied-variants-colours.jpg', quality=95)
            # Native output has a transparent pocket and retains approved rounded wall.
            for heel, dx, dy in [('flat', 0, 0), ('loafer', 35, -1)]:
                result = page.evaluate('''async ({heel,dx,dy})=>{
                  const image=new Image();image.src='assets/worn/'+heel+'.webp';await image.decode();
                  const c=document.createElement('canvas');c.width=image.width;c.height=image.height;
                  const p=c.getContext('2d');p.drawImage(image,0,0);
                  return {pocket:p.getImageData(326+dx,655+dy,1,1).data[3],
                    wall:[...p.getImageData(326+dx,675+dy,5,1).data].filter((v,i)=>i%4===3)};
                }''', {'heel': heel, 'dx': dx, 'dy': dy})
                assert result['pocket'] == 0 and min(result['wall']) > 200, result
            for heel in ['flat', 'loafer']:
                for sock in ['frill', 'lace']:
                    result = page.evaluate('''async ({heel,sock})=>{
                      const image=new Image();image.src='assets/worn/'+heel+'_'+sock+'.webp';
                      await image.decode();const c=document.createElement('canvas');
                      c.width=image.width;c.height=image.height;const p=c.getContext('2d');
                      p.drawImage(image,0,0);const dx=heel==='flat'?0:35,dy=heel==='flat'?0:-1;
                      return {pocket:p.getImageData(326+dx,655+dy,1,1).data[3],
                        wall:p.getImageData(328+dx,675+dy,1,1).data[3]};
                    }''', {'heel': heel, 'sock': sock})
                    assert result['pocket'] == 0 and result['wall'] > 200, (heel, sock, result)
            # Existing load failure/retry contract still works with the new cache version.
            fresh = browser.new_page()
            fresh.route('https://**/*', lambda route: route.abort())
            fresh.route('**/assets/worn/flat_sole.webp*', lambda route: route.abort())
            fresh.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
            fresh.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
            code = '''async()=>{const c=document.createElement('canvas');c.width=1220;c.height=1000;
              return SweetShoe.WornSprites.paint(c,{heel:'flat'},{sock:'none'},'salon',true);}'''
            assert fresh.evaluate(code) is False
            fresh.unroute('**/assets/worn/flat_sole.webp*')
            assert fresh.evaluate(code) is True
            assert page.evaluate('SweetShoe.WornSprites.info().cacheEntries<=8')
            browser.close()
        assert not errors, errors
        sheet.save(OUT / 'applied.jpg', quality=95)
        report = {'status': 'PASS', 'cases': results, 'captures': captures,
                  'page_errors': errors, 'external_https_blocked': True,
                  'local_render_change_cases': 8, 'sock_colour_cases': colour_cases,
                  'procedural_sheer_edge_halo_px': 36,
                  'pocket_and_rounded_wall': 'PASS', 'missing_mask_retry': 'PASS'}
        (OUT / 'applied-browser.json').write_text(json.dumps(report, indent=2)+'\n')
        print(f'PASS: {len(results)} actual fitting renders, eight 2x crops, rounded wall and mask retry.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    main()
