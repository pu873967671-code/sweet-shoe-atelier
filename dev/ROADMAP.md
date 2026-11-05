# 3-day production roadmap (2026-10-22 22:00 → 2026-10-25 22:00 CST)
Read GDD.md first. Codex works in chunks of ≤17 minutes; at the end of EVERY chunk it must update dev/PROGRESS.md
(what is done, what is half-done with file/function names, exact next steps, known bugs) and leave the game runnable
(node --check on all JS, `node smoke-test.js` passing or the failure noted in PROGRESS.md).

Phases (mark [x] in PROGRESS.md when done; the supervisor reviews each phase):
- P1 Architecture + merge core: split code into files under js/ (keep index.html entry, no build step), save v3 with migration from
  v2, merge board (grid, cells, drag/drop with pointer events, merge-2, generators w/ energy + charges + cooldown, crates opening,
  energy regen incl. offline), real item art from assets/items, responsive board in landscape and portrait.
- P2 Orders + economy: order strip, deliver, rewards, item info panel, sell/trash, chests, bubbles, discovery book, idle hint,
  economy simulation in smoke test (orders always achievable, energy pacing ~ 8–12 min per chapter task).
- P3 Integration: navigation hub (Atelier / Boutique / Studio / Collection), commissions requiring crafted unlocks,
  HUD (energy/coins/stars/gems/level), Madame Odette tutorial dialogs (first 3 minutes fully guided), settings.
- P4 Try-on runway: worn-shoe compositing on assets/legs (dynamic layered shoe on feet, pair of feet, 3 poses, sway, mirror
  reflection, sparkles, reaction), entry from post-pack and Collection.
- P5 Boutique renovation + chapters: shop scene with 8 decor slots × 2 levels, star-cost tasks, celebrations, chapter unlocks,
  SDK happytime/midgame between chapters, endless mode.
- P6 Juice + audio + i18n: all polish items in GDD §4, WebAudio sfx per action, zh-CN for all new text.
- P7 QA + compliance: extend qa/screenshot.py to cover every new screen at 1280×720, 800×450, 1920×1080, 390×844, 844×390;
  zero page errors; perf check; packaging script; README.
- P8 Polish loop: fix supervisor review notes (dev/REVIEW.md), balance, visual consistency.

Balance clarification (2026-10-24, PLAYER PRIORITIES): relaxed order comfort takes precedence over the original8–12min minimum chapter-task duration. Keep late tasks ≤12min and test ≥80% sub-two-minute wishes / zero energy waits; preserve rewards, task costs and saved active requests. Current limits and exact simulation evidence are in PROGRESS and GDD§31.


## 2026-10-25 04:35 art follow-up
- [x] Repair original thin product far mounts on9cm/6cm/platform, plus older block/kitten; repair associated internal satin extraction slits.
- [x] Audit all compatible legacy accessories on product/worn dark/light sheets; repair five product cross-band bow extraction holes/scraps.
- [x] Add original pearl-orb sculptural pump with full product/worn kit, premium craft unlock, matching finishes/accessories and saved-gallery flow.
- [x] Retain slender, smooth youthful fitting; move fitting milestone toast clear of primary actions.
- [ ] Continue crystal-chain/flower/wrap sandals with matching open-toe sources; independently painted paired anatomy still pending. Exact final local QA evidence is in PROGRESS.

## 2026-10-25 04:56 continuation
- [x] Finish original broad-ribbon satin re-extraction and tint coverage; preserve each immutable external contour and camera mount.
- [x] Accept the complete lucite sculptural-heel product/worn kit, earned unlock, saved identity and final dark/light actual-UI checks.
- [ ] Complete independent-pair runtime integration from the genuine source master: per-foot masks/anchors, matching socks and ornaments, all finish/fallback/save/layout checks. Source preparation alone does not complete this item.

## 2026-10-25 09:25 open-toe repair
- [x] Preserve opaque-sock toe volume/coverage with camera-local cuffs; protect full cream inner arch/sidewall and counter piping; attach continuous wrap turns in both cameras.
- [x] Exercise all3development candidates through finish/pattern/sock matrices and actual saved fitting/Collection/share/failure flows without changing the runtime registry.
- [ ] Finish every-colour native ART approval, then register complete kits and accept an isolated candidate-containing upload. Existing19style runtime stays playable and packageable until then.

