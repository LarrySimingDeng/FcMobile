#!/usr/bin/env python3
"""Landscape master engine (reads <project>/edl.json): intro + N segments (full 19.5:9 frame + in-frame captions) + Apple-style outro --xfade--> output/landscape_final.mp4
Usage: render_landscape.py [project]"""
import subprocess, os, sys, glob, json
from PIL import Image, ImageDraw, ImageFont
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
EDL=json.load(open(f"{PROJECT}/edl.json",encoding="utf-8"))
CLIPS=f"{PROJECT}/clips"; OUT=f"{PROJECT}/output"; BUILD="/tmp/fcm_build"; LANDING=f"{PROJECT}/{EDL['landing_image']}"
os.makedirs(OUT,exist_ok=True); os.makedirs(BUILD,exist_ok=True)
FONT="/System/Library/Fonts/Hiragino Sans GB.ttc"
# ── Landscape quality (shared default; anti-recompression, no need to touch per player) ──────────────
# Bilibili only routes videos whose short side >= 1600 through its 4K high-bitrate transcode tier; below that it falls back to the lowest bitrate -> blurry. So we lock to 4K + high bitrate.
W,H=3840,1772; VBR="30M"   # 4K (short side 1772 >= 1600 triggers the 4K tier) + 30 Mbps high-bitrate source (Bilibili 4K accepts ~30M)
FPS=60; TRANS=EDL["transition"]; GOLD=(212,175,55)
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
def wrap(d,text,f,mw):
    NOSTART="，。！？、；：）】》」』…"; lines=[]; cur=""
    for ch in text:
        if d.textlength(cur+ch,font=f)<=mw or (ch in NOSTART and cur): cur+=ch
        else: lines.append(cur); cur=ch
    if cur: lines.append(cur)
    return lines
