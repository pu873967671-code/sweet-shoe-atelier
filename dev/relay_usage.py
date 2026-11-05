"""Read-only relay telemetry (summary + per-account quota). Direct HTTPS (no proxy: the proxy overrides Authorization for afgp.cc.cd). Never prints credentials."""
import json,http.client,ssl,sys
CRED='/workspace/files/uploads/hark-readonly-access-bd08c8b4ba98.json'
d=json.load(open(CRED)); out={}
for p in ['summary','accounts']:
  c=http.client.HTTPSConnection("afgp.cc.cd",443,timeout=15,context=ssl.create_default_context())
  c.request("GET",f"/telemetry/v1/{p}.json",headers={"Authorization":d['headers']['Authorization'],"Accept":"application/json"})
  r=c.getresponse(); out[p]=json.loads(r.read()) if r.status==200 else {"http":r.status}
s=out['summary']; print("collected_since",s.get('collection_started_at'),"total_tokens",s.get('totals',{}).get('total_tokens'),"failed",s.get('totals',{}).get('failed_events'))
for a in out['accounts'].get('accounts',[]):
  if a['provider']=='codex': print("codex",a['slot_ref'][:6],a['status'],[(w['window'].split('.')[-1],w['remaining_percent'],w['reset_at']) for w in a['windows']] or a.get('reason'))
