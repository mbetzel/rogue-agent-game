# Too Many Secrets — Print-and-Play Prototype Pack (`v0.38.0`)

Minimalist, ink-saver US Letter (`11" × 8.5"` Landscape) Print-and-Play PDFs synchronized with [RULES.md](../RULES.md).

## Printable PDF Files

| File | Pages | Contents |
| :--- | :---: | :--- |
| **`00_Too_Many_Secrets_Complete_PnP.pdf`** | **14** | Complete all-in-one print bundle (all boards, visual aids, cards, and optional tokens in order). |
| **`01_Player_Boards.pdf`** | **6** | **Pages 1–4:** Company Terminal Mats with empty modular docks for Client Company Cards and White Hat Dossiers (Personal Reserve strip, CI/CD pipeline with **Processing Box** → Scanned Box, four **Shield Slots** each with a Glitched Shield Slot marker spot, `0–17` Market Share track with 2P `13` / 3P `16` / 4P `17` start-max marks and `0` = Market Collapse plus a Market Leader Bonus reminder, and the Public Relations Track at `3 🔬` per Market Share).<br>**Page 5:** `6×` Client Company Cards cut-out sheet (`3.22" × 1.94"` cards with Once-per-Version Institutional Overrides and `v1.0/v2.0/v3.0` checkboxes).<br>**Page 6:** `6×` White Hat Dossier Cards cut-out sheet (`3.22" × 2.03"` cards with Purple Die face breakdown and repeatable `Purple ★` Signature Protocols). |
| **`02_Central_Game_Boards.pdf`** | **2** | **Page 1:** SETEC Central Agent & Compiler Board (`v3.0 / v2.0 / v1.0` tile slots, 4/5/6-space scaled Corruption Track, Cube Effect Summary, Six-Phase Round Reference (with Secret faces, Processing Box, Market Leader Bonus)).<br>**Page 2:** Software Module Market & Central Supply Board (Staging Cup, Exit Sorting Tray, White Contractor `$1/$2/$3` Pool, 4 Market Card Slots [Red, Blue, Green, Yellow], Setup & VP Reference). |
| **`03_Dice_Visual_Aids_and_Market_Cards.pdf`** | **4** | **Page 1:** Full-page Master `1–6` Pip-to-Ability Visual Reference (Secret faces on Red/Blue/Green/Purple Face 5, Yellow Market Share faces, Secret Face Yields table).<br>**Page 2:** `4×` Cut-out Individual Player Pocket Reference Cards (`4.94" × 3.78"`).<br>**Pages 3–4:** All `12×` Software Module Variant (`★`) Market Cards (`1.67" × 2.53"`, sized to fit the 4 Market Board slots) + `4×` Color Summary/Divider Cards (Purple variant cards retired; Purple Face 6 triggers bespoke Archetype Signature Protocols; Variant card text follows RULES_APPENDIX.md `v0.38.0`). |
| **`04_SETEC_Version_Cards_and_Tokens.pdf`** | **2** | **Page 1:** All `6×` SETEC Version Roadmap Tiles (`2.94" × 1.56"`, sized to nest inside the `v1.0 / v2.0 / v3.0` slots on the Agent Board).<br>**Page 2:** Optional cut-out prototype markers & chits (`First Player Marker`, `Active Version`, `4× Market Share Markers`, `Corporate Secrets`, `16× Glitched Shield Slot` markers, `Research Tokens (🔬)`, `$1/$5 Money`, and `Used/Forfeited` slot markers). |

## Printing & Physical Components Guide

1. **Print Settings:** Print at **100% / Actual Size** (do *not* select "Fit to Printable Area" so card/slot dimensions stay exact) on **US Letter (`8.5" × 11"`)** paper or light cardstock (`65–110 lb` recommended for cards/tiles).
2. **Color & B&W Accessibility:** Every game color is paired with a unique geometric symbol (`◆ Red`, `● Blue`, `▲ Green`, `⬡ Yellow`, `▼ Purple`, `■ Black`, `□ Gray`, `◌ White`), allowing full playability whether printed in color or monochrome laser grayscale.
3. **Physical Dice Needed (Standard `1–6` Pipped `d6`s):**
   - `20` Gray Legacy dice (`2` per player at setup; more from Level 1 Breakthroughs)
   - `12` White Contractor dice
   - `8` each of Red, Blue, Green, Yellow (`2 × Players` in Central Market; each player also takes `1` starting colored die of their Client Company color from that stack)
   - `8` Purple Specialist dice (`1` starter + `1` in Personal Reserve per player)
4. **Physical Cubes Needed (`8mm–10mm` wooden cubes + Cube Tower & Cup):**
   - Attack Cubes (`Red`, `Blue`, `Green` — ~`10` per color) + Corruption Cubes (`Black` — ~`12`)
5. **Market Share Markers:** `1` per player (cut-out chit from `04`, or any small marker that fits a Market Share track cell).

## Regenerating Assets

Pure Python 3 standard library (zero external dependencies), run via WSL:

```bash
python3 -m pnp.generate_pnp
```
