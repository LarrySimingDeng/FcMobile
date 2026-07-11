#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fcm-highlights fully-automatic goal detection: locate "our goals" in a full FC Mobile screen recording and cut out the clips.

Usage:
    python hl_ocr.py <video> [project_dir]

Output:
    <project_dir>/highlights/goalN.mp4   auto-cut clips (build-up -> goal -> stops at the player-card popup, EA cutscene excluded)
    <project_dir>/highlights/goals.json  one entry per "our goal": {goal_time, score, clip_in, clip_out, scorer}

Approach:
    1. ffmpeg grabs one frame per second.
    2. The scoreboard is in the top-left; the left score = us. Crop a small patch around each of the two digits
       and detect that the digit **image changes** via a "fixed-threshold binary fingerprint + stable-segment
       comparison" -- left patch changes = our goal, right patch changes = opponent goal (discarded).
    3. The goal moment is anchored by the "player card popping up in the bottom-left" (green vanishes from that
       region); the clip end is anchored by the "EA SPORTS FC MOBILE full-screen cutscene" (center saturation
       collapses and turns white) -- the cut stops just before that cutscene.
    4. score field: assume the match kicks off at 0:0 and accumulate the detected left/right increments (e.g. 1:2, 2:2).
    5. ffmpeg -c:v h264_videotoolbox hardware-encodes the cut clips.

