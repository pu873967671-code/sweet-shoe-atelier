# 3D renderer plan (user-approved 2026-10-23 18:00) — replaces 2D shade/recolor pipeline for shoes
Why: 2D stickers can't light correctly (colours look "floaty"), accessories get covered by the foot, options have weak visible effect. Target look: dev/refs/nikki_style_target.png (Infinity Nikki stylized anime-3D).

## Architecture
- three.js r169 vendored locally: vendor/three.module.min.js (+ vendor/addons/GLTFLoader.js, RoomEnvironment.js, BufferGeometryUtils.js). No CDN. Fix addon import paths to './../three.module.min.js' or an importmap.
- js/shoe3d.js: ONE renderer module used by design studio preview, fitting/showcase, Collection, thumbnails/icons (render-to-texture snapshot cache). Same lights/material = identical look everywhere.
- PARAMETRIC SHOE MESHES (procedural, no external models needed): build each silhouette (flat, block, kitten, wedge) by lofting cross-sections along a shoe-last centreline: separate meshes for upper (with opening/topline), insole, outsole, heel (block/kitten/wedge shapes). Clean UVs on the upper (u around, v toe→heel) so patterns tile without seams. Rounded/pointed toe param. Quality bar: smooth, subdivided (≥ 6–10k tris/shoe), proper normals, slight thickness at the topline (rolled edge) so it reads as a real shoe.
- MATERIALS (MeshPhysicalMaterial): satin (low rough + anisotropy/clearcoat sheen), velvet (sheen), leather (mid rough, clearcoat), lace (alphaMap over base), mesh (alphaTest hole pattern), glitter (sparkle normal/emissive flecks), cotton (rough). Colour = player swatch exactly as base colour; ACES tone mapping exposure tuned so pastels stay pastel. Patterns (flower/heart/dots/stars) = generated canvas textures on the upper's UVs, scale big enough to READ at gameplay size.
- ACCESSORIES as real meshes attached at named sockets: heel-back bow sits OUTSIDE on the heel counter (never intersecting the foot), toe ornament on vamp, straps as tube/ribbon geometry around the ankle.
- LEGS: v1 = stylized procedural legs (calf→ankle→foot lofted, porcelain skin MeshPhysical with subsurface-ish warm sheen, toon-soft lighting) wearing the shoe; foot hidden inside the upper. Poses: relaxed, crossed, step, seated (simple joint rotations at hip/knee/ankle). May later be replaced by an AI-generated mesh (needs HF token; pending).
- SCENE: close-up product framing at ankle height, warm key light + pink rim + RoomEnvironment IBL, soft shadow (PCFSoft / contact shadow plane) + subtle floor reflection; the existing close_*.webp backplates as blurred background planes. Light orbit / drag to rotate on desktop+touch; idle slow turntable in studio.
- Performance: pixelRatio cap 1.5, single renderer reused, render on demand (no continuous loop when idle), dispose on screen exit; must run on mid Android. Fallback: if WebGL unavailable → old 2D path.

## Migration order
1. js/shoe3d.js + parametric flat shoe + materials/colours/patterns + studio preview; screenshots.
2. Other 3 silhouettes + accessories sockets.
3. Legs + poses + fitting scenes (close_* backplates).
4. Collection / thumbnails via snapshot cache; remove 2D recolor path from runtime (keep as fallback).
5. Art refresh toward ART DIRECTION v2 (mentor v3 etc).


2026-10-23 step 2 start: studio now authors block, flared kitten and continuous wedge supports against the pitched last, with heelBack/toe/ankle sockets and all existing accessory choices as meshes. Broad low ballet opening and pale unbranded pad incorporate Supervisor 18:40. Legs/fitting and Collection snapshot migration remain steps 3–4; validate actual worn accessory clearance during step 3. Sequential QA results are in PROGRESS.
