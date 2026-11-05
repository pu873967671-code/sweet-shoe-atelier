import json,base64,sys,time,urllib.request
img,prompt,out,res=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]
b=base64.b64encode(open(img,'rb').read()).decode()
d={"model":"grok-imagine-video","prompt":prompt,"image":{"url":"data:image/png;base64,"+b},"duration":5}
if res!='-': d["resolution"]=res
def call(u,data=None):
    r=urllib.request.Request(u,data=json.dumps(data).encode() if data else None,headers={"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=110))
r=call("https://afgp.cc.cd/v1/videos/generations",d); print(r); i=r["request_id"]
for _ in range(60):
    s=call("https://afgp.cc.cd/v1/videos/"+i)
    if s.get("status")=="done": break
    if s.get("status") in("failed","expired","error"): print(s); sys.exit(1)
    time.sleep(8)
urllib.request.urlretrieve(s["video"]["url"],out); print("ok",out)
