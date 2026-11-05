#!/usr/bin/env python3
"""Blue/green native dye audit, original-hue candidates and 3x edge evidence."""
import base64,functools,http.server,io,json,threading,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
from playwright.sync_api import sync_playwright
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage';BASES=import_module('edges-p-check').BASES
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass

def main():
 global OUT
 strong='--strong' in sys.argv
 if strong:OUT=OUT/'strong-dye';OUT.mkdir(exist_ok=True)
 errors=[];bad=[];rows=[];server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page(viewport=dict(width=1920,height=1080));p.on('pageerror',lambda e:errors.append(str(e)));p.on('response',lambda r:bad.append(r.url) if r.status>=400 else None);p.route('https://**/*',lambda r:r.fulfill(body=''))
   source=(ROOT/'js/worn-sprites.js').read_text().replace('A.WornSprites={','A.__materialNative=tinted;A.WornSprites={')
   if strong:
    for script in ['data','shoe2d']:
     saturated=(ROOT/f'js/{script}.js').read_text().replace('#a9daff','#1749c8').replace('#c6e7a5','#13874f')
     p.route(f'**/js/{script}.js*',lambda r,request,body=saturated:r.fulfill(body=body,content_type='application/javascript'))
   p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=source,content_type='application/javascript'))
   harness=''.join(f'<script src="/js/{n}.js"></script>' for n in ['data','studio-core','showcase','shoe-renderer','accessory-renderer','shoe2d','worn-sprites','fitting2d'])
   p.route('**/__dye',lambda r:r.fulfill(body=harness,content_type='text/html'));p.goto(f'http://127.0.0.1:{server.server_port}/__dye');p.wait_for_function('!!SweetShoe.__materialNative')
   for b in BASES:
    for cam in ['product','worn']:
     src=Image.open(ROOT/(f'assets/shoe2d/{b}_base.webp' if cam=='product' else f'assets/worn/{b}.webp')).convert('RGBA');mask=Image.open(ROOT/(f'assets/shoe2d/{b}_upper.webp' if cam=='product' else f'assets/worn/{b}_mask.webp')).getchannel('A');near=mask.filter(ImageFilter.MaxFilter(7));mp=mask.tobytes();np=near.tobytes()
     for color in ['blue','green']:
      uri=p.evaluate('''async([heel,color,cam])=>{const d=SweetShoe.cleanDesign({heel,color,material:'satin',pattern:'none',strap:'none',decoration:'none',charm:'none'});const c=cam==='product'?await SweetShoe.Shoe2D.composite(d):await SweetShoe.__materialNative(d,{sock:'none',color:'cream'});return c.toDataURL()}''',[b,color,cam]);raw=base64.b64decode(uri.split(',')[1]);im=Image.open(io.BytesIO(raw)).convert('RGBA');(OUT/f'{b}-{cam}-dye-{color}.png').write_bytes(raw);flags=Image.new('L',im.size);f=bytearray(im.width*im.height)
      for i,((r,g,bl,a),(rr,gg,bb,_)) in enumerate(zip(src.getdata(),im.getdata())):
       neutral=max(r,g,bl)-min(r,g,bl)<32 and min(r,g,bl)>140
       pink=r-g>12 and r-bl>0 and r-g<90
       original=abs(r-rr)+abs(g-gg)+abs(bl-bb)<18
       if a>=128 and np[i] and mp[i]<96 and (neutral or pink) and original:f[i]=255
      flags=Image.frombytes('L',im.size,bytes(f));flags.save(OUT/f'{b}-{cam}-dye-{color}-flags.png');rows.append(dict(base=b,camera=cam,color=color,candidates=sum(v>0 for v in f),classification='source-local review required; includes intentional piping, sole and hardware'))
      # Exact source-pixel 3x full-upper review; no resampling of evidence.
      box=(80,60,945,550) if cam=='product' else (0,590,im.width,im.height);cut=im.crop(box);s=Image.new('RGB',(cut.width*3,cut.height*3+24),'#bcae9c');cut=cut.resize((cut.width*3,cut.height*3),Image.Resampling.NEAREST);s.paste(cut,(0,24),cut);ImageDraw.Draw(s).text((8,5),f'{b} {cam} {color} exact 3x; separate flags are candidates',fill='black');s.save(OUT/f'{b}-{cam}-dye-{color}-3x.jpg',quality=90)
    print('PASS blue/green',b,flush=True)
   assert not errors and not bad,(errors,bad)
   (OUT/'dye-blue-green-acceptance.json').write_text(json.dumps(dict(status='PASS',render_cases=len(rows),page_errors=errors,asset_errors=bad,cases=rows),indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
