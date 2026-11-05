Front collar cleanup (2026-10-24)

The original shoe extraction retained a narrow photographic skin triangle and
jagged pink/ivory strip inside each front opening. Run clean-front-collar.py once
at the end of the documented fitting export sequence, after source skin and
Mary Jane/ballet/slingback exports. It removes source-skin pixels above four
authored inner-piping curves, clears corresponding occlusion/cloth masks, and
continues the same cel skin through the opening. Exterior shoe geometry, upper
calves, woven support and every visible pixel outside this opening remain exact.
This is deterministic processing of existing paintings; no new generated art.

QA: python3 qa/collar-seam.py. It compares all six layers for seven styles against
4496951, verifies exact visible pixels/alpha outside the opening, and captures
four heel-specific native camera before/after pairs without runtime readbacks.
The contact sheet is qa/fitting2d/collar-before-after.jpg.
