"""Offline FBX -> indexed, texture-free GLB. Dependencies are vendored dev-only."""
import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start()
out=root/'assets/models/shoes';out.mkdir(exist_ok=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('**/convert.html',lambda r:r.fulfill(content_type='text/html',body='<html></html>'));page.goto(f'http://127.0.0.1:{s.server_port}/convert.html')
 for source,name in [('Classic_Pump','classic-pump'),('MaryJaneHeels','mary-jane')]:
  result=page.evaluate("async file=>(await import('/dev/model-tools/convert.js')).convert(file)",source)
  binary=bytes(result.pop('binary'));(out/(name+'.glb')).write_bytes(binary);print(name,len(binary),json.dumps(result),flush=True)
 b.close()
s.shutdown()
