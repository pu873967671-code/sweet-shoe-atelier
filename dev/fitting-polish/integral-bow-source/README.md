# Integral satin bow repair inputs

The eight WebPs here are the exact pre-repair worn `shoe`, `upper`, `shadow`
and `highlight` layers for bowsling and bowmule. They are retained immutable
inputs, not shipped assets. `../repair-integral-bows.py` restores the clean
original slingback forefoot, then projects each style's own product bow onto
its fitted vamp. Premultiplied cubic interpolation preserves soft edges.

Run the repair after either original integral-bow builder. Product sources,
skin, hosiery, occlusion, outsole, heel, cameras and pair geometry are unchanged.
Generated source invariants are in `qa/integral-bow-source/report.json`;
actual-browser comparisons remain necessary for artistic acceptance.
