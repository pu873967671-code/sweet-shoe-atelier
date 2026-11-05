# Task: upgrade Sweet Shoe Atelier demo to production-quality art (CrazyGames)

The game (index.html / style.css / game.js) works, but the shoe is a crude inline SVG and the UI uses text glyphs. All new painted assets are now in ./assets (webp). Rebuild the visuals around them and polish the whole demo so it feels like a real, juicy, commercial casual game. Keep all existing gameplay, i18n (en/zh), CrazyGames SDK v3 integration (loadingStart/Stop, gameplayStart/Stop, happytime, midgame + rewarded ads with graceful fallback, SDK.data saves with localStorage fallback, no custom fullscreen button), save format compatibility, and keep game logic testable in Node (smoke-test.js must still pass; DOM/canvas code must not run at import in Node).

## Assets (all in ./assets, sizes in assets/sizes.json)
- Shoe bases (white satin, side view, toe LEFT, transparent): shoe_{heel}_{strap}.webp, heel ∈ flat|block|kitten|wedge, strap ∈ none|thin|pearl|cross|ribbon (20 images, 900px wide, heights differ). Anchors (normalized 0..1 of each image) in assets/shoe_anchors.json: `toe` = good spot for toe charm, `back` = top of heel collar for heel décor. EMBED this JSON into game.js as a constant (fetch fails on file://). Feel free to refine offsets.
- Decorations (transparent): bow.webp (white satin bow; small=decoration small, big=decoration big; tint it softly toward the shoe colour or keep white/cream — whichever looks best), pearl_drop.webp (decoration drop), flower.webp (decoration flower), charm_pearl.webp, charm_crystal.webp, charm_minibow.webp (toe charms).
- Material textures: tex_satin, tex_velvet, tex_glitter (opaque grayscale, tileable), tex_mesh, tex_lace (white on transparent, tileable).
- Pattern motifs (white, transparent): motif_flower, motif_heart, motif_star; dots can be drawn procedurally.
- Customers: c_{bride|buns|casual|pink|school|tea}_{neutral|happy|sad}.webp. Map themes to these (existing asset ids c_bride etc). Show neutral while waiting, happy on 3 stars, neutral/slight on 2, sad on 1 star or timeout.
- UI icons: icon_color, icon_material, icon_pattern, icon_strap, icon_decoration, icon_heel, icon_charm (category tabs), icon_coin, icon_star, icon_heart, icon_clock, icon_gift (HUD, rewards, buttons).
- Scene: bg_shop.webp (16:9 boutique), pedestal.webp (shoe stands on it), box_closed.webp, box_open.webp (pack animation), confetti.webp, sparkle.webp (particles), logo.webp ("Sweet Shoe Atelier" wordmark for title/loading; for zh show the Chinese brand text under/near it).

## Shoe renderer (core of the job)
Replace the SVG shoe everywhere (stage, collection/gallery thumbnails, summary best design, box/pack animation, shop previews) with a layered <canvas> renderer with caching:
1. Draw base image shoe_{heel}_{strap}.
2. Tint to the chosen colour (multiply then restore alpha with destination-in; keep satin highlights readable — e.g. add a gentle screen/soft-light highlight pass). Dark "black" must still look nice, not flat.
3. Material via source-atop on the shoe: satin = tex_satin overlay subtle; velvet = tex_velvet multiply + slightly deeper colour, reduced sheen; glitter = tex_glitter screen + a few animated twinkles (sparkle.webp) on stage; mesh = tex_mesh overlay with the body slightly translucent; lace = tex_lace pattern over the upper.
4. Pattern via tiled motifs (createPattern) source-atop, avoid the sole as much as practical (e.g. clip to upper part), tasteful density/opacity, motif tinted white/cream or contrasting soft colour.
5. Heel décor at `back` anchor, toe charm at `toe` anchor, scaled relative to shoe width, soft drop shadow.
6. Never call getImageData on image-derived canvases (file:// tainting). Cap devicePixelRatio at 2. Cache composites by design key.
Shoe sits on pedestal with soft shadow; small bounce + sparkle burst on each change.

## Polish
- Preload all assets with a real progress bar on the loading screen (logo + progress), between SDK loadingStart/loadingStop. Fail-soft if an image fails.
- Category tabs and option swatches use the icons and real previews: colour swatches as glossy circles; material swatches show the texture; pattern swatches show the motif; strap/heel swatches show small thumbnails of the actual shoe image; decoration/charm swatches show the sprite. Locked items show coin price + lock.
- HUD: icon_coin coins counter with coin-fly animation on payout, icon_clock patience bar, stars with pop animation, icon_heart streak.
- Customer: slide/fade entrance, speech bubble with requirement chips (with icons), expression swap on result, exit.
- Pack: shoe shrinks into box_open → lid/box_closed → bounce → confetti on 3 stars → rating card.
- Title screen: bg_shop, logo, main buttons with icons; subtle floating sparkles.
- Typography, spacing, contrast (WCAG AA for text), hover/active/focus states, prefers-reduced-motion support.
- Layout must look great at 1280x720, 800x450 (CrazyGames minimum embed), 1920x1080, and mobile portrait 390x844 / landscape 844x390. No scrollbars on desktop sizes, no overlapping, everything tappable (>=40px touch targets on mobile).
- Remove reference_v1.html. Keep everything relative paths, no external CDNs except the CrazyGames SDK script.

## Testing (required)
- `node --check game.js` and `node smoke-test.js` (update it for any new pure logic).
- Visual QA with headless Chromium: python3 + playwright is installed; launch with `p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])`, serve the folder with `python3 -m http.server`. Write qa/screenshot.py that captures title, gameplay with a complex design (e.g. rose + glitter + stars + pearl strap + big bow + crystal, kitten heel), result screen, collection, shop at 1280x720, 800x450, 390x844, 844x390 into qa/*.png, and also logs console errors (SDK script failure offline is acceptable). Fix every console error from your own code and every visual overlap you find. Also test opening index.html via file://.
- Finally build ../sweet-shoe-atelier-crazygames.zip containing only runtime files (index.html, style.css, game.js, assets/ without sizes.json and shoe_anchors.json if embedded). Keep zip under 10 MB. Update README.md (features, CrazyGames checklist, file list).