def make_caption(text,path):
    img=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(img)
    fnt=font(108); lines=wrap(d,text,fnt,W-520); lh=140; y0=(H-92)-lh*len(lines)
    for i,ln in enumerate(lines):
        d.text((W//2,y0+i*lh+lh//2),ln,font=fnt,fill=(255,255,255,255),anchor="mm",stroke_width=14,stroke_fill=(0,0,0,255))
    img.save(path)
def make_intro():
    src=Image.open(LANDING).convert("RGB"); SW,SH=src.size; AR=H/W
    foc=EDL.get("landing_card_focus",{"cx":1386,"cy":278,"w_horizontal":680})
    FR=f"{BUILD}/introh"; os.makedirs(FR,exist_ok=True)
    START=dict(cx=SW/2,cy=SH/2,w=SH/AR); END=dict(cx=foc["cx"],cy=foc["cy"],w=foc.get("w_horizontal",680))
    TH1,TM,TH2=1.0,2.2,1.4; T=TH1+TM+TH2; N=round(T*FPS)
    def ss(e0,e1,x):
        if e1<=e0: return 0.0 if x<e0 else 1.0
        x=max(0.0,min(1.0,(x-e0)/(e1-e0))); return x*x*(3-2*x)
    for i in range(N):
        t=i/FPS; p=ss(TH1,TH1+TM,t)
        w=START["w"]*(END["w"]/START["w"])**p; cx=START["cx"]+(END["cx"]-START["cx"])*p; cy=START["cy"]+(END["cy"]-START["cy"])*p
        h=w*AR; x0,y0=cx-w/2,cy-h/2; scale=W/w
        ix0,iy0=max(0,x0),max(0,y0); ix1,iy1=min(SW,cx+w/2),min(SH,cy+h/2)
        crop=src.crop((round(ix0),round(iy0),round(ix1),round(iy1)))
        crop=crop.resize((max(1,round((ix1-ix0)*scale)),max(1,round((iy1-iy0)*scale))),Image.LANCZOS)
        fr=Image.new("RGB",(W,H),(0,0,0)); fr.paste(crop,(round((ix0-x0)*scale),round((iy0-y0)*scale))); fr.save(f"{FR}/f_{i:04d}.png")
    out=f"{BUILD}/intro_h.mp4"
    run(["ffmpeg","-y","-v","error","-framerate",str(FPS),"-i",f"{FR}/f_%04d.png","-c:v","h264_videotoolbox","-b:v",VBR,"-pix_fmt","yuv420p",out])
    return out,T
def make_outro():
    img=Image.new("RGB",(W,H),(8,8,10)); d=ImageDraw.Draw(img)
    title=EDL["outro_title"]; f=apple_font(136,2); sp=32
    ws=[d.textlength(ch,font=f) for ch in title]; tw=sum(ws)+sp*(len(title)-1); x=(W-tw)/2; y=H//2-92
    for ch,w in zip(title,ws): d.text((x,y),ch,font=f,fill=(245,245,247),anchor="lm"); x+=w+sp
    d.line((W//2-220,H//2+24,W//2+220,H//2+24),fill=GOLD,width=4)
    d.text((W//2,H//2+116),EDL["outro_subtitle"],font=apple_font(68,0),fill=(150,150,160),anchor="mm")
    p=f"{BUILD}/outro_h.png"; img.save(p); out=f"{BUILD}/outro_h.mp4"
    run(["ffmpeg","-y","-v","error","-loop","1","-t","3","-i",p,"-vf","fade=t=in:st=0:d=0.6,format=yuv420p","-r",str(FPS),"-c:v","h264_videotoolbox","-b:v","16M",out])
    return out,3.0
def make_statcard():  # optional: hold a stat card after the intro (near-fills the frame, dark bars), joins the xfade chain
    img=Image.open(f"{PROJECT}/{EDL['stat_card']}").convert("RGB"); iw,ih=img.size; dur=EDL.get("stat_card_dur",3.0)
    canvas=Image.new("RGB",(W,H),(8,8,10)); disp=img.resize((W,round(ih*W/iw)),Image.LANCZOS); canvas.paste(disp,(0,(H-disp.height)//2))
    p=f"{BUILD}/statcard_h.png"; canvas.save(p); out=f"{BUILD}/statcard_h.mp4"
    run(["ffmpeg","-y","-v","error","-loop","1","-t",str(dur),"-i",p,"-vf","format=yuv420p","-r",str(FPS),"-c:v","h264_videotoolbox","-b:v",VBR,"-pix_fmt","yuv420p",out])
    return out,dur
segs=[]; durs=[]
for pos,num in enumerate(ORDER):
    f=files[num-1]; inp,dd=in_dur(num); cap=CAPTIONS.get(num)
    ins=["-ss",str(inp),"-t",str(dd),"-i",f]; base=f"[0:v]scale={W}:{H}:flags=lanczos"
    if cap:
        cp=f"{BUILD}/caph_{num}.png"; make_caption(cap,cp); ins+=["-i",cp]; fc=f"{base}[b];[b][1:v]overlay=0:0,format=yuv420p[v]"
    else: fc=f"{base},format=yuv420p[v]"
    seg=f"{BUILD}/h_{pos}.mp4"
    run(["ffmpeg","-y","-v","error",*ins,"-filter_complex",fc,"-map","[v]","-t",str(dd),"-r",str(FPS),"-c:v","h264_videotoolbox","-b:v",VBR,"-pix_fmt","yuv420p",seg])
    segs.append(seg); durs.append(dd); print(f"✓ pos{pos+1}=#{num} ({dd}s){' caption' if cap else ''}")
intro,it=make_intro(); segs=[intro]+segs; durs=[it]+durs
if EDL.get("stat_card"):
    sc,scd=make_statcard(); segs.insert(1,sc); durs.insert(1,scd); print(f"✓ stat card hold ({scd}s) inserted after intro")
outro,ot=make_outro(); segs+=[outro]; durs+=[ot]
inputs=[]; [inputs.extend(["-i",s]) for s in segs]
fc=""; prev="[0:v]"
for i in range(1,len(segs)):
    off=sum(durs[j] for j in range(i))-i*TRANS
    fc+=f"{prev}[{i}:v]xfade=transition=fade:duration={TRANS}:offset={off:.3f}[x{i}];"; prev=f"[x{i}]"
fc=fc.rstrip(";")
final=f"{OUT}/landscape_final.mp4"; total=sum(durs)-(len(segs)-1)*TRANS
run(["ffmpeg","-y","-v","error",*inputs,"-filter_complex",fc,"-map",prev,"-r",str(FPS),"-c:v","h264_videotoolbox","-b:v",VBR,"-pix_fmt","yuv420p",final])
if EDL.get("bgm"):
    tmp=final.replace(".mp4","_b.mp4")
    gap=EDL.get("bgm_tail_gap_s",0); fd=EDL.get("bgm_fade_dur_s",2); fe=max(0.1,total-gap); fst=max(0.1,fe-fd)
    run(["ffmpeg","-y","-v","error","-i",final,"-stream_loop","-1","-i",f"{PROJECT}/{EDL['bgm']}","-filter_complex",f"[1:a]volume={EDL.get('bgm_gain_db',-6)}dB,afade=t=out:st={fst:.2f}:d={fd}[a]","-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",tmp]); os.replace(tmp,final)
print(f"✅ Landscape master {final} ({total:.1f}s){' +BGM' if EDL.get('bgm') else ''}")
