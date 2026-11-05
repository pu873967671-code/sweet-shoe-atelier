#!/usr/bin/env python3
"""Offline all-base/material, both-camera acceptance and exact 3x evidence."""
import base64,csv,functools,http.server,io,json,sys,threading,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage'
BASES=import_module('edges-p-check').BASES
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def script_route(route,source):route.fulfill(body=source,content_type='application/javascript')

def main():
 phase='before' if '--before' in sys.argv else 'after';errors=[];assets=[];rows=[]
 bases=['loafer'] if '--loafer-only' in sys.argv else BASES
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page(viewport=dict(width=1920,height=1080));p.set_default_timeout(30000)
   p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:assets.append(r.url) if r.status>=400 else None);p.route('https://**/*',lambda r:r.fulfill(body=''))
   for name in ['shoe2d','worn-sprites']:
    source=(OUT/'baseline'/f'{name}.js' if phase=='before' else ROOT/'js'/f'{name}.js').read_text()
    if name=='worn-sprites':source=source.replace('A.WornSprites={','A.__materialNative=tinted;A.WornSprites={')
    p.route(f'**/js/{name}.js*',functools.partial(script_route,source=source))
   if phase=='before':
    def oldmask(r):
     name=r.request.url.split('/assets/')[1].split('?')[0];path=OUT/'baseline/assets'/name
     r.fulfill(body=(path if path.exists() else ROOT/'assets'/name).read_bytes(),content_type='image/webp')
    p.route('**/assets/**',oldmask)
   harness=''.join(f'<script src="/js/{n}.js"></script>' for n in ['data','studio-core','showcase','shoe-renderer','accessory-renderer','shoe2d','worn-sprites','fitting2d'])
   p.route('**/__material',lambda r:r.fulfill(body=harness,content_type='text/html'));p.goto(f'http://127.0.0.1:{server.server_port}/__material');p.wait_for_function('!!SweetShoe.__materialNative')
   mats=p.evaluate('SweetShoe.opts.material.map(x=>x[0])')
   for b in bases:
    for camera in ['product','worn']:
     for mat in mats:
      result=p.evaluate('''async ([heel,material,camera])=>{const d=SweetShoe.cleanDesign({heel,material,color:'blue',pattern:'none',strap:'none',decoration:'none',charm:'none'});const c=camera==='product'?await SweetShoe.Shoe2D.composite(d):await SweetShoe.__materialNative(d,{sock:'none',color:'cream'});return c.toDataURL()}''',[b,mat,camera])
      raw=base64.b64decode(result.split(',')[1]);im=Image.open(io.BytesIO(raw)).convert('RGBA');path=OUT/f'{b}-{camera}-{mat}-{phase}.png';path.write_bytes(raw)
      rows.append(dict(base=b,camera=camera,material=mat,rendered=True,coverage='pending independent mask scan'))
      if phase=='after' and mat in ['mesh','glitter']:
       old=Image.open(OUT/f'{b}-{camera}-{mat}-before.png').convert('RGBA')
       if camera=='product':boxes={'toe':(90,360,330,540),'trim':(310,260,700,455),'heel':(740,70,935,455)}
       else:
        w,h=im.size;boxes={'toe':(0,int(h*.72),int(w*.55),h),'trim':(int(w*.2),int(h*.60),int(w*.85),int(h*.92)),'heel':(int(w*.68),int(h*.60),w,h)}
       for label,box in boxes.items():
        cuts=[a.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST) for a in [old,im]];sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+24),'#e8ddd4');draw=ImageDraw.Draw(sheet);draw.text((8,6),f'{b} {camera} {mat} {label} BEFORE / AFTER 3x',fill='#302838')
        for i,cut in enumerate(cuts):sheet.paste(cut,(i*cut.width,24),cut)
        sheet.save(OUT/f'{b}-{camera}-{mat}-{label}-3x.png')
    print('PASS',phase,b,len(mats),'materials, both cameras',flush=True)
   for w,h in [(1920,1080),(390,844)]:
    p.set_viewport_size(dict(width=w,height=h));p.evaluate("document.body.style.cssText='margin:0;background:#e7dfd7';document.body.innerHTML='<canvas id=stage></canvas>'")
    for b in bases:
     for mat in ['mesh','glitter']:
      r=p.evaluate('''async ([heel,material,w,h])=>{const c=document.querySelector('#stage');c.width=w;c.height=h;await SweetShoe.Fitting2D.render(c,{heel,material,color:'blue',pattern:'none',strap:'none',decoration:'none',charm:'none'},{sock:'none',color:'cream'},'salon',true);return {...c.dataset}}''',[b,mat,w,h]);assert r.get('renderer')=='worn-sprite',r
      if phase=='after' and b in ['maryjane','slingback','loafer']:p.screenshot(path=str(OUT/f'ui-{b}-{mat}-{w}.png'))
    print('PASS',phase,'projected',w,h,flush=True)
   assert not errors and not assets,(errors,assets)
   info=p.evaluate('({product:SweetShoe.Shoe2D.info(),worn:SweetShoe.WornSprites.info()})');assert info['product']['cacheEntries']<=8 and info['worn']['cacheEntries']<=8
   if '--loafer-only' in sys.argv:
    prior=json.loads((OUT/f'{phase}-browser.json').read_text());rows=[r for r in prior['cases'] if r['base']!='loafer']+rows
   (OUT/f'{phase}-browser.json').write_text(json.dumps(dict(status='PASS',cases=rows,projections=80,page_errors=errors,asset_errors=assets,cache=info),indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
