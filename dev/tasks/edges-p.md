# edges-p: product (non-worn) view edges (user, 2026-11-04 17:00 CST)
User: "除了展示状态，正常状态也去检查这个问题". Besides the worn/salon fitting view, check the NORMAL product shoe
view (collection/workbench/product cards, js/shoe2d.js, js/accessory-renderer.js and their assets) for the same
problems on all 20 bases + maryjane: dye/motif bleeding into cream piping/trim/sole edges, ragged or stair-stepped
dye edges, isolated dark/coloured specks, concave strap shadows.
User approved changing the product-shoe rendering for this. Fix per base (no one template). Allowed: those bases'
product dye/motif mask files at the same size, editing only a narrow band at edges, via a reproducible script;
product-renderer code changes scoped to edge handling. Never alter paintings; no stretching/skewing; keep the
worn-view fixes intact. Do not touch Safari ctx.filter behaviour beyond what's needed. Bump cache version(s).
Acceptance dev/qa-out/edges-p/: survey table (which bases had it), 3x BEFORE/AFTER crops per fixed base for
blue stars, pink satin, misty-blue floral; Chromium desktop+phone, no page errors; README.
If 15 minutes isn't enough, finish the survey + as many bases as possible and list the rest in PROGRESS.md.

## Continuation (second chunk)
If dev/qa-out/edges-p/README.md already exists, continue from PROGRESS.md remaining items (crystalsandal, residual
slingback/bowsling rails, platform steps) instead of redoing finished bases. Also apply the anti-regression rule:
no pixel that was dyed BEFORE may become undyed AFTER except within ~3px of the true cream trim; report counts.
The phone heel-picker layout assertion failure is a pre-existing issue; do not touch it.
- Hark review of chunk 1 (opening-3x crops, case 1 pink satin): REGRESSIONS to fix first:
  loafer: penny-strap/tongue top edge now has a jagged pale/white outline AFTER (was clean pink BEFORE).
  bowmule: bow loop outlines became ragged with white jaggies AFTER. Restore the dye up to the painted edge;
  only real cream trim may be undyed. Check all other bases for the same jaggy-white-outline failure.
