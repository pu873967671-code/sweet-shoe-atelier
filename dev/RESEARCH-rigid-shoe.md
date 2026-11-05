# Research: rigid shoe, adaptive leg (try-on) — Supervisor 2026-10-28 19:45–20:45 CST

Answers USER 19:15–19:16 ("硬掰鞋子都变形了…直接保留鞋子原样让脚去适配") and "花点时间研究".
Prototype: `qa/research-rigid/` (does NOT touch shipping code). Read this before the next Codex chunk.

## 1. Recommendation (TL;DR)

**Stop using the separate worn-camera kit (`assets/fitting2d/<heel>_*`) and every warp on it. Draw the
exact showcase composite (`Shoe2D.composite(design)`, 1024×640, showcase camera) in try-on with ONE
uniform-scale affine per foot, and make the leg fit the shoe instead.** The leg is painted in showcase
coordinates from a few landmarks per shoe and is visible only (a) above the shoe and (b) inside the
shoe's own opening, cut along the near-collar "throat" curve that comes straight from the existing
`assets/shoe2d/<heel>_insole.webp` + `_binding.webp` masks (all 20 styles already have both). The rear
foot is the same rigid shoe at 0.90 scale on a higher ground line, its collar filled by its own leg.

Because the shoe IS the showcase painting, colour/material/pattern/accessories are already correct and
identical to the design page (no re-projection tables), recolouring keeps working, and the 5.0 MiB
`assets/fitting2d/` kit can be dropped from the zip later.

Prototype numbers (`qa/research-rigid/out/verify.json`): shoe silhouette IoU vs uniformly scaled
showcase = **0.9974–0.9979 (pair, with occlusion) / 0.9997–0.9998 (front shoe)**; target ≥ 0.97.

## 2. Where the current pipeline bends the shoe (js/fitting2d.js @ dbedef1)

The try-on shoe is not the showcase painting at all: `source(heel)` loads a *different* painting in a
near-side camera (`assets/fitting2d/<heel>_shoe/upper/shadow/highlight/occlusion/hosiery/legs.webp`),
so pixel identity with the display image is impossible by construction. On top of that:

| # | Where | What it does to shoe pixels |
|---|---|---|
| 1 | `sideCameraPixels()` / `sideCamera()` + `SIDE_CAMERA` (wide 1.13–1.20, depth .90–.94, floor) | Per-row resampling below y350: each row scaled horizontally by an eased factor that grows with y, rows pulled toward `floor`. Different rows get different scales → pointed toe curls/kinks, flat sole bows. **Main culprit of USER 19:15 screenshot 1+2.** |
| 2 | `render()` `slender=.80` | Whole pair (shoe included) drawn at 0.80×1.0 → non-uniform squash. |
| 3 | `drawFrontLeg()` | Rows 650–900 (+extra) each drawn at a different width (perspective .10 + ankle taper .05), then everything below y900 at `scale(.90,1)` → front shoe narrowed 10 %, visible kink at the transition. |
| 4 | `drawUprightLeg(…, .13)` | Shear above `ankle`; clip at `ankle+2` also catches the collar/heel-counter top in the leg canvas. Applied to the rear foot whole. |
| 5 | `rearTransform` + `POSE_SETS` | Uniform .92 (fine) but y −30…−40 only and the same `soleShadow` contacts → front/rear soles nearly collinear (USER "不要在一个平行线上"). |
| 6 | `projectGrandBow()` | flat: `verticalScale=scale*.82` → bow squashed. |
| 7 | `drawRibbon()` | Product ribbon/thin strap mapped by an affine with independent `normal` scale (shear + non-uniform); thin strap additionally per-column `lift=-16*sin(πp)` → curved. |
| 8 | `FLOWER_PROJECTIONS` | source rect → target rect with different aspect (e.g. 125×182 → 115×139). |
| 9 | `WornBodyFidelity.prepare/postProjection` (js/worn-body-fidelity.js) | Further retouching of the worn kit after the side-camera projection. |
| 10 | `tuckMaryJane/finishMaryJaneTab`, loafer cut-outs, slingback underlays | Hand-repairs that only exist because the worn kit ≠ showcase. |

Crystal/pearl toe ornaments (`projectToeOrnament`) are uniform scale and are not a problem, but become
unnecessary once the showcase composite is used directly.

## 3. Research summary

* **Transparent shoe opening as occluder** – AR shoe try-on (ARShoe, arXiv 2108.10515; Snap Lens
  Studio Footwear Try-On) keeps the shoe model rigid and handles the foot/leg by an occluder in the shoe
  opening: the leg is visible only through the opening and above the collar. Our 2D equivalent is the
  insole mask + throat cut. https://arxiv.org/pdf/2108.10515v1 · https://developers.snap.com/lens-studio/features/try-on/foot-tracking
