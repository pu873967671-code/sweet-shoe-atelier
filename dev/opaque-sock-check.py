#!/usr/bin/env python3
"""Opaque cloth acceptance in real Chromium; all evidence is development-only."""
import base64, functools, hashlib, http.server, io, json, re, subprocess, sys, threading
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/opaque-sock'
sys.path.insert(0,str(ROOT/'qa'))
import screenshot as q
BASELINE=(OUT/'before-worn-sprites.js').read_bytes() if (OUT/'before-worn-sprites.js').exists() else subprocess.check_output(['git','show','HEAD:js/worn-sprites.js'],cwd=ROOT)
REFS=json.loads(re.search(r'const SPRITES=(.*?);',(ROOT/'js/worn-sprites.js').read_text()).group(1))
HEELS=[h for h in REFS if '_' not in h]
SAMPLE=['flat','stiletto9','block','bootie','slingback','maryjane']
STATES=[('thigh','black'),('knee','black'),('frill','black'),('lace','black'),('thigh','cream'),('knee','pink')]
RENDER='''async v=>{
 const c=document.createElement('canvas');c.width=v.w||1220;c.height=v.h||1000;
 await SweetShoe.Fitting2D.render(c,{heel:v.heel,color:'pink',material:'satin',pattern:'none',strap:'none',decoration:'none',charm:'none'},
 {sock:v.sock,color:v.colour||'black',...(v.skin?{skin:v.skin}:{})},'salon',true);
 if(c.dataset.renderer!=='worn-sprite'||c.dataset.fallback!=='false')throw Error('Unexpected renderer '+JSON.stringify(c.dataset));
 const room=new Image();room.src='assets/scenes/fixed_salon.webp';await room.decode();
 const g=SweetShoe.Showcase.project('salon',c.width,c.height,true),b=g.background;
 const out=document.createElement('canvas');out.width=c.width;out.height=c.height;
 const p=out.getContext('2d');p.drawImage(room,b.x,b.y,b.width,b.height);p.drawImage(c,0,0);
 return {raw:c.toDataURL().split(',')[1],png:out.toDataURL().split(',')[1],meta:{...c.dataset}};
}'''
def render(p,case):
 r=p.evaluate(RENDER,case)
 decode=lambda s:Image.open(io.BytesIO(base64.b64decode(s))).convert('RGBA')
 return decode(r['raw']),decode(r['png']),r['meta']
