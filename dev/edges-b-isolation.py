#!/usr/bin/env python3
"""Independent native-pixel trim and sock-speck probes for edges-b."""
import sys,json,io,base64,threading,http.server,functools
from pathlib import Path
from PIL import Image,ImageFilter
from playwright.sync_api import sync_playwright
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dev'))
check=import_module('edges-b-check');q=check.q;OUT=check.OUT

def probes(base,variant):
 name=base+variant;src=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA');w,h=src.size
 before=Image.open(OUT/f'{name}_mask-before.webp').getchannel('A').tobytes()
 after=Image.open(ROOT/f'assets/worn/{name}_mask.webp').getchannel('A').tobytes()
 legs=Image.open(ROOT/f'assets/worn/{base}_legs.webp').getchannel('A');aligned=Image.new('L',(w,h));aligned.paste(legs,(-1 if name=='crystalpump_frill' else 0,0))
 exclusion=aligned.filter(ImageFilter.MaxFilter(7))
 if variant:
  sock=Image.open(ROOT/f'assets/worn/{name}_sock.webp').getchannel('A').filter(ImageFilter.MaxFilter(7))
  from PIL import ImageChops
  exclusion=ImageChops.lighter(exclusion,sock)
 ex=exclusion.tobytes();candidates=[]
 for i,(r,g,b,a) in enumerate(src.getdata()):
  if before[i]>=64 and after[i]==0 and not ex[i] and a==255 and r-b>=10 and r>=160:candidates.append([i%w,i//w])
 assert len(candidates)>=5,(name,len(candidates))
 return [candidates[int((len(candidates)-1)*j/9)] for j in range(10)]

def main():
 errors=[];rows=[]
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**/*',lambda r:r.abort())
   page.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=(ROOT/'js/worn-sprites.js').read_bytes().replace(b'A.WornSprites={has',b'A.__edgeTest={load,tinted};A.WornSprites={has'),content_type='application/javascript'))
   page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');page.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
   for base in check.BASES:
    for sock in ['none','frill','lace','knee','thigh']:
     points=probes(base,'_'+sock if sock in ['frill','lace'] else '')
     result=page.evaluate('''async v=>{const rows=[];for(const color of ['blue','pink','black'])for(const pattern of ['none','stars','flowers'])for(const colour of ['cream','white','pink','mint','black']){
      const c=await SweetShoe.__edgeTest.tinted({heel:v.base,color,material:'satin',pattern,strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:colour});const p=c.getContext('2d');rows.push({color,pattern,colour,pixels:v.points.map(([x,y])=>Array.from(p.getImageData(x,y,1,1).data))});}return rows;}''',dict(base=base,sock=sock,points=points))
     assert all(r['pixels']==result[0]['pixels'] for r in result),(base,sock,next(r for r in result if r['pixels']!=result[0]['pixels']))
     rows.append(dict(base=base,sock=sock,probes=points,combinations=len(result),trim_and_hardware_exact=True))
    print('PASS protected trim/hardware across sock colours and finishes',base,flush=True)
   assert not errors,errors
   (OUT/'isolation.json').write_text(json.dumps(dict(status='PASS',cases=sum(r['combinations'] for r in rows),rows=rows,page_errors=errors),indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
