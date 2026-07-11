# Workflow & Directory Model

**English** · [简体中文](WORKFLOW.zh-CN.md)

> One player = one folder, driven by the shared `utils/`. Intermediate files go to `/tmp/fcm_build` and never land in the project. For install/requirements and the full field reference, see [README.md](README.md).

## Directory model

```
FcMobile/
├── utils/                      # Shared engine (all players; never edited)
│   ├── make_video.py           # one-shot build (vertical + landscape)
│   ├── intro.py                # vertical intro (lineup → zoom to card)
│   ├── render_vertical.py      # vertical engine (gold frame + black bars + captions + Apple outro)
│   ├── render_landscape.py     # landscape 4K engine (full frame + captions + Apple outro)
│   ├── cover.py                # cover (card + real-life photo)
│   ├── contact_sheet.py        # thumbnail grid (identify segment numbers)
│   ├── hl_ocr.py               # goal detection (fully automatic; no OCR dependency)
│   └── hl_scan.py              # goal scan (semi-automatic: frame timeline)
├── Mbappe/                     # ← one episode = one folder
│   ├── clips/                  # pre-cut gameplay clips (.MOV/.mov)
│   ├── assets/                 # landing.PNG · cards/ · bgm/ · real-life poster
│   ├── highlights/             # goal clips pulled from a full match (created by hl_ocr.py)
│   ├── edl.json                # this episode's config (order / captions / BGM / cover params)
│   └── output/                 # vertical_final.mp4 · landscape_final.mp4 · cover.jpg
├── assets/                     # shared assets episodes reference via ../assets/ (landing.PNG, bgm/)
├── K77/  Ronaldo/  ...          # future players, same structure
└── README.md · WORKFLOW.md
```

## Daily flow: raw material → finished video

**① Pick highlights** (optional — fully automatic, from a full-match recording)
```bash
uv run utils/hl_ocr.py <full_match.mp4> <player>   # keeps only YOUR goals (left score +1),
                                                   # cuts "goal → card popup", EA cutscene excluded → <player>/highlights/
```
Outputs `goalN.mp4` + `goals.json`. Copy the clips you want into `<player>/clips/`.
(Manual cross-check: `uv run utils/hl_scan.py <video>` renders a frame timeline to inspect by eye.)

**② Identify segments + configure**
```bash
uv run utils/contact_sheet.py <player>        # thumbnail grid → learn which clip is segment #1..#N
```
Then edit `<player>/edl.json`:
- `order` = output order (segment numbers) ← **this is "concatenate + segment"**
- `captions` = per-segment captions (segment# → text) ← **this is "caption each segment"**
- `bgm` = audio path (`null` = silent)

See the [README `edl.json` reference](README.md#edljson-reference) for every field — including `stat_card`/`stat_card_dur` (an optional stat-card hold dissolved in right after the intro) and the shared-assets convention (paths resolve relative to the player folder; shared `landing.PNG`/BGM live at the repo-root `assets/`, referenced as `../assets/...`).

**③ Render**
```bash
uv run utils/make_video.py <player>           # → output/ vertical + landscape (intro/captions/transitions/outro/BGM, all automatic)
```

**④ Cover**
```bash
uv run utils/cover.py <player>                # cut-out card + real-life photo → output/cover.jpg
```

## How "concatenate → segment → caption" maps to files

Highlight clips go into `clips/` → `edl.order` defines the concatenation order (= automatic segmentation) → each segment gets one line in `edl.captions` (= per-segment caption) → edit `edl.json` and re-run `make_video`. **You only ever edit one JSON.**

## Switching players (e.g. Ronaldo)

```bash
mkdir -p Ronaldo/{clips,assets,highlights,output}
# clips → Ronaldo/clips/ ; landing.PNG, card cut-out, real-life poster → Ronaldo/assets/ ; write Ronaldo/edl.json
uv run utils/make_video.py Ronaldo            # utils/ is reused verbatim — not a single line of code changes
```

The one thing you must set per player: `landing_card_focus` in `edl.json` — the new card's center position in the lineup image (so the intro zooms onto the right card).
