# Task: apply approved rear heel counter v2 to runtime assets

User APPROVED dev/qa-out/rear_heel/compare.jpg v2 (commit fb4f9728). Apply it:
1. Replace assets/worn/flat.webp and assets/worn/loafer.webp with the v2 candidates (dev/qa-out/rear_heel/{flat,loafer}_candidate.png), encoded the same way as the existing worn webp files (lossless or same quality settings; keep size and alpha).
2. Apply the SAME local patch to every variant of these two bases that shows that region (assets/worn/flat_frill.webp, flat_lace.webp, loafer_frill.webp, loafer_lace.webp and any other flat_*/loafer_* sprite such as _mask, _legs, _sole, socks): align via SPRITES x/y offsets / bbox, only change pixels inside the patch box; for variants where socks cover the region, patch only where the variant equals the original base there (sock pixels untouched). Update _mask (dye), _sole and _legs (skin) masks consistently so dye, sole protection, skin tone and hosiery match the new shape (re-run the existing generators e.g. dev/build-worn-sole-masks.py / legseg export if that is how they were built).
3. Bump ASSET_V. Render flat & loafer with none/frill/lace/sheer socks, a pattern, and bridal skin tone; write dev/qa-out/rear_heel/applied.jpg (2x crops). Run existing smoke tests.
4. Commit.

Hard constraints: no stretching/warping; outside the patch box pixel-exact; do not touch js/audio.js, qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*, other bases.