def same(a,b):return a.tobytes()==b.tobytes()
def allowed(case,meta):
 h=case['heel'];sock=case['sock'];variant=h+'_'+sock if sock in ['frill','lace'] else h
 path=ROOT/f'assets/worn/{variant}_sock.webp' if sock in ['frill','lace'] else ROOT/f'assets/worn/{h}_legs.webp'
 mask=Image.open(path).getchannel('A');g=json.loads(meta['pairLayout'])
 out=Image.new('L',(1220,1000));out.paste(mask,(round(g['x']),round(g['y'])))
 return out.point(lambda a:255 if a else 0).filter(ImageFilter.MaxFilter(5))
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'before-worn-sprites.js').write_bytes(BASELINE)
 assets={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets/worn').rglob('*.webp')}
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 errors=[];checks=[]
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page(old=False,restricted=False):
    p=browser.new_page(viewport={'width':1336,'height':790},device_scale_factor=1,reduced_motion='reduce')
    p.on('pageerror',lambda e:errors.append(str(e)))
    p.route('https://**/*',lambda r:r.abort())
    if old:p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=BASELINE,content_type='application/javascript'))
    seed=json.loads(json.dumps(q.SEED));seed['gallery'][0]['design']={'heel':'flat','color':'pink','material':'satin','pattern':'none','strap':'none','decoration':'none','charm':'none'};seed['gallery'][0]['fitting']={'sock':'thigh','color':'black'}
    q.seed_page(p,seed)
    p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded')
    p.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
    if restricted:p.evaluate("()=>{CanvasRenderingContext2D.prototype.getImageData=function(){throw new DOMException('Restricted','SecurityError')};}")
    return p
   old,new=page(True),page()
   sheet=Image.new('RGB',(2160,12*600+40),'#eee7df');pen=ImageDraw.Draw(sheet)
   pen.text((12,10),'Opaque sock volume | salon | BEFORE left / AFTER right in each pair',fill='#302838')
   finishing='--finish' in sys.argv
   if finishing:
    checkpoint=json.loads((OUT/'native-acceptance.json').read_text())
    assert checkpoint['renderer_sha256']==hashlib.sha256((ROOT/'js/worn-sprites.js').read_bytes()).hexdigest()
    checks=checkpoint['cases']
   for row,heel in enumerate([] if finishing else SAMPLE):
    for col,(sock,colour) in enumerate(STATES):
     case=dict(heel=heel,sock=sock,colour=colour)
     before,bscene,meta=render(old,case);after,ascene,_=render(new,case)
     assert not same(before,after),(case,'no shading')
     diff=ImageChops.difference(before,after).convert('RGB');bands=diff.split();changed=ImageChops.lighter(ImageChops.lighter(bands[0],bands[1]),bands[2])
     assert ImageChops.multiply(changed,ImageChops.invert(allowed(case,meta))).getbbox() is None,(case,'outside sock changed')
     g=json.loads(meta['pairLayout']);crop=(round(g['x']-5),0,round(g['x']+g['w']+5),round(g['y']+g['h']+12))
     tile=row*6+col;sheet_row=tile//3;sheet_col=tile%3
     for v,im in enumerate([bscene,ascene]):
      im.save(OUT/f'{heel}-{sock}-{colour}-{"before" if v==0 else "after"}.png')
      cut=im.crop(crop);cut.thumbnail((350,540))
      x=sheet_col*720+v*360+(360-cut.width)//2;y=40+sheet_row*600+42
      sheet.paste(cut,(x,y))
     pen.text((sheet_col*720+5,40+sheet_row*600+4),f'{heel} {sock} {colour}',fill='#302838')
     pen.text((sheet_col*720+8,40+sheet_row*600+20),'BEFORE                                                     AFTER',fill='#302838')
     checks.append({**case,'outside_sock_exact':True})
    print('PASS contact',heel,flush=True)
   if not finishing:sheet.save(OUT/'contact.jpg',quality=95)
   # All twenty bases, all five opaque styles. Also lock every unaffected look.
   for heel in ([] if finishing else HEELS):
    for sock in ['opaque','thigh','knee','frill','lace']:
     case=dict(heel=heel,sock=sock)
     a,_,meta=render(old,case);b,_,_=render(new,case)
     assert not same(a,b),(case,'no volume')
     diff=ImageChops.difference(a,b).convert('RGB');r,g,bb=diff.split();diff=ImageChops.lighter(ImageChops.lighter(r,g),bb)
     assert ImageChops.multiply(diff,ImageChops.invert(allowed(case,meta))).getbbox() is None,(case,'outside sock')
    for sock in ['none','sheer','blacksheer','pantyhose','fishnet']:
     case=dict(heel=heel,sock=sock,skin='#8a5a3c')
     a,_,_=render(old,case);b,_,_=render(new,case)
     assert same(a,b),(case,'unaffected look changed')
    print('PASS all styles / preserved looks',heel,flush=True)
   if not finishing:(OUT/'native-acceptance.json').write_text(json.dumps(dict(status='PASS',renderer_sha256=hashlib.sha256((ROOT/'js/worn-sprites.js').read_bytes()).hexdigest(),cases=checks,opaque_cases=100,unchanged_cases=100),indent=2)+'\n')
   restricted_old,restricted=page(True,True),page(False,True)
   for heel in SAMPLE:
    for sock in ['opaque','frill','lace','knee','thigh']:
     case=dict(heel=heel,sock=sock)
     a,_,_=render(restricted_old,case);b,_,_=render(restricted,case)
     assert same(a,b),(case,'read-failure fallback changed')
   # Skin remains visible and independently tintable above the short sock.
   for sock in ['frill','lace']:
    a,_,_=render(new,dict(heel='flat',sock=sock))
    b,_,_=render(new,dict(heel='flat',sock=sock,skin='#8a5a3c'))
    assert not same(a,b),'skin tone stopped working'
   # The complete required matrix at both viewport projections, plus actual UI.
   for w,h in [(1920,1080),(390,844)]:
    new.set_viewport_size(dict(width=w,height=h))
    for heel in SAMPLE:
     for sock,colour in STATES:
      _,scene,_=render(new,dict(heel=heel,sock=sock,colour=colour,w=w,h=h))
      scene.save(OUT/f'{heel}-{sock}-{colour}-{w}x{h}.png')
    if new.locator('[data-action=welcome]').count():q.enter_atelier(new)
    new.locator('[data-nav=collection]').click();new.locator('[data-try-on="0"]').click()
    new.wait_for_function("document.querySelector('.fitting2d-canvas')?.dataset.renderer==='worn-sprite'")
    new.wait_for_function("document.querySelector('.fitting2d-canvas')?.dataset.heel==='flat'&&document.querySelector('.fitting2d-canvas')?.dataset.sock==='thigh'&&document.querySelector('.fitting2d-canvas')?.dataset.sockColor==='black'")
    new.screenshot(path=str(OUT/f'ui-{w}x{h}.png'))
    new.locator('[data-runway-back]').click()
    new.locator('[data-action=close]').click()
   info=new.evaluate('SweetShoe.WornSprites.info()');assert info['cacheEntries']<=8 and info['sourceEntries']<=8 and info['pending']==0,info
   browser.close()
  assert not errors,errors
  assert assets=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets/worn').rglob('*.webp')},'assets changed'
  report=dict(status='PASS',comparison_cases=checks,all_bases_opaque=100,unaffected_looks_exact=100,read_failure_exact=30,viewport_cases=72,skin_tone='PASS',cache=info,errors=errors,protected_worn_assets=len(assets))
  (OUT/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
  print('PASS opaque sock acceptance',flush=True)
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
