# Too Many Secrets — Tabletop Simulator Module (`v0.52.0`)

A Tabletop Simulator save built from the Print-and-Play components in [`pnp/`](../pnp/README.md). The PnP draw functions render every board, card and token to PNG, so the module stays in step with the PDFs.

## Build

```bash
python3 -m tts.build_tts
```

- Renders 29 images into `tts/assets/` (needs `pdftoppm`, from poppler-utils).
- Writes `tts/TooManySecrets.json`, whose images point at GitHub raw URLs on `main`. Use this one for multiplayer once the assets are pushed. Each URL carries a `?v=<hash>` so TTS reloads changed images.
- Add `--install-dir "<TTS Saves folder>"` to copy the images there and write `TooManySecrets_local.json` (it uses `file:///` paths, so it works before pushing, but only on that machine).
- Add `--skip-render` to reuse the existing images.
- `--check` re-renders into a temp folder and exits 1 if `tts/` is stale against `pnp/` (it writes nothing).

## Keeping it in sync

The module is a sync target like `pnp/` and `web/`. After any change to `pnp/generate_pnp.py` (or to the rules it draws), rerun the builder and commit `tts/`. On a version bump, update `VERSION` in `tts/build_tts.py`, the header of `tts/global.lua` and this README's title. The tower odds in `tts/global.lua` mirror the current `sim/config.py` preset, so update them when the tower `[TUNE]` values change.

Edit `tts/global.lua` / `tts/global.xml` for the script and UI, not the generated save.

## What's on the table

| Area | Contents |
| :--- | :--- |
| Centre | SETEC Central Agent & Market Share Board, Software Module Market & Central Supply Board (locked) |
| Left | SETEC Version tile stacks (`v1.0` / `v2.0` / `v3.0`), Client Company and White Hat Dossier decks, Corporate Secret / Research / `$1` / `$5` token bags, First Player Marker, Active Version Marker, Master Dice Reference |
| Right | Red / Blue / Green / Yellow market dice (`8` each), Variant (`★`) card decks per colour and the summary cards, Attack Cube and Corruption Cube supplies, **Staging Cup** bag, **Cube Tower** |
| Each seat (White, Pink, Teal, Orange) | Company Terminal Mat, a 2-sided Player Reference card (dice front, round back), `8` player cubes (named per track or marker), `5` Gray + `2` Purple dice |

Dice are TTS **Custom Dice** with their yields printed on each face, drawn from `DICE_SPECS` in `pnp/generate_pnp.py` (one texture per colour, `tts/assets/die_<colour>.png`). Each face keeps its pip number in the corner, so it still matches the reference cards and the PnP's plain d6s; ⚠ faces carry a LOCKED band (a **Locked Die** during rerolls). The textures follow TTS's own `Modding/Dice Templates/D6.png` layout (`DIE_FACE_CELLS` in `build_tts.py`). The Global script renames each die's six rotation values to the face yields, so roll messages and tooltips read, for example, `5: R&D face [Locked Die]`.

## Scripting

- **Sizing:** objects carry `fit:<w>x<d>` in GM Notes, and the Global script scales them to that size on load. One PnP point equals `16/792` table units, so cards fit the printed board slots.
- **Cube Tower panel** (top right, draggable):
  - **Drop Staging Cup:** compiles the bag's contents with the Shogun Baffle model from `sim/tower.py`, using the `GameConfig.v046()` odds. Exited cubes appear beside the tower in the Exit Tray area. Stuck cubes stay hidden in the script state, which is saved with the game.
  - **Prime the Compiler:** the setup drop. Cubes that exit go back to the supply.
  - **Empty tower:** reset or game end.
- **Quick Setup panel** (below the Cube Tower panel): **2P / 3P / 4P** runs RULES.md Section 3 for that many seats. It uses the seated colours if exactly that many players sit at a mat, else the first mats in order (White, Pink, Teal, Orange). It:
  - deals 1 `v1.0` / `v2.0` / `v3.0` tile into the Agent Board slots, puts the Active Version Marker on `v1.0`, primes the compiler and puts the `v1.0` tile's starting cubes in the Staging Cup;
  - deals 1 Variant card per Market slot with `2 × players` dice beside it;
  - deals each player a Client Company and a White Hat Dossier (face up, beside the mat) and moves that company's starting colored die from its Market stack into Ready for Release;
  - sets each mat: 2 Gray + colored + Purple in Ready for Release, 3 Gray in the Current Sprint, the 2nd Purple die on the Personal Reserve outline, the four track cubes on Level 0, the Operative Signature Cube on its cradle, `$6` and `6` Corporate Secrets (`7` with *Data Scraper*);
  - puts each Vulnerability marker on `0` and each Market Share Marker on `14` (2P) or `18` (3–4P), plus the SETEC Corp Black Cube on `0` in 2-player games;
  - gives the First Player Marker to a random player and posts the deal in chat.

  It runs once per game. The spots come from the PnP board layout (`board_point` and the `MAT_*` / `AGENT_*` / `MARKET_*` constants in `build_tts.py`), so move them if `pnp/generate_pnp.py` moves a zone.
- Everything else is resolved by hand, as in the paper game: Black cubes onto the Corruption Track, Signature Cubes back to their mats, and recycling Red, Blue and Green cubes into the Staging Cup. The save's Notes tab has the setup checklist.
