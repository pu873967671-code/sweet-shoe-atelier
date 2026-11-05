#!/usr/bin/env python3
"""Local Chromium product-camera survey and before/after evidence."""
import base64, functools, hashlib, http.server, io, json, sys, threading
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dev/qa-out/edges-p'
BASES=['flat','block','kitten','stiletto6','stiletto9','wedge','maryjane','ballet','slingback','loafer','platform','bootie','pearlpump','bowsling','crystalpump','studpump','bowmule','pearlheel','luciteheel','crystalsandal']
CASES=[dict(color='blue',material='satin',pattern='stars'),dict(color='pink',material='satin',pattern='none'),dict(color='blue',material='satin',pattern='flowers')]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 before='--before' in sys.argv
 phase='before' if before else 'after'
 if before:
  backup=OUT/'baseline';backup.mkdir(exist_ok=True)
  for b in BASES:
   path=ROOT/f'assets/shoe2d/{b}_upper.webp'
   if not (backup/path.name).exists():
    import subprocess
    (backup/path.name).write_bytes(subprocess.check_output(['git','show','b5f06078c3853cb45658737a0570768dd2346cec:'+str(path.relative_to(ROOT))],cwd=ROOT))
  protected={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets').rglob('*') if p.is_file()}
  for b in BASES:
   protected[f'assets/shoe2d/{b}_upper.webp']=hashlib.sha256((backup/f'{b}_upper.webp').read_bytes()).hexdigest()
  if not (OUT/'protected-before.json').exists():(OUT/'protected-before.json').write_text(json.dumps(protected,indent=2)+'\n')
 errors=[];bad=[];records=[]
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   page=browser.new_page(viewport=dict(width=1920,height=1080))
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('response',lambda r:bad.append(r.url) if r.status>=400 else None)
   page.route('https://**/*',lambda r:r.abort())
   if before:
    def pinned_mask(r):
     name=Path(r.request.url.split('?')[0]).name
     r.fulfill(body=(OUT/'baseline'/name).read_bytes(),content_type='image/webp')
    page.route('**/assets/shoe2d/*_upper.webp*',pinned_mask)
   page.route('**/__edges_p',lambda r:r.fulfill(content_type='text/html',body='<script src="/js/data.js"></script><script src="/js/accessory-renderer.js"></script><script src="/js/shoe2d.js"></script>'))
   page.goto(f'http://127.0.0.1:{server.server_port}/__edges_p');page.wait_for_function('!!globalThis.SweetShoe?.Shoe2D')
   for b in BASES:
    if '--crystalsandal-only' in sys.argv and b!='crystalsandal':continue
    for n,c in enumerate(CASES):
     d=dict(c,heel=b,strap='none',decoration='none',charm='none')
     png=page.evaluate('async d=>(await SweetShoe.Shoe2D.composite(d)).toDataURL()',d)
     im=Image.open(io.BytesIO(base64.b64decode(png.split(',')[1]))).convert('RGBA');im.save(OUT/f'{b}-{n}-{phase}.png');records.append(d)
     if not before:
      old=Image.open(OUT/f'{b}-{n}-before.png').convert('RGBA')
      for label,box in [('opening',(300,170,925,425)),('sole',(90,395,935,550))]:
       cuts=[x.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST) for x in [old,im]]
       sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+24),'#e8ddd4');dr=ImageDraw.Draw(sheet);dr.text((6,6),f'{b} case {n} {label} BEFORE / AFTER 3x',fill='#302838')
       for k,cut in enumerate(cuts):sheet.paste(cut,(k*cut.width,24),cut)
       sheet.save(OUT/f'{b}-{n}-{label}-3x.png')
    # Extra strap evidence, independently rendered in this product camera.
    for strap in ['thin','cross']:
     d=dict(CASES[0],heel=b,strap=strap,decoration='none',charm='none')
     png=page.evaluate('async d=>(await SweetShoe.Shoe2D.composite(d)).toDataURL()',d)
     Image.open(io.BytesIO(base64.b64decode(png.split(',')[1]))).save(OUT/f'{b}-{strap}-{phase}.png')
    print('PASS product',phase,b,flush=True)
   for group in range(4):
    sheet=Image.new('RGB',(1500,5*330),'#e8ddd4');dr=ImageDraw.Draw(sheet)
    for row,b in enumerate(BASES[group*5:group*5+5]):
     for n in range(3):
      im=Image.open(OUT/f'{b}-{n}-{phase}.png').convert('RGBA');im.thumbnail((500,312));sheet.paste(im,(n*500,row*330+18),im);dr.text((n*500+8,row*330+3),f'{b} case {n} {phase}',fill='#302838')
    sheet.save(OUT/f'survey-{group}-{phase}.jpg',quality=95)
   info=page.evaluate('SweetShoe.Shoe2D.info()');assert info['cacheEntries']<=8 and info['pendingComposites']==0
   assert not errors and not bad,(errors,bad)
   (OUT/f'{phase}-browser.json').write_text(json.dumps(dict(status='PASS',cases=records,page_errors=errors,asset_errors=bad,cache=info),indent=2)+'\n')
   browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
