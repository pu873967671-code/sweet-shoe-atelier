#!/usr/bin/env python3
"""Pixel-exhaustive independent mesh ownership against all 20 dye masks."""
import functools,http.server,json,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/material-coverage';BASES=import_module('edges-p-check').BASES
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
def main():
 rows=[];server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
 try:
  with sync_playwright() as pw:
   browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   for phase in ['before','after']:
    p=browser.new_page();source=(OUT/'baseline/shoe2d.js' if phase=='before' else ROOT/'js/shoe2d.js').read_text()
    def script(r):r.fulfill(body=source,content_type='application/javascript')
    p.route('**/js/shoe2d.js*',script);p.route('**/__planes',lambda r:r.fulfill(body='<script src="/js/data.js"></script><script src="/js/shoe2d.js"></script>',content_type='text/html'));p.goto(f'http://127.0.0.1:{server.server_port}/__planes')
    for b in BASES:
     r=p.evaluate('''async heel=>{const im=await new Promise(resolve=>{const i=new Image();i.onload=()=>resolve(i);i.src='/assets/shoe2d/'+heel+'_upper.webp'});const c=document.createElement('canvas');c.width=1024;c.height=640;const p=c.getContext('2d');p.drawImage(im,0,0);const a=p.getImageData(0,0,1024,640).data;const panel=SweetShoe.CoutureFinish.meshPanel({heel,color:'blue',material:'mesh'},im,1024,640);const z=panel.getContext('2d').getImageData(0,0,1024,640).data;let lost=0,outside=0,diff=0;for(let i=3;i<a.length;i+=4){if(a[i]>z[i]+1)lost++;if(z[i]>a[i]+1)outside++;if(Math.abs(a[i]-z[i])>1)diff++;}return {lost,outside,diff}}''',b)
     rows.append(dict(base=b,phase=phase,**r))
    p.close()
   browser.close()
 finally:server.shutdown();server.server_close()
 result=dict(status='PASS' if all(r['diff']==0 for r in rows if r['phase']=='after') else 'FAIL',rows=rows)
 (OUT/'mesh-ownership.json').write_text(json.dumps(result,indent=2)+'\n');assert result['status']=='PASS',result
 print('PASS all 20 per-base mesh masks exact; prior lost pixels',sum(r['lost'] for r in rows if r['phase']=='before'))
if __name__=='__main__':main()
