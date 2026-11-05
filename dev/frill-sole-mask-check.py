#!/usr/bin/env python3
"""Offline Chromium matrix, frozen source-space sole/gap ownership probes.

The forbidden regions are frozen from the pre-fix paintings, before rendering.
Flags count actual nontransparent composite pixels there, including shoe dye,
cloth, and customer skin. This avoids confusing room/contact shadows with yarn.
"""
import base64,csv,functools,http.server,io,json,runpy,subprocess,threading
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];M=runpy.run_path(str(ROOT/'dev/refine-frill-sole-mask.py'));OUT=M['OUT'];REFS=M['REFS'];BASES=list(M['BANDS'])
SOCKS=['none','frill','lace','sheer','knee','thigh','blacksheer','pantyhose','opaque','fishnet']
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
JS="""async([heel,sock,skin])=>{const d=SweetShoe.cleanDesign({heel,color:'pink',material:'satin',pattern:'none',strap:'none',decoration:'none',charm:'none'}),o=SweetShoe.cleanFittingOptions({sock,color:'cream',skin});return (await SweetShoe.__soleNative(d,o)).toDataURL()}"""
def decode(url):return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA')
def main():
 regions={};originals={};shoes={};rows=[];errors=[];bad=[];negative=[]
 for name in REFS:
  src=M['original'](name);regions[name]=M['region'](name,src);originals[name]=src;shoes[name]=M['protected_shoes'](name,src)
  previous=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'63777606:assets/worn/{name}_clear.webp'],cwd=ROOT))).getchannel('A')
  negative.append(dict(sprite=name,previous_shoe_pixels_removed=int(np.sum((np.array(previous)>0)&shoes[name]&(np.array(src)[:,:,3]>0)))))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 harness=''.join(f'<script src="/js/{n}.js"></script>' for n in ['data','studio-core','showcase','shoe-renderer','accessory-renderer','shoe2d','worn-sprites','fitting2d'])
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   source=(ROOT/'js/worn-sprites.js').read_text().replace('A.WornSprites={','A.__soleNative=tinted;A.WornSprites={')
   pages=[]
   for old in [True,False]:
    p=browser.new_page(viewport=dict(width=1920,height=1080));p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:bad.append(r.url) if r.status>=400 else None);p.route('https://**/*',lambda r:r.fulfill(body=''))
    p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=source,content_type='application/javascript'))
    p.route('**/__sole',lambda r:r.fulfill(body=harness,content_type='text/html'))
    if old:
     def route(r):
      path=r.request.url.split('/assets/worn/')[1].split('?')[0]
      if path.endswith('_clear.webp'):
       name=path.removesuffix('_clear.webp');buf=io.BytesIO();Image.new('RGBA',originals[name].size).save(buf,format='PNG');r.fulfill(body=buf.getvalue(),content_type='image/png')
      else:r.continue_()
     p.route('**/assets/worn/*',route)
    p.goto(f'http://127.0.0.1:{server.server_port}/__sole');p.wait_for_function('!!SweetShoe.__soleNative');pages.append(p)
   old,new=pages
   contact=Image.new('RGB',(1200,180*len(BASES)),'#b9e5dc');pen=ImageDraw.Draw(contact)
   for bi,b in enumerate(BASES):
    for sock in SOCKS:
     name=b+('_'+sock if sock in ['frill','lace'] else '');fix=regions[name]
     for tone,skin in [('fair','#f4cfb5'),('dark','#8a5a3c')]:
      after=decode(new.evaluate(JS,[b,sock,skin]));before=decode(old.evaluate(JS,[b,sock,skin]));aa=np.array(after);bb=np.array(before)
      flags=int(np.sum((aa[:,:,3]>0)&fix));beforeflags=int(np.sum((bb[:,:,3]>0)&fix));assert flags==0,(b,sock,tone,flags)
      shoe_changed=int(np.sum(np.any(aa!=bb,axis=2)&shoes[name]));shoe_removed=int(np.sum((aa[:,:,3]<bb[:,:,3])&shoes[name]))
      assert shoe_changed==0 and shoe_removed==0,(b,sock,tone,'shoe pixels changed',shoe_changed,shoe_removed)
      assert np.array_equal(aa[~fix],bb[~fix]),(b,sock,tone,'outside region changed')
      if b=='flat':
       # Independent reviewed front-collar fixture, not computed from fix/shoe masks.
       assert np.array_equal(aa[774:791,208:241],bb[774:791,208:241]),(sock,tone,'front collar/trim notch')
      rows.append(dict(base=b,sock=sock,skin=tone,before=beforeflags,after=flags,shoe_pixels_changed=shoe_changed,shoe_pixels_removed=shoe_removed))
      if sock in ['frill','lace'] and tone=='fair':
       # Both rear inter-shoe gap and front outsole included, exact 3x.
       y0=M['REAR'][b][2]-10;box=(0,y0,after.width,after.height)
       cuts=[im.crop(box).resize((im.width*3,(im.height-y0)*3),Image.Resampling.NEAREST) for im in [before,after]]
       sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+25),'#b9e5dc');d=ImageDraw.Draw(sheet);d.text((5,6),f'{b} {sock}: BEFORE / AFTER exact 3x, both soles + gap',fill='black')
       for i,c in enumerate(cuts):sheet.paste(c,(i*c.width,25),c)
       sheet.save(OUT/f'{b}-{sock}-gap-3x.png')
       if b=='flat':
        previous=Image.open(io.BytesIO(subprocess.check_output(['git','show',f'63777606:assets/worn/{name}_clear.webp'],cwd=ROOT))).getchannel('A')
        reviewed=bb.copy();reviewed[np.array(previous)>0]=0
        detailbox=(145,745,315,810);details=[im.crop(detailbox).resize((510,195),Image.Resampling.NEAREST) for im in [Image.fromarray(reviewed),after]]
        detail=Image.new('RGB',(1020,220),'#b9e5dc');ImageDraw.Draw(detail).text((5,5),f'flat {sock}: REVIEWED NOTCH / REPAIRED, exact 3x',fill='black')
        for i,c in enumerate(details):detail.paste(c,(i*510,25),c)
        detail.save(OUT/f'flat-{sock}-review-notch-3x.png')
       if sock=='frill':
        for i,im in enumerate([before,after]):
         c=im.crop(box);c.thumbnail((590,150));contact.paste(c,(i*600,bi*180+25),c)
        pen.text((5,bi*180+5),b+' BEFORE / AFTER',fill='black')
    print('PASS',b,'20 native cases',flush=True)
   contact.save(OUT/'contact.jpg',quality=93)
   projections=[]
   for w,h in [(1920,1080),(390,844)]:
    new.set_viewport_size(dict(width=w,height=h));new.evaluate("document.body.style.cssText='margin:0;background:#b9e5dc';document.body.innerHTML='<canvas id=stage></canvas>'")
    for b in BASES:
     for s in ['frill','lace']:
      meta=new.evaluate("""async([heel,sock,w,h])=>{const c=document.querySelector('#stage');c.width=w;c.height=h;await SweetShoe.Fitting2D.render(c,{heel,color:'pink',material:'satin',pattern:'none'},{sock,color:'cream'},'salon',true);return {...c.dataset}}""",[b,s,w,h]);assert meta.get('renderer')=='worn-sprite',meta
      if b=='flat':new.screenshot(path=str(OUT/f'chromium-{s}-{w}.png'))
      projections.append(dict(base=b,sock=s,viewport=[w,h]))
   info=new.evaluate('SweetShoe.WornSprites.info()');assert info['cacheEntries']<=8 and info['sourceEntries']<=8
   assert not errors and not bad,(errors,bad)
   browser.close()
  with (OUT/'counts.csv').open('w') as f:
   writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
  (OUT/'counts.md').write_text('| Base | Before flags (20 states) | After flags | Shoe pixels changed / removed |\n|---|---:|---:|---:|\n'+''.join(f"| {b} | {sum(r['before'] for r in rows if r['base']==b)} | {sum(r['after'] for r in rows if r['base']==b)} | 0 / 0 |\n" for b in BASES))
  assert next(r for r in negative if r['sprite']=='flat_frill')['previous_shoe_pixels_removed']>0,'negative control must catch reviewed notch'
  (OUT/'shoe-negative-control.json').write_text(json.dumps(dict(status='PASS',previous_commit='63777606',files=negative),indent=2)+'\n')
  (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',native_cases=len(rows),projections=projections,page_errors=errors,asset_errors=bad,cache=info,flags_after=sum(r['after'] for r in rows),outside_region_exact=True,shoe_silhouette_rgba_exact=True,shoe_pixels_changed=sum(r['shoe_pixels_changed'] for r in rows),shoe_pixels_removed=sum(r['shoe_pixels_removed'] for r in rows),shoe_dilation_px=1),indent=2)+'\n')
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
