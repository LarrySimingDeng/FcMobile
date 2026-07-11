<div align="center">

# ⚽ FcMobile

**Turn pre-cut FC Mobile clips into a vertical (9:16) + 4K-landscape (19.5:9) player-review video — intro, captions, transitions, Apple-style outro, cover, and BGM, all from one command.**

**English** · [简体中文](README.zh-CN.md)

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Needs ffmpeg](https://img.shields.io/badge/needs-ffmpeg-007808?logo=ffmpeg&logoColor=white)
![Built with Pillow](https://img.shields.io/badge/built%20with-Pillow-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20·%20Linux%2FWin%20(swap%20encoder)-lightgrey)

</div>

---

> **Core model: one player = one folder.** The shared engine lives in `utils/` and never changes. Each episode only touches its own `<player>/` folder and a single `<player>/edl.json`. Python + Pillow drive the layout and titling; ffmpeg does the encoding.

## What it produces

Every render — vertical and landscape — has the same fixed structure:

```
Intro (lineup panorama → smooth zoom onto the featured player's card)
   → optional stat-card hold
      → gameplay segments (in-frame captions, played in `order`)
         → Apple-style outro
```

- Original clip audio is muted; a single BGM track plays underneath and fades out just before the outro.
- **Vertical** — 1080×1920, captions inside a gold rounded frame on solid black bars (RED / Douyin).
- **Landscape** — 4K 3840×1772 @ 30 Mbps (Bilibili — see [Why 4K](#why-4k-landscape)).
- Every seam is a cross-fade (dissolve), never a hard cut.

## Results

Videos and covers produced by this exact pipeline:

<div align="center">

| Platform | Format | Link |
| :--- | :--- | :--- |
| Xiaohongshu (RED) | vertical 9:16 | [Profile ↗](https://www.xiaohongshu.com/user/profile/67a8522e000000000e01e9e0) |
| Douyin | vertical 9:16 | [Sample video ↗](https://www.douyin.com/video/7660929349566874752) |
| Bilibili | 4K landscape | [Channel ↗](https://space.bilibili.com/182570647) |

</div>

**Cover style** — `cover.py`, 1280×720, image-only (no text):

```
┌───────────────────────────────────────────┐
│  ░░ atmospheric gradient + gold vignette ░░ │
│   ┌───────┐                                 │
│   │ CARD  │◄ tilted −5°, gold outer glow    │
│   │ (cut- │                 ██████████      │
│   │  out) │            real photo (right,   │
│   └───────┘            left edge feathered  │
│                        into the background) │
└───────────────────────────────────────────┘
```

> Sample covers/videos are **not committed** to this repo — they contain copyrighted player cards and athlete photos (see [Bring your own materials](#bring-your-own-materials)). Link to your own hosted posts above instead.

## Requirements

- **Python 3** — developed on Python 3.14; anything 3.9+ works.
- **[Pillow](https://python-pillow.org/)** — `pip install -r requirements.txt`
- **ffmpeg + ffprobe** on your `PATH` — the one system dependency, not installed by pip:
  - macOS — `brew install ffmpeg`
  - Debian/Ubuntu — `sudo apt install ffmpeg`

> `hl_ocr.py` (automatic goal detection) needs **no OCR engine** — it detects goals by image change, not by reading text, so there is nothing extra to install.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **`make_video.py` runs the render scripts through `.venv/bin/python`** (a virtualenv at the repo root). Create the venv exactly as shown above, or edit the `PY=` line at the top of `utils/make_video.py` to point at your interpreter. The other scripts run under any `python`.

### Platform note

The render scripts encode with Apple's hardware encoder **`h264_videotoolbox`**, which is **macOS-only**. To run on Linux/Windows, swap it for the cross-platform software encoder in `utils/render_vertical.py`, `utils/render_landscape.py`, `utils/intro.py`, and `utils/hl_ocr.py`:

```diff
- "-c:v", "h264_videotoolbox", "-b:v", "12M",
+ "-c:v", "libx264", "-crf", "18", "-preset", "slow",
```

(`libx264` uses CRF rather than a target bitrate; tune `-crf`/`-preset` to taste.)

## Repository layout

```
FcMobile/
├── utils/                     # Shared engine — used by every player, never edited
│   ├── make_video.py          #   one-shot build (vertical + landscape)
│   ├── intro.py               #   vertical intro (lineup → zoom to card)
│   ├── render_vertical.py     #   vertical engine (gold frame + captions + outro)
│   ├── render_landscape.py    #   landscape 4K engine (full frame + captions + outro)
│   ├── cover.py               #   cinematic cover (card + real photo)
│   ├── contact_sheet.py       #   thumbnail grid to identify segment numbers
│   ├── hl_ocr.py              #   automatic goal detection (no OCR dependency)
│   └── hl_scan.py             #   semi-automatic frame-timeline for manual review
├── Mbappe/                    # One episode = one folder (worked example)
│   ├── clips/                 #   pre-cut gameplay clips (.MOV/.mov)
│   ├── assets/                #   cards/ · real-life poster · (per-player art)
│   ├── edl.json               #   this episode's config
│   └── output/                #   vertical_final.mp4 · landscape_final.mp4 · cover.jpg
├── K77/                       # A second example (Kvaratskhelia)
├── assets/                    # Shared assets episodes reference via ../assets/ (landing.PNG, bgm/)
├── requirements.txt
├── LICENSE
└── README.md
```

Media directories keep an empty `.gitkeep` so a fresh clone has the layout; the media itself is git-ignored.

## Quickstart

Copy the worked example, drop in your own materials, edit one JSON, run two commands.

```bash
# 1. Build a thumbnail grid to see which clip is segment #1..#N
python utils/contact_sheet.py Mbappe

# 2. Edit Mbappe/edl.json  →  order / captions / landing_card_focus / poster / bgm

# 3. Render both masters (vertical + landscape 4K)
python utils/make_video.py Mbappe
#   → Mbappe/output/vertical_final.mp4    (1080×1920, RED / Douyin)
#   → Mbappe/output/landscape_final.mp4   (3840×1772 4K, Bilibili)

# 4. Generate the cover
python utils/cover.py Mbappe
#   → Mbappe/output/cover.jpg             (1280×720, image-only)
```

> `cover.py` always writes `output/cover.jpg`. You can also supply a cover by hand under `output/` (any name, e.g. `cover.png`) and skip this step — that's what the `K77` example does.

All scripts default to `Mbappe` when no folder is given. To iterate, change a field in `edl.json` and re-run step 3 or 4 — **you only ever edit one JSON.** Intermediate files go to `/tmp/fcm_build`, never into the project.

### Adding a new player

```bash
mkdir -p Ronaldo/{clips,assets/cards,output}
# clips → Ronaldo/clips/  ·  lineup → Ronaldo/assets/landing.PNG
# card cut-out → Ronaldo/assets/cards/ronaldo_card.png  ·  photo → Ronaldo/assets/ronaldo_poster.jpg
cp Mbappe/edl.json Ronaldo/edl.json      # then edit it (see reference below)
python utils/make_video.py Ronaldo       # utils/ is reused verbatim — no code changes
```

## `edl.json` reference

Copy `Mbappe/edl.json` and change these fields:

| Field | Meaning |
| :--- | :--- |
| `project` | Episode title (used on the outro / for your own reference). |
| `landing_image` | Path to the lineup screenshot the intro zooms into. |
| `order` | Array of segment numbers = the concatenation order (also defines the segmentation). |
| `captions` | `{ "segment#": "caption text" }`. Omit a segment for no caption; `{}` for none at all. |
| `landing_card_focus` | `{cx, cy, w_vertical, w_horizontal}` — the pixel center of the player's card **in the lineup image**. The intro zooms from the full panorama onto this point. **Set this per player** or the zoom lands on the wrong card. Start from Mbappé's `w_vertical`/`w_horizontal` (300 / 680) and nudge. |
| `poster` | `{card, person, card_scale, person_width}` — inputs and sizes for `cover.py`. |
| `stat_card` / `stat_card_dur` | *Optional.* An image (e.g. a stats card) held for `stat_card_dur` seconds right after the intro — blurred background + centered image, joined into the same cross-fade chain. Omit both for none. The `K77` example uses this. |
| `trim_head` / `trim_tail` | Seconds trimmed off the start/end of every clip. |
| `transition` | Cross-fade duration between segments (seconds). |
| `outro_title` / `outro_subtitle` | Text shown on the Apple-style outro card. |
| `bgm` | Path to the music track (`null` = silent). |
| `bgm_gain_db` / `bgm_tail_gap_s` / `bgm_fade_dur_s` | BGM volume, gap before the end, and fade length. |

> **On-screen text stays in the source language.** In the example configs, `captions`, `project`, `outro_title`, and `outro_subtitle` are **Chinese** — that is the text actually burned into the video for Chinese platforms. Replace it with whatever language your audience speaks; it is data, not code.
>
> Example (`Mbappe/edl.json`): `"1": "弧顶直接触发银搓，十射九中"` → *"Triggers the finesse shot from the top of the arc — nine of ten go in."* The pipeline renders CJK via the bundled macOS fonts (`Hiragino Sans GB`, `PingFang`), so keep those font paths if you caption in Chinese.

> **Asset paths are relative to the player folder.** Shared materials live at the repo-root `assets/` and are referenced as `../assets/...` — both examples pull `landing.PNG` and their BGM from there, while per-player art (`poster`, `stat_card`) stays inside the player folder.

### Why 4K landscape?

Bilibili only routes videos whose short side is ≥ 1600 through its high-bitrate 4K transcode tier; anything smaller gets the lowest bitrate and looks mushy. The landscape engine therefore locks to 3840×1772 @ 30 Mbps. This is a deliberate default in `render_landscape.py` — no need to touch it per player.

## Automatic highlights (optional)

If you have a **full-match screen recording** instead of pre-cut clips, let the pipeline find your goals:

```bash
python utils/hl_ocr.py <full_match.mp4> <player>
#   → <player>/highlights/goalN.mp4   (build-up → goal → stops at the card popup, EA cutscene excluded)
#   → <player>/highlights/goals.json  ({goal_time, score, clip_in, clip_out, scorer})
```

It reads the top-left scoreboard, keeps only **your** goals (left score +1), and cuts each clip from the build-up to the moment the scorer's card pops up. Copy the ones you want into `<player>/clips/` and continue from the Quickstart. `hl_scan.py` produces a manual frame-timeline if you want to verify by eye.

## Bring your own materials

This repository ships **code, docs, and two example `edl.json` configs only.** It contains **no** gameplay footage, player cards, athlete photos, or music, and you should not commit any of your own — the `.gitignore` already excludes every common media type.

The materials used in the examples (EA SPORTS FC Mobile player cards, club/player imagery, real-life photographs, music tracks) are copyrighted by their respective owners. To make your own episode, supply your own materials and point `edl.json` at them.

## License

[MIT](LICENSE) © 2026 Siming Deng. The license covers the source and docs only — not any media you add. See the note at the bottom of `LICENSE`.

## Appendix — one-shot handoff prompt

<details>
<summary>A ready-to-paste brief for reproducing an episode end-to-end (click to expand)</summary>

Originally written for driving the pipeline from an AI coding assistant such as Claude Code. Replace `<player>` with your episode's code name.

```text
I want to make a new FC Mobile player-review video, player code name <player>,
exactly like the Mbappe episode, reusing the shared pipeline.

# Ground rules (read first)
- Repo root: <repo-root>
- One player = one folder. The shared scripts in utils/ are generic — never edit them.
  Only touch the <player>/ folder and its edl.json.
- Read: README.md and Mbappe/edl.json (the worked example to copy).

# Fixed output structure (same for vertical & landscape)
Intro (lineup panorama → smooth zoom onto the featured player's card)
  → gameplay segments (captions, in `order`) → Apple-style outro; audio muted + BGM.
The "zoom onto your card" effect comes from assets/landing.PNG plus edl.json's
landing_card_focus (the card's center pixel in the lineup image). Set it per player.

# Materials I will provide (paths given at runtime)
1. Gameplay clips (.MOV/.mov, already cut)
2. One lineup screenshot (for the intro zoom)
3. One player-card CUT-OUT (transparent PNG; cut the background out if it isn't)
4. One real-life photo (jpg/png, for the cover)
5. One BGM track (optional)
6. Caption text per segment (optional)
(If I hand you a FULL-MATCH recording instead of clips, first run
   python utils/hl_ocr.py <full_match.mp4> <player>
 to auto-extract my goals into <player>/highlights/, then copy the ones to use into clips/.)

# Do this, in order
1. Create <player>/{clips,assets/cards,output}.
2. Place materials:
   clips → <player>/clips/ · lineup → <player>/assets/landing.PNG
   card cut-out → <player>/assets/cards/<player>_card.png
   photo → <player>/assets/<player>_poster.jpg · BGM → <player>/assets/bgm/ (or shared assets/bgm/)
3. python utils/contact_sheet.py <player>   # identify segment #1..#N
4. Write <player>/edl.json (copy Mbappe/edl.json), setting:
   project · landing_image · order · captions · landing_card_focus · poster;
   reuse Mbappe's trim_head/trim_tail/transition/bgm*/outro_* values.
5. python utils/make_video.py <player>       # vertical + landscape 4K
6. python utils/cover.py <player>            # cover (skip if you made one by hand)
7. Open the results for review. To adjust captions/order/cover, edit edl.json and re-run 5/6.

# Acceptance
<player>/output/ has vertical_final.mp4, landscape_final.mp4 (4K), and cover.jpg.
One make_video.py produces both videos; one cover.py produces the cover. Done.
```

</details>
