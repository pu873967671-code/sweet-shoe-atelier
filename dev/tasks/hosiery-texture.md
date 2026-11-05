# Task: hosiery texture sample (flat + stiletto only)

Problem: worn hosiery looks flat. js/worn-sprites.js hosiery() applies one uniform multiply fill (sheer/pantyhose/blacksheer) or flat colour + luminance (opaque/knee/thigh).

Build a SAMPLE on two bases only: flat and the main stiletto base (check SPRITES for its id, e.g. stiletto9).
1. Offline script dev/build-hose-maps.py: from assets/worn/<base>_legs/skin mask generate assets/worn/<base>_hose.webp (same size/registration as the sprite): R = edge thickness (normalized distance-to-silhouette across the leg width, 255 at contour fading to 0 at leg centre, smooth), G = soft vertical sheen band along shin/calf front plus small knee and instep highlights (follow the leg's actual centreline from the mask; light side consistent with the art), B = reinforcement (toe and heel area of the foot). No change to source art pixels.
2. hosiery(): when <base>_hose exists, sheer/pantyhose/blacksheer opacity varies with R (centre ~0.22, contour ~0.70; blacksheer a bit stronger), B darkens reinforcement slightly, G adds screen sheen (sheer ~0.18, blacksheer ~0.25), plus a very faint tiled fine knit noise (generated procedurally once, small). Opaque/knee/thigh: subtle edge darkening from R and soft sheen from G. Bases without a hose map keep current behaviour exactly. Skin tone, back-leg shadow, sock variants unaffected.
3. Bump ASSET_V. Render flat and stiletto with sheer (cream/nude), blacksheer, opaque, bare skin and bridal skin; write dev/qa-out/hosiery/compare.jpg: old vs new side by side, full leg + 2x crop of shin. Run smoke tests. Commit.
Constraints: do not touch js/audio.js, qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*, non-worn renderers, other bases' assets.
