# Task: rear heel counter candidates v2 (flat, loafer) — CANDIDATES ONLY

User reviewed dev/qa-out/rear_heel/compare.jpg (see red arrows in dev/qa-out/rear_heel/user_feedback_1830.webp): "the shoe should be a bit thicker, the cut went too far". At the arrows the rear shoe's back edge now ends in a thin, sharp sliver tucked against the front ankle.

User clarification: "the wrapping thickness of the shoe is gone, it was shaved too much" — the rear shoe must still visibly WRAP the heel: keep the shoe wall depth/volume around the back of the heel (the curved counter wrapping the heel), only lower its top edge slightly.

Do: revise dev/rear-heel-counter.py so the repair is less aggressive: keep more of the rear shoe's back collar — the shoe wall at that spot should keep roughly its natural thickness (similar to the wall thickness a little further left), ending with a rounded, fuller back edge and the cream piping following it, instead of tapering to a sliver. Still remove the empty brown lining pocket. Aim between the original and v1 (closer to v1 height, but thicker wall). Same rules: local patch only, outside box pixel-exact, no stretching/warping, transparent background.

Output: overwrite dev/qa-out/rear_heel/flat_candidate.png, loafer_candidate.png, and compare.jpg with THREE columns: BEFORE / v1 / v2 at 2x. Do NOT replace runtime assets. Commit dev files only.

Hard constraints: do not touch js/audio.js, qa/, dev/codex_ledger.csv, dev/codex_tokens.csv, dev/codex_pause_until, assets/src-user-legs-20261029/*, assets/worn/*.