* **Front/behind sprite layers** – 2D dress-up generators (LPC: `cape` + `cape_behind`) split one item
  into a layer under and a layer over the body instead of deforming it.
  https://opengameart.org/forumtopic/cape-layering-lpc-sprite-generator
* **Pose per shoe class, not shoe deformation** – games/avatars switch the *foot pose* by heel class
  (HyperDeep shoe types none/flat/low/high; Reallusion "feet automatically angle by heel height";
  MakeHuman uses rigid vertex groups so heels never deform).
  https://guide.hyperdeep.co/addons/clothing/ · https://www.reallusion.com/character-creator/custom-outfit.html ·
  https://static.makehumancommunity.org/assets/creatingassets/makeclothes/createheels.html
* **Diffusion VTON** (ShoeFit NeurIPS 2025, ShoeModel) synthesises a worn foot from a product shot, but
  explicitly fights view mismatch and does not guarantee pixel-identical shoes → only usable offline,
  with the original shoe pasted back.

### Options judged against our constraints (zip < 20 MiB, 20 styles × colours × materials × accessories × socks at runtime, recolour must work)

| Option | Shoe fidelity | Runtime cost / size | Hosiery & recolour | Verdict |
|---|---|---|---|---|
| (a) Rigid showcase sprite + leg behind/inside + per-shoe opening mask | exact (IoU ≈ 1) | tiny: masks already shipped | leg is our own layer → any sock, any colour | **Use** |
| (b) Leg templates per heel class, selected not warped | n/a (leg only) | a handful of landmark sets | same | **Use, as data for (a)** (pump / flat families share shapes) |
| (c) gpt-image-2 inpainted leg per shoe, shoe pasted back | exact if pasted back | 20× painted legs ≈ +2–4 MiB; ×sock types impossible; recolour of skin↔sock breaks | poor | Not for runtime. Optional later: paint ONE neutral leg texture per family in the showcase camera to replace procedural shading |
| (d) Rear foot = same rigid shoe, smaller, higher, occluded | exact | free | same | **Use** |

## 4. Prototype (qa/research-rigid/)

* `proto.html` (base href = repo root) loads `data.js, studio-core.js, showcase.js, accessory-renderer.js,
  shoe2d.js` + `qa/research-rigid/rigid-fitting.js`. `render.py` serves the repo, drives
  `/usr/bin/chromium` via Playwright, writes `out/`. `verify.py` = acceptance metrics, `sidebyside.py`
  = showcase-vs-try-on boards.
* Composition per foot (all in showcase coordinates, then one `setTransform(s,0,0,s,tx,ty)`):
  1. `shoe = Shoe2D.composite(design)` drawn rigidly.
  2. `throatCut(shoe, insole, binding)` → per-column y: bottom of the opening minus a running-median
     binding thickness (foot stops on top of the near piping); columns without opening use the top of the
     shoe silhouette. Smoothed (median 15 px + tricube local regression ±18 px).
  3. Leg painted from landmarks (`FIT[heel]`: `back` Achilles/calf, `front` shin, `instep` ankle→throat V,
     `ridge` highlight, `contacts`), soft volume = rim darkening from blurred inverse mask + ridge light;
     hosiery is the same shape painted with cloth colours (opaque black / sheer).
  4. Leg ∩ (y < cut) drawn over the shoe → covers the opening (insole + far lining + far rim, which a
     real instep hides) but never the near wall, studs, binding or heel counter. Two exponential
     occlusion bands (3 px/14 px) along the cut make the skin sink into the shoe.
  5. Rear: same shoe at 0.90, toe offset (+76, −42) camera px (≈ +27 css px higher at 390 wide, ≈ +56 px at 1920), its own
     leg (slight leg-only lean −0.024), front visible-foot cast shadow clipped to the rear group.
  6. Floor contact shadows from per-shoe `contacts` (ball segment + heel tip), flattened ellipses.
* Leg-only "pose" (`lean()`) bends the column above the ankle; the shoe never moves.

### Results (390×844 → picture 780×640 @2x; 1920×1080 → 818×670; hires boards 1560×1280)
Best images:
* `qa/research-rigid/out/sbs-studpump-pink-satin-bare.png` – showcase | try-on | try-on + showcase silhouette (cyan)
* `qa/research-rigid/out/sbs-flat-pink-satin-black.png`
* `qa/research-rigid/out/stiletto9-pink-satin-black-1920x1080.png`
* `qa/research-rigid/out/studpump-pink-satin-bare-390x844.png`, `flat-pink-satin-black-390x844.png`

