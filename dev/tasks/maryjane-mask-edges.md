# maryjane-mask-edges (user report 2026-11-04 15:14 CST)
User: "这些边缘有漏色，蒙版不够细". Screenshot = current maryjane, light-blue + white-star pattern, lace cream
socks, salon fitting (ASSET_V 20261104e). Arrows: inner edge of the FRONT and REAR collar piping and the
strap edge. Hark zoom shows: the shoe dye (blue) leaks into the cream collar piping (a thin blue line runs
inside the piping), piping/strap/collar edges are ragged/stair-stepped with blue specks on the cream sock,
and the dye boundary does not follow the painted edges.

## Goal
Refine the maryjane dye/motif masks so colour and pattern stop exactly at the painted shoe edges:
- cream collar piping stays its own cream (no dye, no motif), crisp on both sides;
- strap, buckle, collar and vamp edges anti-aliased and smooth, no jaggies, no blue specks on sock/foot;
- sock/foot side of the edge never tinted.
Cover bare/frill/lace/knee/thigh and all 5 sock colours, all 8 shoe colours × 10 patterns, front & rear.
Keep the 13:53 opaque-sock shading and the 14:08 front-collar gap fix intact.

## Allowed
User asked for finer masks: you MAY regenerate maryjane_mask.webp, maryjane_frill_mask.webp,
maryjane_lace_mask.webp (and the *_sock.webp masks if needed) at the same size. Change only pixels in a
narrow band around edges; everything else byte-identical. Build them with a reproducible script in dev/.
Never alter maryjane.webp / maryjane_frill.webp / maryjane_lace.webp paintings, legs, sole, or any other base.
No stretching/skewing. Bump ASSET_V to 20261104f.

## Survey only (no changes)
Render the other 19 bases (cream lace + blue star pattern, and thigh black) and list in README which show
the same dye bleed into piping/edges, with crops, so Hark can ask the user.

## Acceptance (dev/qa-out/maryjane-edges/)
- zoomed 3x BEFORE/AFTER crops of front collar, rear collar, strap+buckle for: light blue stars + lace cream,
  pink satin + thigh black, black + none, mint floral + frill white.
- Chromium /usr/bin/chromium, desktop + phone, no page errors; README with cause and what changed.

## Addendum (user, 2026-11-04 15:20 CST) — MUST also do
Screenshot: maryjane, misty-blue floral pattern, frill BLACK socks. User: "这个蒙版也不干净，到处都是黑点，还有就是
光影问题，这个带子下投影感觉像凹下去应该不用这个凹的投影".
1. Black specks: dark sock pixels show as black dots along/inside the strap, at the collar piping and near the
   sole/heel edge (rear of the front shoe). Masks must be clean: no isolated dark or coloured specks anywhere on
   the shoe, strap, piping, buckle or sole, in every sock colour (check black hardest).
2. Strap shadow: the shading under/along the strap reads as a groove pressed INTO the foot/sock (concave).
   The strap sits ON TOP of the sock: remove the concave/inset shadow; at most a very soft thin contact shadow
   directly below the strap's lower edge, falling onto the sock, no dark line above/inside. Front and rear foot.
Add to acceptance: frill black + misty blue floral, 3x crops of strap, collar and heel/sole edge, before/after.
