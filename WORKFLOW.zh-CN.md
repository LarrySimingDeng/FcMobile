# 工作流 & 目录模型

[English](WORKFLOW.md) · **简体中文**

> 一个球员 = 一个文件夹，靠公共 `utils/` 出片。中间产物走 `/tmp/fcm_build`，不落进项目。安装 / 依赖和完整字段说明见 [README.zh-CN.md](README.zh-CN.md)。

## 目录模型

```
FcMobile/
├── utils/                      # 公共引擎（所有球员共用；不改）
│   ├── make_video.py           # 一键出片（竖屏 + 横屏）
│   ├── intro.py                # 竖屏片头（阵容 → 缩放到球员卡）
│   ├── render_vertical.py      # 竖屏引擎（金边 + 黑边 + 字幕 + Apple 片尾）
│   ├── render_landscape.py     # 横屏 4K 引擎（完整画面 + 字幕 + Apple 片尾）
│   ├── cover.py                # 封面（卡 + 真人照）
│   ├── contact_sheet.py        # 素材总览图（认段号）
│   ├── hl_ocr.py               # 进球检测（全自动；无 OCR 依赖）
│   └── hl_scan.py              # 进球扫描（半自动：抽帧时间线）
├── Mbappe/                     # ← 一期 = 一个文件夹
│   ├── clips/                  # 剪好的游戏片段（.MOV/.mov）
│   ├── assets/                 # landing.PNG · cards/ · bgm/ · 真人海报
│   ├── highlights/             # 从整场比赛挑出的进球片段（hl_ocr.py 生成）
│   ├── edl.json                # 本期配置（order / captions / BGM / 封面参数）
│   └── output/                 # vertical_final.mp4 · landscape_final.mp4 · cover.jpg
├── assets/                     # 各期通过 ../assets/ 共享的素材（landing.PNG, bgm/）
├── K77/  Ronaldo/  ...          # 未来的球员，同样结构
└── README.md · WORKFLOW.md
```

## 完整流程：素材 → 成片

**① 挑精华**（可选 —— 全自动，从一整场比赛录像里挑）
```bash
uv run utils/hl_ocr.py <整场比赛.mp4> <player>   # 只保留你的进球（左边比分 +1），
                                                 # 裁「进球 → 卡弹出」，不含 EA 过场 → <player>/highlights/
```
输出 `goalN.mp4` + `goals.json`。把想用的片段拷进 `<player>/clips/`。
（人工核对：`uv run utils/hl_scan.py <视频>` 生成抽帧时间线，肉眼看。）

**② 认段号 + 配置**
```bash
uv run utils/contact_sheet.py <player>        # 素材总览图 → 认清哪条片段是第 #1..#N 段
```
然后编辑 `<player>/edl.json`：
- `order` = 成片顺序（段号）← **这就是「拼接 + 分段」**
- `captions` = 各段字幕（段号 → 文案）← **这就是「给每段配字幕」**
- `bgm` = 音频路径（`null` = 无声）

完整字段见 [README 的 edl.json 字段说明](README.zh-CN.md#edljson-字段说明) —— 包括 `stat_card`/`stat_card_dur`（片头后可选定格的数据卡，交叉溶解接入）以及共享素材约定（路径相对球员文件夹；共享的 `landing.PNG`/BGM 放仓库根 `assets/`，用 `../assets/...` 引用）。

**③ 出片**
```bash
uv run utils/make_video.py <player>           # → output/ 竖屏 + 横屏（片头/字幕/转场/片尾/BGM 全自动）
```

**④ 封面**
```bash
uv run utils/cover.py <player>                # 抠图卡 + 真人照 → output/cover.jpg
```

## 「拼接 → 分段 → 配字幕」怎么落到文件上

精彩片段进 `clips/` → `edl.order` 定义拼接顺序（= 自动分段）→ 每段在 `edl.captions` 里配一行字幕（= 分段配字幕）→ 改 `edl.json` 重跑 `make_video`。**你永远只改一个 JSON。**

## 换球员（例如 Ronaldo）

```bash
mkdir -p Ronaldo/{clips,assets,highlights,output}
# 片段 → Ronaldo/clips/ ；landing.PNG、卡抠图、真人海报 → Ronaldo/assets/ ；写 Ronaldo/edl.json
uv run utils/make_video.py Ronaldo            # utils/ 原样复用 —— 一行代码都不改
```

换球员唯一必须调的：`edl.json` 里的 `landing_card_focus` —— 新卡在阵容图里的中心位置（好让片头缩放聚焦到对的卡）。
```