`verify.json`: silhouette IoU pair 0.9974–0.9979, front 0.9997–0.9998. "outer_upper_pixels_changed"
(non-opening shoe pixels altered in the full render) = 0.8 % stiletto9, 4.4 % studpump, 6.5 % flat:
these are exactly the far collar rim / inner back lining that the instep and heel legitimately cover
(they sit above the throat cut), not resampling — the near wall below the cut is untouched.

### What still looks off in the prototype (honest)
1. Leg shading is procedural airbrush: reads clean and matches the soft style, but is flatter than the
   painted calves; black opaque instep looks a bit like a flat fill (needs a stronger ridge light / knit
   sheen).
2. Small cream nib at the heel-counter top (top back piping) shows above the Achilles on pumps.
3. Flat: 1–2 px irregularity of the cut on the near piping around mid-throat (auto-detected curve from
   a noisy binding mask) → author a bezier override for flats.
4. Legs are long straight tubes; calf swell sits mostly above the crop; legs converge only slightly.
5. Rear toe is hidden behind the front foot (by design of the higher/closer stance); if USER wants both
   toes visible, increase rear x offset to ~0.40 shoe length.
6. Prototype covers studpump, stiletto9, flat (bare / opaque-black). Open heel/toe, mule, bootie, ankle
   straps and laces are not prototyped yet (plan below).

## 5. Implementation plan for js/fitting2d.js (NEXT CHUNK, Codex)

Do it as a new renderer behind the same `A.Fitting2D` API (`mount/render/composite`) so app.js does not
change; port `qa/research-rigid/rigid-fitting.js` into `js/fitting2d.js` (or `js/fitting-rigid.js` and
switch `A.Fitting2D` to it).

**Remove / stop calling** (keep in git history): `SIDE_CAMERA`, `sideCameraPixels`, `sideCamera`,
`drawFrontLeg`, the shear path of `drawUprightLeg`, `slender=.80`, `pairedModel` per-row work,
`rearTransform`/`POSE_SETS` (replace by per-family stance data), `CONTACTS`/`soleShadow` worn-camera
tables, `projectGrandBow`, `drawRibbon` (incl. thin-strap `curved` lift), `FLOWER/CRYSTAL/PEARL/RIBBON/
THIN/GRAND` projection tables, `THIN_BUCKLES/drawThinBuckle`, `tuckMaryJane/finishMaryJaneTab`, loafer
and slingback repair blocks, `source()` loading of `assets/fitting2d/*`, `WornBodyFidelity` calls,
`calfSection/paintCalf/HOSIERY_SECTIONS` (worn-camera constants). `fallback()` → draw the showcase shoe
with a plain leg.

**Add**
1. `Shoe2D.compositeLayers(design)` in js/shoe2d.js → `{body, over}`: `body` = base+tint+finish+pattern
   (+accessories that sit on the outside: toe charms, heel bows, flowers); `over` = accessories that
   cross the opening/instep (strap_thin, strap_ribbon, strap_cross, strap_pearl, maryjane band, ballet
   ribbons, laces) so they are drawn **after** the foot. `composite()` stays = body+over for the design page.
2. `FIT` table per style in showcase px: `back[]`, `front[]`, `instep[]` (ankle front → throat V),
   `throat` (V point), `ridge[]`, `contacts.ball[]`, `contacts.heel`, optional `throatCurve` bezier
   override, optional `heelVisible`/`toesVisible` flags. Shapes are shared by family; only the throat
   and heel-cup points differ.
3. `throatCut()` from insole+binding (as prototype) computed once per style and cached (Float32Array(1024)).
4. `paintLeg(fit, sock)` → skin layer + hosiery (reuse `hosieryColour/hosieryOpacity`, re-key yarn/knit
   sections to the leg path cross-section instead of `HOSIERY_SECTIONS`).
5. Pair layout: front toe camera (150,526), shoe length 222 camera px (uniform `s = 222/832*u`), rear
   0.90 scale, toe offset (+76,−42) camera px; floor shadows from `contacts`. Keep `Showcase.project`.

**Layer order (per foot, rear foot first):** floor shadow → shoe `body` → leg ∩ (y < throatCut) with
occlusion bands → shoe `over` accessories → (rear only) front-foot cast shadow clipped to rear group.
Hosiery: painted into the leg layer, so the instep seen in the throat shows the sock automatically;
frill/lace cuff tops draw on the leg above the collar.

