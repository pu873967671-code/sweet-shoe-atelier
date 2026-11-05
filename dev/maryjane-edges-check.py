#!/usr/bin/env python3
"""Local Chromium Mary Jane mask acceptance and read-only other-base survey."""
import functools,http.server,json,threading,sys,itertools
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/maryjane-edges'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
sys.path.insert(0,str(ROOT/'dev'));from importlib import import_module
gap=import_module('maryjane-gap-check');render=gap.render;crop=gap.crop
CASES=[dict(color='blue',pattern='stars',sock='lace',colour='cream'),dict(color='pink',pattern='none',sock='thigh',colour='black'),dict(color='black',pattern='none',sock='none'),dict(color='green',pattern='flowers',sock='frill',colour='white')]
BOXES={'front':(210,730,430,803),'rear':(65,650,320,750),'strap-buckle':(300,680,445,785)}
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start();errors=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page(old=False):
    p=b.new_page(viewport=dict(width=1920,height=1080));p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
    if old:
     def mask_route(r):
      name=Path(r.request.url.split('?')[0]).stem.replace('_mask','');r.fulfill(body=(OUT/(name+'-before.webp')).read_bytes(),content_type='image/webp')
     p.route('**/assets/worn/maryjane*_mask.webp*',mask_route)
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
   survey=Image.new('RGB',(1320,19*260),'#eaded4');d=ImageDraw.Draw(survey);preserved=[]
   for i,heel in enumerate(bases):
    for j,v in enumerate([dict(color='blue',pattern='stars',sock='lace',colour='cream'),dict(color='blue',pattern='stars',sock='thigh',colour='black')]):
     v=dict(v,heel=heel);a,meta=render(old,v);z,_=render(new,v);assert a.tobytes()==z.tobytes(),v;preserved.append(v)
     cut=crop(z,meta,(0,450,650,750) if heel=='bootie' else (0,610,650,840));cut.resize((cut.width*3,cut.height*3),Image.Resampling.NEAREST).save(OUT/f'survey-{heel}-{v["sock"]}-3x.png');cut.thumbnail((650,230));survey.paste(cut,(j*660,i*260+25),cut);d.text((j*660+5,i*260+5),heel+' / '+v['sock']+' '+v['colour'],fill='#302838')
   survey.save(OUT/'other-bases-survey.jpg',quality=95);print('PASS 38 exact survey comparisons',flush=True)
   if '--survey' in sys.argv:b.close();return
   colours=['pink','cream','blue','green','purple','peach','rose','black'];patterns=['none','flowers','hearts','dots','stars','rosebuds','diamonds','gingham','scallops','pinstripes']
   # Compare all finishes on independently painted cream piping pixels in both shoes.
   batch='''async cases=>{const c=document.createElement('canvas');c.width=1220;c.height=1000;const result=[];
    for(const v of cases){await SweetShoe.Fitting2D.render(c,{heel:'maryjane',color:v.color,material:'satin',pattern:v.pattern,strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:v.colour},'salon',true);
    if(c.dataset.fallback!=='false')throw Error('fallback');const g=JSON.parse(c.dataset.pairLayout),p=c.getContext('2d');
    result.push({samples:''' + 'SAMPLES' + ''',layout:c.dataset.pairLayout});}return result;}'''
   # Source piping samples sufficiently inside the cream trim, away from interpolation.
   pts=[(300,789),(160,740),(235,762),(350,750)]
   batch=batch.replace('SAMPLES',json.dumps(pts)+'.map(([x,y])=>Array.from(p.getImageData(Math.round(g.x+x*g.scale),Math.round(g.y+y*g.scale),1,1).data))')
   count=0;matrix=[]
   for sock in ['none','frill','lace','knee','thigh']:
    for colour in (['cream'] if sock=='none' else ['cream','white','pink','mint','black']):
     cases=[dict(sock=sock,colour=colour,color=c,pattern=p) for c,p in itertools.product(colours,patterns)]
     rows=new.evaluate(batch,cases);assert all(len({tuple(r['samples'][i]) for r in rows})==1 for i in range(len(pts))),(sock,colour,'dye/motif leaks onto piping');matrix.append(dict(sock=sock,colour=colour,cases=len(rows),unique_piping=[len({tuple(r['samples'][i]) for r in rows}) for i in range(len(pts))]));count+=len(rows)
     print('matrix',sock,colour,len(rows),matrix[-1]['unique_piping'],flush=True)
   negative=[]
   for sock in ['none','frill','lace','knee','thigh']:
    v=[dict(sock=sock,colour='cream',color=c,pattern=p) for c,p in [('blue','stars'),('black','none')]]
    rows=old.evaluate(batch,v);assert rows[0]['samples']!=rows[1]['samples'],(sock,'negative control');negative.append(sock)
   for w,h in [(390,844),(1920,1080)]:
    new.set_viewport_size(dict(width=w,height=h))
    for n,v in enumerate(CASES):
     im,_=render(new,dict(v,w=w,h=h));im.save(OUT/f'fitting-{n}-{w}x{h}.png')
   cache=new.evaluate('SweetShoe.WornSprites.info()');assert cache['cacheEntries']<=8 and cache['sourceEntries']<=8 and cache['pending']==0;assert not errors,errors
   (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',matrix_cases=count,matrix=matrix,negative_controls=negative,other_bases_exact=preserved,cache=cache,page_errors=errors),indent=2)+'\n');b.close();print('PASS exhaustive matrix, negative controls, phone/desktop and zero page errors',flush=True)
 finally:server.shutdown();server.server_close()
if __name__=='__main__':main()
