# Sweet Shoe Atelier — photo set for the fitting card

Prompt pack for GPT Image or Gemini. It produces one photo per shoe shape × sock style
(20 × 10 = 200 photos). The game recolours the shoe and socks to the player's
design, so every photo uses a **white shoe** and **white (or fixed-colour) socks**.

## Run it directly (GPT Image or Gemini)

`dev/generate-photos.py` reads the prompts and tables below and calls the API for you,
in the right order (master → shapes → socks). Python 3 only, nothing to install.

```sh
git clone -b claude/game-art-defects-aesthetics-hre0nm https://github.com/pu873967671-code/sweet-shoe-atelier.git
cd sweet-shoe-atelier

export OPENAI_API_KEY=sk-...          # for GPT Image (gpt-image-1, 1024x1536)
python3 dev/generate-photos.py --provider openai --test

export GEMINI_API_KEY=...             # or Gemini (gemini-2.5-flash-image, 3:4)
python3 dev/generate-photos.py --provider gemini --test
```

- `--test` makes the 9-photo test batch; leave it out for all 200.
- `--shapes flat,maryjane --socks none,fishnet` makes only those.
- `--masks` also makes the Prompt D colour maps.
- `--dry-run` prints what would be made, without calling the API.
- Photos go to `photos/` (not committed). Files that exist are skipped: delete a
  photo and run again to redo it. If you don't like `master.png`, delete the whole
  folder and start again, since every photo is an edit of it.
- Editing the prompts or tables in this file changes what the script sends.

## How to work (important for consistency)

1. **Make one master photo first** (Prompt A). Regenerate until you love it. Every
   other photo is an **edit of this master**, attached as the reference image, so
   the legs, pose, camera, floor and light stay identical.
2. **Per shoe shape:** attach the master, run Prompt B once per shape (20 photos,
   bare legs). Check the feet stay in exactly the same place.
3. **Per sock style:** attach that shape's bare-leg photo, run Prompt C once per
   sock style (9 more per shape).
4. Start with a **test batch**: Flat, Mary Jane and Slim pump 9 cm, each with
   Bare legs, Sheer tights, Diamond knit (9 photos). Send them to me before the
   full run, so I can confirm they work in the game.

## Delivery

- Portrait PNG: 3:4 (Gemini, or 1536 × 2048 by hand) or 2:3 1024 × 1536 (GPT Image); the game crops.
- File name: `<shape-id>__<sock-id>.png`, e.g. `maryjane__fishnet.png`, `flat__none.png`.
- Optional masks (Prompt D): `maryjane__fishnet__mask.png`. If the generator can't
  keep masks aligned, skip them and I will cut the masks myself.

---

## Prompt A — master photo (run once, keep the best)

```
Anime illustration in the style of a dress-up game's detailed outfit art: clearly
hand-drawn, with fine clean line art in soft brown-pink, and rich painterly anime
shading on top of it: smooth soft gradients, glossy luminous materials, delicate rim
light, stylised elegant proportions with long slender legs and small dainty feet, pale
porcelain skin with a soft pink blush on the ankles and insteps. The satin shoes are
painted with a pearly sheen, crisp white highlight shapes and a few four-point
sparkles. Soft pastel palette. It must read as a drawing, not a photo and not a 3D
render: no realistic skin texture, no photographic lighting, no film grain.
Portrait 2:3. A first-person "shoe selfie": what she sees when she bows her head and
looks down at her own feet while standing. Steep high-angle view from above, camera
pointing almost vertically down at the floor. Because of the foreshortening only the
lower shins are seen, coming down from the top edge, with no knees and no thighs, and
the feet are the largest thing in the frame.
Pose: a cute fashion-selfie stance. The left foot points straight ahead toward the
bottom of the frame, its shoe seen from above. The right foot is placed slightly
forward and turned outward about 70 degrees, so that shoe is seen in side profile from
above: its whole silhouette is readable, including the arch of the sole and the full
heel from seat to tip standing on the floor. Both shoes fully visible, not overlapping,
centred in the frame. No tattoos, no jewellery.
Shoes: classic pointed-toe pumps on a slim 6 cm heel in plain pure-white satin, with a
thin cream piping along the opening and a tan sole. No ornaments, no logos.
Floor: pale cream marble tiles painted simply with thin tile lines and very faint
veining, matte, filling the whole background, no reflections. Nothing else in the
frame: no phone, no hands, no bag, no skirt, no furniture, no flowers, no text, no
watermark, no signature.
Mood: sweet, dreamy, casual and candid; a soft simple shadow under each shoe.
```

*(The chosen master is an illustrated look-down "shoe selfie": the shoe on the left of
the picture is in side profile so its heel shows, the shoe on the right is seen from
above. The master wears a 6 cm pump, not a flat.)*

## Prompt B — change the shoe (attach the master)

```
Edit the attached illustration. Keep EVERYTHING identical — the drawing style,
line art, legs, skin, pose, foot positions, camera angle, framing, floor, light
and shadows — and replace only the shoes on both feet with: {SHAPE DESCRIPTION}.
The shoes are plain pure-white satin with a thin cream piping along the opening
and a tan leather sole, unless the description names another fixed part
(pearls, crystals, clear heel, metal studs, bow). Same size and placement as
the original shoes: the shoe on the left of the picture still in side profile
with its heel (or flat sole) fully visible, the shoe on the right still seen
from above. Nothing added to the background; no text or watermark.
```

### Shape descriptions (paste one into `{SHAPE DESCRIPTION}`)

