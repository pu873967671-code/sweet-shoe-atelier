# frill-sole-mask (user, 2026-11-05 10:11 SGT)
Ref: dev/user-ref/20261105-frill-rear-sole-mask.jpeg — worn view, flat (pink pointed flat), sock = 荷叶边 (frill).
Between the rear (far) shoe's heel/sole and the front shoe, under the rear foot, the frill-sock layer leaves an
uncleaned sole/foot mask: grey/dark specks and a sliver of mask edge visible in the gap (red circle). The sock or
its mask is not cut cleanly where the rear foot's sole meets the shoe/floor.
Fix: cut the frill (and check lace, and every other sock/hose variant) layer cleanly along the shoe sole/heel of
BOTH feet so no grey specks, mask fringes or sock pixels show in the gap below/behind the shoe. Do this on all 20
bases (each base's own geometry, no templates). Do not stretch/warp pixels; pixels outside the fix region unchanged.
Automate a check: render every base x every sock variant (fair + dark skin), and flag non-background, non-shoe,
non-leg pixels in the region under each shoe's sole line / in the inter-shoe gap; must be 0 after fix.
Acceptance: dev/qa-out/frill-sole-mask/ with before/after 3x crops of the gap for every base (frill + lace at least),
the flag counts table, desktop + phone Chromium no page errors. Bump cache versions. Commit.

## Follow-up (Hark review of 63777606)
dev/qa-out/frill-sole-mask/flat-frill-gap-3x.png AFTER: the gap is clean, but the clearance cut into the FRONT shoe:
its collar/opening line at the rear-shoe side now has a hard stair-step notch (pink upper and cream trim cut away
in a jagged "\_/" shape, background showing through). The clearance must only remove sock/mask residue in the gap;
never remove pixels belonging to either shoe's upper, trim or sole. Restrict the clear region with the shoe masks
(subtract both shoes' full silhouettes, dilated 1px), keep edges antialiased. Re-check every base x sock for this:
add a check that shoe-silhouette pixels are identical before/after (0 shoe pixels removed). Provide 3x crops again.
