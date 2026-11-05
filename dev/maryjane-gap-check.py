#!/usr/bin/env python3
"""Mary Jane collar acceptance in local Chromium; development evidence only."""
import base64,functools,http.server,io,json,threading,sys,hashlib,itertools
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/maryjane-gap'
sys.path.insert(0,str(ROOT/'qa'));import screenshot as q
RENDER='''async v=>{const c=document.createElement('canvas');c.width=v.w||1220;c.height=v.h||1000;
await SweetShoe.Fitting2D.render(c,{heel:v.heel||'maryjane',color:v.color||'blue',material:v.material||'satin',pattern:v.pattern||'flowers',strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:v.colour||'cream'},'salon',true);
if(c.dataset.renderer!=='worn-sprite'||c.dataset.fallback!=='false')throw Error('Unexpected renderer');
return {png:c.toDataURL().split(',')[1],meta:{...c.dataset}};}'''
def render(p,case):
 r=p.evaluate(RENDER,case);return Image.open(io.BytesIO(base64.b64decode(r['png']))).convert('RGBA'),r['meta']
def crop(im,meta,box):
 g=json.loads(meta['pairLayout']);k=g['scale'];x,y=g['x'],g['y'];return im.crop(tuple(round(v) for v in (x+box[0]*k,y+box[1]*k,x+box[2]*k,y+box[3]*k)))
