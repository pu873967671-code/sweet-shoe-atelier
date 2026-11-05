#!/usr/bin/env python3
"""Independent mask coverage/format/scope checks against the pre-repair commit."""
import io
import json
import runpy
import subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
cfg=runpy.run_path(str(ROOT/'dev/repair-sock-masks.py'))
NAMES,BASELINE=cfg['NAMES'],cfg['BASELINE']
allowed={f'assets/worn/{n}{suffix}.webp' for n in NAMES for suffix in ['_sock','_mask']}
changed=set(subprocess.check_output(['git','diff','--name-only',BASELINE,'--','assets'],cwd=ROOT,text=True).splitlines())
assert changed <= allowed,changed-allowed
rows=[]
for name in NAMES:
 sprite=Image.open(ROOT/f'assets/worn/{name}.webp').convert('RGBA')
 sock=Image.open(ROOT/f'assets/worn/{name}_sock.webp').convert('RGBA')
 dye=Image.open(ROOT/f'assets/worn/{name}_mask.webp').convert('RGBA')
 oldsock=cfg['original'](f'assets/worn/{name}_sock.webp')
 olddye=cfg['original'](f'assets/worn/{name}_mask.webp')
 assert sprite.size==sock.size==dye.size
 covered=missing=outside=overlap=0
 for src,s,d,os,od in zip(sprite.getdata(),sock.getdata(),dye.getdata(),oldsock.getdata(),olddye.getdata()):
  r,g,b,a=src;green=min(g-r,g-b)
  if a>245 and green>20:
   covered+=1
   missing+=s[3]<240
  if s!=os:
   assert s[0]==s[1]==s[2]
   assert green>2 and a>0,('non-yarn change',name,src)
  if d!=od:
   assert d[:3]==od[:3] and d[3]<od[3]
   assert green>2 and a>0
  if s[3]==255 and green>10:
   overlap+=d[3]>0
  if green<=2 or not a:
   assert s==os and d==od,('outside pixels changed',name)
 assert missing==0 and overlap==0,(name,missing,overlap)
 rows.append({'name':name,'solid_yarn_pixels':covered,'missing':missing,'dye_overlap':overlap,'outside_exact':True})
out={'status':'PASS','asset_diff_count':len(changed),'all_other_assets_unchanged':True,'masks':rows}
(ROOT/'dev/qa-out/sock-repair/verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
