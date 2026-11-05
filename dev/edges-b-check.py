#!/usr/bin/env python3
"""Reproduce edges-b Chromium comparisons, protected-base and real UI checks."""
import base64,functools,http.server,io,json,threading,sys,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-b'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
sys.path.insert(0,str(ROOT/'dev'));from importlib import import_module
gap=import_module('maryjane-gap-check')
RENDER=gap.RENDER.replace("strap:'none'","strap:v.strap||'none'")
BASES=['platform','bootie','pearlpump','crystalpump','studpump']
CASES=[dict(color='blue',pattern='stars',sock='lace',colour='cream'),dict(color='pink',pattern='none',sock='thigh',colour='black'),dict(color='blue',pattern='flowers',sock='frill',colour='black')]
def render(page,v):
 r=page.evaluate(RENDER,v);return Image.open(io.BytesIO(base64.b64decode(r['png']))).convert('RGBA'),r['meta']
def main():
 OUT.mkdir(parents=True,exist_ok=True);errors=[];records=[];preserved=[]
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page(old=False,w=1920,h=1080):
    p=browser.new_page(viewport=dict(width=w,height=h),device_scale_factor=1,reduced_motion='reduce');p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
    p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=(ROOT/'js/worn-sprites.js').read_bytes().replace(b'A.WornSprites={has',b'A.__edgeTest={load,tinted};A.WornSprites={has'),content_type='application/javascript'))
    if old:
     p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=(OUT/'before-worn-sprites.js').read_bytes(),content_type='application/javascript'))
     def asset(r):
      name=Path(r.request.url.split('?')[0]).stem;backup=OUT/f'{name}-before.webp'
      if backup.exists():r.fulfill(body=backup.read_bytes(),content_type='image/webp')
      else:r.continue_()
     p.route('**/assets/worn/*.webp*',asset)
    p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');p.wait_for_function('!!globalThis.SweetShoe?.WornSprites');return p
   old,new=page(True),page()
   if '--finish' not in sys.argv:
    contacts=[]
    
    for base in BASES:
     # Source boxes are expressed in each last's own registered pixel frame.
     width=Image.open(ROOT/f'assets/worn/{base}.webp').width
     boxes={'front-opening-trim':(int(width*.22),535 if base=='bootie' else 590,width,670 if base=='bootie' else 835),'rear-opening-trim':(0,530 if base=='bootie' else 570,int(width*.67),650 if base=='bootie' else 810),'front-sole':(int(width*.3),750,width,850),'front-strap':(int(width*.4),520,width,720),'rear-strap':(0,520,int(width*.7),720)}
     for n,c in enumerate(CASES):
      for strap in ['none','thin']:
       v=dict(c,heel=base,strap=strap);a,am=render(old,v);z,zm=render(new,v);assert am['pairLayout']==zm['pairLayout'],v
       prefix=f'{base}-case-{n}'+('-strap' if strap!='none' else '')
       a.save(OUT/f'{prefix}-before.png');z.save(OUT/f'{prefix}-after.png')
       for label,box in boxes.items():
        cuts=[gap.crop(im,meta,box) for im,meta in [(a,am),(z,zm)]];cuts=[im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST) for im in cuts]
        sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+28),'#e8ddd4');d=ImageDraw.Draw(sheet);d.text((5,7),f'{prefix} {label} | BEFORE / AFTER 3x',fill='#302838')
        for k,im in enumerate(cuts):sheet.paste(im,(k*im.width,28),im)
        sheet.save(OUT/f'{prefix}-{label}-3x.png')
       if strap=='none':
        cuts=[gap.crop(im,meta,(0,530 if base=='bootie' else 570,width,850)) for im,meta in [(a,am),(z,zm)]]
        row=Image.new('RGB',(1000,230),'#e8ddd4');d=ImageDraw.Draw(row);d.text((5,5),f'{base} {c} | BEFORE / AFTER',fill='#302838')
        for k,im in enumerate(cuts):
         im.thumbnail((490,200));row.paste(im,(k*500,25),im)
        contacts.append(row)
       records.append(v)
     print('PASS native crops',base,flush=True)
    contact=Image.new('RGB',(1000,len(contacts)*230),'#e8ddd4')
    for i,row in enumerate(contacts):contact.paste(row,(0,i*230))
    contact.save(OUT/'contact.jpg',quality=94)
    if '--preview' in sys.argv:browser.close();return
    for base in ['flat','block','kitten','stiletto6','wedge','stiletto9','maryjane','ballet','slingback','loafer','bowsling','bowmule','pearlheel','luciteheel','crystalsandal']:
     for sock in ['none','frill','lace','knee','thigh']:
      v=dict(heel=base,sock=sock,colour='black',color='blue',pattern='stars');a,am=render(old,v);z,zm=render(new,v)
      assert a.tobytes()==z.tobytes(),v;assert am['pairLayout']==zm['pairLayout'];preserved.append(v)
    print('PASS 75 other-base byte-exact comparisons',flush=True)
    # Exercise all five sock colours and styles at native source resolution.
    matrix=[]
    for base in BASES:
     result=new.evaluate("""async base=>{const rows=[];
      for(const sock of ['none','frill','lace','knee','thigh'])for(const colour of ['cream','white','pink','mint','black']){
       const d={heel:base,color:'blue',material:'satin',pattern:'flowers',strap:'thin',decoration:'none',charm:'none'};
       const c=await SweetShoe.__edgeTest.tinted(d,{sock,color:colour});
       rows.push({base,sock,colour,width:c.width,height:c.height});}return rows;}""",base)
     assert len(result)==25;matrix.extend(result)
    print('PASS 125 native sock-colour/style cases with optional straps',flush=True)
   else:
    log=(OUT/'browser.log').read_text()
    assert 'PASS 75 other-base byte-exact comparisons' in log and 'PASS 125 native sock-colour/style cases' in log
    guard=json.loads((OUT/'protected-checks.json').read_text())
    for row in guard['changed']:assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['sha256']
    assert hashlib.sha256((ROOT/'js/worn-sprites.js').read_bytes()).hexdigest()==json.loads((OUT/'checks.json').read_text())['renderer_sha256']
    records=[dict(c,heel=b,strap=t) for b in BASES for c in CASES for t in ['none','thin']]
    preserved=[dict(heel=b,sock=t) for b in ['flat','block','kitten','stiletto6','wedge','stiletto9','maryjane','ballet','slingback','loafer','bowsling','bowmule','pearlheel','luciteheel','crystalsandal'] for t in ['none','frill','lace','knee','thigh']]
    matrix=[dict(base=b,sock=t,colour=c) for b in BASES for t in ['none','frill','lace','knee','thigh'] for c in ['cream','white','pink','mint','black']]
   # Real Collection -> salon, all five bases in one seeded gallery per viewport.
   ui=[]
   for w,h in [(390,844),(1920,1080)]:
    p=browser.new_page(viewport=dict(width=w,height=h),device_scale_factor=1,reduced_motion='reduce');p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
    seed=json.loads(json.dumps(q.SEED));template=seed['gallery'][0];seed['gallery']=[]
    for base in BASES:
     item=json.loads(json.dumps(template));item['design']=dict(heel=base,color='blue',material='satin',pattern='flowers',strap='thin',decoration='none',charm='none');item['fitting']=dict(sock='frill',color='black');seed['gallery'].append(item)
    q.seed_page(p,seed);p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');q.enter_atelier(p)
    for index,base in enumerate(BASES):
     if not p.locator('[data-gallery-select]').count():p.locator('[data-nav=collection]').click()
     p.locator(f'[data-gallery-select="{index}"]').click();p.locator(f'[data-try-on="{index}"]').click()
     def ready(sock,colour):p.wait_for_function("v=>{const d=document.querySelector('.fitting2d-canvas')?.dataset;return d?.renderer==='worn-sprite'&&d.heel===v[0]&&d.sock===v[1]&&d.sockColor===v[2]}",arg=[base,sock,colour])
     ready('frill','black');p.screenshot(path=str(OUT/f'ui-{base}-{w}x{h}.png'))
     p.locator('[data-fitting-color=cream]').click();ready('frill','cream');p.locator('[data-fitting-sock=lace]').click();ready('lace','cream')
     p.locator('[data-fitting-sock=thigh]').click();ready('thigh','cream');p.locator('[data-fitting-color=black]').click();ready('thigh','black');p.keyboard.press('Escape');ui.append(dict(base=base,viewport=[w,h],controls=True))
    p.reload(wait_until='domcontentloaded');q.enter_atelier(p);p.locator('[data-nav=collection]').click();p.locator('[data-gallery-select="4"]').click();p.locator('[data-try-on="4"]').click();ready('thigh','black');p.close()
    print('PASS real UI and saved reload',w,h,flush=True)
   for w,h in [(390,844),(1920,1080)]:
    new.set_viewport_size(dict(width=w,height=h))
    for base in BASES:
     for i,c in enumerate(CASES):
      im,_=render(new,dict(c,heel=base,w=w,h=h));im.save(OUT/f'fitting-{base}-{i}-{w}x{h}.png')
   cache=new.evaluate('SweetShoe.WornSprites.info()');assert cache['cacheEntries']<=8 and cache['sourceEntries']<=8 and cache['pending']==0,cache;assert not errors,errors
   (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',resumed_ui='--finish' in sys.argv,matrix=matrix,crops=records,other_bases_exact=preserved,ui=ui,cache=cache,page_errors=errors),indent=2)+'\n');browser.close();print('PASS requested desktop/phone projections, bounded caches and zero page errors',flush=True)
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