def main():
 OUT.mkdir(exist_ok=True,parents=True);baseline=(OUT/'before-worn-sprites.js').read_bytes()
 assets={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets').rglob('*') if p.is_file()}
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(q.QuietHandler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 errors=[];cases=[]
 try:
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   def page(old):
    p=b.new_page(viewport={'width':1336,'height':790});p.on('pageerror',lambda e:errors.append(str(e)));p.route('https://**/*',lambda r:r.abort())
    if old:p.route('**/js/worn-sprites.js*',lambda r:r.fulfill(body=baseline,content_type='application/javascript'))
    p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');p.wait_for_function('!!globalThis.SweetShoe?.WornSprites');return p
   old,new=page(True),page(False)
   if '--extra' in sys.argv:
    extra(old,new,page,errors);b.close();return
   sheet=Image.new('RGB',(1600,5*430+30),'#e6dacf');pen=ImageDraw.Draw(sheet)
   for i,sock in enumerate(['none','frill','lace','knee','thigh']):
    case=dict(sock=sock);a,meta=render(old,case);z,_=render(new,case)
    for j,im in enumerate([a,z]):
     im.save(OUT/f'{sock}-{"before" if j==0 else "after"}.png')
     cut=crop(im,meta,(0,600,550,815));bg=Image.new('RGBA',cut.size,'#e6dacf');bg.alpha_composite(cut);bg=bg.convert('RGB').resize((770,350))
     sheet.paste(bg,(j*800+10,i*430+60));pen.text((j*800+10,i*430+35),f'{sock} blue flowers cream / {"BEFORE" if j==0 else "AFTER"}',fill='#302838')
   sheet.save(OUT/'contact.jpg',quality=95)
   if '--preview' in sys.argv:b.close();return
   # Exhaustive requested cross product: all eight shoe colours, ten motifs,
   # five sock colours and all five requested sock types (none is colourless).
   colours=['pink','cream','blue','green','purple','peach','rose','black']
   patterns=['none','flowers','hearts','dots','stars','rosebuds','diamonds','gingham','scallops','pinstripes']
   batch="""async cases=>{
    const c=document.createElement('canvas');c.width=1220;c.height=1000;
    const atlas=document.createElement('canvas');atlas.width=410;atlas.height=cases.length*134;
    const a=atlas.getContext('2d');a.fillStyle='#e6dacf';a.fillRect(0,0,atlas.width,atlas.height);
    const records=[];
    for(let i=0;i<cases.length;i++){const v=cases[i];
     await SweetShoe.Fitting2D.render(c,{heel:'maryjane',color:v.color,material:'satin',pattern:v.pattern,strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:v.colour},'salon',true);
     if(c.dataset.fallback!=='false'||c.dataset.renderer!=='worn-sprite')throw Error('fallback');
     const g=JSON.parse(c.dataset.pairLayout),p=c.getContext('2d');
     a.fillStyle='#302838';a.font='12px sans-serif';a.fillText(v.color+' '+v.pattern+' '+v.sock+' '+v.colour,4,i*134+15);
     a.drawImage(c,g.x+210,g.y+735,85,57,0,i*134+20,170,114);
     a.drawImage(c,g.x+65,g.y+697,120,57,170,i*134+20,240,114);
     records.push({pixel:Array.from(p.getImageData(g.x+235,g.y+762,1,1).data),layout:c.dataset.pairLayout});
    }
    return {png:atlas.toDataURL().split(',')[1],records};
   }"""
   for sock in ['none','frill','lace','knee','thigh']:
    for colour in (['cream'] if sock=='none' else ['cream','white','pink','mint','black']):
     states=[dict(sock=sock,colour=colour,color=c,pattern=p) for c,p in itertools.product(colours,patterns)]
     left=old.evaluate(batch,states);right=new.evaluate(batch,states)
     decode=lambda r:Image.open(io.BytesIO(base64.b64decode(r['png']))).convert('RGB')
     pair=Image.new('RGB',(820,len(states)*134+24),'#e6dacf');d=ImageDraw.Draw(pair);d.text((5,5),'BEFORE / FRONT then REAR',fill='#302838');d.text((415,5),'AFTER / FRONT then REAR',fill='#302838')
     pair.paste(decode(left),(0,24));pair.paste(decode(right),(410,24));pair.save(OUT/f'matrix-{sock}-{colour}.jpg',quality=92)
     assert len({tuple(r['pixel']) for r in right['records']})==1,(sock,colour,'shoe finish leaked onto foot')
     assert len({tuple(r['pixel']) for r in left['records']})>1,(sock,colour,'negative control failed')
     for v,aa,zz in zip(states,left['records'],right['records']):
      assert aa['layout']==zz['layout'],v
      assert aa['pixel']!=zz['pixel'],(v,'pocket unchanged')
      assert zz['pixel'][3]==255,(v,'transparent pocket')
      cases.append({**v,'before':aa['pixel'],'after':zz['pixel']})
     print('PASS matrix',sock,colour,len(states),flush=True)
   # Pixel-exact preservation of other bases and the rear Mary Jane collar.
   preserved=[]
   for heel in ['flat','block','kitten','stiletto6','stiletto9','wedge','ballet','slingback','loafer','platform','bootie','pearlpump','bowsling','crystalpump','studpump','bowmule','pearlheel','luciteheel','crystalsandal','maryjane']:
    for sock in ['none','frill','lace','knee','thigh']:
     v=dict(heel=heel,sock=sock,colour='black');a,meta=render(old,v);z,_=render(new,v)
     if heel!='maryjane':assert a.tobytes()==z.tobytes(),v
     else:
      diff=ImageChops.difference(a,z).convert('RGB');g=json.loads(meta['pairLayout']);d=ImageDraw.Draw(diff);d.rectangle((g['x']+214,g['y']+730,g['x']+276,g['y']+790),fill='black')
      assert diff.getbbox() is None,(v,'outside front collar changed')
     preserved.append(v)
   for w,h in [(390,844),(1920,1080)]:
    for sock in ['none','frill','lace','knee','thigh']:
     im,_=render(new,dict(sock=sock,w=w,h=h));im.save(OUT/f'{sock}-{w}x{h}.png')
   cache=new.evaluate('SweetShoe.WornSprites.info()');assert cache['cacheEntries']<=8 and cache['sourceEntries']<=8 and cache['pending']==0,cache
   b.close()
  assert not errors,errors
  assert assets=={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets').rglob('*') if p.is_file()},'asset changed'
  (OUT/'acceptance.json').write_text(json.dumps(dict(status='PASS',matrix_cases=len(cases),collar_independent_of_shoe_finish=True,cases=cases,preservation=preserved,cache=cache,page_errors=errors,assets_unchanged=len(assets)),indent=2)+'\n')
 finally:server.shutdown();server.server_close()
def extra(old,new,page,errors):
 # Other finishes must leave the corrected foot independent of the shoe.
 checks=[]
 for sock in ['none','frill','lace','knee','thigh']:
  pixels=[]
  for material in ['satin','mesh','lace','velvet','glitter','patent','metallic','pearlescent','suede','brocade','pave']:
   im,meta=render(new,dict(sock=sock,material=material));g=json.loads(meta['pairLayout']);pixels.append(im.getpixel((round(g['x'])+235,round(g['y'])+762)))
  assert len(set(pixels))==1,(sock,'material leaked into collar')
  checks.append(dict(sock=sock,all_materials=True))
 # Pixel restrictions must retain the old renderer and its safe source fallback.
 restricted_old,restricted=page(True),page(False)
 for p in [restricted_old,restricted]:p.evaluate("()=>{CanvasRenderingContext2D.prototype.getImageData=()=>{throw Error('Read restricted')}}")
 for sock in ['none','frill','lace','knee','thigh']:
  a,_=render(restricted_old,dict(sock=sock));z,_=render(restricted,dict(sock=sock));assert a.tobytes()==z.tobytes(),(sock,'unsafe read-failure fallback')
 assert not errors,errors
 (OUT/'extra-acceptance.json').write_text(json.dumps(dict(status='PASS',material_cases=55,cases=checks,read_failure_exact=5,page_errors=errors),indent=2)+'\n')
 print('PASS all materials and safe restricted-read fallback',flush=True)
if __name__=='__main__':main()
