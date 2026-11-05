#!/usr/bin/env python3
"""Align gpt-image-2 shoe edits, isolate changed ornament paint, export fixed-frame layers.
The runtime base painting is never modified. Source edits and extraction diagnostics
are source-only. Rebuild: python3 dev/extract-accessory-edits.py [--only STEM].
"""
import argparse, fcntl, hashlib, json, os, tempfile
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'dev/accessory-edits'; OUT=ROOT/'assets/shoe2d/accessories'
HEELS=['flat','kitten','block','wedge']
OPTIONS={'strap':['thin','ribbon','cross','pearl'],'decoration':['small','big','flower','drop'],'charm':['mini','pearl','crystal']}
SIZE=(1024,640)
# Avoid oversubscribing the offline batch (ECC already works on a small frame).
cv2.setNumThreads(1)

def save_image(image,path,**options):
    """Readers always see a complete old or new image, including during QA."""
    temporary=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
    try:
        image.save(temporary,format=Image.registered_extensions()[path.suffix],**options)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

def save_report(path,report):
    temporary=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
    try:
        temporary.write_text(json.dumps(report,indent=2)+'\n')
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
def region(heel,category,value):
    if category=='decoration': return (700,5,1015,490 if heel=='flat' else 410)
    if category=='charm': return (135,310,490,505)
    if value=='cross': return (160,270,745,505)
    return (365,130 if heel=='flat' else 65,875,520)
def key(arr):
    a=arr.astype(np.float32); r,g,b=a[:,:,0],a[:,:,1],a[:,:,2]
    return np.clip(1-(g-np.maximum(r,b)-12)/110,0,1)
