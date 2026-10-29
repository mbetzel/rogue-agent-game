# Too Many Secrets — Print-and-Play Prototype Pack (`v0.11.0`)

Minimalist, ink-saver US Letter (`11" × 8.5"` Landscape) Print-and-Play PDFs synchronized with [RULES.md](../RULES.md).

## Printable PDF Files

| File | Pages | Contents |
| :--- | :---: | :--- |
| **`00_Too_Many_Secrets_Complete_PnP.pdf`** | **14** | Complete all-in-one print bundle (all boards, visual aids, cards, and optional tokens in order). |
| **`01_Player_Boards.pdf`** | **6** | Full-page Consultancy Terminal Mats for *The Acoustic*, *The Phreaker*, *The Prodigy*, *The Spook*, *The Cipher*, and *The Operator* (with integrated `v1.0 / v2.0 / v3.0` ability tracks and 16mm die guides). |
| **`02_Central_Game_Boards.pdf`** | **2** | **Page 1:** SETEC Central Agent & Compiler Board (`v3.0 / v2.0 / v1.0` tile slots, 4/5/6-space scaled Corruption Track, Cube Effect Summary, Game Sequence Overview).<br>**Page 2:** Software Module Market & Central Supply Board (Staging Cup, Exit Sorting Tray, White Contractor `$1/$2/$3` Pool, 5 Market Card Slots, Setup & VP Reference). |
| **`03_Dice_Visual_Aids_and_Market_Cards.pdf`** | **4** | **Page 1:** Full-page Master `1–6` Pip-to-Ability Visual Reference.<br>**Page 2:** `4×` Cut-out Individual Player Pocket Reference Cards (`4.94" × 3.78"`).<br>**Pages 3–4:** All `15×` Software Module Variant (`★`) Market Cards (`1.67" × 2.53"`, sized to fit the Market Board slots) + `5×` Color Summary/Divider Cards. |
| **`04_SETEC_Version_Cards_and_Tokens.pdf`** | **2** | **Page 1:** All `6×` SETEC Version Roadmap Tiles (`2.94" × 1.56"`, sized to nest inside the `v1.0 / v2.0 / v3.0` slots on the Agent Board).<br>**Page 2:** Optional cut-out prototype markers & chits (`Lead Consultant`, `Active Version`, `Secrets`, `Patches`, `$1/$5 Credits`, and `Used/Forfeited` slot markers). |

## Printing & Physical Components Guide

1. **Print Settings:** Print at **100% / Actual Size** (do *not* select "Fit to Printable Area" so card/slot dimensions stay exact) on **US Letter (`8.5" × 11"`)** paper or light cardstock (`65–110 lb` recommended for cards/tiles).
2. **Color & B&W Accessibility:** Every game color is paired with a unique geometric symbol (`◆ Red`, `● Blue`, `▲ Green`, `⬡ Yellow`, `▼ Purple`, `■ Black`, `□ Gray`, `◌ White`), allowing full playability whether printed in color or monochrome laser grayscale.
3. **Physical Dice Needed (Standard `1–6` Pipped `d6`s):**
   - `16` Gray (4 per player)
   - `12` White (Contractor supply)
   - `8` each of Red, Blue, Green, Yellow, and Purple (`2 × Players` used per match)
4. **Physical Cubes Needed (`8mm–10mm` wooden cubes + Cube Tower & Cup):**
   - Attack Cubes (`Red`, `Blue`, `Green` — ~`10` per color) + Corruption Cubes (`Black` — ~`12`)

## Regenerating Assets

Pure Python 3 standard library (zero external dependencies), run via WSL:

```bash
python3 -m pnp.generate_pnp
```
