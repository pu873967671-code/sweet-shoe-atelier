#!/usr/bin/env python3
"""Native footwear probes at original detached sock/legs contamination sites."""
import sys,json,threading,http.server,functools
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'dev'))
check=import_module('edges-c-check');repair=import_module('refine-edges-c');q=check.q;OUT=check.OUT

def points(base,sock):
 name=base+('_'+sock if sock in ['frill','lace'] else '')
 painting=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA');w,h=painting.size;src=painting.tobytes()
 if sock in ['frill','lace']:
  old=Image.open(OUT/f'{name}_sock-before.webp').getchannel('A').tobytes()
  new=Image.open(ROOT/f'assets/worn/{name}_sock.webp').getchannel('A').tobytes()
 else:
  leg=Image.open(ROOT/f'assets/worn/{base}_legs.webp').getchannel('A');old=leg.tobytes();new=repair.components(old,w,h)
 y0=repair.BASES[base][0]
 candidates=[i for i in range(y0*w,w*h) if old[i] and not new[i] and src[i*4+3]>=200 and min(src[i*4+1]-src[i*4],src[i*4+1]-src[i*4+2])<6]
 candidates.sort(key=lambda i:old[i],reverse=True)
 # Rank by original coverage so the strongest old specks are tested first.
 selected=candidates[:32]
 return [[i%w,i//w] for i in selected]

def main():
 rows=[];errors=[]
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=browser.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.route('https://**/*',lambda r:r.abort())
   page.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=(ROOT/'js/worn-sprites.js').read_bytes().replace(b'A.WornSprites={has',b'A.__edgeTest={load,tinted};A.WornSprites={has'),content_type='application/javascript'))
   page.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');page.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
   for base in check.BASES:
    for sock in ['frill','lace','knee','thigh']:
     probes=points(base,sock)
     if not probes:
      rows.append(dict(base=base,sock=sock,probes=[],reason='No original detached contamination at opaque painted footwear'));continue
     result=page.evaluate('''async v=>{const rows=[];for(const colour of ['cream','white','pink','mint','black']){
      const c=await SweetShoe.__edgeTest.tinted({heel:v.base,color:'blue',material:'satin',pattern:'stars',strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:colour});const p=c.getContext('2d');rows.push({colour,pixels:v.points.map(([x,y])=>Array.from(p.getImageData(x,y,1,1).data))});}return rows;}''',dict(base=base,sock=sock,points=probes))
     assert all(r['pixels']==result[0]['pixels'] for r in result),(base,sock,result)
     rows.append(dict(base=base,sock=sock,probes=probes,sock_colours=5,footwear_colour_invariant=True))
    print('PASS original sock/leg speck sites',base,flush=True)
   assert not errors,errors
   (OUT/'specks.json').write_text(json.dumps(dict(status='PASS',rows=rows,page_errors=errors),indent=2)+'\n');browser.close()
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
