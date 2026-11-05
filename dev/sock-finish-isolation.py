#!/usr/bin/env python3
"""Assert dots cannot paint the recovered sock interiors."""
import importlib.util
import json
import functools
import http.server
import threading
from PIL import Image,ImageFilter
from playwright.sync_api import sync_playwright
spec=importlib.util.spec_from_file_location('check','dev/sock-repair-check.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(m.Quiet,directory=str(m.ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
results=[]
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  p=browser.new_page();p.route('https://**/*',lambda r:r.abort())
  p.goto(f'http://127.0.0.1:{server.server_port}/',wait_until='domcontentloaded');p.wait_for_function('!!globalThis.SweetShoe?.WornSprites')
  for name in m.NAMES:
   heel,sock=name.rsplit('_',1)
   _,dots,meta=m.render(p,{'heel':heel,'sock':sock})
   _,plain,_=m.render(p,{'heel':heel,'sock':sock,'pattern':'none'})
   g=json.loads(meta['pairLayout']);x,y=round(g['x']),round(g['y'])
   mask=Image.open(m.ROOT/f'assets/worn/{name}_sock.webp').getchannel('A').filter(ImageFilter.MinFilter(7))
   tested=0
   for sy in range(mask.height):
    for sx in range(mask.width):
     if mask.getpixel((sx,sy))==255:
      assert dots.getpixel((sx+x,sy+y))==plain.getpixel((sx+x,sy+y)),(name,sx,sy)
      tested+=1
   assert tested>30000
   results.append({'name':name,'interior_pixels_without_dots':tested})
   print('PASS',name,tested,flush=True)
  browser.close()
 (m.OUT/'finish-isolation.json').write_text(json.dumps({'status':'PASS','cases':results},indent=2)+'\n')
finally:server.shutdown();server.server_close()
