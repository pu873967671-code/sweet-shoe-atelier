#!/usr/bin/env python3
"""Compare skin/socks/shadows to HEAD; exercise mask failure and file loading."""
import functools,http.server,json,os,subprocess,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
report={};old=subprocess.check_output(['git', 'show', 'b15609abb19833eb556520fe8173f4cc7db41e04:js/worn-sprites.js'],cwd=ROOT,text=True)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=b.new_page(viewport={'width':390,'height':844});p.route('https://**/*',lambda r:r.abort());p.goto(f'http://127.0.0.1:{server.server_port}/');p.wait_for_function('window.SweetShoe?.WornSprites');p.evaluate('window.fixedWorn=SweetShoe.WornSprites');p.evaluate('(s)=>eval(s)',old);p.evaluate('window.oldWorn=SweetShoe.WornSprites;SweetShoe.WornSprites=fixedWorn')
  result=p.evaluate('''async()=>{const A=SweetShoe,checks=[];for(const heel of ['flat','stiletto9','wedge','luciteheel'])for(const sock of ['none','frill','lace','sheer','pantyhose','blacksheer','opaque','knee','thigh','fishnet']){
   const before=document.createElement('canvas'),after=document.createElement('canvas');before.width=after.width=780;before.height=after.height=1688;
   const d={heel,color:'black',material:'glitter',pattern:'flowers',strap:'none',decoration:'none',charm:'none'},o={sock,color:'mint',skin:'#8a5a3c'};
   if(!await oldWorn.paint(before,d,o,'salon',true)||!await fixedWorn.paint(after,d,o,'salon',true))throw Error('render failed '+heel+sock);
   const a=before.getContext('2d').getImageData(0,0,780,1688).data,c=after.getContext('2d').getImageData(0,0,780,1688).data,g=JSON.parse(after.dataset.pairLayout);let alpha=0,top=0;
   for(let i=0;i<a.length;i+=4){if(a[i+3]!==c[i+3])alpha++;if((i/4/780)<g.y+g.h*.58&&(a[i]!==c[i]||a[i+1]!==c[i+1]||a[i+2]!==c[i+2]))top++;}
   if(alpha||top)throw Error(JSON.stringify({heel,sock,alpha,top}));if(before.dataset.shadowContacts!==after.dataset.shadowContacts)throw Error('shadow contacts');checks.push(heel+'/'+sock);
  }return checks}''');report['skinSockShadowCases']=result
  # A failed mandatory sole mask must fall back cleanly and retry next draw.
  fresh=b.new_page();fresh.route('https://**/*',lambda r:r.abort());fresh.route('**/assets/worn/flat_sole.webp*',lambda r:r.abort());fresh.goto(f'http://127.0.0.1:{server.server_port}/');fresh.wait_for_function('window.SweetShoe?.WornSprites');code="""async()=>{const c=document.createElement('canvas');c.width=1220;c.height=1000;return SweetShoe.WornSprites.paint(c,{heel:'flat'},{sock:'none'},'salon',true)}""";assert fresh.evaluate(code) is False;fresh.unroute('**/assets/worn/flat_sole.webp*');assert fresh.evaluate(code) is True;report['missingMaskRetry']='PASS'
  f=b.new_page();f.route('https://**/*',lambda r:r.abort());f.goto((ROOT/'index.html').as_uri());f.wait_for_function('window.SweetShoe?.WornSprites');f.evaluate("()=>{CanvasRenderingContext2D.prototype.getImageData=()=>{throw Error('read forbidden')}}");assert f.evaluate(code);report['fileDrawOnly']='PASS';b.close()
 report['status']='PASS';(ROOT/'dev/qa-out/pattern-sole-regression.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
finally:server.shutdown();server.server_close()
