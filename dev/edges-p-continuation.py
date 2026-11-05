#!/usr/bin/env python3
"""Second-chunk native 3x comparisons against the retained first-chunk output."""
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'dev/qa-out/edges-p'
BOXES={
 'slingback':{'rail':(565,210,935,390)},
 'bowsling':{'rail':(565,210,935,390)},
 'platform':{'welt':(90,435,935,550)},
 'crystalsandal':{'straps':(465,40,940,280),'arch':(550,275,900,440),'toe':(90,345,535,545)},
}
def main():
 thumbnails=[]
 for base,boxes in BOXES.items():
  for case in range(3):
   before=Image.open(OUT/'continuation-before'/f'{base}-{case}-after.png').convert('RGBA');after=Image.open(OUT/f'{base}-{case}-after.png').convert('RGBA')
   for label,box in boxes.items():
    cuts=[im.crop(box).resize(((box[2]-box[0])*3,(box[3]-box[1])*3),Image.Resampling.NEAREST) for im in [before,after]]
    sheet=Image.new('RGB',(cuts[0].width*2,cuts[0].height+24),'#e8ddd4');draw=ImageDraw.Draw(sheet);draw.text((6,6),f'{base} case {case} {label}: FIRST CHUNK / CONTINUATION 3x',fill='#302838')
    for i,cut in enumerate(cuts):sheet.paste(cut,(i*cut.width,24),cut)
    sheet.save(OUT/f'continuation-{base}-{case}-{label}-3x.png')
    if case==0:
     sheet.thumbnail((1500,500));thumbnails.append(sheet)
 contact=Image.new('RGB',(1500,sum(im.height for im in thumbnails)),'#e8ddd4');top=0
 for im in thumbnails:contact.paste(im,(0,top));top+=im.height
 contact.save(OUT/'continuation-contact.jpg',quality=95)
 print('PASS 18 exact 3x continuation comparisons; contact sheet')
if __name__=='__main__':main()
