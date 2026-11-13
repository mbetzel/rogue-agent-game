# Too Many Secrets — Print-and-Play Prototype Pack (`v0.42.0`)

Minimalist, ink-saver US Letter (`11" × 8.5"` Landscape) Print-and-Play PDFs synchronized with [RULES.md](../RULES.md).

## Printable PDF Files

| File | Pages | Contents |
| :--- | :---: | :--- |
| **`00_Too_Many_Secrets_Complete_PnP.pdf`** | **15** | Complete all-in-one print bundle (all boards, visual aids, reference cards, cards, and optional tokens in order). |
| **`01_Player_Boards.pdf`** | **6** | **Pages 1–4:** Company Terminal Mats with vertical resource holders (Corporate Secrets, Liquid Cash, Research Tokens), expanded 5-level Public Relations Track with dedicated Level 3 Personal Reserve Purple die outline, setup die outline spaces across all tracks unlocking dice (Defense Grid L1, Triage L1, Release L1, Public Relations L3), CI/CD pipeline (`Ready for Release` → `In Production` → `Under Development` with unbounded `Scanned Box` and elongated FIFO queue `Processing Box`), and four spacious **Shield Slots** each with a Glitched Shield Slot marker spot.<br>**Page 5:** `6×` Client Company Cards cut-out sheet (`3.22" × 1.94"` cards with Once-per-Version Institutional Overrides and `v1.0/v2.0/v3.0` checkboxes, dealt alongside terminal mat).<br>**Page 6:** `6×` White Hat Dossier Cards cut-out sheet (`3.22" × 2.03"` cards with Purple Die face breakdown and repeatable `Purple ★` Signature Protocols, dealt alongside terminal mat). |
| **`02_Central_Game_Boards.pdf`** | **2** | **Page 1:** SETEC Central Agent & Market Share Board (`v3.0 / v2.0 / v1.0` tile slots, 4/5/6-space scaled Corruption Track, Cube Effect Summary, and the shared **Central Market Share Track** (`17` down to `0` with 2P `13` / 3P `16` / 4P `17` start-max marks, `0` = Market Collapse, and Market Leader Bonus / Tiebreaker summary)).<br>**Page 2:** Software Module Market & Central Supply Board (Staging Cup, Exit Sorting Tray, 4 Market Card Slots [Red, Blue, Green, Yellow], Setup & VP Reference). |
| **`03_Dice_Visual_Aids_and_Market_Cards.pdf`** | **5** | **Page 1:** Full-page Master `1–6` Pip-to-Ability Visual Reference (Secret faces on Red/Blue/Green/Purple Face 5, Yellow Market Share faces, Secret Face Yields table).<br>**Page 2:** `4×` Cut-out Individual Player Dice & Secret Yields Reference Cards (`4.94" × 3.78"`).<br>**Page 3:** `4×` Cut-out Individual Player Six-Phase Round Reference Cards (`4.94" × 3.78"` — sized to pair or back-to-back with the Dice Reference Cards).<br>**Pages 4–5:** All `12×` Software Module Variant (`★`) Market Cards (`1.75" × 2.69"`, sized to fit the 4 Market Board slots) + `4×` Color Summary/Divider Cards (Purple variant cards retired; Purple Face 6 triggers bespoke Archetype Signature Protocols; Variant card text follows RULES_APPENDIX.md `v0.38.0`). |
| **`04_SETEC_Version_Cards_and_Tokens.pdf`** | **2** | **Page 1:** All `6×` SETEC Version Roadmap Tiles (`2.94" × 1.56"`, sized to nest inside the `v1.0 / v2.0 / v3.0` slots on the Agent Board).<br>**Page 2:** Optional cut-out prototype markers & chits (`First Player Marker`, `Active Version`, `4× Market Share Markers`, `Corporate Secrets`, `16× Glitched Shield Slot` markers, `Research Tokens (🔬)`, `$1/$5 Money`, and `Used/Forfeited` slot markers). |

## Printing & Physical Components Guide

1. **Print Settings:** Print at **100% / Actual Size** (do *not* select "Fit to Printable Area" so card/slot dimensions stay exact) on **US Letter (`8.5" × 11"`)** paper or light cardstock (`65–110 lb` recommended for cards/tiles).
2. **Color & B&W Accessibility:** Every game color is paired with a unique geometric symbol (`◆ Red`, `● Blue`, `▲ Green`, `⬡ Yellow`, `▼ Purple`, `■ Black`, `□ Gray`), allowing full playability whether printed in color or monochrome laser grayscale.
3. **Physical Dice Needed (Standard `1–6` Pipped `d6`s):**
   - `20` Gray Legacy dice (`2` per player at setup; more from Level 1 Breakthroughs)
   - `8` each of Red, Blue, Green, Yellow (`2 × Players` in Central Market; each player also takes `1` starting colored die of their Client Company color from that stack)
   - `8` Purple Specialist dice (`1` starter + `1` in Personal Reserve per player)
4. **Physical Cubes Needed (`8mm–10mm` wooden cubes + Cube Tower & Cup):**
   - Attack Cubes (`Red`, `Blue`, `Green` — ~`10` per color) + Corruption Cubes (`Black` — ~`12`)
5. **Market Share Markers:** `1` per player (cut-out chit from `04`, or any small marker that fits a Central Market Share Track cell).

## Regenerating Assets

Pure Python 3 standard library (zero external dependencies), run via WSL:

```bash
python3 -m pnp.generate_pnp
```
