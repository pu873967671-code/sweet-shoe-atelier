# Sweet Shoe Atelier · 甜甜小鞋铺

A local-first merge and shoe design game for CrazyGames, built with vanilla JavaScript, CSS and Canvas. All artwork, the licensed Chinese font, CC0 music and synthesized effects are local. Effects and music have independent controls; audio cancels scheduled notes during pause/ads/backgrounding, sleeps its music clock and bounds overlapping voices. The CrazyGames v3 SDK is the only external script; the game works when it is unavailable.

## Play locally

```sh
python3 -m http.server 8000
```

Open http://localhost:8000/. Directly opening `index.html` also supports offline play and local saves.

Gather and merge materials in Atelier, deliver customer wishes for coins and renovation stars, and spend stars in Boutique. Sixteen renovations open three chapters, new customers, expert tools and new material chains. Craft discoveries permanently unlock shoe details. Serve customers in the studio, pack commissions, then admire the styled pair in five fitting scenes. Free design and Collection remain available from navigation. After the final renovation, five daily neighborhood wishes offer a thank-you reward.

Odette’s introduction teaches gathering, merging, crate opening, deliveries, star spending, crafted details, a first commission, fitting and Collection. Each lesson saves its progress and can be skipped. Commission patience rests during teaching. Existing players keep their saves without being required to repeat the introduction.

Use **P**, **Esc**, or Pause for independent music/effects controls, English/简体中文, and reset confirmation. Material cells support keyboard arrows and tap-then-tap merging as well as dragging. Reduced motion is supported. The seven target viewports include 1336×790 and 1180×684 plus 1280×720, 800×450, 1920×1080, 390×844 and 844×390.

## Verification

```sh
find . -name '*.js' -not -path './dist/*' -exec node --check {} \;
node smoke-test.js
node qa/startup-test.js
node qa/audio-test.js
node qa/pacing-test.js
python3 qa/cloud-startup.py
python3 qa/generator-status.py
python3 qa/screenshot.py
python3 qa/introduction-test.py
python3 qa/device-preview.py
python3 qa/layout-1247-test.py
python3 qa/calf-1247-test.py
python3 qa/leg-smooth-test.py
python3 qa/skin-pixel-test.py
```

Browser QA requires Python Playwright and `/usr/bin/chromium`; it starts its own local server. Screenshots are written to `qa/`, with assertions and error reports in `qa/report.json`. The suite covers the five viewports, onboarding/reload, crafting, deliveries, chests, bubbles, renovation, chapters, daily rewards, commissions, fitting, localization, SDK callbacks and offline fallbacks. Use `--group screens`, `--group progression`, `--group economy` and `--group integration` to run independently reproducible sections; each writes `<group>-report.json`. The default command executes all four from scratch and only writes PASS after every section succeeds. `--progression-only` remains an alias. `python3 qa/audio-browser.py` verifies actual local MP3 decoding/playback, scene crossfades, mute/pause/resume and missing-file fallback. `qa/device-preview.py` adds actual touch gathering/dragging, portrait-to-landscape rotation, audio pause cleanup, DPR 3 rendering bounds and frame samples at 4× CPU slowdown. It writes `qa/device-report.json` and device screenshots; timings describe the local headless browser and depend on host load. Use `--desktop-only` for a quick 1280×720 preview.

Current fitting acceptance uses `qa/layout-1247-test.py`: five scenes at six sizes, the approved 610×500 crop of a fixed 610×620 camera, unchanged shoe scale, adjacent header/stage/dock, disabled zoom, resize recovery and cropped PNG sharing. `qa/calf-1247-test.py` and `qa/leg-smooth-test.py` check smooth shared bare/hosiery contours and continuous cloth patterns; `qa/skin-pixel-test.py` checks collar coverage across all registered styles. `qa/fitting2d-test.py --recovery-only` checks missing-art recovery. Older pose/zoom harnesses describe superseded fitting layouts.

Node checks cover corrupted saves and v2 migration, resource atomicity, weighted achievable wishes, clock recovery, expert tools, chapter gates, daily rewards, introduction checkpoints, audio buses and a deterministic pacing simulation. Simulation timings are estimates; human playtesting remains necessary.

## Package for CrazyGames

```sh
python3 dev/release.py
```

The final release command stages the upload, checks every JavaScript file, runs smoke/startup/audio/pacing and package/release rejection tests, then plays the extracted ZIP in Chromium. Only a clean result replaces `dist/sweet-shoe-atelier-crazygames.zip` and `dist/release-report.json`. The report records the exact SHA256, catalog, checks and persistent screenshots under `dist/release-evidence/`. Failed validation preserves the previous ZIP/report; publication failure restores both. This prepares local files and does not upload or publish the game.