def accessory_mask(aligned,base,source_alpha,heel,category,value):
    """Keep changed ornament components, never an edit's repainted shoe/matte.

    Jewellery uses its warm bezel/neutral pearl cores; closing their outlines
    retains gemstone interiors without admitting the source's lilac upper.
    Feather is inward and every final pixel is gated by the original difference.
    """
    a=aligned.astype(np.float32); b=base.astype(np.float32)
    delta=np.max(np.abs(a-b),axis=2)
    x0,y0,x1,y1=region(heel,category,value)
    support=np.zeros(delta.shape,np.uint8); support[y0:y1,x0:x1]=1
    coverage=np.minimum(key(aligned),source_alpha)
    changed=(delta>18)&(coverage>.05)&(support>0)
    lilac=(a[:,:,2]-a[:,:,1]>3)&(a[:,:,0]-a[:,:,1]>2)&(a[:,:,1]<237)
    fabric_option=(category=='strap' and value!='pearl') or (category=='decoration' and value in ('small','big')) or (category=='charm' and value=='mini')
    if fabric_option or value=='flower':
        seed=changed & (delta>27) & lilac
        # Gold buckles and flower centres belong to the adjacent painted fabric.
        warm=(a[:,:,0]-a[:,:,2]>16)&(a[:,:,0]-a[:,:,1]>5)
        seed |= changed & warm & (cv2.dilate(seed.astype('uint8'),np.ones((11,11),np.uint8))>0)
    else:
        warm=(a[:,:,0]-a[:,:,2]>15)&(a[:,:,0]-a[:,:,1]>4)
        neutral=(np.min(a,axis=2)>193)&(np.ptp(a,axis=2)<27)
        seed=changed & (delta>27) & (warm|neutral)
    # Reject isolated noise and narrow piping fragments away from the ornament.
    seed=cv2.morphologyEx(seed.astype('uint8'),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(seed,8)
    solid=np.zeros(delta.shape,np.uint8)
    for i in range(1,n):
        area=stats[i,cv2.CC_STAT_AREA]; w=stats[i,cv2.CC_STAT_WIDTH]; h=stats[i,cv2.CC_STAT_HEIGHT]
        if area<22 or (not fabric_option and value!='flower' and max(w,h)>max(90,min(w,h)*8)): continue
        # A uniformly changed crop is a regenerated matte, never an ornament.
        # Difference gating alone cannot reject it when the entire matte changed.
        if w*h>.6*(x1-x0)*(y1-y0) and area/(w*h)>.9: continue
        component=(labels==i).astype('uint8')
        # Jewellery bezels enclose pale-lilac crystals; keep their interior.
        if not fabric_option:
            contours,_=cv2.findContours(component,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(component,contours,-1,1,cv2.FILLED)
        solid|=component
    # Authored jewellery windows isolate the compact bezel/pendant rather than
    # the regenerated lilac upper. A filled contour spanning the shoe piping
    # otherwise encloses an entire triangular piece of the original shoe.
    if category=='charm' and value in ('pearl','crystal'):
        windows={
            'flat': {'pearl':(250,371,319,430),'crystal':(246,383,349,444)},
            'kitten': {'pearl':(278,380,351,444),'crystal':(270,380,371,454)},
            'block': {'pearl':(285,374,372,434),'crystal':(246,389,350,457)},
            'wedge': {'pearl':(250,347,337,412),'crystal':(237,341,347,427)},
        }
        xx0,yy0,xx1,yy1=windows[heel][value]
        local=np.zeros_like(solid)
        cv2.ellipse(local,((xx0+xx1)//2,(yy0+yy1)//2),((xx1-xx0)//2,(yy1-yy0)//2),0,0,360,1,-1)
        solid &= local
        solid[lilac]=0
    elif category=='decoration' and value=='drop':
        # Keep the actual right-side chain and pear drop, excluding the
        # unrelated diagonal collar and vertical heel-face streak.
        local=np.zeros_like(solid)
        yy0,yy1={'flat':(164,297),'kitten':(62,228),'block':(62,213),'wedge':(85,244)}[heel]
        local[yy0:yy1,856:946]=1
        solid &= local
        solid[lilac]=0
        count,parts,areas,_=cv2.connectedComponentsWithStats(solid,8)
        keep=1+np.argmax(areas[1:,cv2.CC_STAT_AREA]) if count>1 else 0
        solid=(parts==keep).astype('uint8') if keep else solid
    elif category=='strap' and value=='pearl':
        # Pearl cores are neutral; lavender shoe repainting is never jewellery.
        solid[lilac]=0
        # Isolated collar piping is warm like the bezel. Require proximity to
        # a compact, truly neutral pearl core, then retain its surrounding gold.
        cores=((np.min(a,axis=2)>205)&(np.ptp(a,axis=2)<17)&(solid>0)).astype('uint8')
        count,parts,areas,_=cv2.connectedComponentsWithStats(cores,8)
        cores=np.isin(parts,[i for i in range(1,count) if areas[i,cv2.CC_STAT_AREA]>55 and min(areas[i,cv2.CC_STAT_WIDTH],areas[i,cv2.CC_STAT_HEIGHT])>6]).astype('uint8')
        proximity=cv2.distanceTransform(1-cores,cv2.DIST_L2,5)
        solid &= (proximity<13).astype('uint8')
        solid=cv2.morphologyEx(solid,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    elif category=='strap' and value=='cross':
        solid=cv2.morphologyEx(solid,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
        count,parts,areas,_=cv2.connectedComponentsWithStats(solid,8)
        solid=np.isin(parts,[i for i in range(1,count) if areas[i,cv2.CC_STAT_AREA]>=95]).astype('uint8')
    # A 1.5px inward feather preserves thin cords, with no outward matte halo.
    solid=(solid>0)&changed
    distance=cv2.distanceTransform(solid.astype('uint8'),cv2.DIST_L2,5)
    alpha=np.clip(distance/1.5,0,1)*coverage
    lum_a=a@np.array([.2126,.7152,.0722]); lum_b=b@np.array([.2126,.7152,.0722])
    near=(cv2.dilate(solid.astype('uint8'),np.ones((5,5),np.uint8))>0)&~solid
    shadow=np.clip((lum_b-lum_a-12)/np.maximum(30,lum_b),0,.28)*near*changed*(key(base)>.8)*coverage
    # Never turn broad lilac shoe recolouring into a dark rectangular shadow.
    if not fabric_option and value!='flower': shadow*=~lilac
    rgb=a.copy(); rgb[:,:,1]=np.minimum(rgb[:,:,1],np.maximum(rgb[:,:,0],rgb[:,:,2])+5)
    fabric=lilac & solid if fabric_option else np.zeros(delta.shape,bool)
    gray=np.clip(lum_a*1.2,0,255)
    rgb=np.where(fabric[:,:,None],gray[:,:,None],rgb)
    rgb=np.where(solid[:,:,None],rgb,0)
    alpha=np.maximum(alpha,shadow)
    alpha[~changed]=0
    return rgb,alpha,fabric,delta

def extract(heel,category,value):
    name=f'{heel}_{category}_{value}'; path=SRC/(name+'.png')
    if not path.exists(): raise FileNotFoundError('Missing accessory source: '+str(path))
    base=np.array(Image.open(SRC/(heel+'-input.png')).convert('RGB'))
    source=Image.open(path).convert('RGBA').resize(SIZE,Image.Resampling.LANCZOS)
    green=Image.new('RGBA',SIZE,'#00ff00');green.alpha_composite(source)
    edit=np.array(green.convert('RGB'))
    roi=region(heel,category,value); x0,y0,x1,y1=roi
    mask=np.full((640,1024),255,np.uint8);mask[max(0,y0-25):min(640,y1+25),max(0,x0-25):min(1024,x1+25)]=0
    # Stable sole/quarter edges outside ornament determine camera registration.
    warp=np.eye(2,3,dtype=np.float32); score=None
    try:
        score,warp=cv2.findTransformECC(cv2.cvtColor(base,cv2.COLOR_RGB2GRAY).astype(np.float32)/255,cv2.cvtColor(edit,cv2.COLOR_RGB2GRAY).astype(np.float32)/255,warp,cv2.MOTION_AFFINE,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,100,1e-5),mask,5)
        if not (.82<np.linalg.det(warp[:,:2])<1.22): warp=np.eye(2,3,dtype=np.float32);score=None
    except cv2.error: pass
    aligned=cv2.warpAffine(edit,warp,SIZE,flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,255,0))
    source_alpha=cv2.warpAffine(np.array(source)[:,:,3].astype('float32')/255,warp,SIZE,flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    rgb,alpha,fabric,delta=accessory_mask(aligned,base,source_alpha,heel,category,value)
    rgba=np.dstack((rgb,np.round(alpha*255))).clip(0,255).astype('uint8')
    # Lossless alpha retains the narrow feather; unchanged pixels stay exact zero.
    rgba[rgba[:,:,3]==0,:3]=0
    OUT.mkdir(exist_ok=True)
    save_image(Image.fromarray(rgba,'RGBA'),OUT/(name+'.webp'),quality=90,method=6,exact=True)
    tint_path=OUT/(name+'_tint.webp')
    if fabric.any():
        tint=np.dstack((np.full((640,1024,3),255,dtype='uint8'),np.round(fabric*alpha*255).astype('uint8')))
        save_image(Image.fromarray(tint,'RGBA'),tint_path,lossless=True,method=6)
    else:
        tint_path.unlink(missing_ok=True)
    assert not rgba[delta<=18,3].any(), name+' retained unchanged shoe pixels'
    bbox=Image.fromarray(rgba,'RGBA').getbbox()
    diagnostic=Image.new('RGB',(2048,640),'#eef7f2');diagnostic.paste(Image.fromarray(base),(0,0))
    render=Image.open(ROOT/f'assets/shoe2d/{heel}_base.webp').convert('RGBA');render.alpha_composite(Image.fromarray(rgba,'RGBA'))
    bg=Image.new('RGBA',SIZE,'#eef7f2');bg.alpha_composite(render);diagnostic.paste(bg.convert('RGB'),(1024,0))
    save_image(diagnostic,SRC/(name+'-review.jpg'),quality=90)
    return {'name':name,'roi':roi,'bbox':bbox,'pixels':int((rgba[:,:,3]>0).sum()),'ecc':score,'warp':warp.tolist(),'source':str(path.relative_to(ROOT))}
def build():
    names=[f'{h}_{c}_{v}' for h in HEELS for c,vs in OPTIONS.items() for v in vs]
    p=argparse.ArgumentParser();p.add_argument('--only',choices=names);args=p.parse_args();records=[]
    for h in HEELS:
      for c,vs in OPTIONS.items():
       for v in vs:
        if args.only and args.only!=f'{h}_{c}_{v}': continue
        result=extract(h,c,v)
        if result: records.append(result);print(result['name'],result['pixels'],result['bbox'],flush=True)
    report_path=SRC/'extraction-report.json'
    # A focused repair must not discard registration evidence for the other43.
    if args.only and report_path.exists():
        previous={r['name']:r for r in json.loads(report_path.read_text())['layers']}
        previous.update({r['name']:r for r in records})
        records=[previous[name] for name in names if name in previous]
    save_report(report_path,{'canvas':SIZE,'layers':records})
    if records:
      for background,label in [('#eef7f2','light'),('#202a36','dark')]:
       # Separate sprite and shoe sheets expose alpha defects that an ivory shoe hides.
       for sprites_only,kind in [(False,'contact'),(True,'sprites')]:
        sheet=Image.new('RGB',(4400,4*280),background);draw=ImageDraw.Draw(sheet)
        for hi,h in enumerate(HEELS):
         for ci,(c,v) in enumerate((c,v) for c,vs in OPTIONS.items() for v in vs):
          path=OUT/f'{h}_{c}_{v}.webp'
          if not path.exists(): continue
          art=Image.new('RGBA',SIZE) if sprites_only else Image.open(ROOT/f'assets/shoe2d/{h}_base.webp').convert('RGBA')
          art.alpha_composite(Image.open(path).convert('RGBA'));art.thumbnail((400,250))
          tile=Image.new('RGBA',(400,280),background);tile.alpha_composite(art)
          sheet.paste(tile.convert('RGB'),(ci*400,hi*280))
          draw.text((ci*400+3,hi*280+255),h+'/'+c+'/'+v,fill='#284d46' if label=='light' else '#f0f8f4')
        save_image(sheet,SRC/f'extraction-{kind}-{label}.jpg',quality=96)

def main():
    # Two simultaneous rebuilds must not mix sprite/report generations.
    key=hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
    with open(Path(tempfile.gettempdir())/('accessory-extract-'+key+'.lock'),'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        build()
if __name__=='__main__':main()
