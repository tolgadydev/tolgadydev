# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

The GitHub profile README repo for `tolgadydev`. `README.md` shows an animated banner (`dark.svg` / `light.svg`, loaded from `raw.githubusercontent.com/.../main/`), plus third-party stats cards, social badges and a contribution snake. The rest of the repo is an offline pipeline that generates the banner SVGs. Code comments and docstrings are in Turkish, mostly written without diacritics.

There is no build system, test suite or linter. `npm test` is a placeholder. Each script is run by hand from the repo root, and all paths are relative to the root. Python scripts run inside `.venv` (`.\.venv\Scripts\Activate.ps1`).

## Banner generation pipeline

Run the stages in this order. Each stage reads the previous stage's outputs from the repo root:

```
python remove_bg.py        # tolga_photo.jpeg -> subject_transparent.png, subject_on_dark.png, mask.png (rembg, u2net_human_seg)
python crop_top.py         # crops half the empty space above the subject, editing both PNGs in place
python portrait_dither.py  # -> dark_dots.npy, light_dots.npy, mask_clean.npy, gray_*.npy (+ preview_*.png)
python build_banner.py     # -> dark.svg, light.svg, banner_metrics.json
node screenshot_banner.js  # Playwright: shot_<theme>_<label>.png frames for checking the banner visually
```

- **The `.npy` files are committed and are the source of truth.** To change only text, layout or colors, edit `build_banner.py` and rerun that one script. The earlier stages are needed only when the photo changes.
- `.gitignore` excludes the intermediate outputs (`mask.png`, `subject_*.png`, `preview_*.png`, `shot_*.png`, `banner_metrics.json`) because they can be regenerated.
- Python deps (no requirements file): `numpy`, `scipy`, `Pillow`, `scikit-image`, `rembg`. Node deps: `npm install` (playwright). `screenshot_banner.js` may also need `npx playwright install chromium`.

### Coupled values that must stay in sync

- **Grid size:** `GRID_W, GRID_H = 300, 340` is defined separately in `portrait_dither.py` and `build_banner.py`.
- **Crop amount:** `CROP_TOP = 36` in `portrait_dither.py` is hardcoded to match what `crop_top.py` removes from `tolga_photo.jpeg`. Update it whenever the photo changes. `crop_top.py` crops the PNGs in place, so rerun `remove_bg.py` before running it again.
- **Colors:**
  - Dark and light hex values in `build_banner.py`'s `PALETTE` are reused in the README's stats-card URLs and in the snake colors in `.github/workflows/snake.yml`. Keep them consistent.
  - The dark background `#0A101F` is also hardcoded in `remove_bg.py` and `portrait_dither.py`.

### How the banner works (`build_banner.py`)

The output is a single SVG that uses SMIL animation, with no JS:

1. On load, the dithered portrait fades in over `INTRO_FADE` seconds in `N_INTRO_GROUPS` random groups, then stays static.
2. The right-hand info panel comes from the `ROWS` list of `(label, value)` 2-tuples. Profile text changes go there. The `@tolgadydev` pill and the SVG `<title>` are hardcoded in `build_info_panel` and `build_svg`.

`banner_metrics.json` holds the dot count, intro group evenness and SVG size for each theme. Use it to compare before and after a change.

## CI

`.github/workflows/snake.yml` runs Platane/snk every 12 hours, on push to `main`, and on manual dispatch. It force-publishes `snake-dark.svg` and `snake-light.svg` to the `output` branch, which the README loads. Don't commit to `output` by hand.
