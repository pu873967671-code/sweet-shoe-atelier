#!/usr/bin/env python3
"""Worn sole acceptance; writes evidence only under dev/qa-out/."""
import base64,functools,http.server,io,json,os,re,sys,threading,hashlib,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out';PHASE=sys.argv[1] if len(sys.argv)>1 else 'after'
REFS=json.loads(re.search(r'const SPRITES=(.*);', (ROOT/'js/worn-sprites.js').read_text()).group(1));HEELS=[k for k in REFS if '_' not in k]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
folder=OUT/('pattern-sole-'+PHASE);folder.mkdir(parents=True,exist_ok=True)
report={'phase':PHASE,'cases':[],'errors':[]};sheet=None
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']) if os.environ.get('SOLE_BROWSER')=='chromium' else pw.webkit.launch(env={k:v for k,v in os.environ.items() if 'proxy' not in k.lower()})
  page=browser.new_page();page.set_default_timeout(90000);page.route('https://**/*',lambda r:r.abort());page.on('pageerror',lambda e:report['errors'].append(str(e)))
  
  if PHASE=='before':page.route('**/js/worn-sprites.js',lambda r:r.fulfill(body=subprocess.check_output(['git','show','b15609abb19833eb556520fe8173f4cc7db41e04:js/worn-sprites.js'],cwd=ROOT,text=True),content_type='application/javascript'))
  page.goto(f'http://127.0.0.1:{server.server_port}/index.html');page.wait_for_function('window.SweetShoe?.WornSprites')
  patterns=page.evaluate('SweetShoe.opts.pattern.map(x=>x[0])');patterns=['flowers'] if os.environ.get('SOLE_QUICK') else patterns;sheet=Image.new('RGB',(300*len(patterns),140*len(HEELS)*4),'#e4e0d9')
  page.evaluate("""()=>{window.soleRead=CanvasRenderingContext2D.prototype.getImageData;CanvasRenderingContext2D.prototype.getImageData=()=>{throw Error('Runtime read forbidden')};}""")
  for hi,heel in enumerate(HEELS):
   if os.environ.get('SOLE_SLICE') and hi%4!=int(os.environ['SOLE_SLICE']):continue
   for si,sock in enumerate(['none','frill']):
    for ci,(color,material) in enumerate([('pink','lace'),('black','glitter')]):
     for pi,pattern in enumerate(patterns):
      v={'heel':heel,'sock':sock,'color':color,'material':material,'pattern':pattern}
      result=page.evaluate("""async v=>{const c=document.createElement('canvas');c.width=1220;c.height=1000;const ok=await SweetShoe.WornSprites.paint(c,{...v,strap:'none',decoration:'none',charm:'none'},{sock:v.sock,color:'cream'},'salon',true);if(!ok)throw Error('Sprite failed '+JSON.stringify(v));const g=JSON.parse(c.dataset.pairLayout);const b=document.createElement('canvas');b.width=Math.ceil(g.w);b.height=Math.ceil(g.h);b.getContext('2d').drawImage(c,-g.x,-g.y);return {png:b.toDataURL().split(',')[1],layout:g,contacts:c.dataset.shadowContacts};}""",v)
      raw=base64.b64decode(result.pop('png'));name=f'{heel}-{sock}-{color}-{material}-{pattern}.png';(folder/name).write_bytes(raw)
      im=Image.open(io.BytesIO(raw)).convert('RGBA');upper=hashlib.sha256(im.crop((0,0,im.width,im.height-285)).tobytes()).hexdigest();crop=im.crop((0,im.height-270,im.width,im.height));crop.thumbnail((296,116));x=pi*300;y=(hi*4+si*2+ci)*140;sheet.paste(crop,(x,y+22),crop);ImageDraw.Draw(sheet).text((x+3,y+3),f'{heel} {sock} {color} {material} {pattern}',fill='#252525')
      report['cases'].append({**v,'file':name,'upper':upper,**result})
   print(PHASE,heel,flush=True)
  report['cache']=page.evaluate('SweetShoe.WornSprites.info()');assert report['cache']['cacheEntries']<=8 and report['cache']['sourceEntries']<=8
  assert not report['errors'],report['errors'];browser.close()
 sheet.save(OUT/('pattern_sole_'+PHASE+os.environ.get('SOLE_SLICE','')+'.jpg'),quality=88)
 report['status']='PASS';(OUT/('pattern-sole-'+PHASE+os.environ.get('SOLE_SLICE','')+'.json')).write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(report['cases']),flush=True)
finally:server.shutdown();server.server_close()