The archive contains `index.html`, `style.css`, browser scripts, local art/music/font and licenses. It excludes development candidates and stays below 20 MiB. Set `--output /path/to/upload.zip` and optionally `--report /path/to/report.json` for another destination. `python3 dev/package.py` remains available for a quick preflight build during development. Final packaging uses `dev/release.py`; its explicit unreleased-style gate must stay in place until the remaining official sandal acceptance is complete.

## Implementation and platform checks

Browser scripts load directly without a build step. `game.js` is the Node compatibility entry. Saves use validated version 3 data, localStorage and CrazyGames data when available, with migration from v2. The renderer caps device pixel ratio at 2, skips unchanged canvas allocations and shares a 24 MiB source-art cache across studio and worn shoes. Pose transforms do not inflate backing stores; worn masks never read image pixels at runtime. Asset provenance and the Chinese font rebuild command are in `assets/MANIFEST.md`.

SDK loading/gameplay callbacks follow loading, active play, visibility, menus and ads. Chapter completion uses happytime; optional ads retain offline/error fallbacks and duplicate-callback protection. Actual ad fill, production cloud behavior, device audio and touch performance still need verification on the CrazyGames preview host before publishing. Listing images and metadata remain release work.

Fitting keeps one baked platform per scene and uniformly scales the complete cropped picture; zoom is disabled. Shared PNGs use the same 1220×1000 composition. Scene prices are earned coins only: 120 / 240 / 360 / 500.


Final upload verification is included in `python3 dev/release.py`. For a focused archive check, use `python3 qa/upload-test.py --zip /path/to/upload.zip --sock knee --sock-color white --report-dir /path/to/evidence`. The packager parses exact browser JavaScript bytes and rejects incomplete registered kits, ornaments, icons, preload art, scenes and décor. Camera images must match exact registered filenames or explicitly retained legacy sources; using an accepted style prefix cannot admit experimental layers. The upload check serves only extracted ZIP contents, renders every registered style in both cameras, decodes all material/UI icons and exercises saved designs and Collection/reload at 800×450, 390×844 and 1336×790. It selects and decodes every fixed room, verifies the crop, dock adjacency, disabled zoom, overlap, relative shoe scale, saved hosiery/colour, actual resize roundtrip and an opaque cropped PNG download. Release validation requires the complete 15-case fitting audit and binds it to the tested ZIP hash; absent or damaged evidence preserves the last good release.

`python3 qa/upload-rejection-test.py --zip /path/to/upload.zip` verifies that actual damaged archives with a reverted stage crop or undecodable backdrop fail isolated browser acceptance, while preserving the healthy archive. It writes evidence under `qa/upload-rejections/`.

The packager also rejects camera artwork whose style or ornament source is absent from the runtime registry. Development exporters cannot silently add an unfinished shoe to the upload by copying its files into `assets/`; failed preflight leaves the last good ZIP intact.

Development sandal acceptance: `python3 qa/sandal-upload-test.py` builds and serves a temporary ZIP containing the crystal and flower candidates, with prototype catalog metadata. It verifies both cameras for every staged style, actual saved fitting, socks, PNG sharing, Collection/reload and missing-layer recovery without browser asset or registry overrides. Use `--styles wrapsandal --report-dir qa/sandal-wrap-upload` for the wrap candidate. These isolated checks never change the shipped catalog or release ZIP and do not substitute for native art, bilingual catalog or final release acceptance. Three candidate kits together currently exceed the 20 MiB budget.

Platform data reads have a two-second deadline. Failed or stalled cloud reads fall back to local progress and disable cloud writes for that session, protecting unread cloud progress; reopening retries normally. Backgrounding during startup cannot save temporary fresh state. `qa/cloud-startup.py` verifies these cases, successful newest-save selection and legacy migration in Chromium. `qa/generator-status.py` checks real basket selection, live rest timers, energy/space blockers and gathering after recharge in both languages.

Focused painted-fitting checks: `python3 qa/fitting2d-test.py` verifies essential-layer failure, fitted emergency artwork, recovery without reload and latest-update readiness; `python3 qa/paired-fitting-test.py` covers every registered shoe, socks, fixed anchors, resize, PNG sharing and save recovery. `python3 qa/order-energy.py` checks deliberate free wish relief at zero energy, and `python3 qa/order-status.py` checks neutral tier numbers versus fulfilled green checks. Both order checks exercise real merges in English and Chinese at portrait, desktop and short-landscape sizes.
