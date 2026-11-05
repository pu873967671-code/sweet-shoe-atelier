#!/usr/bin/env python3
"""Capture the actual Mary Jane salon UI and saved sock controls in Chromium."""
import functools,http.server,json,threading,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/maryjane-specks'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
errors=[];checks=[]
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for w,h in [(1920,1080),(390,844)]:
   p=b.new_page(viewport=dict(width=w,height=h),device_scale_factor=1,reduced_motion='reduce');p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
   seed=json.loads(json.dumps(q.SEED));seed['gallery'][0]['design']={'heel':'maryjane','color':'blue','material':'satin','pattern':'flowers','strap':'none','decoration':'none','charm':'none'};seed['gallery'][0]['fitting']={'sock':'frill','color':'black'}
   q.seed_page(p,seed);p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');q.enter_atelier(p)
   p.locator('[data-nav=collection]').click();p.locator('[data-try-on="0"]').click()
   def ready(sock,colour):p.wait_for_function("v=>{const d=document.querySelector('.fitting2d-canvas')?.dataset;return d?.renderer==='worn-sprite'&&d.heel==='maryjane'&&d.sock===v[0]&&d.sockColor===v[1]}",arg=[sock,colour])
   ready('frill','black');p.screenshot(path=str(OUT/f'ui-{w}x{h}.png'))
   p.locator('[data-fitting-color=cream]').click();ready('frill','cream')
   for sock in ['none','frill','knee','thigh','lace']:
    p.locator(f'[data-fitting-sock="{sock}"]').click();ready(sock,'cream')
   p.locator('[data-fitting-color=black]').click();ready('lace','black')
   p.locator('[data-fitting-color=cream]').click();ready('lace','cream')
   p.reload(wait_until='domcontentloaded');q.enter_atelier(p);p.locator('[data-nav=collection]').click();p.locator('[data-try-on="0"]').click();ready('lace','cream')
   checks.append(dict(viewport=f'{w}x{h}',sock_controls=True,reload=True));p.close()
  b.close()
 assert not errors,errors
 (OUT/'ui-acceptance.json').write_text(json.dumps(dict(status='PASS',checks=checks,page_errors=errors),indent=2)+'\n');print('PASS actual salon UI and reload')
finally:server.shutdown();server.server_close()
