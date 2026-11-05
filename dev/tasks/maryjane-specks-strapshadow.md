# maryjane-specks-strapshadow (user, 2026-11-04 15:20 CST)
Continues maryjane-mask-edges (commit 8e5d02d1, ASSET_V 20261104f) — keep that edge refinement, the opaque
sock shading and the front-collar gap fix.
User screenshot: maryjane, misty-blue floral pattern (雾霭蓝 floral), frill BLACK socks, salon fitting. User:
"这个蒙版也不干净，到处都是黑点，还有就是光影问题，这个带子下投影感觉像凹下去应该不用这个凹的投影".
1. Black specks: dark sock pixels appear as black dots on/along the strap, at the collar piping, and near the
   heel/sole edge at the back of the front shoe. Find the source (sock mask vs strap/shoe mask overlap, sock
   layer drawn over strap, codec fringe, opaque-sock shading pass) and make every mask clean: no isolated dark
   or coloured specks anywhere on shoe, strap, piping, buckle, sole, for all 5 sock colours (black hardest) and
   frill/lace/knee/thigh/none.
2. Strap shadow reads as a groove pressed INTO the sock/foot (concave). The strap sits ON TOP: remove the
   concave/inset shading around the strap on the sock/foot; at most a very soft thin contact shadow just below
   the strap's lower edge falling onto the sock. Front and rear foot.
Allowed: maryjane-only code and the maryjane *_mask/*_sock webps (same size, change only needed pixels,
reproducible script). Never alter paintings, legs, sole, other bases. No stretching/skewing. ASSET_V 20261104g.
Acceptance dev/qa-out/maryjane-specks/: 3x BEFORE/AFTER crops of strap, collar, heel/sole edge, front+rear,
for misty-blue floral + frill black, blue stars + lace cream, pink satin + thigh black, black + knee white.
Chromium desktop+phone, no page errors; README.
