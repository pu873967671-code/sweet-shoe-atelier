# Grand bow extraction originals

Immutable pre-repair product Grand bow paintings and tint maps, copied from
`assets/shoe2d/accessories` before the 2026-10-27 repair. These are the accepted
local original image-edit derivatives, not newly generated paintings.

`python3 dev/fitting-polish/clean-grand-bow.py` restores enclosed satin holes
from the retained registered originals in `dev/accessory-edits/*_decoration_big.png`
and `dev/accessory-edits/extraction-report.json`. Derived stiletto/platform RGB
uses the existing camera-local shifts documented in their builders. Every final
camera's own exterior alpha/bounds is retained exactly. Satin/tint coverage
matches completely. No source shoe, skin, hosiery or worn ornament is changed.

Run this after legacy accessory, thin-height and platform exporters.
`python3 qa/grand-bow-cleanup-test.py` verifies all 14 deterministic outputs,
seven negative-control cases, exterior coverage/bounds and protected-body hashes.
Native light/dark before/after evidence: `qa/session-0425-bow-cleanup/`.

Scope: enclosed extraction holes, neutral satin and missing tint pixels only.
Tiny inherited jagged scraps on the shoe-side exterior remain an artistic
follow-up; do not use this repair as acceptance of shared worn projection.
