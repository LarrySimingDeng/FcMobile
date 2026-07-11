#!/usr/bin/env python3
"""Contact sheet (for identifying segment numbers): grab one mid-clip frame from each file in clips/ and tile them into a grid. Usage: contact_sheet.py [project]"""
import subprocess, os, sys, glob
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
CLIPS=f"{PROJECT}/clips"; FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
TMP="/tmp/fcm_build/cs"; os.makedirs(TMP,exist_ok=True)
def font(s,b=True):
    try: return ImageFont.truetype(FONT,s,index=1 if b else 0)
    except Exception: return ImageFont.truetype(FONT,s,index=0)
files=sorted(glob.glob(f"{CLIPS}/*.MOV")+glob.glob(f"{CLIPS}/*.mov"))
TW,TH,COLS,GAP,MX,MY,LBL=360,166,3,16,24,110,52
rows=(len(files)+COLS-1)//COLS
CW=MX*2+COLS*TW+(COLS-1)*GAP; CH=MY+rows*(TH+LBL+GAP)+20
c=Image.new("RGB",(CW,CH),(14,20,32)); d=ImageDraw.Draw(c)
d.text((MX,36),"Contact sheet · For each #, tell me: which seconds to use + what caption",font=font(30),fill=(212,175,55))
for i,f in enumerate(files):
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
    jf=f"{TMP}/{i}.jpg"; subprocess.run(["ffmpeg","-y","-v","error","-ss",str(dur/2),"-i",f,"-frames:v","1","-vf",f"scale={TW}:{TH}",jf],check=True)
    r,col=divmod(i,COLS); x=MX+col*(TW+GAP); y=MY+r*(TH+LBL+GAP)
    c.paste(Image.open(jf),(x,y)); d.rectangle((x,y,x+TW,y+TH),outline=(212,175,55),width=2)
    d.rectangle((x,y,x+64,y+40),fill=(212,175,55)); d.text((x+32,y+20),f"#{i+1}",font=font(28),fill=(14,20,32),anchor="mm")
    d.text((x+4,y+TH+6),os.path.basename(f).replace("ScreenRecording_","")[:26],font=font(19,False),fill=(200,200,210))
    d.text((x+4,y+TH+30),f"{dur:.1f}s",font=font(24),fill=(255,255,255))
out=f"{TMP}/contact_sheet.jpg"; c.save(out,quality=90); print("✅ Contact sheet:",out)
subprocess.run(["open",out])
