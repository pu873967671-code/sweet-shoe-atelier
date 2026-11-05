# opaque-sock-shading (user request 2026-11-04 13:19 CST)

User: "这些袜子也优化下，太平了，尤其深色". Screenshots: worn fitting (flat shoe, salon scene) with
长筒袜 (thigh) black and 荷叶边 (frill) / 蕾丝 (lace) black. The opaque sock area renders as one flat
solid colour: no volume, no shin/calf highlight, no edge darkening; legs read as flat cut-outs.
Dark colours are worst.

## Goal
Give OPAQUE hosiery/socks real fabric volume on the worn sprite fitting path (js/worn-sprites.js) for ALL
20 shoe bases: styles frill, lace (short-sock body), knee, thigh, opaque. Keep the chosen colour as the
mid-tone. Add form shading derived from the underlying *_legs.webp luminance/shape (soft cylindrical
highlight down shin/calf, rim darkening toward silhouette edges, slight occlusion at the shoe collar and
cuff). Dark colours get a cool soft sheen so black reads as knit fabric, not a hole; light colours get
gentler shading (never grey/dirty). Very low-contrast knit texture OK. Reference volume: the sheer hose
look on flat/stiletto9 (flat_hose.webp), but opaque. For flat/stiletto9 the hose map may be reused.

## Hard constraints
- Code change only. Do NOT replace/alter any assets/worn/*.webp.
- Do not change sheer / blacksheer / pantyhose / fishnet looks, shoe pixels, non-worn product shoes,
  js/audio.js. Pixels outside the sock area unchanged. No stretching/skewing.
- Skin tone tint still works. If canvas pixel reads fail, fall back to current look without errors.
- Don't add qa/ failures beyond the 3 known ones in dev/PROGRESS.md; never delete qa/.
- Bump ASSET_V in js/worn-sprites.js (currently 20261104c) to 20261104d.

## Acceptance (dev/qa-out/opaque-sock/)
- contact.jpg: BEFORE vs AFTER, legs crop, salon fitting, for flat, stiletto9, block, bootie, slingback,
  maryjane × {thigh black, knee black, frill black, lace black, thigh cream, knee pink}.
- Chromium /usr/bin/chromium, desktop + phone viewport, no page errors. README with what changed.

## Addendum (user, 2026-11-04 13:27 CST)
"这些颜色的袜子都要优化，很平，都按照这种标准处理就行" — ALL five colours (pink, mint, cream, white, black)
get the same volume standard. Screenshot: maryjane + 长筒袜 + cream reads as a flat grey-beige slab;
cream/white must stay clean warm cream/white with real shading, not grey.
- (user, 13:28 CST) "不同鞋型光影不要硬套": do NOT apply one fixed shading template to every base. Derive
  highlights/shadows per base from that base's own *_legs.webp geometry and lighting (leg pose, foot angle,
  heel height differ), so light sits where each leg actually turns. Verify per base in the contact sheet.
