#!/usr/bin/env python3
"""Bilibili cover (cinematic, image-only, no text): real-life poster (right, feather-blended) + cut-out card (left, tilted with gold glow) + atmospheric background.
Usage: cover.py [project]   reads the edl.poster config"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFilter
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT=os.path.abspath(sys.argv[1]) if len(sys.argv)>1 else f"{ROOT}/Mbappe"
EDL=json.load(open(f"{PROJECT}/edl.json",encoding="utf-8")); P=EDL["poster"]
CARD=f"{PROJECT}/{P['card']}"; POSTER=f"{PROJECT}/{P['person']}"
CARD_H=P.get("card_scale",460); PERSON_W=P.get("person_width",920)
OUT=f"{PROJECT}/output"; os.makedirs(OUT,exist_ok=True)
W,H=1280,720; GOLD=(212,175,55)
def blur(i,r): return i.filter(ImageFilter.GaussianBlur(r))
# Atmospheric background
bg=Image.new("RGB",(W,H),(14,16,26)); d=ImageDraw.Draw(bg)
for y in range(H):
    t=y/H; d.line((0,y,W,y),fill=(int(16+t*14),int(18+t*12),int(30+t*16)))
g=Image.new("L",(W,H),0); ImageDraw.Draw(g).ellipse((W-780,H//2-460,W+180,H//2+460),fill=120)
bg=Image.composite(Image.new("RGB",(W,H),(210,170,80)),bg,blur(g,150))
# Real photo on the right: cover-fit + sharpen + feather the left edge
poster=Image.open(POSTER).convert("RGB"); ph=H; pw=round(poster.width*ph/poster.height)
poster=poster.resize((pw,ph),Image.LANCZOS)
crop=poster.crop((max(0,pw-PERSON_W),0,pw,ph)) if pw>=PERSON_W else poster.resize((PERSON_W,ph))
crop=crop.filter(ImageFilter.UnsharpMask(radius=2,percent=120))
feather=Image.new("L",(PERSON_W,H),255); fd=ImageDraw.Draw(feather)
for x in range(200): fd.line((x,0,x,H),fill=int(255*(x/200)))
rp=crop.convert("RGBA"); rp.putalpha(feather)
tmp=Image.new("RGBA",(W,H),(0,0,0,0)); tmp.paste(rp,(W-PERSON_W,0),rp)
bg=Image.alpha_composite(bg.convert("RGBA"),tmp).convert("RGB")
# Cut-out card on the left: trim + resize + tilt + gold outer glow
card=Image.open(CARD).convert("RGBA"); card=card.crop(card.getbbox())
cw=round(card.width*CARD_H/card.height); card=card.resize((cw,CARD_H),Image.LANCZOS)
card=card.rotate(-5,expand=True,resample=Image.BICUBIC); cx,cy=60,(H-card.height)//2
glow=Image.new("RGBA",(W,H),(0,0,0,0)); ImageDraw.Draw(glow).ellipse((cx-30,cy-10,cx+card.width+30,cy+card.height+10),fill=(212,175,55,130))
bg=Image.alpha_composite(bg.convert("RGBA"),blur(glow,40)).convert("RGB")
bg.paste(card,(cx,cy),card)
out=f"{OUT}/cover.jpg"; bg.save(out,quality=94); print("✅ Cover",out,bg.size)
