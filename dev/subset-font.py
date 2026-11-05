#!/usr/bin/env python3
"""Build the local Chinese font from an OFL NotoSansSC-VF.ttf source.
Usage: python3 dev/subset-font.py /path/to/NotoSansSC-VF.ttf
Source and license are documented in assets/MANIFEST.md. No runtime download.
"""
from pathlib import Path
import sys
from fontTools import subset
ROOT=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1])
text=''.join(p.read_text() for p in [ROOT/'index.html',*sorted((ROOT/'js').glob('*.js'))])
chars={ord(c) for c in text if '\u2e80'<=c<='\u9fff' or '\uff00'<=c<='\uffef'}
font=subset.load_font(str(source),subset.Options())
missing=chars-set(font.getBestCmap())
if missing: raise SystemExit('Source font misses: '+''.join(map(chr,sorted(missing))))
options=subset.Options();options.layout_features=['*'];options.name_IDs=['*'];options.name_legacy=True
builder=subset.Subsetter(options=options);builder.populate(unicodes=chars);builder.subset(font)
subset.save_font(font,str(ROOT/'assets/fonts/atelier-sc.ttf'),options)
print(f'Subset includes {len(chars)} Chinese/full-width characters')
