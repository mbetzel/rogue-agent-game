# Too Many Secrets — Tabletop Simulator Module (`v0.51.0`)

A Tabletop Simulator save built from the Print-and-Play components in [`pnp/`](../pnp/README.md). The PnP draw functions render every board, card and token to PNG, so the module stays in step with the PDFs.

## Build

```bash
python3 -m tts.build_tts
```

- Renders 23 images into `tts/assets/` (needs `pdftoppm`, from poppler-utils).
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

Dice are standard tinted d6s, matching the PnP (the reference cards map pips to abilities).

## Scripting

- **Sizing:** objects carry `fit:<w>x<d>` in GM Notes, and the Global script scales them to that size on load. One PnP point equals `16/792` table units, so cards fit the printed board slots.
- **Cube Tower panel** (top right, draggable):
  - **Drop Staging Cup:** compiles the bag's contents with the Shogun Baffle model from `sim/tower.py`, using the `GameConfig.v046()` odds. Exited cubes appear beside the tower in the Exit Tray area. Stuck cubes stay hidden in the script state, which is saved with the game.
  - **Prime the Compiler:** the setup drop. Cubes that exit go back to the supply.
  - **Empty tower:** reset or game end.
- Everything else is resolved by hand, as in the paper game: Black cubes onto the Corruption Track, Signature Cubes back to their mats, and recycling Red, Blue and Green cubes into the Staging Cup. The save's Notes tab has the setup checklist.