## 2026-10-25 09:55 final acceptance slice
- [x] Catch and repair the candidate toe-underside/opaque-sock skin leak with a camera-local contact contour; preserve cream footbed, calf and finish masks.
- [x] Reject unregistered camera artwork in release packaging, including orphan ornament sources; preserve the previous upload on rejection.
- [x] Add isolated candidate-containing ZIP flow acceptance without browser asset/registry overrides or changes to the shipped catalog.
- [x] Complete full source-native ART150checks/252captures and isolated candidate ZIP acceptance; actual paired matrix146/153cases complete.
- [x] Complete remaining7desktop wrap paired-colour cases; full153/153candidate matrix and39locked hashes accepted in the10:25session.
- [ ] Complete bilingual catalog/craft/commission acceptance and a budget-compliant release before sandal registration. Three candidate kits together currently exceed20MiB; exact settled reports and scope are in PROGRESS.

## 2026-10-25 10:25 final release preparation
- [x] Require exact accepted camera filenames, rejecting experiments under existing style prefixes.
- [x] Add staged final release validation with exact ZIP SHA256/catalog, persistent screenshots and last-good ZIP/report recovery.
- [x] Recheck seven-size screens and complete fitting recovery after the previous interrupted run; preserve19accepted runtime styles.

## 2026-10-25 22:13 feedback repair
- [x] Deliver committed fitting result exactly once and load next customer through all exits; cover ordinary/final-day and personal fitting cases.
- [x] Remove fitting inset cut/fade; extend overlapping slim calves above actual frame, preserve socks and ornaments; accept35viewport/sock captures.
- [x] Ship local Kenney CC0 sampled SFX with two codecs and reliable gesture-started saved BGM; validate audio/package and retain upload budget.
- [ ] Complete human physical-device listening/production-host checks; continue REVIEW22:20content requests separately.

## 2026-10-25 15:55 priority continuation
- [x] Reverify exact-once commission exits, gesture-started local recorded audio and final seven-size fitting/long-hosiery composition. Close previous unfinished validation.
- [x] Add six earned bilingual straps/heel/toe ornaments with independent product/worn mounts, saved identities, No-bows semantics,280native variants and12actual bilingual saved-flow checks.
- [x] Rebuild validated708-file17.92MiB local release through complete staged release checks; isolated ZIP acceptance and exact byte binding pass.
- [ ] Continue material/pattern variety toward the22:20content target; native19-style review and real saved UI journeys remain required for each addition.
- [ ] Physical Safari listening and production-host acceptance remain outstanding.

## 2026-10-25 fitting perspective repair (USER00:55)
- [x] Replace all five room backplates with a consistent low camera and no painted platform; update picker thumbnails and retain source provenance.
- [x] Use one platform and per-room centre/radii/horizon data; derive feet, ellipse and background crop through the same responsive projection.
- [x] Screenshot all five scenes at all seven supported sizes; inspect native desktop, portrait and short landscape and validate shoe contact/horizon/clearance.
- [ ] Rebuild staged final release before any production upload; current dist ZIP predates this repair.

## 2026-10-25 localized hosiery polish (USER01:11)
- [x] Smooth the inherited front instep kink and soften its contact shadow without changing approved pair composition or camera.
- [x] Replace all three hosiery lighting paths with broad matte cloth volume; project ribs/lace/knit around the shin and instep.
- [x] Complete camera-specific ankle-to-counter coverage beneath the original shoe collars; retain deterministic inputs/rebuild instructions.
- [x] Settle final every-style/every-colour light/dark screenshots and all-shoe junction acceptance: 407 checks / 844 captures; exact evidence and limits in newest PROGRESS.


## 2026-10-25 20:26 priority continuation
- [x] Reverify latest01:35knee-high repair across all5colours/seven UI sizes; both calves full-frame, no cuff sliver and readable curved ribs.
- [x] Expand patterns to10with original curved scalloped embroidery and fine satin pinstripes, earned gates, bilingual picker/commissions and persistent saved styling. Rebuild631glyph local font.
- [x] Settle final19-style304pattern/finish checks,24bilingual saved-flow checks/84captures and required7size63screens/100checks.
- [x] Settle exact staged release708files/18.09MiB with syntax/smoke/startup/audio/pacing/cloud/package/release recovery and isolated-ZIP acceptance. Interrupted broad hosiery/perspective reruns remain follow-up (focused knee-high30/18 passes).


