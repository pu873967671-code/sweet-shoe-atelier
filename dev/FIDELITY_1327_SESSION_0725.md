# USER13:27 / 15:17 independent fidelity review — 2026-10-26 07:25 UTC

This review opened the complete 20-style plain product | worn light/dark atlases
from `qa/fidelity-1327/final/`, plus the 20-style compatible legacy ribbon and
flower selections. Fresh focused flat/platform/stiletto6 sheets were opened
for the motif repair below. Root owns the final settled-source all20 refresh
and lace acceptance. A successful render is not full artistic acceptance.

## Implemented in this slice

`js/shoe2d.js` now supplies one simple motif recipe to both compositors: hearts,
stars, five-petal flowers and dots retain the product silhouettes, opacity,
repeat and orientation. `js/fitting2d.js` no longer uses independently shaped
hearts/flowers or smaller, differently spaced dots. The worn source-plane
projection scales motifs and rich checks/embroidery to .76 of product source
units (measured upper span roughly632 versus832pixels), and turns with the
instep. Lace/mesh use the same corrected relative repeat instead of the prior
.90 projection. This keeps original shoe, skin, masks, feet, hosiery and camera
geometry intact. Repeated fields are bounded by inverse-transformed native
canvas corners plus a whole-petal margin rather than a3072-square field.

`qa/pattern-fidelity-test.py`: **PASS4normalized motif size cases plus27actual
composite invariants** (flat/platform/stiletto6 × all9patterns). Native connected
component area normalized by the separately measured upper lengths must agree
within15%; the unscaled old recipe's1.73ratio fails this acceptance. Every
pattern leaves original alpha exact and changes no pixel outside the actual
source upper mask, including fishnet skin. Evidence: `qa/fidelity-1327/patterns/`.

The intermediate three-style paired run rendered294pairs but correctly rejected
its own source hash because the parallel lace implementation changed during
the run. Its captures are diagnostic only (`session-0725-patterns/`); root's
final settled-source run is the acceptance evidence.

## Per-style body review

| Style | Current product / worn finding |
| --- | --- |
| flat | Pointed toe and low heel now retained; rear heel joins still merit native final review. Cream collar is less distinct in worn view. |
| block | Worn toe is visibly rounder/shorter than the sharp product toe. Heel remains the correct block class. Source repair outstanding. |
| kitten | Worn toe is visibly rounder than product. Thin kitten heel class retained. Source repair outstanding. |
| stiletto6 | Pointed toe and thin heel identity retained. Worn cream collar is quieter. |
| stiletto9 | Pointed toe and tall thin heel identity retained. Worn cream collar is quieter. |
| wedge | Worn front welt/sole is thicker and toe rounder; woven wedge class retained. Source repair outstanding. |
| maryjane | Pointed low-flat identity and built-in gold buckle retained; cream collar difference follows flat kit. |
| ballet | Pointed low-flat identity retained. Built-in wrapped ankle ribbons/bow remain visible and separate from selectable cross lacing. |
| slingback | Pointed toe, open back, gold fastening and thin heel retained. |
| loafer | Rounded loafer toe, penny saddle and low stacked heel retained. |
| platform | Square platform toe and substantial block heel retained. Worn cream collar is more conspicuous near arch. |
| bootie | Closed ankle boot, pointed toe and block heel retained. |
| pearlpump | Pointed pump, exterior pearls and thin heel retained. |
| bowsling | Pointed slingback and toe bow retained; worn toe bow reads relatively larger. |
| crystalpump | Pointed pump and toe jewel retained; worn jewel reads relatively larger. |
| studpump | Pointed pump, fixed exterior studs and heel retained. |
| bowmule | Pointed open back mule and toe bow retained; worn bow reads relatively larger. |
| pearlheel | Pointed pump and oversized suspended pearl heel identity retained. |
| luciteheel | Pointed pump and transparent heel identity retained. |
| crystalsandal | Open toe, crossed crystal bands, ankle buckle and thin heel retained. |

## Confirmed remaining ornament differences

- Legacy `strap:ribbon` is a broad folded sash with substantial side knot in
  product but a slim strip/smaller bow in worn. Confirmed on all9compatible
  styles (flat/block/kitten/stiletto6/stiletto9/wedge/platform/pearlheel/luciteheel).
  This remains separate from the newly rebuilt `strap:cross` system.
- Legacy `decoration:flower` product is a lilac layered rosette with dark/gold
  centre; worn is a cream open blossom with yellow centre. All compatible
  sheets show this identity difference, including flat/maryjane/ballet/loafer.
  Camera-specific replacement is still needed; do not certify this as fixed.
- Cream collar binding and the three source toe/welt mismatches above remain
  explicit follow-ups. Premium toe ornaments merit individual size acceptance.

Diagnostic extracted sheets are `qa/fidelity-1327/strap-ribbon-all20-review.jpg`
and `decoration-flower-all20-review.jpg`; they preserve incompatible labels.
Do not mark USER13:27 complete from this session's technical checks. The fixed
610×500crop, approved legs/overlap, hosiery and baked platforms are preserved.
