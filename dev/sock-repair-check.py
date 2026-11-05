#!/usr/bin/env python3
"""Real Chromium before/after short sock matrix; evidence only under dev/."""
import base64
import functools
import http.server
import io
import json
import re
import subprocess
import threading
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw
from playwright.sync_api import sync_playwright
import runpy
ROOT = Path(__file__).resolve().parents[1]
REPAIR = runpy.run_path(str(ROOT/'dev/repair-sock-masks.py'))
NAMES, BASELINE = REPAIR['NAMES'], REPAIR['BASELINE']
OUT = ROOT/'dev/qa-out/sock-repair'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

RENDER = """async v=>{
 const c=document.createElement('canvas');c.width=v.w||1220;c.height=v.h||1000;
 await SweetShoe.Fitting2D.render(c,{heel:v.heel,color:'pink',material:'satin',
 pattern:v.pattern||'dots',strap:'none',decoration:'none',charm:'none'},
 {sock:v.sock,color:v.colour||'cream'},'salon',true);
 const meta={...c.dataset};
 const room=new Image();room.src='assets/scenes/fixed_salon.webp';await room.decode();
 const g=SweetShoe.Showcase.project('salon',c.width,c.height,true),b=g.background;
 const out=document.createElement('canvas');out.width=c.width;out.height=c.height;
 const p=out.getContext('2d');p.drawImage(room,b.x,b.y,b.width,b.height);p.drawImage(c,0,0);
 return {png:out.toDataURL().split(',')[1],raw:c.toDataURL().split(',')[1],meta};
}"""

def render(page, case):
    r=page.evaluate(RENDER,case)
    assert r['meta']['renderer']=='worn-sprite' and r['meta']['fallback']=='false',r['meta']
    decode=lambda v:Image.open(io.BytesIO(base64.b64decode(v))).convert('RGBA')
    return decode(r['png']),decode(r['raw']),r['meta']

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    refs=json.loads(re.search(r'const SPRITES=(.*?);',(ROOT/'js/worn-sprites.js').read_text()).group(1))
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    errors=[];cases=[]
    heels=[k for k in refs if '_' not in k]
    states=[{'heel':heel,'sock':sock,'colour':'cream'} for heel in heels for sock in ['lace','frill']]
    states += [{'heel':'slingback','sock':'lace','colour':c} for c in ['mint','black','pink']]
    sheet=Image.new('RGB',(1280,len(states)*290+35),'#f4eee8');pen=ImageDraw.Draw(sheet)
    pen.text((12,10),'Sock repair / BEFORE left (pre-repair HEAD) / AFTER right / salon, pink satin, dots',fill='#332825')
    try:
      with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        def page(old=False):
            p=browser.new_page(viewport={'width':1336,'height':790})
            p.on('pageerror',lambda e:errors.append(str(e)))
            p.route('https://**/*',lambda r:r.abort())
            if old:
                def route(r):
                    path=r.request.url.split('/assets/worn/')[1].split('?')[0]
                    data=subprocess.check_output(['git','show',f'{BASELINE}:assets/worn/{path}'],cwd=ROOT)
                    r.fulfill(body=data,content_type='image/webp')
                p.route('**/assets/worn/*',route)
            p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded')
            p.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
            p.evaluate("()=>{CanvasRenderingContext2D.prototype.getImageData=()=>{throw Error('Runtime pixel read forbidden')}}")
            return p
        old,new=page(True),page()
        for i,case in enumerate(states):
            before,braw,meta=render(old,case);after,araw,_=render(new,case)
            changed=case['heel']+'_'+case['sock'] in NAMES
            assert (braw.tobytes()!=araw.tobytes())==changed,(case,'unexpected preservation result')
            g=json.loads(meta['pairLayout']);x,y,w,h=[g[k] for k in ['x','y','w','h']]
            crop=(round(x-10),round(y+490),round(x+w+10),round(y+h+25))
            for col,im in enumerate([before,after]):
                foot=im.crop(crop);foot.thumbnail((626,258))
                sheet.paste(foot,(col*640+7,35+i*290+25))
                pen.text((col*640+10,35+i*290+5),f"{case['heel']} {case['sock']} {case['colour']} / {'BEFORE' if col==0 else 'AFTER'}",fill='#332825')
            if changed:
                # Independently sample all fully green yarn, away from soft edges.
                sprite=Image.open(ROOT/f"assets/worn/{case['heel']}_{case['sock']}.webp").convert('RGBA')
                mask=Image.open(ROOT/f"assets/worn/{case['heel']}_{case['sock']}_sock.webp").convert('RGBA')
                bad=total=0
                for sy in range(sprite.height):
                    for sx in range(sprite.width):
                        r,gg,b,a=sprite.getpixel((sx,sy))
                        if a==255 and min(gg-r,gg-b)>20 and mask.getpixel((sx,sy))[3]==255:
                            total+=1
                            rr,gg,bb,_=araw.getpixel((round(x)+sx,round(y)+sy))
                            if case['colour']=='cream' and gg>rr+8 and gg>bb+8:bad+=1
                assert bad==0,(case,bad,total)
            cases.append({**case,'changed':changed})
            print('PASS',case,flush=True)
        # Phone and desktop projections, including the original bare state.
        for width,height in [(390,844),(1920,1080)]:
            for sock in ['none','lace','frill']:
                render(new,{'heel':'slingback','sock':sock,'w':width,'h':height})
        cache=new.evaluate('SweetShoe.WornSprites.info()')
        assert cache['cacheEntries']<=8 and cache['sourceEntries']<=8
        assert not errors,errors
        browser.close()
      sheet.save(OUT/'contact.jpg',quality=94)
      (OUT/'acceptance.json').write_text(json.dumps({'status':'PASS','baseline':BASELINE,'cases':cases,'errors':errors,'cache':cache},indent=2)+'\n')
    finally:
      server.shutdown();server.server_close()

if __name__=='__main__':main()
