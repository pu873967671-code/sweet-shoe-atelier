#!/usr/bin/env python3
"""Keep genuine camera-specific crystal brooch pixels on the accepted 6cm kit.

The hand-reviewed contours follow individual bezels, never the edited shoe.
No generated body or skin pixels replace the immutable accepted paintings.
"""
from pathlib import Path
import json
import shutil
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'dev/crystalpump-source'
# Separate contours preserve the satin gaps between the crystal leaves.
REGIONS = {
 'product': [
  [(340,410),(346,409),(351,413),(365,413),(377,418),(384,425),(390,438),(388,443),(379,446),(366,442),(357,437),(350,428),(346,420),(341,418)],
  [(284,437),(289,434),(302,430),(318,430),(334,434),(348,441),(359,448),(365,448),(367,453),(360,457),(347,461),(331,461),(316,458),(300,451),(289,444),(284,442)],
  [(392,431),(399,430),(411,432),(418,439),(422,447),(419,455),(411,461),(402,463),(393,460),(389,453),(387,444)],
  [(384,455),(390,456),(390,466),(385,476),(376,484),(365,489),(350,491),(336,491),(332,494),(328,491),(330,486),(335,482),(341,472),(352,463),(367,458)],
  [(403,461),(412,460),(421,470),(425,482),(424,496),(420,506),(421,510),(416,514),(412,511),(411,505),(403,498),(398,488),(398,475)],
  [(421,448),(429,450),(438,457),(445,467),(449,475),(453,477),(453,483),(448,485),(444,481),(435,479),(426,473),(421,466),(418,457)]
 ],
 'fitting': [
  [(347,838),(353,838),(358,841),(374,837),(387,839),(399,845),(408,853),(415,862),(413,868),(406,870),(393,870),(379,865),(366,858),(357,849),(349,847),(346,843)],
  [(416,859),(422,854),(429,855),(437,861),(441,869),(439,879),(432,884),(423,883),(417,878),(414,869)],
  [(412,870),(416,876),(410,885),(401,894),(390,899),(375,902),(362,902),(353,900),(349,902),(346,900),(347,893),(353,888),(360,880),(373,873),(389,869),(404,868)],
  [(417,879),(423,883),(423,895),(419,909),(412,919),(402,925),(393,929),(391,933),(386,934),(383,930),(385,924),(384,914),(388,901),(395,889),(405,881)],
  [(437,881),(448,882),(461,893),(471,906),(477,919),(478,928),(482,932),(481,938),(475,940),(470,935),(459,933),(447,927),(438,918),(433,906),(432,893)],
  [(441,869),(454,866),(467,866),(479,871),(486,880),(490,883),(495,883),(497,889),(493,893),(488,893),(479,896),(467,896),(455,891),(445,884),(440,877)]
 ]
}

def rgba(path):
 return np.array(Image.open(path).convert('RGBA'))

def save(path, pixels):
 Image.fromarray(np.clip(pixels,0,255).astype('uint8')).save(path,lossless=True,method=6,exact=True)

