#!/usr/bin/env python3
"""Actual Collection -> fitting controls and saved reload at both viewports."""
import copy,functools,http.server,json,sys,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
OUT=ROOT/'dev/qa-out/frill-sole-mask'
def main():
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();errors=[];rows=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   for w,h in [(390,844),(1920,1080)]:
    p=b.new_page(viewport=dict(width=w,height=h),reduced_motion='reduce');p.set_default_timeout(20000);p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.fulfill(body=''));p.add_init_script("window.CrazyGames={SDK:{environment:'disabled',init:async()=>{}}}")
    seed=copy.deepcopy(q.SEED);item=copy.deepcopy(seed['gallery'][0]);item['design']=dict(heel='flat',color='pink',material='satin',pattern='none',strap='none',decoration='none',charm='none');item['fitting']=dict(sock='frill',color='cream');seed['gallery']=[item];q.seed_page(p,seed)
    p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');q.enter_atelier(p);p.locator('[data-nav=collection]').click();p.locator('[data-gallery-select="0"]').click();p.locator('[data-try-on="0"]').click()
    def ready(sock):p.wait_for_function("s=>{const d=document.querySelector('.fitting2d-canvas')?.dataset;return d?.renderer==='worn-sprite'&&d.heel==='flat'&&d.sock===s}",arg=sock)
    ready('frill');p.screenshot(path=str(OUT/f'game-frill-{w}.png'));p.locator('[data-fitting-sock=lace]').click();ready('lace');p.screenshot(path=str(OUT/f'game-lace-{w}.png'));p.reload(wait_until='domcontentloaded');q.enter_atelier(p);p.locator('[data-nav=collection]').click();p.locator('[data-gallery-select="0"]').click();p.locator('[data-try-on="0"]').click();ready('lace');rows.append(dict(viewport=[w,h],controls=True,saved_reload=True));p.close();print('PASS full game',w,h,flush=True)
   b.close()
  assert not errors,errors
  (OUT/'ui-acceptance.json').write_text(json.dumps(dict(status='PASS',cases=rows,page_errors=errors),indent=2)+'\n')
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
