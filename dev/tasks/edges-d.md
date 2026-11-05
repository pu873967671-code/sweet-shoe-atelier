# edges-d (user approved 2026-11-04 17:00 CST: "一起")
Apply the Mary Jane edge standard (see dev/tasks/maryjane-mask-edges.md, maryjane-specks-strapshadow.md, and
dev/refine-maryjane-edges.py / dev/clean-maryjane-specks.py, commits 8e5d02d1 + 83fb1675) to these bases ONLY:
ballet slingback bowsling crystalsandal
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
Acceptance dev/qa-out/edges-d/: per base 3x BEFORE/AFTER crops of front + rear opening/trim (and strap if any)
for blue stars + lace cream, pink satin + thigh black, misty-blue floral + frill black. Chromium desktop+phone,
no page errors, other bases byte-identical; README.

## MANDATORY anti-regression (Hark review of edges-a/b/c, 2026-11-04)
Earlier chunks cut the dye mask too far: pale UNDYED blotches appeared inside the shoe body next to the trim,
on heel counters, heels and bows (worst: loafer, bowmule, pearlheel, stiletto9, platform, wedge).
Only the cream trim/piping itself may become undyed. Before committing, for every base/case compute pixels that
were dyed BEFORE and are undyed AFTER; any such pixel farther than ~3px from the true cream trim is a bug -> fix.
Report the counts per base in the README. Pink satin case is the most revealing; check it at 3x.
