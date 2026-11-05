# Independent pair — source candidate, not shipped

The original `pair-neutral-original.png` is a genuine independently painted
left/right pair generated in the previous session from the three references
listed in `prompt.txt`; `generation.log` records the successful edit. The new
source is 1254×1254, not the requested 1024. Never resize an individual layer or
reuse the old single-foot camera coordinates.

Run `python3 dev/build-independent-pair-source.py` from the repository root.
It preserves source RGB in every retained non-green pixel, removes invisible
alpha specks, and writes all source outputs locally under this directory.
Nothing here is registered or copied to `assets/`.

`candidate-kit/` contains separate visible front/rear skin, shoe, dye-upper,
shadow, highlight and painted occlusion layers, plus exact source
reconstruction. The two feet are independently painted rather than mirrored or
cloned. Foreground occlusion is retained from the master; no hidden rear pixels
have been invented. The source calves already bleed through the upper edge.

`anchors.json` records the immutable camera, collar/vamp/toe coordinates,
preliminary perspective cuff ellipses and remaining integration requirements.
`partition-*.jpg` exposes each visible shoe region; `dye-review-*.jpg` exposes
skin spill and conservative untouched collar/sole margins. Native light/dark
master previews are `pair-{light,dark}-native.jpg`.

The automated source checks verify exact RGBA reconstruction, disjoint visible
partitions, dye-mask containment and top/bottom clearance. They do **not** certify
finished runtime masks. Native review still shows conservative pale dye margins
and the collar partitions need final pixel refinement. Before integration:

1. Refine upper/collar masks and accept the complete material colour ramps.
2. Author every raster/procedural ornament for both new cameras; existing worn
   anchors must not be affine-pasted onto the new openings.
3. Draw all five sock choices with the new calf contours, perspective cuffs,
   foreground overlap and original collar occlusion.
4. Add a complete source-specific pair renderer/cache/retry/fallback path and
   verify save/gallery/share plus every finish and ornament at fixed toe/floor
   pixels in the seven supported layouts.
5. Produce matching independent paired sources for other heel silhouettes.

Current runtime continues to use the accepted single-foot paintings and its
existing safe fitted composition. A neutral source master is not the completed
independent runtime pair requested in REVIEW.
