# Task: repaint the rear shoe's heel counter (flat, loafer) — CANDIDATES ONLY

## Problem
In assets/worn/flat.webp and assets/worn/loafer.webp (worn try-on, two legs, rear leg on the left/behind), the REAR shoe's back collar/heel counter pokes up just behind the FRONT leg's ankle (around x 300-360, y 600-680 in the sprite), but no rear heel/foot is visible there, so the rear shoe reads as too big / not fitting. Check the other 18 bases (keys of SPRITES in js/worn-sprites.js) for the same defect and list them.

## Do
- For each affected base, repaint ONLY that small region so the rear shoe's heel counter sits low and snug and disappears naturally behind the front leg (front leg skin/outline continues; background stays transparent). Use gpt-image-2 edits via the relay (see skill notes: POST https://afgp.cc.cd/v1/images/edits, multipart, model=gpt-image-2, short single-purpose prompt with curl --form-string, crop the region with margin, then paste back ONLY inside a feathered mask), or hand-paint with PIL if simpler. Match line weight and colours exactly. No stretching, shearing or warping of pixels.
- DO NOT overwrite assets. Write candidates to dev/qa-out/rear_heel/<base>_candidate.png (full-size sprite, RGBA) and a before/after zoom sheet dev/qa-out/rear_heel/compare.jpg (crop around the region, 2x zoom, on light bg). Also note which _frill/_lace variants would need the same patch.
- Do not commit asset changes; commit only the dev/qa-out files and any script.

## Hard constraints
Do not touch js/audio.js, qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*.
