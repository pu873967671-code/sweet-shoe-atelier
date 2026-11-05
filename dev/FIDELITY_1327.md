# USER13:27 — product / try-on fidelity handoff

Status (2026-10-26 07:15 UTC): **partially repaired; full art acceptance remains
open**. The prior interrupted slice installed pointed-flat/low-heel source
repairs. This continuation visually verified their smooth heel arcs and added
a native negative-control regression. Both cameras now use the same logical
cross-lace model, with fixed gold eyelets, satin crossings and a side bow;
worn thin bands now retain the product's missing gold buckle. Current evidence
and remaining differences are in the newest `dev/PROGRESS.md` entry.

`qa/flat-heel-edge-test.py` rejects the original unfiltered heel displacement
(2.067 px subpixel curvature) while all three current low-flat arcs pass
(0.106 px). Native light/dark images are in `qa/fidelity-1327/flat/`.
`qa/lace-fidelity-test.py` checks both cameras of all nine compatible styles,
including eyelet/bow visibility and dye-independent metal.
`qa/thin-buckle-test.py` covers the same nine compatible styles in three colours.
`qa/fidelity-matrix-test.py` produces every registered style's compatible
ornament selections on light/dark grounds; these are single-axis variants,
not every possible combined design. Camera equivalence still needs visual
review; automatic pixel changes alone cannot certify art acceptance.

## Original evidence and causes (retained diagnosis)

Read the latest USER13:27 entry in `dev/REVIEW.md`. Compare the four supplied
`dev/refs/user_{showcase,tryon}_{flat,lace}_1327.webp` images side by side.

1. **Flat shape is baked into different camera paintings.**
   `assets/shoe2d/flat_base.webp` is pointed with a thin sole and very low heel;
   `assets/fitting2d/flat_shoe.webp` is rounded with a visibly raised heel.
   `js/fitting2d.js:source()` correctly loads the requested heel's own kit; this
   is not evidence of a wrong saved heel or registry alias.
   The original `flat` job in `dev/fitting-source/prompts.json` explicitly asks
   for **“a tiny 2cm square heel, soft rounded toe, thin sole”**. Re-running
   `dev/build-fitting2d.py` against that unchanged painting repeats the mismatch.

2. **Cross-lace metal is lost during extraction; the bow was never painted.**
   `js/accessory-renderer.js:OPTIONS/handles()` excludes strap `cross`.
   `js/fitting2d.js:drawOrnaments()/ornament()` therefore loads
   `assets/fitting2d/accessories/<accessoryBase>_strap_cross.webp` plus its tint.
   `js/shoe2d.js:drawAccessories()` loads the separate product-camera painting;
   `drawLegacyAccessories()` also contains an eyelet/cord/bow fallback.
   The original `dev/fitting-accessories/kitten-lace.png`, resized to 1024 square
   as the builder does, contains three near gold eyelets and shaded ribbons.
   `dev/build-fitting-accessories.py:extract()` treats this as fabric:
   `seed=lilac & (delta>19) & ...`; the gold eyelets fail the lilac test and
   disappear from the exported ornament. Its tint mask also uses `alpha*lilac`.
   Both original `flat-lace` and `kitten-lace` prompts in
   `dev/fitting-accessories/prompts.json` ask for **“three rows ... far eyelets
   disappear behind foot”**, and do not request a side bow. The raw kitten
   painting has no tied side bow to recover.

3. **Finish fidelity also needs a visual audit.**
   Product `js/shoe2d.js:materialLayer()/patternLayer()` and worn
   `js/fitting2d.js:finish()` use separate mesh/lace/motif recipes and source
   spacings. Matching design IDs alone do not guarantee matching feature count,
   size or direction on the smaller worn upper. This is an audit target;
   all other styles have not yet received USER13:27 side-by-side acceptance.

Local ignored review aids: `qa/session-0525-fitting/fidelity-triage.jpg` shows
the two flat bodies and product/worn flat/kitten cross PNGs;
`qa/session-0525-fitting/raw-worn-lace.png` shows the original eyelets.
Reproduce by opening the files above; resize the raw worn painting to
1024×1024 before cropping its vamp, matching `extract()`.

## Recommended implementation order

1. Pin current source hashes and build `qa/fidelity-1327/` native side-by-side
   product | worn sheets for every registered style with an identical cleaned
   design. Include plain satin first, then every compatible strap, rear decor
   and toe ornament on light/dark grounds. Record incompatibilities explicitly.
   Review actual Collection → try-on journeys at phone and desktop scale.
2. Repair the **flat worn source only** to match the approved product pointed
   toe, thin sole, tiny heel, cream piping and opening. Derive its shoe, upper,
   shadow/highlight, occlusion and hosiery layers from immutable repaired inputs
   with camera-local semantic contours. Retain all original calf/ankle art and
   shared transforms. Validate intended shoe-silhouette differences explicitly;
   do not silently replace unrelated historical alpha references.
3. Repair cross laces in each compatible worn camera: recover fixed gold
   eyelets separately from tintable satin, preserve ribbon highlights/shadows,
   match actual product crossing count/over-under order, and add a perspective
   side knot/bow attached to the outer mount. Far eyelets can be occluded by the
   foot but must have defined mounts. Use independent semantic extraction masks
   for fabric, metal and contact shading; do not stretch the incomplete PNG.
   A shared logical lace model in `AccessoryRenderer` is an alternative only
   with independently authored product/worn anchors and native art review.
4. Continue the same sheets through strap/buckle/ankle-tie/bow/trim/heel and
   finish differences. Normalize material feature size/direction to each shoe's
   local upper plane rather than whole-canvas dimensions.

## Preserve and validate

- Preserve the 610×620 source camera, y100..600 crop (610×500), original feet
  display scale, .80 slender proportions, front/rear overlap, smooth calf
  curves, baked platform and source-aligned contact shadows. No try-on zoom.
- Preserve recorded audio, progression, saved IDs and all unrelated accepted
  paintings. Keep runtime assets local and ZIP below 20 MiB.
- Required QA after repairs: `node --check` every JS; `node smoke-test.js`;
  `python3 qa/screenshot.py --group screens`; inspect all generated UI sheets.
- Run `qa/layout-1247-test.py` (all five scenes × six requested sizes),
  `qa/calf-1247-test.py`, `qa/calf-1247-flow.py`, `qa/leg-smooth-test.py`,
  `qa/skin-pixel-test.py` (240 cases/20 pairs), and
  `qa/fitting2d-test.py --recovery-only`. Require unchanged framing/overlap,
  zero uncovered opaque collar skin, continuous yarn/contours and complete
  failure recovery. Exercise saved Collection/reload/PNG sharing.
- Add fidelity-specific semantic assertions: expected toe/heel/sole class,
  visible eyelet coverage, matching crossing/bow identity, metal unaffected by
  dye, zero viewport jitter. Human native side-by-side review remains required;
  image-difference or source-hash checks alone cannot certify design fidelity.
- Rebuild and accept the exact extracted ZIP after final artwork acceptance.

Known limit: current pair still recomposes one worn painting with authored
calves. This task does not require replacing that approved pose or claiming
independently painted paired anatomy. Physical-device/production-host acceptance
and human audio listening remain separate.