Why not real OCR? The local tesseract 5.5.2 works, but in practice it is extremely unstable on this game's score
font: the digit "1" is never read, and the same "0"/"2" image flips between readable and unreadable due to tiny
encoding differences. So we use the fallback suggested in the environment notes -- only judging whether the score
patch "changed" (and which side changed), which is far more reliable than reading "what number it is" and needs no
OCR dependency at all. The scorer name on the card/banner is likewise not reliably OCR-able, so it is left blank
(an optional field in the spec).
"""
import subprocess, os, sys, glob, json, shutil
from PIL import Image

# ── Frame-size assumption: decoded as landscape 2796x1290 (iPhone recordings carry rotation, so extracted frames are already landscape)───────────
FW, FH = 2796, 1290
STEP = 1.0                       # frame-extraction interval (seconds)

# ── Key UI regions (actual pixels at 2796x1290; x, y, w, h)──────────────────────────────
LEFT_BOX   = (560, 40, 95, 82)   # left score digit (us)
RIGHT_BOX  = (678, 40, 95, 82)   # right score digit (opponent)
CENTER_BOX = (950, 300, 900, 650)# screen center: pitch vs EA cutscene white grid
CARD_BOX   = (180, 300, 560, 620)# bottom-left: pitch/joystick vs scorer's player card

# ── Detection thresholds (all calibrated on the test video; see the top-of-file docstring)───────────────────────────────
SB_SAT_MAX, SB_BRI_MIN = 30, 140 # scoreboard "present" test: low saturation (gray backing) + bright enough
FP_SIZE, FP_THR = 20, 140        # digit fingerprint: downscale to 20x20, grayscale < 140 counts as ink
INK_MIN, INK_MAX = 12, 80        # valid ink-pixel count for one digit (filters out blank / flash transition frames)
MERGE_TH = 22                    # Hamming distance < this = "same digit", merge into one stable segment
CHANGE_TH = 24                   # adjacent stable segments with Hamming distance >= this = the digit really changed (a goal)
MIN_STABLE = 2                   # minimum frames a stable segment must last
EA_SAT_MAX, EA_BRI_MIN = 22, 150 # EA cutscene: very low center saturation + bright
CARD_GRN_MAX, CARD_BRI_MAX = 35, 180  # player card: green vanishes from bottom-left (and not the pure-white cutscene)

PRE_ROLL = 8.0                   # pre-goal build-up (seconds)
POST_FALLBACK = 5.0              # fallback clip tail when no EA cutscene is found (seconds)
BITRATE = "14M"

TMP = "/tmp/fcm_ocr"


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def probe_duration(video):
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", video])
    try:
        return float(r.stdout.decode().strip())
    except ValueError:
        return 0.0


def extract_frames(video):
    """Extract one full-resolution JPEG every STEP seconds into TMP/; return [(t, path), ...]."""
    if os.path.isdir(TMP):
        shutil.rmtree(TMP)
    os.makedirs(TMP)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", video,
                    "-vf", f"fps=1/{STEP}", "-q:v", "3", f"{TMP}/f_%05d.jpg"],
                   check=True)
    paths = sorted(glob.glob(f"{TMP}/f_*.jpg"))
    return [((i * STEP), p) for i, p in enumerate(paths)]


# ── Per-frame feature extraction ──────────────────────────────────────────────────────────────
def region_stats(im, box, small=(90, 65)):
    """Region-average saturation / brightness / greenness (g - (r+b)/2)."""
    x, y, w, h = box
    px = list(im.crop((x, y, x + w, y + h)).resize(small).get_flattened_data())
    n = len(px)
    sat = sum(max(p) - min(p) for p in px) / n
    bri = sum(sum(p) / 3 for p in px) / n
    grn = sum(p[1] - (p[0] + p[2]) / 2 for p in px) / n
    return sat, bri, grn


def digit_fp(im, box):
    """Binary fingerprint of the digit patch (fixed threshold) + ink-pixel count."""
    x, y, w, h = box
    g = im.crop((x, y, x + w, y + h)).convert("L").resize((FP_SIZE, FP_SIZE), Image.LANCZOS)
    bits = [1 if v < FP_THR else 0 for v in g.get_flattened_data()]
    return bits, sum(bits)


def ham(a, b):
    return sum(x != y for x, y in zip(a, b))


def scaled_boxes(w, h):
    """Scale the calibration-baseline (2796x1290) detection regions to the actual decoded resolution."""
    sx, sy = w / FW, h / FH
    s = lambda b: (round(b[0] * sx), round(b[1] * sy), round(b[2] * sx), round(b[3] * sy))
    return {"L": s(LEFT_BOX), "R": s(RIGHT_BOX),
            "center": s(CENTER_BOX), "card": s(CARD_BOX)}


def analyze(frames, boxes):
    """Return a list of per-frame dicts."""
    feats = []
    for t, p in frames:
        im = Image.open(p).convert("RGB")
        f = {"t": t}
        for name in ("L", "R"):
            box = boxes[name]
            s, b, _ = region_stats(im, box, (48, 41))
            present = s < SB_SAT_MAX and b > SB_BRI_MIN
            bits, ink = digit_fp(im, box)
            clean = present and INK_MIN <= ink <= INK_MAX
            f[name] = {"clean": clean, "bits": bits, "ink": ink}
        cs, cb, _ = region_stats(im, boxes["center"])
        f["ea"] = (cs < EA_SAT_MAX and cb > EA_BRI_MIN)
        _, db, dg = region_stats(im, boxes["card"])
        f["card"] = (dg < CARD_GRN_MAX and db < CARD_BRI_MAX)
        feats.append(f)
    return feats


# ── Stable segments & goal-event detection ─────────────────────────────────────────────────────
def stable_segments(feats, side):
    """Merge one side's (L/R) clean frames into stable digit segments: [{t0,t1,bits,n}]."""
    segs = []
    for f in feats:
        d = f[side]
        if not d["clean"]:
            continue
        if segs and ham(d["bits"], segs[-1]["bits"]) < MERGE_TH:
            segs[-1]["t1"] = f["t"]; segs[-1]["n"] += 1
        else:
            segs.append({"t0": f["t"], "t1": f["t"], "bits": d["bits"], "n": 1})
    return [s for s in segs if s["n"] >= MIN_STABLE]


def detect_changes(feats, side):
    """Return the timestamps where that side's digit changed (= that side's goal moments)."""
    segs = stable_segments(feats, side)
    changes = []
    for i in range(1, len(segs)):
        if ham(segs[i]["bits"], segs[i - 1]["bits"]) >= CHANGE_TH:
            changes.append(segs[i]["t0"])   # the moment the new digit first stabilizes
    return changes


# ── Moment anchoring: player-card start / EA-cutscene start ────────────────────────────────────────
def card_start_near(feats, t, lo=-3.0, hi=4.0):
    """Earliest player-card popup near change_time (anchors the goal instant)."""
    cand = [f["t"] for f in feats if f["card"] and t + lo <= f["t"] <= t + hi]
    return min(cand) if cand else None