## 2026-10-25 20:54 fitting polish
- [x] Reverify exterior pearls and full-frame slim fitting legs across product/worn/light/dark and actual phone/compact views.
- [x] Repair platform cream-binding extraction slits with immutable-source rebuilding and exact exterior/anchor invariants.
- [x] Keep saved hosiery chips visible on reopening/rotation/scene changes without interrupting manual browsing; bilingual real saved journeys pass.
- [x] Extend actual browser audio checks to application visibility, scheduled-effect cleanup and current-scene resume.
- [ ] Physical iOS/Android listening and CrazyGames production-host acceptance remain external. Independent paired art and official sandal integration remain separate gated work.
- [x] Make Diamond knit readable at phone scale with separate contour-clipped colour-matched yarn; final native five-colour and actual portrait/compact review passes.

## 2026-10-25 21:54 material / audio continuation
- [x] Add earned original crystal pavé with matching product/worn source-coordinate facets, local swatch, bilingual saved identities and font coverage.
- [x] Correct worn finish blending to preserve antialiased edge alpha across material switches; retain approved fitting geometry.
- [x] Recover local BGM after transient loading errors with gesture-driven bounded retries and real-browser regression.
- [x] Final strict152native pavé checks,12bilingual saved flows,304old-material checks,407/844hosiery,6/12recovery,63/100seven-size screens and10-stage18.10MiBrelease pass; initial rejected edge-alpha evidence retained.
- [ ] Physical-device audio and production-host acceptance remain external; independent pair and official sandal gates remain separate.

## 2026-10-25 22:24 single sandal acceptance
- [x] Official Crystal chain sandal: current11material/10pattern/45hosiery native acceptance, bilingual real crafting/commission/save/share/recovery,634glyph local font and hash-bound13layer source lock.
- [x] Fix open-toe patent highlights missing narrow straps; preserve exact alpha, masks and existing closed-shoe finish paths.
- [x] Required7size63/100screens and10-stage721file18.85MiBrelease; supplemental exact crystalZIP journeys pass.
- [ ] Independent painted pair, flower/wrap registration, further authored sandal heel heights and physical-device/production-host checks remain scoped follow-ups.

## 2026-10-26 07:00 heel-counter skin peek
- [x] Diagnose baked shoe-layer skin and add deterministic per-camera hosiery coverage without modifying approved source art or transforms.
- [x] Require collar maps in runtime recovery and package completeness checks.
- [x] Final native skin-pixel240cases/20pairs, seven-size screens63captures/100checks, knee-high30checks/18captures and perspective35checks/35captures; exact evidence and scope are recorded at the top of PROGRESS.


## Supervisor2026-10-26 07:30 gameplay feel
- [x] Preserve07:02audio; settle live-browser signal, loop, toggle/pause/recovery sanity and correct recorded-track credit.
- [x] Shorten repeated first-minute dialogue while preserving illustrated targets, accessible instructions and saved route.
- [x] Add free inventory-safe Sort, five-second real-pair hints, squash/tier feedback and reduced-motion support.
- [x] Make all16renovations visibly dress the room, with latest-detail Before/after, distinct deluxe details and short reveals.
- [x] Settle seven-size screen/progression/economy QA246captures/265checks and exact741file19.43MiBcandidate upload; see newest PROGRESS.


## Supervisor2026-10-26 08:05 gameplay comfort
- [x] Audit44pxdialog exits and remove repeated discovery interruptions; compact Chinese Summary/Bubble actions fit without scrolling.
- [x] Exact-tier per-requirement progress, gentle near-full Sort action and free persisted holding slot.
- [x] Three fresh20min no-forced-wait simulations, real app commission fallback/empty-energy/full-board cases and visible free Studio route.
- [x] Boutique ambient visitors, finite purchase sparkles, hidden/reduced-motion handling and Chinese844×390 audit.
- [x] All48JSsyntax, smoke/audio/session checks,7size screens63/100, focused browser acceptance and exact19.44MiBcandidate ZIP.
- [ ] Continue physical-device/CrazyGames-host and human pacing/audio acceptance; keep07:02audio and20MiBbudget fixed.


## USER2026-10-26 11:55 fixed fitting camera
- [x] Replace all five try-on paintings and picker previews with supplied fixed_*.webp; record native baked-platform ellipse measurements/provenance.
- [x] Lock610×620composition, reference-sized feet/visible calves and one uniform resize; remove code platform and disable try-on zoom.
- [x] Accept all5scenes×6requestedviewports, actual resize roundtrip, PNG sharing, source-aligned visible contacts across20styles and preserved socks. Final syntax/smoke/audio/screens/skin evidence is in current PROGRESS.
- [ ] Physical-device and production-host acceptance remain external; do not reopen the superseded adaptive-platform approach.