metadata = {}
for view, folder, basepart in [('product','shoe2d','base'),('fitting','fitting2d','shoe')]:
 original = rgba(ROOT/f'assets/{folder}/stiletto6_{basepart}.webp')
 generated = Image.open(SRC/f'{view}.png').convert('RGBA')
 if view == 'product':
  bounds = generated.getchannel('A').point(lambda a:255 if a>127 else 0).getbbox()
  crop = generated.crop(bounds).resize((833,490),Image.Resampling.LANCZOS)
  generated = Image.new('RGBA',(1024,640));generated.paste(crop,(96,51))
 else:
  generated = generated.resize((1024,1024),Image.Resampling.LANCZOS)
 generated.save(SRC/f'{view}-normalized.png')
 generated = np.array(generated)
 region = Image.new('L',(original.shape[1],original.shape[0]))
 draw = ImageDraw.Draw(region)
 for points in REGIONS[view]:draw.polygon(points,fill=255)
 mask = cv2.GaussianBlur(np.array(region).astype('float32'),(0,0),.55)
 mask[mask<1] = 0
 upper = rgba(ROOT/f'assets/{folder}/stiletto6_upper.webp')
 # Original accepted cloth bounds are the final authority; ornaments never
 # paint on skin, cream collar, outsole or an empty camera-background pixel.
 mask *= upper[:,:,3]/255
 # The service exports nominally opaque interiors at alpha253/254. These
 # solid silver bezels/gems are opaque; our contour feather owns the edge.
 mask *= np.where(generated[:,:,3]>240,1,generated[:,:,3]/255)
 # Gaussian float rounding can otherwise turn an opaque 255 core into254,
 # leaving a one-level fabric wash over every gem facet.
 mask[mask>254] = 255
 studs = generated.copy();studs[:,:,3]=mask.astype('uint8')
 save(SRC/f'{view}-crystals.webp',studs)
 output = Image.fromarray(original);output.alpha_composite(Image.fromarray(studs))
 output = np.array(output);outside=mask==0;output[outside]=original[outside]
 save(ROOT/f'assets/{folder}/crystalpump_{basepart}.webp',output)
 assert np.array_equal(rgba(ROOT/f'assets/{folder}/crystalpump_{basepart}.webp')[outside],original[outside])
 assert np.array_equal(output[:,:,3],original[:,:,3]),'crystal brooch changed silhouette'
 for part in (['binding','insole','sole'] if view=='product' else ['legs','occlusion']):
  shutil.copyfile(ROOT/f'assets/{folder}/stiletto6_{part}.webp',ROOT/f'assets/{folder}/crystalpump_{part}.webp')
 for part in ['upper','shadow','highlight']:
  effect=rgba(ROOT/f'assets/{folder}/stiletto6_{part}.webp')
  # Opaque gem facets retain source colour under ALL finishes; only the
  # one-pixel antialiased bezel edge blends with the chosen fabric.
  effect[:,:,3]=(effect[:,:,3]*(1-mask/255)).astype('uint8')
  save(ROOT/f'assets/{folder}/crystalpump_{part}.webp',effect)
 metadata[view]={'base':'stiletto6','frame':[original.shape[1],original.shape[0]],'regions':REGIONS[view], 'outsideCrystalsExactRGBA':True,'exactBodyAlpha':True,'toeX':96 if view=='product' else 171,'groundY':540 if view=='product' else 964,'source':view+'.png'}
metadata['workflow']={'model':'gpt-image-2','mode':'images/edits','quality':'high','endpoint':'https://afgp.cc.cd/v1','runtimeNetwork':False}
(SRC/'export.json').write_text(json.dumps(metadata,indent=2)+'\n')
(SRC/'anchors.json').write_text(json.dumps(metadata,indent=2)+'\n')
sheet=Image.new('RGB',(1440,1100),'#ecfff5');draw=ImageDraw.Draw(sheet)
for col,(folder,part) in enumerate([('shoe2d','base'),('fitting2d','shoe')]):
 for row,bg in enumerate(['#fff4ed','#233c43']):
  im=Image.open(ROOT/f'assets/{folder}/crystalpump_{part}.webp').convert('RGBA')
  if col:
   legs=Image.open(ROOT/'assets/fitting2d/crystalpump_legs.webp').convert('RGBA')
   legs.putalpha(ImageChops.subtract(legs.getchannel('A'),Image.open(ROOT/'assets/fitting2d/crystalpump_occlusion.webp').getchannel('A')))
   legs.alpha_composite(im);im=legs
  im.thumbnail((690,510));tile=Image.new('RGB',(720,550),bg);tile.paste(im,((720-im.width)//2,0),im);sheet.paste(tile,(col*720,row*550));draw.text((col*720+12,row*550+525),folder+' / genuine crystal spray / exact accepted body and calf',fill='#f680ae')
sheet.save(SRC/'export-contact.jpg',quality=95)
print('PASS:13 layers, exact body alpha/outside-crystal RGBA, original skin/sole; camera-specific crystal extraction')