| id | name | description |
|---|---|---|
| `flat` | Flat | pointed-toe ballet flat, no heel |
| `block` | Block heel | pointed-toe pump on a 6 cm chunky block heel |
| `kitten` | Kitten heel | pointed-toe pump on a slim 3 cm kitten heel |
| `stiletto6` | Slim pump · 6 cm | pointed-toe pump on a slim 6 cm stiletto heel |
| `stiletto9` | Slim pump · 9 cm | pointed-toe pump on a very high, thin 9 cm stiletto heel, clearly taller than a 6 cm heel: the heel is about as tall as the shoe is long and the foot stands steeply arched, almost on tiptoe |
| `wedge` | Wedge | pointed-toe closed shoe on a 7 cm woven natural jute wedge |
| `maryjane` | Mary Jane | pointed-toe flat with one thin strap across the instep and a small gold buckle on the outer side |
| `ballet` | Ribbon ballet | ballet flat with white satin ribbons crossing over the ankle and tied |
| `slingback` | Slingback | pointed-toe pump on a 6 cm slim heel, open back with a thin strap behind the heel and a small gold buckle |
| `loafer` | Penny loafer | low penny loafer with a stitched strap across the vamp, 2 cm stacked heel |
| `platform` | Platform pump | round-toe pump with a 2 cm platform sole and a 10 cm chunky block heel |
| `bootie` | Ankle bootie | pointed-toe ankle boot ending just above the ankle bone, 6 cm block heel |
| `pearlpump` | Pearl satin pump | pointed-toe 7 cm stiletto pump with a row of small ivory pearls along the opening |
| `bowsling` | Bow slingback | slingback on a 6 cm slim heel with a soft satin bow on the toe |
| `crystalpump` | Crystal spray pump | pointed-toe 8 cm stiletto pump with a small spray of clear crystals on the toe |
| `studpump` | Studded pointed pump | pointed-toe 8 cm stiletto pump with a line of tiny silver studs along the opening |
| `bowmule` | Bow mule | backless pointed-toe mule on a 6 cm slim heel with a large soft satin bow on the vamp |
| `pearlheel` | Pearl orb pump | pointed-toe pump whose 7 cm heel is a stack ending in one large ivory pearl ball |
| `luciteheel` | Lucite heel pump | pointed-toe pump on a 8 cm transparent clear acrylic heel |
| `crystalsandal` | Crystal chain sandal | open-toe sandal on a 8 cm stiletto, thin white satin straps crossing the foot, a fine crystal chain around the ankle |

## Prompt C — add the socks (attach that shape's bare-leg photo)

```
Edit the attached illustration. Keep EVERYTHING identical — the drawing style,
line art, shoes, legs, pose, camera, framing, floor, light and shadows — and
dress the legs in:
{SOCK DESCRIPTION}.
The hosiery must follow the 3D shape of the calves, ankles and feet naturally
(pattern and texture wrap around the leg and continue smoothly into the shoe),
with realistic sheen and transparency. Do not change the shoes. No text or
watermark.
```

### Sock descriptions (paste one into `{SOCK DESCRIPTION}`)

| id | name | description |
|---|---|---|
| `none` | Bare legs | *(skip — the bare-leg photo from Prompt B is this one)* |
| `frill` | Frill socks | pure-white ankle socks with a soft ruffled frill cuff folded over just above the shoe |
| `lace` | Lace socks | pure-white ankle socks with a delicate scalloped lace cuff just above the shoe |
| `sheer` | Sheer tights | very sheer 10-denier white tights, a barely-there veil: the skin tone clearly shows through everywhere, with only a faint white haze, a soft matte sheen, and slightly whiter edges where the leg turns away; not opaque, not pearly, not glossy |
| `knee` | Knee-high | pure-white matte knit knee-high socks ending just below the knee with a fine ribbed top band |
| `thigh` | Thigh-high | pure-white soft satin-sheen opaque stockings covering the whole visible leg |
| `blacksheer` | Black sheer | sheer 20-denier black tights, skin visible through them, darker at the leg edges |
| `pantyhose` | Sheer pantyhose | sheer 10-denier nude/tan pantyhose with a soft natural sheen |
| `opaque` | Opaque tights | matte opaque 80-denier pure-white tights |
| `fishnet` | Diamond knit | pure-white fishnet tights with a medium diamond mesh (about 1 cm holes) that wraps around the leg and continues over the top of the foot |

*(White socks and tights are recoloured in the game to pink, mint, cream, white
or midnight. Black sheer and pantyhose keep their own colour.)*

## Prompt D — optional masks (attach the finished photo)

```
Return the attached photo pixel-aligned and unchanged in size and framing, but
flattened into a colour map: the shoe uppers (the fabric part only) in pure
#FF00FF, the soles, heels, piping, pearls, crystals, studs, bows-hardware and
buckles in pure #0000FF, the socks/tights in pure #00FF00, bare skin in pure
#FFCC99, and everything else (floor, shadows) in pure black #000000. Hard flat
colours, no shading, no anti-aliasing beyond 1 px, no text.
```

## Quality checklist before sending

- Feet in the **same position** as the master in every photo (flick between two
  photos: only the shoe or the socks should change).
- Shoe is **plain white** (no tint) with the cream piping and tan sole.
- Both shoes fully in frame, nothing cut off; top edge just below the knees.
- No extra objects, hands, text, logos or watermarks.
- Hosiery wraps the leg; no flat pattern pasted on; no seam at the ankle.