## USER2026-10-26 11:58 continuous hosiery and calf outlines
- [x] Remove fishnet's six-source-pixel sample gap and align knee/fishnet yarn through both joins.
- [x] Match extension/source contour tangents for bare legs and every hosiery; retain approved footwear, overlap and fixed camera.
- [x] Add pinned-before seam/edge-curvature regression plus native and six-size saved-fitting evidence in qa/leg-smooth/.
- [x] Final34/36continuity,63/100screens,30/30framing,240/20skin and6/12recovery acceptance; exact evidence is recorded at the top of PROGRESS.
- [ ] Physical-device/production-host acceptance remains external.


## 2026-10-26 05:36 release refresh
- [x] Reverify USER12:47all5scenes/sixsizes, bare/all-hosiery calf contours and240skin cases; seven-size general screens pass.
- [x] Bind final release to actual15scene/size extracted-ZIP crop/dock/pair/hosiery/share/resize evidence;34negative acceptance cases preserve prior outputs.
- [x] Refresh local687file17.22MiBrelease through all10validation stages; no production deployment.
- [ ] USER13:27: repair worn flat shape and metal-eyelet/side-bow fidelity, then complete all-style/camera/ornament side-by-side art audit. See dev/FIDELITY_1327.md.

## 2026-10-26 07:05 USER13:27 continuation
- [x] Verify retained flat/ballet/maryjane heel repair on light/dark native closeups; add negative-control subpixel edge regression without changing approved legs/hosiery.
- [x] Route both product and worn cross-laces through shared logical satin/metal/side-bow artwork, preserving independently authored camera mounts.
- [x] Restore the missing worn thin-band gold buckle; verify fixed metal across pink/blue/black.
- [ ] Complete final all20-style compatible-ornament paired-sheet acceptance; retain broad-ribbon, flower and cream-binding differences as explicit follow-ups if not repaired. See current PROGRESS for final QA counts.

## 2026-10-27 approved Mimi / studio follow-up
- [x] Integrate exact40user-repaired think frames with lazy local8fpsplayback, calibrated static fallback and lifecycle cleanup.
- [x] Repair REVIEW22:30portrait brief/picker density and1080-height desktop design-box whitespace; retain complete samples and accessible navigation.
- [ ] Retain boutique coarse-overlay art and full20style finish/decor parity as next priorities; final settled session QA is recorded in PROGRESS.


## 2026-10-27 display / worn crystal continuation
- [x] Repair the legacy Crystal toe brooch identity using shared accepted product art and seven fixed worn-camera mounts, retaining missing-product fallback.
- [x] Produce fresh real-browser all20-style display|worn comparisons and bilingual saved Collection/hosiery/PNG-share evidence; scoped results are in PROGRESS.
- [ ] Clean Grand-bow source extraction before shared projection; continue pearl charm scale, integral bows and finish-repeat parity. Full artistic signoff and remaining CrazyGames quality gates remain open.


## 2026-10-27 Pearl / Grand extraction continuation
- [x] Restore original product Pearl nacre coverage and share the braided gold-set identity with fitted cameras, retaining complete missing-art fallback.
- [x] Restore continuous original Grand product satin/tint without moving the exterior silhouette; retain deterministic inputs and native light/dark evidence.
- [ ] Finish Grand exterior scraps and matching worn knot/loop/tail projection; integral bow volumes, bootie fullness and camera-specific repeats remain open. Exact settled scoped QA/legacy baseline failures are in PROGRESS.


## 2026-10-27 Grand satin / REVIEW continuation
- [x] Share original Grand loops/knot/tails through measured camera mounts, correct far-loop occlusion and complete missing-art fallback.
- [x] Replace rejected boutique counter/window/shelf vectors with feathered native paint restoration; preserve visible16-step progression.
- [x] Refresh seven-size screens and16:9/21:9/mobile fitting seams; migrate stale lace browser camera checks with negative controls.
- [ ] Finish tiny Grand contour scraps/wedge collar detail, integral bows, bootie fullness and all-style finish/repeat artistic acceptance. See current PROGRESS for exact validation scope.

## 2026-10-27 integral bow fidelity continuation
- [x] Replace bowsling/bowmule worn compact folds with each original display bow, including registered dye and lighting masks; preserve accepted body, calf, hosiery and low throats.
- [x] Verify native colour/hosiery comparisons and actual bilingual Collection/share/reload flows; retain immutable originals and deterministic rebuild script.
- [ ] Continue tiny Grand contour scraps/wedge collar detail, bootie fullness and camera-specific pattern repeats. All20-style combined artistic acceptance and exact release-ZIP acceptance remain separate gates; see current PROGRESS.

