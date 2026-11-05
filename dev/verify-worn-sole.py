#!/usr/bin/env python3
"""Compare the exhaustive before/after renders without touching qa/."""
import json,re
from pathlib import Path
import numpy as np
from PIL import Image,ImageFilter
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out';refs=json.loads(re.search(r'const SPRITES=(.*);',(ROOT/'js/worn-sprites.js').read_text()).group(1))
before=json.loads((OUT/'pattern-sole-before.json').read_text());after=json.loads((OUT/'pattern-sole-after.json').read_text());assert len(before['cases'])==len(after['cases'])==800
report={'cases':800,'findings':{},'errors':[]};protected=0
for b,a in zip(before['cases'],after['cases']):
 assert b['file']==a['file'];name=a['file'];heel=a['heel'];key=heel+('_frill' if a['sock']=='frill' else '');ref=refs[key];base=refs[heel]
 old=np.array(Image.open(OUT/'pattern-sole-before'/name).convert('RGBA'));new=np.array(Image.open(OUT/'pattern-sole-after'/name).convert('RGBA'));src=np.array(Image.open(ROOT/f'assets/worn/{key}.webp').convert('RGBA'))
 mask=Image.new('L',(ref['w'],ref['h']));mask.paste(Image.open(ROOT/f'assets/worn/{heel}_sole.webp').getchannel('A'),(base['x']-ref['x'],base['y']-ref['y']));m=np.array(mask)>0
 assert old.shape==new.shape
 # Drawing a registered source preserves upper legs, sock, silhouette and shadows.
 assert np.array_equal(old[:int(old.shape[0]*.58)],new[:int(new.shape[0]*.58)]),('upper changed',name)
 assert b['layout']==a['layout'] and b['contacts']==a['contacts'],('geometry changed',name)
 assert np.array_equal(old[:,:,3],new[:,:,3]),('alpha changed',name)
 change=np.max(np.abs(old[:,:,:3].astype(int)-new[:,:,:3].astype(int)),axis=2)>1
 # Interpolation can influence a neighbouring pixel at the exclusion boundary.
 expanded=np.array(mask.filter(ImageFilter.MaxFilter(5)))>0
 assert not np.any(change&~expanded),('outside protection',name,int(np.sum(change&~expanded)))
 # Protected fully opaque source pixels retain their actual painted RGB.
 valid=m&(src[:,:,3]==255)
 if a['sock']=='frill':valid &= np.array(Image.open(ROOT/f'assets/worn/{key}_sock.webp').convert('RGBA'))[:,:,3]==0
 valid &= np.array(Image.open(ROOT/f'assets/worn/{key}_mask.webp').convert('RGBA'))[:,:,3]>200
 error=np.max(np.abs(src[:,:,:3].astype(int)-new[:,:,:3].astype(int)),axis=2)
 # Source masking/draw premultiplication rounds at most one RGB level.
 assert not np.any((error>1)&valid),('protected source changed',name,int(np.sum((error>1)&valid)),int(error[valid].max()))
 protected+=int(valid.sum())
 report['findings'].setdefault(heel,{'cases':0,'affectedBefore':0,'maxChangedPixels':0});f=report['findings'][heel];f['cases']+=1;f['affectedBefore']+=bool(change.any());f['maxChangedPixels']=max(f['maxChangedPixels'],int(change.sum()))
report.update(status='PASS',protectedPixelComparisons=protected)
(OUT/'pattern-sole-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
