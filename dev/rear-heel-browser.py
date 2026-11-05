#!/usr/bin/env python3
"""Read-only browser acceptance; evidence stays with review candidates."""
import functools
import http.server
import json
import re
import threading
from pathlib import Path

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
    refs = json.loads(re.search(r'const SPRITES=(.*?);',
                               (ROOT / 'js/worn-sprites.js').read_text()).group(1))
    keys = [key for key in refs if '_' not in key]
    errors = []
    results = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('https://**/*', lambda route: route.abort())
            page.goto(f'http://127.0.0.1:{server.server_port}/', wait_until='domcontentloaded')
            page.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
            for key in keys:
                for sock in (['none', 'frill', 'lace'] if key in ['flat', 'loafer'] else ['none']):
                    result = page.evaluate('''async ({heel,sock}) => {
                      const c=document.createElement('canvas'); c.width=390;c.height=844;
                      const ok=await SweetShoe.WornSprites.paint(c,
                        {heel,color:'pink',material:'satin',pattern:'none',strap:'none',decoration:'none',charm:'none'},
                        {sock,color:'cream'},'salon',true);
                      return {heel,sock,ok,renderer:c.dataset.renderer};
                    }''', {'heel': key, 'sock': sock})
                    assert result['ok'] and result['renderer'] == 'worn-sprite', result
                    results.append(result)
            for key in ['flat', 'loafer']:
                result = page.evaluate('''async key => {
                  const image=new Image();image.src='dev/qa-out/rear_heel/'+key+'_candidate.png';
                  await image.decode(); const c=document.createElement('canvas');
                  c.width=image.naturalWidth;c.height=image.naturalHeight;
                  const p=c.getContext('2d');p.drawImage(image,0,0);
                  const x=key==='flat'?326:361,y=key==='flat'?655:654;
                  return {key,w:c.width,h:c.height,pocketAlpha:p.getImageData(x,y,1,1).data[3]};
                }''', key)
                assert result['pocketAlpha'] == 0, result
                assert (result['w'], result['h']) == (refs[key]['w'], refs[key]['h']), result
                results.append(result)
            browser.close()
        assert not errors, errors
        report = {'status': 'PASS', 'checks': results, 'page_errors': errors,
                  'external_https_blocked': True, 'runtime_assets_modified': False}
        (OUT / 'browser-validation.json').write_text(json.dumps(report, indent=2)+'\n')
        print(f'PASS: {len(keys)} runtime bases, four sock variants, two full-size transparent candidates; no page errors.')
    finally:
        server.shutdown()


if __name__ == '__main__':
    main()
