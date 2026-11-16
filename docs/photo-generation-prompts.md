# Sweet Shoe Atelier — photo set for the fitting card

Prompt pack for GPT Image or Gemini. It produces one photo per shoe shape × sock style
(20 × 10 = 200 photos). The game recolours the shoe and socks to the player's
design, so every photo uses a **white shoe** and **white (or fixed-colour) socks**.

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

- 3:4 portrait, **1536 × 2048 px**, PNG.
- File name: `<shape-id>__<sock-id>.png`, e.g. `maryjane__fishnet.png`, `flat__none.png`.
- Optional masks (Prompt D): `maryjane__fishnet__mask.png`. If the generator can't
  keep masks aligned, skip them and I will cut the masks myself.

---

## Prompt A — master photo (run once, keep the best)

```
Photorealistic close-up lifestyle photo, 3:4 portrait, shot on a phone in soft
natural daylight. A young woman's legs from just below the knees down to the
floor, standing relaxed: the right foot forward and slightly to the right, the
left foot a little behind it, toes pointing toward the lower left of the frame,
both shoes fully visible and not overlapping. Camera at knee height, looking
slightly down (about 25°), front three-quarter view, both feet centred
horizontally, the soles about 15% above the bottom edge, the top edge cutting
just below the knees. Fair, smooth skin with natural shading, slim calves,
no tattoos, no jewellery.
Shoes: simple pointed-toe ballet flats in plain pure-white satin with a thin
cream piping along the opening and a tan leather sole. No logos.
Floor: soft light warm-grey low-pile carpet, fine texture, nothing else in the
frame — no furniture, no walls, no hands, no bags, no text, no watermark.
Mood: calm, airy, cute, like a tidy "outfit of the day" photo; gentle soft
shadow under each shoe; true-to-life colour, not oversaturated, slight film grain.
```

## Prompt B — change the shoe (attach the master)

```
Edit the attached photo. Keep EVERYTHING identical — the legs, skin, pose,
foot positions, camera angle, framing, carpet, light and shadows — and replace
only the shoes on both feet with: {SHAPE DESCRIPTION}.
The shoes are plain pure-white satin with a thin cream piping along the opening
and a tan leather sole, unless the description names another fixed part
(pearls, crystals, clear heel, metal studs, bow). Same size and placement as
the original shoes; nothing added to the background; no text or watermark.
```

### Shape descriptions (paste one into `{SHAPE DESCRIPTION}`)

| id | name | description |
|---|---|---|
| `flat` | Flat | pointed-toe ballet flat, no heel |
| `block` | Block heel | pointed-toe pump on a 6 cm chunky block heel |
| `kitten` | Kitten heel | pointed-toe pump on a slim 3 cm kitten heel |
| `stiletto6` | Slim pump · 6 cm | pointed-toe pump on a slim 6 cm stiletto heel |
| `stiletto9` | Slim pump · 9 cm | pointed-toe pump on a slim 9 cm stiletto heel |
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
Edit the attached photo. Keep EVERYTHING identical — the shoes, legs, pose,
camera, framing, carpet, light and shadows — and dress the legs in:
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
| `sheer` | Sheer tights | sheer 15-denier pure-white tights, skin softly visible through them |
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
