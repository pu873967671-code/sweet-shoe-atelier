# Task: pattern/material must not cover the sole and heel (worn try-on)

## Bug
In the worn try-on (js/worn-sprites.js, sprites in assets/worn/), a printed pattern (e.g. the pink floral/lace "flowers" pattern, user screenshot: flat with frill socks, pattern covers the brown outsole and the heel lift at the back) is painted over the sole and heel block. In the product view (non-worn renderer) the same shoe keeps a plain brown sole and heel — that is correct and is the reference.

## Do
1. Verify first: render every one of the 20 worn heels (keys of SPRITES in js/worn-sprites.js) with every pattern option and a couple of colours/materials, sock none and frill; find every case where pattern or colour/material tint lands on the outsole, sole edge, heel lift/heel block (incl. stiletto heels), insole or piping that should keep its original colour. Write dev/qa-out/pattern_sole_before.jpg (contact sheet, zoomed on shoe bottoms).
2. Fix: build a per-sprite "no-pattern" region (sole/heel/outsole, and anything the product view keeps unpatterned) and exclude it from the pattern (and from colour tint if the product view also keeps those parts untinted). Prefer deriving it from existing per-sprite data (assets/worn/*_mask.webp alpha = dye mask; sprite colours: brown/tan sole, heel) into a NEW small mask file per base, e.g. assets/worn/<base>_sole.webp, applied for _frill/_lace variants via SPRITES x/y offsets. Do not edit existing image files. Bump ASSET_V.
3. Write dev/qa-out/pattern_sole_after.jpg (same cases) and confirm no regressions in sock/skin/shadow rendering.

## Hard constraints
- Do not modify existing image assets; only add new mask files. Do not touch js/audio.js routing, qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*.
- No pixel stretching/warping. Do not change non-worn product renderers.
- Render harness example: /workspace/work/fitqa/stage7.py (WebKit via playwright, already installed).
- Commit with a clear message.
