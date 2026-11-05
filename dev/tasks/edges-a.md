# edges-a (user approved 2026-11-04 17:00 CST: "一起")
Apply the Mary Jane edge standard (see dev/tasks/maryjane-mask-edges.md, maryjane-specks-strapshadow.md, and
dev/refine-maryjane-edges.py / dev/clean-maryjane-specks.py, commits 8e5d02d1 + 83fb1675) to these bases ONLY:
flat block kitten stiletto6 wedge
Per base, from its own paintings/masks (no one-template-fits-all; "不同鞋型光影不要硬套"):
1. Dye/motif must stop exactly at painted edges: cream piping/trim keeps its own colour (no blue inner line,
   no motif incursion), strap/collar/vamp edges smooth anti-aliased, no dye on sock/foot side.
2. No isolated dark/coloured specks on shoe, straps, piping, buckle, sole in any sock colour (black hardest).
3. If the base has a strap over the foot, no concave/inset shadow on the sock; at most a soft contact shadow
   just below the strap's lower edge.
Allowed: regenerate these bases' *_mask.webp, *_frill_mask.webp, *_lace_mask.webp, *_frill_sock.webp,
*_lace_sock.webp at the same size, changing only pixels in a narrow band at the edges, via a reproducible
script in dev/. Base-specific code only if needed. Never alter paintings, legs, sole, hose, or other bases;
keep maryjane and earlier fixes (opaque sock shading, flat knee) intact. No stretching/skewing.
Bump ASSET_V in js/worn-sprites.js by one letter.
Acceptance dev/qa-out/edges-a/: per base 3x BEFORE/AFTER crops of front + rear opening/trim (and strap if any)
for blue stars + lace cream, pink satin + thigh black, misty-blue floral + frill black. Chromium desktop+phone,
no page errors, other bases byte-identical; README.
