#!/usr/bin/env python3
"""One-shot build: read <project>/edl.json -> vertical intro + vertical master + landscape master (captions / transitions / intro+outro / BGM).
Usage: python utils/make_video.py [project folder]   (defaults to Mbappe)"""
import subprocess, sys, os
UTILS=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(UTILS)
PY=f"{ROOT}/.venv/bin/python"
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
print(f"Project: {PROJECT}")
for name,scr in [("vertical intro","intro.py"),("vertical master","render_vertical.py"),("landscape master","render_landscape.py")]:
    print(f"\n=== {name} ({scr}) ===")
    if subprocess.run([PY,f"{UTILS}/{scr}",PROJECT]).returncode!=0:
        print(f"✗ {name} failed"); sys.exit(1)
print(f"\n🎉 Done → {PROJECT}/output/vertical_final.mp4 + landscape_final.mp4")
