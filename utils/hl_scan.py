#!/usr/bin/env python3
"""fcm-highlights scan: full-frame thumbnail timeline for locating goals / celebrations / scorers.
Usage: hl_scan.py <video> [step_sec=4] [start_sec=0] [dur_sec=all]"""
import subprocess, os, glob, sys
from PIL import Image, ImageDraw, ImageFont
F=sys.argv[1]; STEP=float(sys.argv[2]) if len(sys.argv)>2 else 4
START=float(sys.argv[3]) if len(sys.argv)>3 else 0
DUR=sys.argv[4] if len(sys.argv)>4 else None
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
OUT="/tmp/fcm_hl"; FR=f"{OUT}/fr"; os.makedirs(FR,exist_ok=True)
for x in glob.glob(f"{FR}/*.jpg"): os.remove(x)
cmd=["ffmpeg","-y","-v","error"]
if START>0: cmd+=["-ss",str(START)]
if DUR: cmd+=["-t",str(DUR)]
cmd+=["-i",F,"-vf",f"fps=1/{STEP}","-q:v","3",f"{FR}/f_%03d.jpg"]
subprocess.run(cmd,check=True)
frames=sorted(glob.glob(f"{FR}/f_*.jpg"))
COLS=8; tw,th,pad,lblh=320,148,5,20
rows=(len(frames)+COLS-1)//COLS
W=COLS*(tw+pad)+pad; H=rows*(th+lblh+pad)+pad+30
c=Image.new("RGB",(W,H),(18,18,22)); d=ImageDraw.Draw(c)
f16=ImageFont.truetype(FONT,16); f22=ImageFont.truetype(FONT,22)
d.text((pad,6),f"Full-frame timeline: from {START:.0f}s, one frame every {STEP}s ({len(frames)} frames) - find score jumps + goal celebrations + scorer names",font=f22,fill=(255,210,80))
for i,fp in enumerate(frames):
    th_img=Image.open(fp).resize((tw,th),Image.LANCZOS)
    r,col=divmod(i,COLS); x=pad+col*(tw+pad); y=30+pad+r*(th+lblh+pad)
    c.paste(th_img,(x,y)); d.text((x+2,y+th+1),f"{START+i*STEP:.0f}s",font=f16,fill=(120,230,255))
out=f"{OUT}/timeline.jpg"; c.save(out,quality=90)
print(f"✓ {len(frames)} frames → {out}")
