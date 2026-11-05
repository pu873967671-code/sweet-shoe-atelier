import numpy as np,cv2,glob,os
from PIL import Image
src=np.asarray(Image.open('mentor_think_clean.png').convert('RGBA')).astype(np.float32)
srcg=cv2.cvtColor(cv2.imread('in_white2.png'),cv2.COLOR_BGR2GRAY).astype(np.float32)
H,W=srcg.shape
mask=np.zeros((H,W),np.float32); cv2.ellipse(mask,(458,172),(70,56),-18,0,360,1,-1)
mask=cv2.GaussianBlur(mask,(0,0),9)
head=np.zeros((H,W),np.uint8); cv2.ellipse(head,(455,160),(120,110),-18,0,360,255,-1)
M0=np.load('M.npy'); os.makedirs('fp',exist_ok=True); R=np.eye(2,3,dtype=np.float32); log=[]
for f in sorted(glob.glob('f2/f_*.png')):
    fr=cv2.imread(f)
    w=cv2.warpAffine(fr,M0,(W,H),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REPLICATE)
    wg=cv2.cvtColor(w,cv2.COLOR_BGR2GRAY).astype(np.float32)
    try: cc,R=cv2.findTransformECC(srcg,wg,R.copy(),cv2.MOTION_EUCLIDEAN,(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,200,1e-6),head,5)
    except cv2.error: cc=-1
    al=cv2.warpAffine(w,R,(W,H),flags=cv2.INTER_LANCZOS4|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
    al=cv2.cvtColor(al,cv2.COLOR_BGR2RGB).astype(np.float32)
    # match colour to static (per-channel mean in mask)
    mm=mask>0.5
    for c in range(3): al[...,c]+= src[...,c][mm].mean()-al[...,c][mm].mean()
    out=src.copy(); out[...,:3]=src[...,:3]*(1-mask[...,None])+np.clip(al,0,255)*mask[...,None]
    Image.fromarray(out.astype(np.uint8),'RGBA').save('fp/'+os.path.basename(f).replace('f_','s_').replace('.png','.webp'),quality=95)
    log.append(round(float(cc),3))
print(log)
