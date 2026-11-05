import functools,http.server,threading,json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[2]
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
s=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=s.serve_forever,daemon=True).start()
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page();page.route('**/model-inspect.html',lambda r:r.fulfill(content_type='text/html',body='<html></html>'));page.goto(f'http://127.0.0.1:{s.server_port}/model-inspect.html')
 print(json.dumps(page.evaluate('''async()=>{const T=await import('/vendor/three.module.min.js'),{FBXLoader}=await import('/dev/model-tools/FBXLoader.js');const results=[];for(const file of ['Classic_Pump','MaryJaneHeels']){const g=await new FBXLoader().loadAsync('/dev/asset_candidates/hiirusama/'+file+'.fbx');g.updateMatrixWorld(true);const items=[];g.traverse(o=>{if(o.isMesh){const box=new T.Box3().setFromObject(o);items.push({name:o.name,vertices:o.geometry.attributes.position.count,groups:o.geometry.groups.map(gr=>{const b=new T.Box3(),v=new T.Vector3();for(let i=gr.start;i<gr.start+gr.count;i++)b.expandByPoint(v.fromBufferAttribute(o.geometry.attributes.position,i).applyMatrix4(o.matrixWorld));return {...gr,min:b.min.toArray(),max:b.max.toArray()}}),materials:(Array.isArray(o.material)?o.material:[o.material]).map(m=>m.name),min:box.min.toArray(),max:box.max.toArray()})}});results.push({file,items})}return results}'''),indent=2));b.close()
s.shutdown()
