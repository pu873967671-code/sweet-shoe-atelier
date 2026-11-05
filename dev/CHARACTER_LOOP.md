# Character loop — Supervisor 13:32 (2026-10-24)

## Iteration 1 — baseline personally read
- Opened existing `qa/atelier_390x844.png`, all six neutral customer portraits in `qa/character-current-sheet.jpg`, and the original full-size Mimi think source.
- Existing customers share recognizable cartoon faces but costume colours are muted; Mimi's source has more painterly detail. Root is handling matching mint/candy art.
- Mobile used a 128×112px bust window with a 310px source, making Mimi much smaller than desktop. Expanding vertically would shrink the nine-row board; rejected that approach.

## Iteration 2 — render, personal read, critique
- Added a 152px reserved horizontal lane with a 360px bust source; maintained 112px row height and all nine board rows. Real runtime `qa/character-test.py 2` PASS: seven viewports, all art decoded, 44px order portraits, no Mimi/board overlap; portrait guide and Mimi do not overlap.
- Personally opened full-size portrait 390×844, desktop 1336×790 and short landscape 844×390. Mobile guide's complete tier chain remains visible and no customer/order/action overlaps.
- Critique: Mimi's face can still be larger within the same crop. Next iteration increases source to 400px (+29% from baseline); preserve lane and board. Desktop/short landscape retain established art placement.

## Iteration 3 — final larger mobile bust / seven-size runtime read
- Enlarged the source crop to 400px (+29% over original310), in a152×112px lane (+19% width), without changing the board row height. PASS `python3 qa/character-test.py 3`: seven actual viewports (1336×790,1180×684,1280×720,800×450,1920×1080,390×844,844×390); decoded art, all44px order avatars, no Mimi/board overlap; portrait speech surface does not overlap Mimi.
- Personally opened full-size final390×844 plus a contact sheet of all seven captures. Mobile face and hand read more clearly, complete nine-row board remains visible, all tier thumbnails retained. Desktop/short-landscape placement is unchanged. Accepted this layout.

## Iteration 4 — existing cartoon assets, garment palette / personally inspected
- Built `dev/build-character-palette.py`:18 customer expression busts +6 Mimi poses +neutral. Reads original pixels from fixed git source revision `92ab7cf`, applies narrow garment hue/position masks; no cumulative recolouring. Existing3D cartoon faces/identity/anatomy are retained. This is a clothing palette unification, **not newly generated art or a geometry/style regeneration**.
- Casual hoodie now fresh mint; school blue/navy becomes pale mint/seafoam with deeper teal outlines; tea floral blouse retains cream with mint floral details; pink costumes receive a small clean candy lift. Bridal cream, original skin/hair and Mimi pink skirt remain restrained. Mimi's existing green sewing tape/vest is cleaned toward mint.
- Personally opened customer before/after sheets and Mimi after, then final decoded WebP customer/Mimi sheets and full-size school bust. Rejected lossless output because it inflated runtime assets by2.92MiB; switched to quality90WebP. Final25 assets total1,186,760bytes vs original1,205,642 (18,882bytes smaller).
- Script assertions prove exact alpha after WebP decode, exact protected pixels before RGB encoding, and customer facial top140rows unchanged before encoding. RGB quality90 encoding can alter a few source RGB values; no global face/skin grade is applied. Build-time Pillow/NumPy only; no runtime dependency/CDN.
- Final asset report and personally inspected sheets: `qa/character-palette/report.json`, `customers-final.jpg`, `mimi-final.jpg`. Final frozen-art runtime regression PASS: `qa/supervisor-1332-final-screens.json`, 18 screenshots / 28 checks, desktop and mobile personally read; no page/local-asset errors.


## Iterations 5–6 — genuine full cast redraw (2026-10-24)
- Built-in image tool returned no artifact; used the user-authorized existing `/workspace/work/gen` generator. Exact prompts and eight raw sheets retained under dev/. All six customer identities × three expressions are newly drawn, alongside six Mimi poses and matching neutral. Mint/candy/cream, rounded Western animated-feature 3D forms, clean hair volumes and dimensional faces replace the prior clothing-only grade.
- Personally read all expression and pose sheets. First Mimi fixed-third extraction included the neighbouring present hair in surprise; rejected that export and split at real empty source columns. Reopened corrected `qa/character-art-accepted/mimi-poses.jpg`: stray fragment gone. Alpha sources stay alpha; RGB green source is keyed with edge colour decontamination. Head-centred padded canvases keep gestures from moving portrait faces.
- Root personally opened final `qa/character-loop-6/atelier_390x844.png`, `atelier_844x390.png`, desktop Atelier/result and all-expression sheet. New faces remain readable at44px; mobile Mimi bust is expressive and board/guide remain unobstructed. Wide present/point pose canvas padding makes contain-style source thumbnails look smaller; runtime uses authored height and equal face framing.
- PASS offline25asset audit and actual7layout character suite. Runtime ZIP19.20MiB. Saved raw sheets/importers/prompts are source-only; no online art dependency.
