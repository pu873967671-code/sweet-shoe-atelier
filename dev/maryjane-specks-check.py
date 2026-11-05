#!/usr/bin/env python3
"""Local Chromium Mary Jane mask acceptance and read-only other-base survey."""
import functools,http.server,json,threading,sys,itertools,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/maryjane-specks'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
sys.path.insert(0,str(ROOT/'dev'));from importlib import import_module
gap=import_module('maryjane-gap-check');render=gap.render;crop=gap.crop
CASES=[dict(color='blue',pattern='flowers',sock='frill',colour='black'),dict(color='blue',pattern='stars',sock='lace',colour='cream'),dict(color='pink',pattern='none',sock='thigh',colour='black'),dict(color='black',pattern='none',sock='knee',colour='white')]
BOXES={'front-strap':(295,682,439,781),'rear-strap':(141,644,256,735),'front-collar':(210,735,435,803),'rear-collar':(60,665,322,756),'front-heel-sole':(382,735,550,835),'rear-heel-sole':(0,750,300,807)}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'before-worn-sprites.js').write_bytes(subprocess.check_output(['git','show','8e5d02d1:js/worn-sprites.js'],cwd=ROOT))
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();errors=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page(old=False):
    p=b.new_page(viewport=dict(width=1920,height=1080));p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
    def instrument(raw):return raw.replace(b'A.WornSprites={has',b'A.__maryTest={load,tinted,opaqueRelief};A.WornSprites={has')
    p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=instrument((OUT/'before-worn-sprites.js').read_bytes() if old else (ROOT/'js/worn-sprites.js').read_bytes()),content_type='application/javascript'))
    if old:
     p.route('**/assets/worn/maryjane*_sock.webp*',lambda r:r.fulfill(body=(OUT/(Path(r.request.url.split('?')[0]).stem.replace('_sock','')+'-before.webp')).read_bytes(),content_type='image/webp'))
    p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');p.wait_for_function('!!globalThis.SweetShoe?.WornSprites');return p
   old,new=page(True),page()
   for n,v in enumerate(CASES):
    a,meta=render(old,v);z,zm=render(new,v);assert meta['pairLayout']==zm['pairLayout']
    for label,box in BOXES.items():
     aa=crop(a,meta,box);zz=crop(z,zm,box);aa=aa.resize((aa.width*3,aa.height*3),Image.Resampling.NEAREST);zz=zz.resize((zz.width*3,zz.height*3),Image.Resampling.NEAREST)
     sheet=Image.new('RGB',(aa.width*2,aa.height+30),'#eaded4');d=ImageDraw.Draw(sheet);d.text((8,8),f'BEFORE / AFTER 3x | {v} | {label}',fill='#302838');sheet.paste(aa,(0,30),aa);sheet.paste(zz,(aa.width,30),zz);sheet.save(OUT/f'case-{n}-{label}.png')
    a.save(OUT/f'case-{n}-before.png');z.save(OUT/f'case-{n}-after.png')
   print('PASS required 3x comparisons',flush=True)
   if '--preview' in sys.argv:b.close();return
   bases=['flat','block','kitten','stiletto6','stiletto9','wedge','ballet','slingback','loafer','platform','bootie','pearlpump','bowsling','crystalpump','studpump','bowmule','pearlheel','luciteheel','crystalsandal']
   preserved=[]
   for heel in bases:
    for sock in ['none','frill','lace','knee','thigh']:
     v=dict(heel=heel,sock=sock,colour='black',color='blue',pattern='stars');a,meta=render(old,v);z,_=render(new,v)
     assert a.tobytes()==z.tobytes(),v;preserved.append(v)
   print('PASS 95 exact other-base comparisons',flush=True)
   # All requested colours and sock types, four requested finish contrasts. Pinned
   # source coordinates are detached shoe/strap/sole contamination, not cloth.
   batch='''async cases=>{const result=[];
    for(const v of cases){const d={heel:'maryjane',color:v.color,material:'satin',pattern:v.pattern,strap:'none',decoration:'none',charm:'none'};
     const c=await SweetShoe.__maryTest.tinted(d,{sock:v.sock,color:v.colour});const p=c.getContext('2d');
     result.push({pixels:POINTS.map(([x,y])=>Array.from(p.getImageData(x,y,1,1).data))});}return result;}'''
   points=[(176,669),(201,680),(338,709),(382,725),(405,742),(443,762),(450,805),(295,697),(429,808)]
   batch=batch.replace('POINTS',json.dumps(points))
   matrix=[]
   for sock in ['none','frill','lace','knee','thigh']:
    for shoe,pattern in [('blue','flowers'),('blue','stars'),('pink','none'),('black','none')]:
     cases=[dict(sock=sock,colour=c,color=shoe,pattern=pattern) for c in ['black','cream','white','pink','mint']]
     rows=new.evaluate(batch,cases)
     assert all(r['pixels']==rows[0]['pixels'] for r in rows),(sock,shoe,pattern,'sock speck remains on protected shoe sample')
     matrix.extend(cases)
   print('PASS 100 colour/style/finish cases; shoe samples invariant to sock colour',flush=True)
   # Negative controls establish that the tests see the original defect.
   negative=[]
   for sock in ['frill','lace','knee','thigh']:
    rows=old.evaluate(batch,[dict(sock=sock,colour=c,color='blue',pattern='flowers') for c in ['black','white']])
    assert rows[0]['pixels']!=rows[1]['pixels'],sock;negative.append(sock)
   for w,h in [(390,844),(1920,1080)]:
    new.set_viewport_size(dict(width=w,height=h))
    for n,v in enumerate(CASES):
     im,_=render(new,dict(v,w=w,h=h));im.save(OUT/f'fitting-{n}-{w}x{h}.png')
   cache=new.evaluate('SweetShoe.WornSprites.info()');assert cache['cacheEntries']<=8 and cache['sourceEntries']<=8 and cache['pending']==0;assert not errors,errors
   (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',matrix=matrix,negative_controls=negative,other_bases_exact=preserved,cache=cache,page_errors=errors),indent=2)+'\n');b.close();print('PASS requested crops, phone/desktop and zero page errors',flush=True)
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
