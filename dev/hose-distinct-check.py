#!/usr/bin/env python3
"""Offline Chromium hosiery acceptance. All evidence stays under dev/qa-out."""
import base64,copy,functools,http.server,io,json,sys,threading,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/hose-distinct';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
BASES=['flat','maryjane','stiletto9','block','bootie']
SOCKS=['none','frill','lace','sheer','knee','thigh','blacksheer','pantyhose','opaque','fishnet']
ALL=list(json.loads((ROOT/'dev/hose-landmarks.json').read_text()));ALL=BASES+[b for b in ALL if not b.startswith('_') and b not in BASES]
JS="""async ([heel,sock,skin,colour])=>{const d=SweetShoe.cleanDesign({heel,color:'pink',material:'satin',pattern:'flowers',strap:'none',decoration:'none',charm:'none'}),o=SweetShoe.cleanFittingOptions({sock,color:colour,...(skin?{skin}:{})});const c=await SweetShoe.__hoseNative(d,o);return c.toDataURL()}"""
def frame(p,b,s,skin=None,colour=None):
 url=p.evaluate(JS,[b,s,skin,colour or ('black' if s in ['sheer','blacksheer','fishnet'] else 'cream')]);return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA')
def main():
 errors=[];assets=[];records=[];ui=[];frames={}
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   p=browser.new_page(viewport={'width':1920,'height':1080},reduced_motion='reduce')
   p.set_default_timeout(120000)
   p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
   p.add_init_script("window.CrazyGames={SDK:{environment:'disabled',init:async()=>{}}}")
   source=(ROOT/'js/worn-sprites.js').read_text().replace('A.WornSprites={','A.__hoseNative=tinted;A.WornSprites={')
   p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=source,content_type='application/javascript'))
   p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:assets.append(r.url) if r.status>=400 else None)
   seed=copy.deepcopy(q.SEED);template=copy.deepcopy(seed['gallery'][0]);seed['gallery']=[]
   for b in BASES:
    item=copy.deepcopy(template);item['design']=dict(heel=b,color='pink',material='satin',pattern='flowers',strap='none',decoration='none',charm='none');item['fitting']=dict(sock='none',color='cream');seed['gallery'].append(item)
   q.seed_page(p,seed)
   harness='<script src="/js/data.js"></script><script src="/js/studio-core.js"></script><script src="/js/showcase.js"></script><script src="/js/shoe-renderer.js"></script><script src="/js/accessory-renderer.js"></script><script src="/js/shoe2d.js"></script><script src="/js/worn-sprites.js"></script><script src="/js/fitting2d.js"></script>'
   p.route('**/__hose',lambda r:r.fulfill(body=harness,content_type='text/html'))
   p.goto(f'http://127.0.0.1:{server.server_port}/__hose',wait_until='domcontentloaded')
   p.wait_for_function('!!SweetShoe.__hoseNative')
   for b in (ALL if '--all-bases' in sys.argv else BASES):
    for tone,skin in [('fair',None),('dark','#8a5a3c')]:
     styles=SOCKS if b in BASES else ['sheer','pantyhose','blacksheer','knee','thigh','opaque']
     for s in styles:
      im=Image.open(OUT/f'{b}-{tone}-{s}.png').convert('RGBA') if '--resume' in sys.argv else frame(p,b,s,skin);frames[b,tone,s]=im
      if b in BASES:im.save(OUT/f'{b}-{tone}-{s}.png')
     if b in BASES:
      bare=frames[b,tone,'none'];top=(0,0,bare.width,22)
      for s in ['knee','thigh']:
       delta=ImageStat.Stat(ImageChops.difference(bare.crop(top).convert('RGB'),frames[b,tone,s].crop(top).convert('RGB'))).mean
       assert max(delta)<.8,(b,tone,s,'bare skin above',delta)
      signatures={hashlib.sha256(frames[b,tone,s].tobytes()).hexdigest() for s in styles};assert len(signatures)==10,(b,tone,'identical styles')
     records.append(dict(base=b,tone=tone,styles=styles));print('PASS native',b,tone,flush=True)
   for b in BASES:
    for tone in ['fair','dark']:
     row=Image.new('RGB',(260*10,470),'#e7dfd7');d=ImageDraw.Draw(row)
     for i,s in enumerate(SOCKS):
      im=frames[b,tone,s].copy();im.thumbnail((250,430));row.paste(im,(i*260,30),im);d.text((i*260+5,8),f'{b} {tone} {s}',fill='#302438')
     row.save(OUT/f'{b}-{tone}-row.jpg',quality=95)
     for group,styles in [('tops',['knee','thigh','opaque']),('sheer',['sheer','pantyhose','blacksheer'])]:
      sheet=Image.new('RGB',(660*3,690),'#e7dfd7');d=ImageDraw.Draw(sheet)
      for i,s in enumerate(styles):
       im=frames[b,tone,s].crop((0,0,220,220)).resize((660,660),Image.Resampling.NEAREST);sheet.paste(im,(i*660,30),im);d.text((i*660+5,8),f'{b} {tone} {s} knee 3x',fill='#302438')
      sheet.save(OUT/f'{b}-{tone}-{group}-3x.png')
   contact=Image.new('RGB',(2600,470*10),'#e7dfd7')
   for i,(b,tone) in enumerate((b,t) for b in BASES for t in ['fair','dark']):contact.paste(Image.open(OUT/f'{b}-{tone}-row.jpg'),(0,i*470))
   contact.save(OUT/'contact.jpg',quality=93)
   (OUT/'native-acceptance.json').write_text(json.dumps(dict(status='PASS',native=records),indent=2)+'\n')
   for w,h in [(1920,1080),(390,844)]:
    p.set_viewport_size(dict(width=w,height=h))
    p.evaluate("document.body.style.cssText='margin:0;background:#e7dfd7';document.body.innerHTML='<canvas id=\"stage\"></canvas>'")
    for b in BASES:
     for sock in ['knee','thigh','opaque','sheer','pantyhose','blacksheer']:
      result=p.evaluate("""async ([heel,sock,w,h])=>{const c=document.querySelector('#stage');c.width=w;c.height=h;await SweetShoe.Fitting2D.render(c,{heel,color:'pink',material:'satin',pattern:'flowers',strap:'none',decoration:'none',charm:'none'},{sock,color:['sheer','blacksheer'].includes(sock)?'black':'cream'},'salon',true);return {...c.dataset}}""",[b,sock,w,h])
      assert result['renderer']=='worn-sprite' and result['sock']==sock,result
      p.screenshot(path=str(OUT/f'ui-{b}-{sock}-{w}.png'))
     ui.append(dict(base=b,viewport=[w,h],styles=6,surface='Fitting2D projected canvas'));print('PASS projected',b,w,flush=True)
   # Read-restricted draw-only fallback, including dark customer skin.
   p.evaluate("()=>{CanvasRenderingContext2D.prototype.getImageData=()=>{throw Error('read restricted')}}")
   fallback=[]
   for b in BASES:
    for s in ['knee','thigh','sheer','pantyhose','blacksheer']:
     result=p.evaluate("""async ([heel,sock])=>{const c=document.createElement('canvas');c.width=1220;c.height=1000;await SweetShoe.Fitting2D.render(c,{heel,color:'pink',pattern:'flowers'},{sock,color:'black',skin:'#8a5a3c'},'salon',true);return {...c.dataset}}""",[b,s]);assert result['renderer']=='worn-sprite',result;fallback.append([b,s])
   assert p.evaluate('SweetShoe.WornSprites.info().cacheEntries<=8&&SweetShoe.WornSprites.info().sourceEntries<=8')
   browser.close()
  assert not errors and not assets,(errors,assets)
  (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',native=records,ui=ui,read_restricted_cases=fallback,page_errors=errors,asset_errors=assets),indent=2)+'\n')
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
