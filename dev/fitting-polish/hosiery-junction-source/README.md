# REVIEW 2026-10-26 01:11 local fitting repair

These are immutable pre-repair runtime skin and occlusion inputs for all 19
accepted cameras, retained 2026-10-25. No generated or downloaded art is added.

Rebuild with `python3 dev/fitting-polish/repair-hosiery-junction.py` after any
skin/style exporter. The Pillow-only finish smooths the tiny inherited instep
ledge within y620–725, continues skin/fabric beneath each camera's actual heel
counter at y410–630, and prevents counter occlusion from cutting a transparent
seam. Shoe, piping, finishes, ornaments, calves and pair/camera transforms are
unchanged. Newly covered pixels use the existing broad peach palette.

Native 2× before/after counter crops and exact changed bounds are written to
`qa/hosiery-junction/`; full runtime hosiery QA is `qa/hosiery-polish/`.
