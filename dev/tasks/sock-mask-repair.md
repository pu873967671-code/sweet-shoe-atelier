# Codex task: repair near-empty short-sock masks (user-approved 2026-11-04 08:09, "好")

## Problem
These 17 sock masks in assets/worn/ are almost empty (alpha >=128 on ~0 pixels; only thin outlines), while good ones (flat_lace, kitten_lace, stiletto9_lace/frill...) cover ~45k-55k px:

stiletto6_lace, stiletto6_frill, slingback_lace, slingback_frill, pearlpump_lace, pearlpump_frill, bowsling_lace, bowsling_frill, crystalpump_lace, crystalpump_frill, studpump_lace, studpump_frill, bowmule_lace, bowmule_frill, luciteheel_lace, luciteheel_frill, kitten_frill

(bootie_* masks are small on purpose - boot covers the sock; leave them.)

Result in game: on these variants the short sock is treated as shoe upper - it gets the shoe colour/pattern (e.g. polka dots), looks grey-green translucent, and shows the satin sheen as one or two hard diagonal light bands. User reported it on slingback lace socks.

## Do
1. Find how the good `<heel>_<frill|lace>_sock.webp` were produced (git log: 7b324e0e, 3a0396fc, 435e1587, e510e436, 9392063f; dev/build-worn-assets.py; PROGRESS `## worn-socks`). The sprites `<heel>_<variant>.webp` have socks painted light green. Rebuild the 17 masks with the same method/format as the good ones (same size as the variant sprite, same channel convention: RGB = baked grey sock shade as in 9392063f, alpha = sock coverage, soft edge), covering the whole sock (cuff/lace/frill trim included) and nothing that is shoe, strap, buckle, bow, stud, crystal, pearl, heel or skin.
2. Also make sure the matching `<heel>_<variant>_mask.webp` (shoe dye mask) does not include sock pixels, so the shoe dye/pattern/sheen never lands on the sock. Change those only if they do include sock pixels.
3. Bump ASSET_V in js/worn-sprites.js (to 20261104b).

## Do not
- Touch any other asset, any good sock mask, non-worn renderers, js/audio.js routing, assets/src-user-legs-20261029/*, assets/fitting2d/*, qa/research-rigid/**. Do not delete qa/ or dev/codex_*.
- No stretching/shearing/warping pixels. Pixels outside the sock/shoe-mask regions unchanged.

## Acceptance
1. node --check js/*.js; existing tests (smoke-test.js, qa/worn-sprites-test.py, others that exist) pass.
2. Contact sheet `dev/qa-out/sock-repair/contact.jpg`: all 20 bases x lace and frill, pink satin shoe with 'dots' pattern, cream socks, salon scene (crop on feet), BEFORE (HEAD~) vs AFTER. Also slingback lace in mint/black/pink sock colours. Sock must be solid cream (no dots, no hard light band, no green), shoe covers sock at opening.
3. Print a per-file table of alpha>=128 pixel counts before/after for the 17 masks.
4. Commit; update dev/PROGRESS.md `## sock-mask-repair`.
