#!/usr/bin/env python3
"""Physical-action cues from local CC0 Kenney recordings (cloth, paper, tissue, coins).
Run this first, then dev/build-elegant-sfx.py, which composes the tuned chimes.
Originals/licenses remain development-only."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
 # Boutique cues (2026-11-14): paper, satin, ribbon and tissue instead of
 # generic interface blips. Entries: pack, source, length, start, gain dB.
 'switch':('kenney_casino-audio','card-slide-1',0.34,0.08,-4),
 'pick':('kenney_rpg-audio','cloth4',0.24,0.02,10),
 'drop':('kenney_rpg-audio','cloth2',0.3,0.02,4),
 'box':('kenney_casino-audio','cards-pack-take-out-1',0.45,0,-3),
 'ribbon':('kenney_rpg-audio','clothBelt',0.5,0.03,7),
 'tryon':('kenney_rpg-audio','cloth1',0.5,0.03,2),
}
out=ROOT/'assets/sfx';out.mkdir(exist_ok=True)
lines=['Sweet Shoe Atelier — local SFX, CC0 1.0 public domain.','Originals by Kenney (www.kenney.nl): Interface Sounds 1.0, RPG Audio, Casino Audio.','License: https://creativecommons.org/publicdomain/zero/1.0/','Sources and original License.txt files: dev/sfx_src (not shipped).','Processed with ffmpeg: mono 32 kHz, warm 6.5 kHz lowpass, soft limiter, short fade, Vorbis + MP3 Safari fallback.','']
for name,(pack,source,length,*rest) in SOURCES.items():
 start=rest[0] if rest else 0
 gain=rest[1] if len(rest)>1 else 0
 src=ROOT/'dev/sfx_src'/pack/'Audio'/(source+'.ogg')
 for extension,codec in [('ogg',['-c:a','libvorbis','-q:a','2']),('mp3',['-c:a','libmp3lame','-b:a','64k'])]:
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(src),'-t',str(length),'-ac','1','-ar','32000','-af',f'volume={gain}dB,highpass=f=70,lowpass=f={12000 if name in ("coin","sparkle") else 6500},alimiter=limit=0.8:level=false,afade=t=out:st={max(.03,length-.04)}:d=0.04',*codec,str(out/(name+'.'+extension))],check=True)
 lines.append(f'{name}.ogg / {name}.mp3 <- {pack}/Audio/{source}.ogg')
(out/'LICENSE.txt').write_text('\n'.join(lines)+'\n')
size=sum(p.stat().st_size for p in out.iterdir())
assert size<600*1024,size  # all cues, both scripts
print(f'PASS: {len(SOURCES)} CC0 cues, two codecs, {size:,} bytes')
