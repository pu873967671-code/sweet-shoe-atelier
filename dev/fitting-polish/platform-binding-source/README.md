# Platform inner binding alpha repair

These two immutable source layers are the accepted platform worn camera immediately before the localized binding repair. The source RGB already contains the complete cream/tan piping; its extraction had punched ragged transparency holes between the inner piping edge and the outer cloth. Runtime skin, upper/finish masks, ornament mounts, camera, toe and floor are unchanged.

Run `python3 dev/fitting-polish/repair-platform-binding.py` (Pillow only). It restores alpha only inside the explicit retained piping run, leaving all RGB and every pixel outside that interior strip exact. Matching shoe/occlusion coverage prevents skin or socks showing through the binding. Pixel invariants and enlarged before/after evidence are written to `qa/session-2054-platform-binding/`.

Do not rerun the older broad platform asset exporter over the finished skin/masks or this localized repair; that exporter precedes later accepted fitting polish. This repair deliberately starts from the retained final camera layers instead.
