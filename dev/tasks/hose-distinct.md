# hose-distinct: make each sock/stocking style visibly different; restore the old sheer look (user, 2026-11-04 19:53 CST)
User feedback with screenshots in dev/user-ref/:
1. 20261104-knee-thigh-opaque-same.webp: 及膝袜 (knee), 长筒袜 (thigh) and 厚连裤袜 (opaque) look IDENTICAL (whole visible
   leg solid). Knee-high must visibly end just below the knee with a soft knit welt/band and bare (skin-toned, follows
   customer skin tone) leg above. Thigh-high must end on the upper thigh with a visible welt band (lace or knit) and
   skin above; if the thigh top falls outside the frame on some bases, place the band at the highest visible thigh
   area so it still reads as a stocking, not tights. Opaque tights stay continuous to the top of frame.
   Each base's leg geometry differs: locate knee per base from its own legs art (no one template).
2. 20261104-sheer-vs-sheerpantyhose-same.webp: 薄丝袜 (sheer) and 薄连裤袜 (pantyhose) look IDENTICAL (flat grey).
3. 20261104-old-sheer-wanted.webp: the EARLIER sheer stocking look the user liked has disappeared: skin shows through,
   denser/darker at the leg silhouette edges (denier falloff), a soft sheen highlight down the shin/knee, slight
   translucency. Find where it came from (git log -S hose / flat_hose.webp / HOSE_BASES / earlier sheer render in
   js/worn-sprites.js; check commits f3528ebf, 4b13b674 and before) and why it is gone (likely the opaque/sock shading
   or edges chunks changed the path, or `mapped` hose pixels now get overridden). Restore it for 薄丝袜, and give
   薄连裤袜 its own clearly different look (e.g. nude/skin-toned, more even matte denier, subtle reinforced toe), and
   黑丝袜 a black sheer version of the old look. Extend the sheer look to all 20 bases (per-base geometry; user
   asked for this earlier) if feasible within the chunk, else flat + stiletto9 + maryjane first and list the rest.
Constraints: don't touch shoe dye masks/edge fixes; no stretching/skewing of art; keep file:// fallback working;
skin tone sync. Bump ASSET_V. Acceptance dev/qa-out/hose-distinct/: for flat, maryjane, stiletto9, block, bootie:
one contact row per base with all 10 sock styles side by side (pink floral shoe, default skin + one dark skin),
plus 3x knee crops for knee/thigh/opaque and sheer/pantyhose/blacksheer; Chromium desktop+phone, no page errors.
