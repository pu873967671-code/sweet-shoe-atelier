# Pearl orb pump — original sculptural support

Original code-native pearl-ball heel, authored with deterministic smooth sphere shading and small champagne mount geometry. The product and worn cameras have individually positioned supports. This is not a generated raster design or new anatomical painting; the accepted 6cm pump supplies the complete upper, forefoot, arch, binding and fitting anatomy.

Rebuild: `python3 dev/build-pearlheel-assets.py` (Pillow + NumPy). Thirteen complete local layers are exported: seven product 1024×640 layers and six worn 1024² layers. Only the distal heel support is replaced. The original toe/forefoot ground coordinates remain exactly 96/540 in product and 171/964 in worn. The full worn leg and shoe occlusion are byte-for-byte copies of the accepted, softened stiletto6 layers, preserving the shared slim fitting proportions. Finish masks exclude the neutral pearl and champagne fittings. There is no runtime network, image API, pixel readback or third-party art dependency.

Developer-only prerequisites can be installed with `python3 -m pip install Pillow numpy`. This session used `/usr/local/bin/python3` (Python 3.12), existing Pillow, and NumPy 2.5.4 from the user site `/home/sandbox/.local/lib/python3.12/site-packages`. No Python package is required by the browser or upload builder.

`anchors.json` / `export.json` record the separate camera geometry. `export-contact.jpg` shows both camera sources against light/dark backgrounds. `product-support.webp` and `fitting-support.webp` retain the authored native hardware separately for verification. This is one premium fixed-height style, earned from the tier-six sparkle brooch (`spk6`) or 125 coins, with compatible 6cm camera accessories retained.

Acceptance: `python3 qa/new-style-test.py --style pearlheel` checks craft discovery, locked/unlocked orders, complete bounded masks, finish-safe skin and real studio→save→fitting→Collection→reload at 390×844, 1336×790 and 800×450.
