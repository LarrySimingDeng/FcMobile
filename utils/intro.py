#!/usr/bin/env python3
"""Vertical intro: landing lineup panorama -> zoom in and focus on the player's card. Usage: intro.py [project]"""
import subprocess, os, sys, json
from PIL import Image, ImageFilter
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
EDL=json.load(open(f"{PROJECT}/edl.json",encoding="utf-8"))
LANDING=f"{PROJECT}/{EDL['landing_image']}"
BUILD="/tmp/fcm_build"; FR=f"{BUILD}/intro_frames"; os.makedirs(FR,exist_ok=True)
W,H=1080,1920; FPS=60
src=Image.open(LANDING).convert("RGB"); SW,SH=src.size
foc=EDL.get("landing_card_focus",{"cx":SW/2,"cy":SH/2,"w_vertical":300})
START=dict(cx=SW/2,cy=SH/2,w=SW); END=dict(cx=foc["cx"],cy=foc["cy"],w=foc.get("w_vertical",300))
AR=H/W; TH1,TM,TH2=1.0,2.2,1.6; T=TH1+TM+TH2; N=round(T*FPS)
def ss(e0,e1,x):
    if e1<=e0: return 0.0 if x<e0 else 1.0
    x=max(0.0,min(1.0,(x-e0)/(e1-e0))); return x*x*(3-2*x)
def lerp(a,b,p): return a+(b-a)*p
s=max(W/SW,H/SH); big=src.resize((round(SW*s),round(SH*s)),Image.LANCZOS)
bx=(big.width-W)//2; by=(big.height-H)//2
BG=Image.blend(big.crop((bx,by,bx+W,by+H)).filter(ImageFilter.GaussianBlur(48)),Image.new("RGB",(W,H),(0,0,0)),0.5)
for i in range(N):
    t=i/FPS; p=ss(TH1,TH1+TM,t)
    w=START["w"]*(END["w"]/START["w"])**p; cx=lerp(START["cx"],END["cx"],p); cy=lerp(START["cy"],END["cy"],p); h=w*AR
    x0,y0=cx-w/2,cy-h/2; scale=W/w; frame=BG.copy()
    ix0,iy0=max(0,x0),max(0,y0); ix1,iy1=min(SW,cx+w/2),min(SH,cy+h/2)
    if ix1>ix0 and iy1>iy0:
        crop=src.crop((round(ix0),round(iy0),round(ix1),round(iy1)))
        crop=crop.resize((max(1,round((ix1-ix0)*scale)),max(1,round((iy1-iy0)*scale))),Image.LANCZOS)
        frame.paste(crop,(round((ix0-x0)*scale),round((iy0-y0)*scale)))
    frame.save(f"{FR}/f_{i:04d}.png")
out=f"{BUILD}/intro.mp4"
subprocess.run(["ffmpeg","-y","-v","error","-framerate",str(FPS),"-i",f"{FR}/f_%04d.png","-c:v","h264_videotoolbox","-b:v","14M","-pix_fmt","yuv420p",out],check=True)
print(f"✅ Intro {out} ({T:.1f}s)")
