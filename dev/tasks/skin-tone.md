# Task: customer skin tone on the worn try-on legs

## Goal
Customers can have different skin tones (e.g. the bride `c_bride` has deep brown skin; the others are fair). When a customer tries shoes on, the legs/feet in the worn try-on (js/worn-sprites.js) must take that customer's skin tone, with hosiery layered on top as today. Free design / no customer = current default skin (no tint).

## Implementation
1. js/data.js: add an optional `skin` field per customer (hex colour). Set it for every customer using asset `c_bride` (deep warm brown, around #8a5a3c; tune so it matches the bride portrait assets/c_bride_neutral.webp). Leave fair customers without the field (= no tint).
2. Pass the active customer's skin to the fitting render (find where Fitting2D.render / WornSprites paint is called for a customer order; add it to the fitting options, e.g. `o.skin`, and make sure A.cleanFittingOptions keeps it).
3. js/worn-sprites.js: tint only skin pixels, using `assets/worn/<base>_legs.webp` ALPHA as the skin mask (RGB there is front/back leg shading info, ignore it for tinting). Load the legs map for ALL sock types (currently skipped for short socks). Apply the tint to the sprite BEFORE hosiery is applied, so sheer/fishnet/opaque layer on top of the tinted skin. Tint method must keep the painted shading and outlines: e.g. luminance-preserving recolour (multiply by tone + soft-light/screen for highlights), no flat fill. Shoe pixels must stay untouched. Include skin in the cache key. Bump ASSET_V.
4. Non-worn renderers: do not change.

## Hard constraints
- Do not modify any image asset files. Do not change js/audio.js routing. Do not touch qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*.
- No pixel stretching/warping. Don't change shoe colours, shadows (contacts), sprite positions.

## Acceptance
- node --check on changed js; game loads with no console errors.
- Write dev/qa-out/skin_sheet.jpg: WebKit (playwright, already installed) renders at 780x390 of Fitting2D.render for heels studpump, crystalsandal, ballet, kitten with socks none/sheer/fishnet/ankle-or-short (one row each) for skin '#8a5a3c', plus one row with no skin for comparison. See /workspace/work/fitqa/stage6.py for a working render harness.
- Commit with a clear message.
