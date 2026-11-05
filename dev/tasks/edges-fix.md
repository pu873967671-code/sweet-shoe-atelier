# edges-fix: Hark review findings on edges-a..d (2026-11-04)
Fix these regressions from the edges-* chunks, then re-verify:
- wedge (edges-a, case-1 pink satin + thigh black): on the REAR shoe's inner heel counter / collar return
  (just inside the trim, left of the rear leg) pale whitish undyed blotches appeared AFTER that were pink
  BEFORE. Dye mask was cut too far into the shoe body. Restore dye there; only the cream trim stays undyed.
  Check the same failure mode (undyed blotches just inside trim) on every edges-* base, all cases.
(append more findings below)
- platform (edges-b, case-1 pink satin): same failure, pale undyed blotches on the heel counter back edge and
  on the block heel (rear-opening-trim 3x crop, right side). Restore dye.
- studpump (edges-b, case-2): small white specks along the back edge of the heel counter AFTER; remove.
- Do a systematic automated check for every edges-* base/case: count pixels that were dyed BEFORE and are
  undyed AFTER outside the cream trim/piping; anything beyond a thin trim band is a regression -> fix.
- edges-c is the worst: loafer (penny strap & heel area), bowmule (bow loops and mule back), pearlheel, luciteheel,
  stiletto9 all show large undyed white/pale patches in pink satin case-1. Restore dye there.
- Applies to ALL 15 bases of edges-a, edges-b, edges-c. Fix each; keep the blue-line removal on the trim.
  If 15 min isn't enough, do the worst first and list the rest in PROGRESS.md under "## edges-fix remaining".
- Report per-base regression pixel counts before/after this fix in dev/qa-out/edges-fix/README.md.
