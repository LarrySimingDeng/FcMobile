#!/usr/bin/env python3
"""Vertical master engine (reads <project>/edl.json): intro + N segments (gold frame + solid black bars + in-frame captions) + Apple-style outro --xfade--> output/vertical_final.mp4
Usage: render_vertical.py [project]"""
import subprocess, os, sys, glob, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
EDL=json.load(open(f"{PROJECT}/edl.json",encoding="utf-8"))
CLIPS=f"{PROJECT}/clips"; OUT=f"{PROJECT}/output"; BUILD="/tmp/fcm_build"
os.makedirs(OUT,exist_ok=True); os.makedirs(BUILD,exist_ok=True)
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
W,H=1080,1920; GOLD=(212,175,55); FGW,FGH=1040,480; FX,FY=(W-FGW)//2,(H-FGH)//2; TRANS=EDL["transition"]
files=sorted(glob.glob(f"{CLIPS}/*.MOV")+glob.glob(f"{CLIPS}/*.mov"))
def dur_of(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
ORDER=EDL["order"]; CAPTIONS={int(k):v for k,v in EDL["captions"].items()}
def in_dur(num): d=dur_of(files[num-1]); return EDL["trim_head"], round(max(2.0,d-EDL["trim_head"]-EDL["trim_tail"]),2)
def font(sz,bold=True):
    try: return ImageFont.truetype(FONT,sz,index=1 if bold else 0)
    except Exception: return ImageFont.truetype(FONT,sz,index=0)
def apple_font(sz,idx=1):
    for p,i in [("/System/Library/Fonts/PingFang.ttc",idx),("/System/Library/Fonts/PingFang.ttc",0),(FONT,0)]:
        try: return ImageFont.truetype(p,sz,index=i)
        except Exception: continue
    return ImageFont.truetype(FONT,sz,index=0)
def run(cmd):
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode!=0: print("ERR\n",r.stderr[-1600:]); raise SystemExit(1)
frame_png=f"{BUILD}/gold_frame.png"
_g=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(_g).rounded_rectangle((FX,FY,FX+FGW,FY+FGH),radius=22,outline=GOLD+(255,),width=6); _g.save(frame_png)
def wrap(d,text,fnt,maxw):
    NOSTART="，。！？、；：）】》」』…"; lines=[]; cur=""
    for ch in text:
        if d.textlength(cur+ch,font=fnt)<=maxw or (ch in NOSTART and cur): cur+=ch
        else: lines.append(cur); cur=ch
    if cur: lines.append(cur)
    return lines
def make_caption(text,path):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    fnt=font(28); lines=wrap(d,text,fnt,FGW-80); lh=38; y0=(FY+FGH-22)-lh*len(lines)
    for i,ln in enumerate(lines):
        d.text((W//2,y0+i*lh+lh//2),ln,font=fnt,fill=(255,255,255,255),anchor="mm",stroke_width=4,stroke_fill=(0,0,0,255))
    img.save(path)
def make_outro():
    img=Image.new("RGB",(W,H),(8,8,10)); d=ImageDraw.Draw(img)
    title=EDL["outro_title"]; f=apple_font(92,2); sp=22
    ws=[d.textlength(ch,font=f) for ch in title]; tw=sum(ws)+sp*(len(title)-1); x=(W-tw)/2; y=H//2-64
    for ch,w in zip(title,ws): d.text((x,y),ch,font=f,fill=(245,245,247),anchor="lm"); x+=w+sp
    d.line((W//2-130,H//2+20,W//2+130,H//2+20),fill=GOLD,width=2)
    d.text((W//2,H//2+74),EDL["outro_subtitle"],font=apple_font(40,0),fill=(150,150,160),anchor="mm")
    p=f"{BUILD}/outro.png"; img.save(p); outro=f"{BUILD}/outro.mp4"
    run(["ffmpeg","-y","-v","error","-loop","1","-t","3","-i",p,"-vf","fade=t=in:st=0:d=0.6,format=yuv420p","-r","60","-c:v","h264_videotoolbox","-b:v","10M",outro])
    return outro,3.0
def make_statcard():  # optional: hold a stat card after the intro (blurred bg + centered image), joins the xfade chain
    img=Image.open(f"{PROJECT}/{EDL['stat_card']}").convert("RGB"); iw,ih=img.size; dur=EDL.get("stat_card_dur",3.0)
    s=max(W/iw,H/ih); big=img.resize((round(iw*s),round(ih*s)),Image.LANCZOS); bx=(big.width-W)//2; by=(big.height-H)//2
    bg=Image.blend(big.crop((bx,by,bx+W,by+H)).filter(ImageFilter.GaussianBlur(48)),Image.new("RGB",(W,H),(0,0,0)),0.5)
    fh=round(ih*W/iw); bg.paste(img.resize((W,fh),Image.LANCZOS),(0,(H-fh)//2))
    p=f"{BUILD}/statcard_v.png"; bg.save(p); out=f"{BUILD}/statcard_v.mp4"
    run(["ffmpeg","-y","-v","error","-loop","1","-t",str(dur),"-i",p,"-vf","format=yuv420p","-r","60","-c:v","h264_videotoolbox","-b:v","12M","-pix_fmt","yuv420p",out])
    return out,dur
segs=[]; durs=[]
for pos,num in enumerate(ORDER):
    f=files[num-1]; inp,dd=in_dur(num); cap=CAPTIONS.get(num)
    ins=["-ss",str(inp),"-t",str(dd),"-i",f,"-i",frame_png]
    fc=(f"color=c=black:s={W}x{H}:r=60[bg];[0:v]scale={FGW}:{FGH}[fg];[bg][fg]overlay={FX}:{FY}[a];[a][1:v]overlay=0:0")
    if cap:
        cp=f"{BUILD}/cap_{num}.png"; make_caption(cap,cp); ins+=["-i",cp]; fc+="[b];[b][2:v]overlay=0:0"
    fc+=",format=yuv420p[v]"
    seg=f"{BUILD}/s_{pos}.mp4"
    run(["ffmpeg","-y","-v","error",*ins,"-filter_complex",fc,"-map","[v]","-t",str(dd),"-r","60","-c:v","h264_videotoolbox","-b:v","12M","-pix_fmt","yuv420p",seg])
    segs.append(seg); durs.append(dd); print(f"✓ pos{pos+1}=#{num} ({dd}s){' caption' if cap else ''}")
intro=f"{BUILD}/intro.mp4"
if os.path.exists(intro): segs=[intro]+segs; durs=[dur_of(intro)]+durs
if EDL.get("stat_card"):
    sc,scd=make_statcard(); ip=1 if os.path.exists(intro) else 0; segs.insert(ip,sc); durs.insert(ip,scd); print(f"✓ stat card hold ({scd}s) inserted after intro")
outro,od=make_outro(); segs+=[outro]; durs+=[od]
inputs=[]; [inputs.extend(["-i",s]) for s in segs]
fc=""; prev="[0:v]"
for i in range(1,len(segs)):
    off=sum(durs[j] for j in range(i))-i*TRANS
    fc+=f"{prev}[{i}:v]xfade=transition=fade:duration={TRANS}:offset={off:.3f}[x{i}];"; prev=f"[x{i}]"
fc=fc.rstrip(";")
final=f"{OUT}/vertical_final.mp4"; total=sum(durs)-(len(segs)-1)*TRANS
run(["ffmpeg","-y","-v","error",*inputs,"-filter_complex",fc,"-map",prev,"-r","60","-c:v","h264_videotoolbox","-b:v","12M","-pix_fmt","yuv420p",final])
if EDL.get("bgm"):
    tmp=final.replace(".mp4","_b.mp4")
    gap=EDL.get("bgm_tail_gap_s",0); fd=EDL.get("bgm_fade_dur_s",2); fe=max(0.1,total-gap); fst=max(0.1,fe-fd)
    run(["ffmpeg","-y","-v","error","-i",final,"-stream_loop","-1","-i",f"{PROJECT}/{EDL['bgm']}","-filter_complex",f"[1:a]volume={EDL.get('bgm_gain_db',-6)}dB,afade=t=out:st={fst:.2f}:d={fd}[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",tmp]); os.replace(tmp,final)
print(f"✅ Vertical master {final} ({total:.1f}s){' +BGM' if EDL.get('bgm') else ''}")
