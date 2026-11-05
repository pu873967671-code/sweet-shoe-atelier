# edges-p3: fix regressions from edges-p in the product (non-worn) view (Hark review 2026-11-04 19:15 CST)
Product view assets assets/shoe2d/*_upper.webp (and related masks) were edited by edges-p chunks.
In dev/qa-out/edges-p/*-1-opening-3x.png (pink satin) these REGRESSIONS remain:
- loafer: the penny-strap/tongue top edge has a jagged pale/white outline AFTER that was clean pink BEFORE.
- bowmule: the bow loop outlines became ragged with white jaggies AFTER.
Fix: restore dye/edge up to the painted edge there (use the pre-edges-p version as reference: git show
c69f3e06:<path>); only true cream trim/piping may be undyed. Then scan ALL 20 bases x 3 cases for the same
"jagged white outline on a dyed part (straps, bows, tongues, heels)" failure, automatically (compare to the
pre-edges-p render: pixels whose colour moved toward cream/white outside the true trim) and fix each.
Keep the good parts of edges-p (pink/blue fringe removed from cream trim). No painting changes, no stretching.
Bump cache version. Acceptance in dev/qa-out/edges-p3/: per fixed base 3x BEFORE(pre-edges-p)/AFTER crops,
counts table, Chromium desktop+phone no page errors, README. Phone heel-picker assertion is pre-existing; ignore.