**Roll-out by family (20 styles)**
* Closed pumps, showcase camera like studpump: stiletto6, stiletto9, studpump, pearlpump, crystalpump,
  luciteheel, pearlheel, kitten, block, platform, wedge – reuse PUMP leg, tune `throat`, `back` heel
  point, `contacts` per style (≈10 min each with the grid overlay script).
* Flats: flat, ballet, loafer, maryjane – FLAT leg; maryjane/ballet bands go to `over`; loafer saddle is
  part of `body` (outside), its high vamp simply moves the throat V back.
* Open heel: slingback, bowsling, bowmule – the heel of the foot is visible: extend the leg with a
  painted heel/sole-contact lobe behind the counter-less seat, cut by the insole mask only; strap in `over`.
* Open toe: crystalsandal – needs a small toe sprite (5 toes, skin + sock tint) placed at the toe opening;
  chain in `over`.
* Bootie: cut = shaft top; leg only above the shaft (no instep visible).

**Acceptance tests (extend qa/research-rigid/verify.py into qa/rigid-shoe-test.py)**
1. Shoe silhouette IoU (shoe-only pass vs PIL uniformly scaled `Shoe2D.composite`) ≥ 0.97 per foot
   (prototype 0.997+); no per-row/per-column resampling call anywhere in fitting code (grep test:
   no `getImageData` on shoe pixels except the one-off throat scan, no `setTransform` with sx≠sy on shoe).
2. Near-wall fidelity: pixels of the front shoe *below* the throat cut and outside the opening differ
   from the scaled showcase by mean ≤ 1/255.
3. No skin/sock below the cut or outside (shoe ∪ above-shoe region): leg alpha there = 0.
4. Rear collar filled: inside the rear opening (insole mask) leg/sock alpha > 250 for ≥ 98 % of the
   pixels not covered by the front foot.
5. Ground lines: rear toe/heel contacts 25–40 css px higher than front at 390 wide (prototype ≈ 27 css px
   at 390×844), both inside the platform
   top ellipse, contact shadow under each ball + heel tip.
6. Visual: 390×844 + 1920×1080 for every style × bare / opaque black / white; supervisor 3× zoom:
   no bent toe, no bowed sole, no squashed shoe, no collinear soles, no floating rear, no halos/seams at
   the throat.

## Iteration 2: anatomy (Supervisor 2026-10-28 20:13–20:35 CST)

USER 20:13 on iteration 1: "都不成脚型了😅" – procedural leg = flat straight tube (no malleolus, no Achilles
dip, no heel bulge, no instep, no calf curve, parallel legs, black tights = flat fill). Shoe side was right and
is unchanged (same `Shoe2D.composite`, one uniform scale; `out2/verify.json` IoU pair 0.9976–0.998, front
0.9996–0.9998, PASS).

### Approaches compared
* **(A) warp the old painted legs (`assets/fitting2d/<style>_legs.webp`)** – rejected after inspection: they are
  painted in the old near-side, low worn camera; the whole foot is hidden by the old shoe, so there is **no
  painted instep/toe region** for the showcase camera, which looks down into the opening. A TPS warp could
  supply only the column above the ankle, and the view angle of the ankle bone/heel bulge would still disagree.
