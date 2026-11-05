# Codex task: worn-shoe sprites in the fitting room (user-approved 2026-11-02 15:57)

## Goal
The fitting room (试穿间, `A.Fitting2D.render` in js/fitting2d.js, which may route to `A.RigidFitting`) must draw the NEW per-shoe worn sprites in `assets/worn/` instead of the old leg/shoe kits. The user approved these sprites (one per shoe style, both lower legs + feet + white shoes in the same standing pose). Every colour/material of the same style reuses the same sprite.

## Assets (already in place, do not regenerate)
- `assets/worn/<heel>.webp`: transparent RGBA, legs + white shoes. `<heel>` = the 20 ids in `A.SHOE_STYLES` / opts.heel.
- `assets/worn/<heel>_mask.webp`: grayscale, white = shoe pixels to dye (skin = black).
- `assets/worn/worn.json`: for each heel, `{x,y,w,h}` where the sprite sits in the REFERENCE frame = `A.Fitting2D.render(canvas 1220×1000, design, options, 'salon', cropped=true)` output. Embed it as a JS constant (no fetch; file:// must work).
- The sprite top edge is y=0 of the reference frame (legs run off the top).

## Implementation
1. New module `js/worn-sprites.js` (load it in index.html before fitting2d.js, add to any build/dist list the project uses). Export `A.WornSprites = {has(heel), paint(target, design, options, sceneId, cropped)}`.
2. Placement: map reference → target with `A.Showcase.project`: `g0 = project('salon',1220,1000,true)`, `g = project(sceneId,target.width,target.height,cropped)`; `k = g.scale/g0.scale`; `x' = g.cx + (x - g0.cx)*k`, `y' = g.floor + (y - g0.floor)*k` (use whatever fields project really returns; verify that in salon 1220×1000 the sprite lands exactly where the old flat figure was). When the mapped sprite top is > 0 (tall/portrait viewports), extend the legs upward so no cut is visible: stretch the top 6% rows of the sprite up to y=0 (legs are near-vertical there), or equivalent.
3. Dye: shoe colour from the design colour (opts.color hex). Draw sprite; on a copy, multiply the colour only where the mask is white (keep satin highlights readable like the product renderer does; dark colours like black must still show sheen: e.g. multiply then a soft screen of the original luminance at ~25%). Material: reuse the product renderer's material textures (satin/velvet/glitter/mesh/lace/patent…) clipped to the mask, same look as in js/shoe-renderer.js. Pattern motifs clipped to the mask the same way. If decorations/charms already have worn-pose projections that cannot be mapped, skip them in this pass rather than placing them wrong; list what was skipped in PROGRESS.md.
4. Soft contact shadow under each shoe (ellipse, multiply), like the old soleShadow.
5. Socks: the sprites are bare-legged. When `options.sock !== 'none'`, keep using the old renderer for now (do not break socks). Record this in PROGRESS.md.
6. In `render()`: if `A.WornSprites?.has(d.heel)` and sock is none → `return A.WornSprites.paint(...)`; set the same dataset fields (`fitting2dReady='true'`, `renderer='worn-sprite'`, heel, color…) so existing QA and app code keep working.
7. Cache tinted results by design key (bounded, like the existing cache). Never call getImageData on image-derived canvases. Cap DPR at 2.

## Do not
- Do not delete or edit the old kit assets (`assets/fitting2d/*`, `assets/src-user-legs-20261029/*`, `qa/research-rigid/**`).
- Do not touch js/audio.js routing or its test. Do not delete `qa/`, `dev/codex_*`.
- Do not change product (non-worn) shoe rendering.

## Acceptance
1. `node --check` every JS file; `node smoke-test.js`; `node qa/audio-test.js`; `node qa/pacing-test.js`; `node qa/scene-customer-test.js` pass. Update any test that asserted the old renderer name for the no-sock case.
2. Chromium (executable /usr/bin/chromium): contact sheet `qa/contact/worn-sprites-<time>.jpg` with all 20 heels in salon at 1336×790 (pink satin), plus flat & stiletto9 in black, cream glitter, and on all 5 scenes, and 390×844 for flat and stiletto9. Feet must sit on the pedestal, no seams, no cut-off legs at the top.
3. Commit after each step; update dev/PROGRESS.md section `## worn-sprites`.