## 2026-10-28 — gen5 rigid fitting rollout
- [x] Port the accepted studpump, flat and Mary Jane half-on front feet with separate standing rear anatomy behind Fitting2D's existing mount/render API.
- [x] Keep exact product shoe pixels under one uniform transform; derive anatomy cuts offline and retain local colour/material/accessory composition.
- [ ] Extend only after generating and reviewing each remaining shoe's own foot camera; slingback/strapped styles need a loosened strap behind the raised foot. Initial-download optimization remains queued after anatomy rollout.


## 2026-10-28 — stiletto9 out4 continuation
- [x] Extend the accepted high-heel whole-foot painting to 9cm pumps with its own automatic opening cut, independent standing rear source, and full-height calf continuation.
- [x] Keep product pixels rigid, use shoe-specific heel shadows, and derive packaging requirements from the actual rigid-style registry.
- [ ] Continue one style at a time after native review; strapped/open-heel sources still require loosened straps behind the raised heel. See current PROGRESS for exact checks and limitations.


## 2026-10-28 — stiletto6 out4 continuation
- [x] Extend the individually reviewed high-heel front and independent standing rear to 6cm pumps, using its own automatic opening cut and shoe-specific contact shadows.
- [x] Verify saved bare/black/white fitting, rigid silhouette, PNG sharing and missing-generated-foot recovery at phone/desktop sizes; preserve the user's hand-editing flat source.
- [ ] Continue kitten as an individual native-review slice; retain loose-strap source requirements for strapped/open-heel styles. Complete broader finish/accessory acceptance and improve package headroom before further rollout. Exact session regression results are in PROGRESS.

### 2026-10-29 REVIEW12:58 counter repair
- [x] Replace stiletto6's rejected raised front heel with retained seated anatomy; broaden the rear leg into its own counter and restore white-hosiery ankle/instep shading. Shoe pixels remain rigid.
- [ ] Supervisor review of the single new before/after contact sheet; see current PROGRESS for exact local checks and remaining limits.


## 2026-10-28 — kitten out4 closed-pump continuation
- [x] Fit approved half-on front and independent standing rear to kitten's own insole/binding without changing original shoe pixels; use its measured low-heel contact shadows.
- [x] Inspect phone/desktop bare, opaque black and opaque white at3×; verify saved hosiery, share, missing-art fallback/recovery and protected user flat hashes.
- [x] 2026-10-29: remove front heel/arch extraction ledges through the reviewed stiletto6 contour process; verify all hosiery outlines, actual rigid draws and five-room grounding; inspect the single1600px supervisor sheet. Exact evidence is in the newest PROGRESS entry.
- [ ] Recover package headroom before further per-style rollout; continue native review one closed pump at a time and keep loose-strap source requirements for strapped/open-heel styles. Exact session checks and remaining source-art limits are in current PROGRESS.


## 2026-10-29 USER23:52 kitten continuation
- [x] Migrate kitten bare/opaque-black/opaque-white to the immutable returned front/rear sources; preserve original contours through whole-image uniform transforms and original-shoe occlusion.
- [x] Carry accepted flat/stiletto6 close crossed pose and0.78rear stack to kitten; inspect390×844/1920×1080and3×crops beside user pair reference.
- [x] Retire unused legacy body-camera upload bytes for authoritative user-source styles while preserving complete local source validation and shared accessories.
- [x] Migrate studpump to the returned user anatomy, close crossed pose and0.78rear stack; pass native/source fidelity, opaque black/white, two-size Chromium, reference contact, saved/recovery and extracted-upload checks.
- [x] Migrate Mary Jane individually to returned user anatomy, close crossed pose and0.78rear stack; retain original integral strap over bare/opaque-black/opaque-white insteps and near-collar occlusion. Exact final source, screenshot, recovery and upload evidence is in newest PROGRESS.

## 2026-10-30 SUPERVISOR12:00 — stiletto6 only
- [x] Restore source-painted opaque white ankle/Achilles/heel/instep/toe relief; correct returning heel-counter collar cut, retain approved v2 rear and equal effective leg widths.
- [x] Actual phone/desktop3×reference contact, saved/share/recovery,10-region runtime relief guard, required syntax/smoke/audio/screens/diff checks and18.953858MiBZIP.
- [ ] Complete exact anatomical seating: front lining triangle, high toe roots and rear heel-ball/counter mismatch remain. Continue stiletto6 before kitten; see newest PROGRESS.
