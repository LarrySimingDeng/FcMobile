<div align="center">

# ⚽ FcMobile

**一条命令，把剪好的 FC Mobile 片段拼成竖屏 (9:16) + 横屏 4K (19.5:9) 球员测评视频 —— 片头、字幕、转场、Apple 风格片尾、封面、BGM 全自动。**

[English](README.md) · **简体中文**

![License](https://img.shields.io/badge/License-MIT-green.svg)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Needs ffmpeg](https://img.shields.io/badge/needs-ffmpeg-007808?logo=ffmpeg&logoColor=white)
![Built with Pillow](https://img.shields.io/badge/built%20with-Pillow-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20·%20Linux%2FWin%20(换编码器)-lightgrey)

</div>

---

> **核心模型：一个球员 = 一个文件夹。** 公共引擎在 `utils/`，永远不改；每一期只动自己的 `<player>/` 文件夹和一个 `<player>/edl.json`。布局和标题由 Python + Pillow 负责，编码由 ffmpeg 负责。

## 成片包含什么

每条成片 —— 竖屏和横屏 —— 都是同一套固定结构：

```
片头（阵容全景 → 平滑缩放聚焦到本期球员卡）
   → 可选的数据卡定格
      → 各段游戏镜头（按 order 顺序，带嵌入式字幕）
         → Apple 风格片尾
```

- 原声全部静音；底下铺一条 BGM，在片尾前淡出。
- **竖屏** —— 1080×1920，字幕放在金色圆角框里、上下纯黑边（小红书 / 抖音）。
- **横屏** —— 4K 3840×1772 @ 30 Mbps（B 站 —— 见 [为什么要 4K](#为什么横屏要-4k)）。
- 每个接缝都是交叉溶解（淡入淡出），绝不硬切。

## 效果展示

用这套管线做出来的视频和封面：

<div align="center">

| 平台 | 格式 | 链接 |
| :--- | :--- | :--- |
| 小红书 | 竖屏 9:16 | [主页 ↗](https://www.xiaohongshu.com/user/profile/67a8522e000000000e01e9e0) |
| 抖音 | 竖屏 9:16 | [示例视频 ↗](https://www.douyin.com/video/7660929349566874752) |
| B 站 | 横屏 4K | [主页 ↗](https://space.bilibili.com/182570647) |

</div>

**封面风格** —— `cover.py`，1280×720，纯图无文字：

```
┌───────────────────────────────────────────┐
│  ░░ 氛围渐变背景 + 金色暗角 ░░               │
│   ┌───────┐                                 │
│   │ 球员卡 │◄ 倾斜 −5°，金色外发光            │
│   │ (抠图) │                 ██████████      │
│   │       │            真人照（右侧，        │
│   └───────┘            左缘羽化融入背景）      │
│                                             │
└───────────────────────────────────────────┘
```

> 示例封面 / 视频**不会**提交到仓库 —— 里面有版权的球员卡和真人照（见 [素材请自备](#素材请自备)）。请在上面的表格里贴你自己发布的外链。

## 环境依赖

- **Python 3** —— 在 Python 3.14 上开发；3.9+ 都能跑。
- **[Pillow](https://python-pillow.org/)** —— `pip install -r requirements.txt`
- **ffmpeg + ffprobe** 在 `PATH` 里 —— 唯一的系统依赖，pip 装不了：
  - macOS —— `brew install ffmpeg`
  - Debian/Ubuntu —— `sudo apt install ffmpeg`

> `hl_ocr.py`（自动进球检测）**不需要任何 OCR 引擎** —— 它靠图像变化而非识别文字来判进球，所以没有额外东西要装。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> **`make_video.py` 通过 `.venv/bin/python` 调用各渲染脚本**（仓库根目录下的虚拟环境）。请照上面的方式建好 venv，或者改 `utils/make_video.py` 顶部的 `PY=` 那行指向你的解释器。其余脚本用任何 `python` 都能跑。

### 平台说明

渲染脚本用的是 Apple 硬件编码器 **`h264_videotoolbox`**，**只在 macOS 上有**。想在 Linux/Windows 上跑，就在 `utils/render_vertical.py`、`utils/render_landscape.py`、`utils/intro.py`、`utils/hl_ocr.py` 里把它换成跨平台的软件编码器：

```diff
- "-c:v", "h264_videotoolbox", "-b:v", "12M",
+ "-c:v", "libx264", "-crf", "18", "-preset", "slow",
```

（`libx264` 用 CRF 而不是目标码率；`-crf`/`-preset` 自己按需调。）

## 目录结构

```
FcMobile/
├── utils/                     # 公共引擎 —— 所有球员共用，永远不改
│   ├── make_video.py          #   一键出片（竖屏 + 横屏）
│   ├── intro.py               #   竖屏片头（阵容 → 缩放到球员卡）
│   ├── render_vertical.py     #   竖屏引擎（金边 + 字幕 + 片尾）
│   ├── render_landscape.py    #   横屏 4K 引擎（完整画面 + 字幕 + 片尾）
│   ├── cover.py               #   电影感封面（卡 + 真人照）
│   ├── contact_sheet.py       #   素材总览图（认段号）
│   ├── hl_ocr.py              #   自动进球检测（无 OCR 依赖）
│   └── hl_scan.py             #   半自动抽帧时间线（人工核对）
├── Mbappe/                    # 一期 = 一个文件夹（现成范例）
│   ├── clips/                 #   剪好的游戏片段（.MOV/.mov）
│   ├── assets/                #   cards/ · 真人海报 · （本期专属素材）
│   ├── edl.json               #   本期配置
│   └── output/                #   vertical_final.mp4 · landscape_final.mp4 · cover.jpg
├── K77/                       # 第二个范例（Kvaratskhelia）
├── assets/                    # 各期通过 ../assets/ 共享的素材（landing.PNG, bgm/）
├── requirements.txt
├── LICENSE
└── README.md
```

素材目录里放了空的 `.gitkeep`，克隆下来就有骨架；素材本体全部被 git 忽略。

## 快速上手

复制现成范例 → 换上你自己的素材 → 改一个 JSON → 跑两条命令。

```bash
# 1. 生成素材总览图，看清哪条片段是第 #1..#N 段
python utils/contact_sheet.py Mbappe

# 2. 编辑 Mbappe/edl.json  →  order / captions / landing_card_focus / poster / bgm

# 3. 出两条成片（竖屏 + 横屏 4K）
python utils/make_video.py Mbappe
#   → Mbappe/output/vertical_final.mp4    (1080×1920, 小红书 / 抖音)
#   → Mbappe/output/landscape_final.mp4   (3840×1772 4K, B 站)

# 4. 出封面
python utils/cover.py Mbappe
#   → Mbappe/output/cover.jpg             (1280×720, 纯图)
```

> `cover.py` 永远写到 `output/cover.jpg`。你也可以手工做一张封面放进 `output/`（随便命名，比如 `cover.png`）然后跳过这步 —— `K77` 范例就是这么做的。

不带文件夹参数时，所有脚本默认跑 `Mbappe`。要迭代，就改 `edl.json` 里的某个字段再重跑第 3 / 4 步 —— **你永远只改一个 JSON。** 中间产物走 `/tmp/fcm_build`，不落进项目。

### 加一个新球员

```bash
mkdir -p Ronaldo/{clips,assets/cards,output}
# 片段 → Ronaldo/clips/  ·  阵容图 → Ronaldo/assets/landing.PNG
# 卡抠图 → Ronaldo/assets/cards/ronaldo_card.png  ·  真人照 → Ronaldo/assets/ronaldo_poster.jpg
cp Mbappe/edl.json Ronaldo/edl.json      # 然后照下面的说明改它
python utils/make_video.py Ronaldo       # utils/ 原样复用 —— 一行代码都不用改
```

## `edl.json` 字段说明

复制 `Mbappe/edl.json`，改这些字段：

| 字段 | 含义 |
| :--- | :--- |
| `project` | 片名（用在片尾 / 你自己参考）。 |
| `landing_image` | 片头要缩放进去的那张阵容截图路径。 |
| `order` | 段号数组 = 拼接顺序（同时定义了分段）。 |
| `captions` | `{ "段号": "字幕文案" }`。某段不配就省略；完全不要就写 `{}`。 |
| `landing_card_focus` | `{cx, cy, w_vertical, w_horizontal}` —— 本期球员卡**在阵容图里**的中心像素坐标。片头会从全景缩放聚焦到这个点。**每个球员都要设**，不然缩放会聚焦到别的卡。先沿用姆巴佩的 `w_vertical`/`w_horizontal`（300 / 680）再微调。 |
| `poster` | `{card, person, card_scale, person_width}` —— `cover.py` 的输入和尺寸。 |
| `stat_card` / `stat_card_dur` | *可选。* 片头之后定格 `stat_card_dur` 秒的一张图（比如数据卡）—— 模糊背景 + 居中图片，接进同一条交叉溶解链。两个都省略就没有。`K77` 范例用了这个。 |
| `trim_head` / `trim_tail` | 每段片段头 / 尾各裁掉的秒数。 |
| `transition` | 段间交叉溶解的时长（秒）。 |
| `outro_title` / `outro_subtitle` | Apple 风格片尾卡上的文字。 |
| `bgm` | 音乐路径（`null` = 无声）。 |
| `bgm_gain_db` / `bgm_tail_gap_s` / `bgm_fade_dur_s` | BGM 音量、离结尾的留白、淡出时长。 |

> **屏幕上显示的文字保持源语言。** 示例配置里的 `captions`、`project`、`outro_title`、`outro_subtitle` 是**中文** —— 那就是给中文平台实际烧进画面的文案。换成你受众的语言即可，它是数据不是代码。
>
> 例（`Mbappe/edl.json`）：`"1": "弧顶直接触发银搓，十射九中"` 就是第 1 段烧进画面的字幕。管线靠内置的 macOS 字体（`Hiragino Sans GB`、`PingFang`）渲染中日韩文字，所以配中文字幕就别删那两个字体路径。

> **素材路径相对于球员文件夹。** 共享素材放在仓库根目录的 `assets/`，用 `../assets/...` 引用 —— 两个范例的 `landing.PNG` 和 BGM 都来自这里；本期专属美术（`poster`、`stat_card`）则放在球员文件夹内。

### 为什么横屏要 4K？

B 站只把**短边 ≥ 1600** 的视频送进它的 4K 高码率转码档；低于这个就只给最低码率，糊。所以横屏引擎锁死 3840×1772 @ 30 Mbps。这是 `render_landscape.py` 里刻意设的默认值 —— 换球员不用动。

## 自动挑进球（可选）

如果你手上是**一整场比赛录屏**而不是剪好的片段，让管线自动帮你找进球：

```bash
python utils/hl_ocr.py <整场比赛.mp4> <player>
#   → <player>/highlights/goalN.mp4   (进球铺垫 → 进球 → 止于球员卡弹出，不含 EA 过场)
#   → <player>/highlights/goals.json  ({goal_time, score, clip_in, clip_out, scorer})
```

它读左上角比分板，只保留**你**的进球（左边比分 +1），把每段从铺垫裁到进球者卡弹出的那一刻。把想用的拷进 `<player>/clips/`，再接着走「快速上手」。想人工核对就用 `hl_scan.py` 生成抽帧时间线。

## 素材请自备

本仓库**只发布代码、文档和两个示例 `edl.json`**。里面**没有**任何游戏片段、球员卡、真人照或音乐，你也不该提交自己的 —— `.gitignore` 已经把常见媒体格式全挡掉了。

范例里用到的素材（EA SPORTS FC Mobile 球员卡、俱乐部 / 球员肖像、真人照片、音乐）版权归各自所有者。要做自己的一期，请自备素材，并让 `edl.json` 指向它们。

## 许可证

[MIT](LICENSE) © 2026 Siming Deng。许可证只覆盖源码和文档 —— 不覆盖你添加的任何素材。见 `LICENSE` 末尾的说明。

## 附录 —— 一键接力 Prompt

<details>
<summary>一段可直接粘贴、端到端复现一期的说明（点击展开）</summary>

最初是为了用 AI 编程助手（如 Claude Code）驱动管线而写的。把 `<player>` 换成本期代号。

```text
我要做一期新的 FC Mobile 球员测评视频，球员代号 <player>，做法和 Mbappe 那期完全一样，复用公共管线。

# 铁律（先读）
- 仓库根目录：<repo-root>
- 一个球员 = 一个文件夹。utils/ 里的公共脚本是通用的 —— 永远别改；只动 <player>/ 文件夹和它的 edl.json。
- 先读：README.md（或 README.zh-CN.md）和 Mbappe/edl.json（照抄的范例）。

# 固定成片结构（竖屏 & 横屏一致）
片头（阵容全景 → 平滑缩放聚焦到本期球员卡）
  → 各段游戏镜头（带字幕，按 order） → Apple 风格片尾；原声静音 + BGM。
「缩放到你的卡」这个效果靠 assets/landing.PNG + edl.json 的 landing_card_focus
（卡在阵容图里的中心像素）实现。每个球员都要设对。

# 我会提供的素材（路径届时给）
1. 游戏片段（.MOV/.mov，已剪好）
2. 一张阵容截图（片头缩放用）
3. 一张球员卡「抠图」（透明底 PNG；不是的话先抠背景）
4. 一张真人照（jpg/png，封面用）
5. 一首 BGM（可选）
6. 每段字幕文案（可选）
（如果给的是「一整场录像」而不是片段，先跑
   python utils/hl_ocr.py <整场比赛.mp4> <player>
 自动把我的进球挑到 <player>/highlights/，再把要用的拷进 clips/。）

# 按顺序做
1. 建 <player>/{clips,assets/cards,output}。
2. 素材归位：
   片段 → <player>/clips/ · 阵容图 → <player>/assets/landing.PNG
   卡抠图 → <player>/assets/cards/<player>_card.png
   真人照 → <player>/assets/<player>_poster.jpg · BGM → <player>/assets/bgm/（或共享 assets/bgm/）
3. python utils/contact_sheet.py <player>   # 认段号 #1..#N
4. 写 <player>/edl.json（复制 Mbappe/edl.json），设：
   project · landing_image · order · captions · landing_card_focus · poster；
   trim_head/trim_tail/transition/bgm*/outro_* 沿用 Mbappe 的值。
5. python utils/make_video.py <player>       # 竖屏 + 横屏 4K
6. python utils/cover.py <player>            # 封面（手工做好就跳过）
7. 打开成片给我看。要调字幕/顺序/封面就改 edl.json 重跑 5/6。

# 验收
<player>/output/ 下有 vertical_final.mp4、landscape_final.mp4(4K)、cover.jpg。
一条 make_video.py 出两条片，一条 cover.py 出封面。就算完成。
```

</details>
