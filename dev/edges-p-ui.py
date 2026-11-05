#!/usr/bin/env python3
"""Actual Collection and Studio products in offline Chromium, phone/desktop."""
import functools,http.server,json,sys,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-p'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
from importlib import import_module
survey=import_module('edges-p-check')
def main():
 errors=[];assets=[];rows=[]
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   for w,h in [(390,844),(1920,1080)]:
    p=browser.new_page(viewport=dict(width=w,height=h),device_scale_factor=1,reduced_motion='reduce')
    p.route('https://**/*',lambda r:r.abort());p.add_init_script("window.CrazyGames={SDK:{environment:'disabled',init:async()=>{}}}")
    p.on('pageerror',lambda e:errors.append(str(e)))
    p.on('response',lambda r:assets.append(r.url) if r.status>=400 and '/assets/' in r.url else None)
    seed=json.loads(json.dumps(q.SEED));template=seed['gallery'][0];seed['gallery']=[]
    seed['unlocks'] += ['heel:'+b for b in survey.BASES]
    for b in survey.BASES:
     for c in survey.CASES[:1]:
      item=json.loads(json.dumps(template));item['design']=dict(c,heel=b,strap='none',decoration='none',charm='none');seed['gallery'].append(item)
    q.seed_page(p,seed);p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');q.enter_atelier(p)
    p.add_locator_handler(p.locator('.guide-dialogue'),lambda _:q.acknowledge_dialogue(p))
    p.locator('[data-nav=collection]').click()
    for index,b in enumerate(survey.BASES):
     if '--crystalsandal-only' in sys.argv and b!='crystalsandal':continue
     if '--quick' in sys.argv and b not in ['maryjane','slingback','bowsling','platform','crystalsandal']:continue
     p.locator(f'[data-gallery-select="{index}"]').click()
     p.wait_for_function("b=>[...document.querySelectorAll('.collection-stage canvas.product-canvas')].some(c=>c.dataset.heel===b&&c.dataset.shoe2dReady==='true')",arg=b)
     p.screenshot(path=str(OUT/f'collection-{b}-{w}x{h}.png'))
     rows.append(dict(surface='collection',base=b,viewport=[w,h]))
     print('PASS Collection',w,b,flush=True)
    p.keyboard.press('Escape');p.locator('[data-nav=free]').click()
    p.wait_for_function("()=>[...document.querySelectorAll('#preview canvas')].some(c=>c.dataset.shoe2dReady==='true')")
    p.screenshot(path=str(OUT/f'workbench-{w}x{h}.png'))
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    rows.append(dict(surface='workbench',viewport=[w,h]));p.close();print('PASS product UI',w,h,flush=True)
   assert not errors and not assets,(errors,assets)
   (OUT/'ui-acceptance.json').write_text(json.dumps(dict(status='PASS',cases=rows,page_errors=errors,asset_errors=assets),indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
