# Mary Jane / ribbon ballet source and provenance

Built-in image_gen returned no artifact. Following REVIEW 21:52/23:05's explicit gpt-image-2 image-edit workflow, the imagegen skill bundled CLI generated four genuine edits through the established local-project endpoint https://afgp.cc.cd/v1. Model: gpt-image-2, quality: high. Exact prompts are the four `*-prompt.txt` files; original images are `product.png`, `fitting.png`, `ballet-product.png`, `ballet-fitting.png`. CLI logs record completion. API outputs were 1586×992 product and1254-square fitting despite the requested1024 frames; deterministic exports normalize each back to its input canvas.

Input `product-input.png` is the accepted `assets/shoe2d/flat_base.webp`; `fitting-input.png` is the existing `dev/fitting-source/flat.png`. Only the generated strap/ribbons and gold buckle are extracted from the edits. Original base bodies, heel/sole, toe anchors and accepted stylized skin remain immutable. Body anatomy is not newly generated. Lavender extraction cloth is neutralized before tint, gold buckle stays gold.

Rebuild: `python3 dev/build-new-shoe-styles.py --style maryjane` or `--style ballet` (`all` defaults to both). Product exports include base/upper/binding/insole/sole/shadow/highlight; fitting exports include shoe/upper/shadow/highlight/occlusion/legs. Product1024×640 and fitting1024-square; source-coordinate ornament component bounds are in each `*-export.json`.

Ballet retains the current accepted flat's small low heel; it is not a newly painted zero-drop last. Ribbon ties wrap above the ankle in worn view. This limitation must remain explicit in PROGRESS until a genuinely flat-foot source is accepted.
