#!/usr/bin/env python3
"""Remove detached source-shoe scraps from worn ribbon extraction.

Run after worn ornament and thin-height/platform remap exporters. These fixed,
reviewed rectangles contain only detached shoe-source fragments, never the
connected ankle ribbon (whose leftmost pixel is beyond the rectangle).
No skin, shoe base, main ribbon or product-camera asset is modified.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'qa/ribbon-residue'
OUT.mkdir(exist_ok=True)
STYLES=['flat','kitten','block','wedge','stiletto6','stiletto9','platform']
report={'checks':[]}
sheet=Image.new('RGB',(1400,640),'#263a34')
for index,heel in enumerate(STYLES):
    roi=(300,760,425,900) if heel=='platform' else (300,800,410,900)
    for suffix in ['', '_tint']:
        path=ROOT/f'assets/fitting2d/accessories/{heel}_strap_ribbon{suffix}.webp'
        before=Image.open(path).convert('RGBA')
        after=before.copy();after.paste((0,0,0,0),roi)
        removed=sum(before.getchannel('A').crop(roi).histogram()[1:])
        # Exact RGBA invariance outside the narrowly reviewed source rectangle.
        expected=before.copy();expected.paste((0,0,0,0),roi)
        assert expected.tobytes()==after.tobytes()
        after.save(path,lossless=True,exact=True)
        decoded=Image.open(path).convert('RGBA')
        assert decoded.tobytes()==after.tobytes(),(heel,suffix,'lossless encoding drift')
        assert decoded.getchannel('A').crop(roi).getbbox() is None
        # Preserve all four surrounding rectangles, not just a bounding box.
        x0,y0,x1,y1=roi
        for region in [(0,0,1024,y0),(0,y1,1024,1024),(0,y0,x0,y1),(x1,y0,1024,y1)]:
            assert before.crop(region).tobytes()==decoded.crop(region).tobytes(),(heel,suffix,region)
        report['checks'].append({'style':heel,'layer':suffix or 'painting','removed_alpha_pixels':removed,'roi':roi,'outside_rgba_exact':True})
        if not suffix:
            for row,im in enumerate([before,decoded]):
                tile=im.crop((300,560,800,960)).resize((200,280))
                sheet.paste(tile,(index*200,row*320+20),tile)
                ImageDraw.Draw(sheet).text((index*200+5,row*320+3),heel+(' before' if row==0 else ' after'),fill='white')
report['status']='PASS'
(OUT/'report.json').write_text(json.dumps(report,indent=2))
sheet.save(OUT/'before-after.jpg',quality=95)
print(json.dumps({'status':'PASS','checks':len(report['checks']),'removed_alpha_pixels':sum(x['removed_alpha_pixels'] for x in report['checks'])}))
