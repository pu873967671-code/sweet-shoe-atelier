# Codex task: socks on worn sprites (user-approved 2026-11-02 16:30, "继续")

Context: js/worn-sprites.js (your previous task, see PROGRESS `## worn-sprites`) now draws every shoe with no socks. Socks still fall back to the old kit renderer. Make ALL 9 sock options render on the worn sprites, then remove the old-kit fallback for every case that the sprites cover.

## New assets (already in place in assets/worn/, worn.json updated — re-embed the JSON constant)
- `<heel>_frill.webp`, `<heel>_lace.webp`: full sprites (legs + ankle socks + white shoes), same reference frame as `<heel>.webp`, own x/y/w/h in worn.json `sprites["<heel>_frill"]` etc.
- `<heel>_frill_mask.webp` / `_lace_mask.webp`: shoe dye mask (as before).
- `<heel>_frill_sock.webp` / `_lace_sock.webp`: sock mask (white = sock). The socks are painted light green in the sprite: recolour them by luminance to the chosen sock colour (options.color: pink, mint, cream, white, black — use the same hex values the old sock code used). Formula that tested well: sockRGB = colour × (lum / lumRef) where lum = 0.3R+0.59G+0.11B of the sprite and lumRef ≈ the 80th-percentile lum of sock pixels (precompute once per sprite, or use a constant ~205). Black must stay readable (lift: max(colour, 34) per channel before multiply). Blend by the sock mask alpha.
- The base `<heel>.webp`/`_mask.webp` were also re-keyed (cleaner shoe mask); nothing to change for them.

## Long hosiery (sheer, knee, thigh, blacksheer, pantyhose, opaque, fishnet) — procedural, no new art
Use the plain `<heel>` sprite. Skin region = sprite alpha AND NOT shoe mask. Paint over the skin region only (shoe drawn/dyed on top so the shoe still covers the foot):
- sheer / pantyhose: colour multiply at ~35% opacity + edge darkening (denier effect): darker near the leg silhouette edges (use a blurred-alpha edge term, e.g. 1 − blur(alpha, 18px) remapped) + keep a soft specular highlight from the original skin luminance. pantyhose = sheer with nude-tone default when color is cream/white.
- blacksheer: same with black fixed, ~55% opacity, strong edge darkening.
- opaque: ~90% opacity colour, edge darkening, subtle knit noise optional.
- knee / thigh: opaque-ish (~85%) sock colour; knee-high has a cuff band visible only if the cuff falls inside the frame (in the reference frame the knee is above y=0, so effectively full coverage — that is fine).
- fishnet (Diamond knit): sheer base 15% + diamond lattice pattern (~14px cells at reference scale, thin lines in sock colour), clipped to skin region, following the leg roughly (a simple rotated lattice is acceptable).
All of this must be done with canvas compositing (no per-pixel getImageData on image canvases), cached per (heel, sock, colour, material, shoe colour, size).

## Integration
- fitting2d.js render(): route every sock option to A.WornSprites when the heel has a sprite. Keep the old renderer only as a load-failure fallback.
- dataset: `renderer='worn-sprite'`, `sock=<id>`, `sockColor=<id>`.

## Do not
- Do not edit/delete assets in assets/worn/ (other than reading), assets/fitting2d/*, assets/src-user-legs-20261029/*, qa/research-rigid/**. Do not touch js/audio.js routing. Do not delete qa/ or dev/codex_*.

## Acceptance
1. node --check; smoke-test.js, qa/audio-test.js, qa/pacing-test.js, qa/scene-customer-test.js, qa/worn-sprites-test.py pass (update assertions that expected the old renderer for sock cases).
2. Chromium contact sheet `qa/contact/worn-socks-<time>.jpg`: flat, stiletto9, ballet, crystalsandal, bootie × all 10 sock options (none + 9) in salon 1336×790, pink satin shoe, cream socks; plus stiletto9 × each sock colour for frill and sheer; plus 390×844 stiletto9 frill. No seams, sock colours correct, shoe covers sock at the opening, no green showing.
3. Commit per step; update dev/PROGRESS.md `## worn-socks`.