* **(B) gpt-image-2 painted leg per shoe, shoe pixels discarded – CHOSEN.** 3 edit calls total (budget 12).
  Input = the exact showcase composite at 0.85 on a 1024×1536 portrait canvas (`gen/<heel>-in.png`) + old painted
  leg as style ref (`gen/styleref.png`), short prompt ("slender, pretty anime-style female leg and bare foot
  wearing this exact shoe … instep rises from the opening with a soft arch and slight toe cleavage; slim ankle
  with visible ankle bone; Achilles dip into the heel cup; gentle calf curve … plain background"). gpt-image-2
  edits return a **transparent background**, so the leg is already matted.
  Pipeline (`qa/research-rigid/`): `register.py` (scale+shift fit of the model's redrawn shoe to ours on the
  lower 50 % of the silhouette: flat IoU 0.989, studpump 0.920, stiletto9 0.78 → stiletto9 rejected, see below)
  → `legkit.py` (map to showcase coords, leg canvas 1024×1840, LOY=1200; throat cut as iteration 1 but with a
  minimum near-piping band of 12 px so the cream piping stays visible) → `footmask.py` (Bayes colour classifier:
  skin histogram from the leg column vs the model's shoe below our cut → foot mask, connected to the leg, holes
  filled; then **leg-only per-column vertical stretch** (≤95 px, smoothed along x) so the foot's lower edge,
  which sat on the model's own collar, lands exactly on OUR throat cut – no double binding, no insole gap)
  → `export_legs.py` (defringe the matte edge, slim the leg above the ankle to 0.86 width at the top, leg-only
  lean: front +0.03, rear −0.095 so the pair converges/knees together) → `gen/<heel>-leg-{front,rear}.png`.
  Runtime (`rigid-fitting.js`, `cfg.painted`): load the PNG, hosiery = per-pixel recolour from the bare leg's own
  luminance (`HOSE` table: opaque-black / sheer-black / opaque-white: shade = lo..hi by luminance + knit sheen on
  the lit ridge), so tights keep the ankle bone, Achilles and calf volume. AO bands at the cut kept (lighter).
  Rear offset (+128,−46) camera px (was +76): the rear heel/counter clears the front leg.
* **Family sharing works:** stiletto9 uses the **studpump** leg (same pump family, same showcase camera); its own
  generation was rejected (model redrew the stiletto at 0.89 scale → stepped toes at the throat). Production
  plan: one painted leg per family/camera, not per colour/material/sock.

### Results (`qa/research-rigid/out2/`)
Best boards (showcase | try-on | try-on + cyan showcase silhouette):
* `out2/sbs2-studpump-pink-satin-bare.png`
* `out2/sbs2-flat-pink-satin-black.png`
* `out2/sbs2-studpump-pink-satin-white.png`, `sbs2-stiletto9-pink-satin-black.png`
Full frames: `out2/<case>-390x844.png`, `out2/<case>-1920x1080.png` (studpump bare/black/sheer/white,
stiletto9 bare/black, flat bare/black). At 2–3× the foot reads as a real foot: malleolus, Achilles tendon into the
heel cup, heel bulge, instep arch and toe-cleavage hint in the V throat, tapered calf, rear foot connected into its
own shoe. Opaque black and white tights keep full volume.

### Remaining issues (honest)
1. **Sheer black** still reads as a muddy taupe; needs a proper denier model (skin × transmission, darker at the
   silhouette edges by view angle, lighter on the shin ridge) instead of a flat mix.
2. Legs are now slender and converge, but at 390 the two calves still read a bit like a mirrored copy (same
   painting, only leaned). A second generated *rear* pose (weight-free leg, slightly bent knee) per family would
   fix it (1–2 more image calls per family).
3. Flat: a small tan insole wedge + a pale speck in front of the toes at the throat tip (the painted toes stop
   short of the opening tip). Fix by extending the foot mask to the opening tip or a hand-authored tip patch.
4. A few dark/pale specks on the rear leg's outer edge (matte fringe after the lean resample); 1-px erosion of
   alpha after the lean will remove them.
5. The model's leg tops out at showcase y≈−1167; at very tall viewports the leg would end – extend the column by
   a smooth vertical continuation or generate taller.
6. Not yet done: other families (closed pumps should reuse the studpump leg; flats/ballet/loafer/maryjane the
   flat leg; open-heel, sandal and bootie need their own generations), skin-tone variants, and `over` accessories
   on top of the painted foot.

### Plan for the shipping port (replaces §5 step 4 "paintLeg")
* Ship `assets/fitting-rigid/<family>_leg_{front,rear}.webp` (≈150–250 KB each as webp q90; ~8 families ≈ 3 MB,
  while dropping the 5 MiB `assets/fitting2d/` kit) – generated offline by `qa/research-rigid/{gen_edit.sh,
  register.py, footmask.py, export_legs.py}`; leg PNG already clipped to the style's throat cut, or ship unclipped
  + cut at runtime when a family shares a leg across styles (as stiletto9 does).
* Hosiery at runtime = luminance recolour (`HOSE`) + existing yarn/fishnet textures masked by leg alpha.

## Production integration — 2026-10-28

`js/fitting-rigid.js` now supplies the accepted gen5 studpump/flat/maryjane
anatomy through the existing `Fitting2D.render` and modal/PNG-share entry points.
Front and rear sources remain distinct. `dev/build-rigid-legs.py` moves automatic
insole/binding throat scans, skin/cloth luminance and contact occlusion offline;
shipping code only draws local WebP layers, so cross-origin canvas taint does not
prevent rendering. Product shoes retain one uniform transform and their shared
product material/pattern/ornament pixels. Crossing optional straps use a second
product-coordinate overlay above the foot. Missing anatomy falls back to the
complete existing fitted camera and retries failed local images on a later use.
No procedural substitute or unreviewed shared foot is applied to other styles.
Final scoped browser evidence and outstanding work are recorded in PROGRESS.
