#!/usr/bin/env python3
"""Small local CC0 Kenney cues; originals/licenses remain development-only."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 'tap':('kenney_interface-sounds','drop_003',0.19),
 'spawn':('kenney_interface-sounds','maximize_008',0.23),
 'merge':('kenney_interface-sounds','maximize_006',0.38),
 'coin':('kenney_rpg-audio','handleCoins2',0.3,0.04),
 'switch':('kenney_interface-sounds','bong_001',0.12),
 'pick':('kenney_interface-sounds','drop_002',0.19),
 'drop':('kenney_interface-sounds','drop_004',0.28),
 'box':('kenney_interface-sounds','minimize_006',0.38),
 'ribbon':('kenney_interface-sounds','question_002',0.33),
 'delivery':('kenney_interface-sounds','confirmation_001',0.29),
 'level':('kenney_interface-sounds','confirmation_004',0.49),
 'error':('kenney_interface-sounds','error_005',0.5),
 'unlock':('kenney_interface-sounds','question_001',0.49),
 'sparkle':('kenney_interface-sounds','glass_006',0.13),
}
out=ROOT/'assets/sfx';out.mkdir(exist_ok=True)
lines=['Sweet Shoe Atelier — local SFX, CC0 1.0 public domain.','Originals by Kenney (www.kenney.nl), Interface Sounds 1.0.','License: https://creativecommons.org/publicdomain/zero/1.0/','Sources and original License.txt files: dev/sfx_src (not shipped).','Processed with ffmpeg: mono 32 kHz, warm 6.5 kHz lowpass, soft limiter, short fade, Vorbis + MP3 Safari fallback.','']
for name,(pack,source,length,*rest) in SOURCES.items():
 start=rest[0] if rest else 0
 src=ROOT/'dev/sfx_src'/pack/'Audio'/(source+'.ogg')
 for extension,codec in [('ogg',['-c:a','libvorbis','-q:a','2']),('mp3',['-c:a','libmp3lame','-b:a','64k'])]:
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(src),'-t',str(length),'-ac','1','-ar','32000','-af',f'highpass=f=70,lowpass=f={12000 if name in ("coin","sparkle") else 6500},alimiter=limit=0.8:level=false,afade=t=out:st={max(.03,length-.04)}:d=0.04',*codec,str(out/(name+'.'+extension))],check=True)
 lines.append(f'{name}.ogg / {name}.mp3 <- {pack}/Audio/{source}.ogg')
(out/'LICENSE.txt').write_text('\n'.join(lines)+'\n')
size=sum(p.stat().st_size for p in out.iterdir())
assert size<600*1024,size
print(f'PASS: {len(SOURCES)} CC0 cues, two codecs, {size:,} bytes')
