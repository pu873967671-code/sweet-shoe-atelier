# material-coverage: material textures must cover the whole dyed upper (user, 2026-11-04 19:54 CST)
Screenshot dev/user-ref/20261104-mesh-not-covering.webp: product (non-worn) view, maryjane, colour 樱花粉, material
透明网纱 (mesh). The mesh texture does NOT cover the whole upper: the toe cap (red box) is plain pink with no mesh, and
along the cream trim, along the sole line and at the heel back there is a plain pink band without mesh (arrows).
"没覆盖全". Likely the material/texture region mask (fabric-regions / product material mask / toe region) is narrower
than the dye mask, possibly made worse by the edges-p/p3 mask edits (compare with c69f3e06 and earlier).
Fix so every dyed pixel of the upper gets the material texture right up to the trim/sole/painted edge, including the
toe. Check ALL materials (缎面, 透明网纱, 蕾丝, 闪粉, 漆皮, 金属, 柔和绒面, 花朵织锻, 密镶, …) on ALL 20 bases in the
product view, and in the worn/salon view too (same rule). Per-base, no one template. Keep cream trim/sole/heel and
fixed ornaments untextured. Don't regress edges-p3 or worn edge fixes. Bump cache versions.
Acceptance dev/qa-out/material-coverage/: survey table (base x material: covered yes/no before/after), 3x BEFORE/AFTER
crops of toe + trim band + heel back for mesh and one more material per fixed base; Chromium desktop+phone, no errors.

## Also: COLOUR (dye) coverage, finer (user, 2026-11-04 19:58 CST: "换色覆盖也是没覆盖全…能再细一点就更好")
Screens dev/user-ref/20261104-slingback-buckle-product.webp (product, 雾霾蓝) and
dev/user-ref/20261104-slingback-buckle-worn.webp (worn, green): on slingback the strap around/under the gold buckle
stays undyed (original pink/white leather shows next to the buckle and on the strap end beyond it). Dye must cover
the strap up to the buckle frame, with only the metal buckle undyed. Then do a finer dye-coverage pass on ALL 20 bases,
both views: any leather/fabric part of the upper that keeps its original colour after a recolour (strap ends, tongues,
keepers, bow undersides, heel-counter ends, toe tips) is a miss. Automated: recolour to a strong colour (e.g. blue and
green) and flag regions of original-pink/white hue inside the shoe silhouette that are not trim/sole/heel/metal/ornament.

## Also: ragged trim edges (user, 2026-11-04 19:59 CST: "这些就很明显了…让codex都去检查吧")
dev/user-ref/20261104-loafer-trim-ragged-worn.webp (worn view, loafer, pink): the cream collar trim on both shoes is
wavy/scalloped and jagged where pink dye meets it (arrows on the collar edges and the inner collar). The trim/dye
boundary must be a clean smooth line following the painted piping, with an even trim width. Check and fix this on
ALL 20 bases in both views (worn and product), all trim/piping edges, using 3x crops in a strong colour; automate a
jaggedness check (boundary curvature/width variance along the trim) so nothing is missed. The user wants Codex to
check everything thoroughly.

## Continuation (chunk 2+)
Material coverage + slingback buckle are done (see PROGRESS). Now do the remaining finer all-base dye-coverage pass
and the ragged-trim smoothing (loafer first; the previous loafer smoothing attempt was reverted — find a method that
follows the painted piping edge, e.g. derive the boundary from the painting's cream-vs-leather luminance/hue at
sub-pixel precision and feather 1px, instead of morphological smoothing). Keep everything already fixed.