def ea_start_after(feats, t, window=14.0):
    """Earliest EA cutscene after the goal (= clip end, just before the cutscene)."""
    cand = [f["t"] for f in feats if f["ea"] and t < f["t"] <= t + window]
    return min(cand) if cand else None


# ── Cut the clip ────────────────────────────────────────────────────────────────────
def cut_clip(video, cin, cout, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{cin:.2f}", "-i", video,
                    "-t", f"{cout - cin:.2f}", "-c:v", "h264_videotoolbox",
                    "-b:v", BITRATE, "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k", out], check=True)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    video = sys.argv[1]
    proj = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
    if not os.path.exists(video):
        print(f"Video not found: {video}"); sys.exit(1)
    out_dir = os.path.join(proj, "highlights")
    os.makedirs(out_dir, exist_ok=True)

    dur = probe_duration(video)
    print(f"▶ Video {os.path.basename(video)}  duration {dur:.0f}s  frame step {STEP}s …")
    frames = extract_frames(video)
    if not frames:
        print("Failed to extract any frames; check whether the video is decodable."); sys.exit(1)
    w, h = Image.open(frames[0][1]).size
    if (w, h) != (FW, FH):
        print(f"  ⚠ Decoded frame is {w}x{h}, different from the {FW}x{FH} calibration baseline; scaling detection regions proportionally (best effort)")
    boxes = scaled_boxes(w, h)
    print(f"  Extracted {len(frames)} frames; analyzing the scoreboard …")
    feats = analyze(frames, boxes)

    our_goals = detect_changes(feats, "L")   # left score change = our goal
    opp_goals = detect_changes(feats, "R")   # right score change = opponent goal (discarded)
    print(f"  Detected: our goals {len(our_goals)} @ {[f'{t:.0f}' for t in our_goals]}"
          f" | opponent goals {len(opp_goals)} @ {[f'{t:.0f}' for t in opp_goals]} (discarded)")

    # ── Score: assume kickoff at 0:0, accumulate left/right increments in time order ──
    l = r = 0
    events = sorted([(t, "L") for t in our_goals] + [(t, "R") for t in opp_goals])
    score_at = {}
    for t, side in events:
        if side == "L": l += 1
        else: r += 1
        score_at[(t, side)] = f"{l}:{r}"

    # ── Compute a clip for each of our goals ──
    goals = []
    for i, gt in enumerate(our_goals, 1):
        cstart = card_start_near(feats, gt)
        goal_time = cstart if cstart is not None else gt   # card-popup start ≈ goal instant
        ea = ea_start_after(feats, goal_time)
        # Clip end stops before the EA cutscene: back off half a sampling step so the white grid never sweeps in
        clip_out = (ea - 0.5) if ea is not None else goal_time + POST_FALLBACK
        clip_out = max(clip_out, goal_time + 3.0)          # at least the goal + card popup
        clip_in = max(0.0, goal_time - PRE_ROLL)           # pre-goal build-up
        clip_path = os.path.join(out_dir, f"goal{i}.mp4")
        cut_clip(video, clip_in, clip_out, clip_path)
        goals.append({"goal_time": round(goal_time, 1),
                      "score": score_at.get((gt, "L"), "?:?"),
                      "clip_in": round(clip_in, 1), "clip_out": round(clip_out, 1),
                      "scorer": None, "clip": os.path.basename(clip_path)})

    with open(os.path.join(out_dir, "goals.json"), "w") as fp:
        json.dump({"video": os.path.basename(video), "our_goals": goals},
                  fp, ensure_ascii=False, indent=2)

    # ── Print results ──
    print("\n════════ Our goal clips ════════")
    for g in goals:
        print(f"  #{g['clip']}  goal_time={g['goal_time']:>6.1f}s  "
              f"score={g['score']:<12}  clip=[{g['clip_in']:.1f}, {g['clip_out']:.1f}]"
              f"  scorer={g['scorer'] or '-'}")
    print(f"\n✓ {len(goals)} clips total + goals.json → {out_dir}")


if __name__ == "__main__":
    main()
