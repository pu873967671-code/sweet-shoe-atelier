# Task: tune hosiery sample (continue hosiery-texture, commit 9a0744aa)

User reviewed dev/qa-out/hosiery/compare.jpg. Keep the approach, tune values (flat + stiletto9 only):
- Sheer cream / nude pantyhose: now reads almost like bare skin and too orange. Raise centre opacity to ~0.38, contour ~0.75; keep the stocking colour clearly visible (closer to OLD colour at centre, but with the edge gradient). Sheen ~0.12.
- Black sheer: shape is good, but centre is too pale/silver-grey. Centre opacity ~0.52, contour ~0.85; sheen weaker (~0.10) and neutral-warm, not silver; skin should only faintly show through on the shin.
- Opaque/knee/thigh: keep the OLD colour/brightness exactly as before; only add subtle edge darkening and a soft sheen (~0.06).
- Bare skin/skin tone unchanged.
Regenerate dev/qa-out/hosiery/compare.jpg (OLD = pre-task commit, NEW = tuned), run hosiery-check and smoke tests, bump ASSET_V, commit.
Same constraints as dev/tasks/hosiery-texture.md.
