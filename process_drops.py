# -*- coding: utf-8 -*-
"""ドロップ宝石→フラッドフィル白抜き透過(128px)、背景→JPEG化"""
import os
import numpy as np
from PIL import Image, ImageFilter
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "assets_raw")
DST = os.path.join(BASE, "assets")

def flood_white(img, thresh=90):
    a = np.array(img.convert("RGBA")).astype(np.int16)
    h, w = a.shape[:2]
    near = (255 - a[:,:,:3]).sum(axis=2) < thresh
    bg = np.zeros((h,w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h-1):
            if near[y,x] and not bg[y,x]: bg[y,x]=True; dq.append((y,x))
    for y in range(h):
        for x in (0, w-1):
            if near[y,x] and not bg[y,x]: bg[y,x]=True; dq.append((y,x))
    while dq:
        y,x = dq.popleft()
        for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0<=ny<h and 0<=nx<w and near[ny,nx] and not bg[ny,nx]:
                bg[ny,nx]=True; dq.append((ny,nx))
    a[:,:,3] = np.where(bg, 0, 255)
    img = Image.fromarray(a.clip(0,255).astype(np.uint8))
    al = Image.fromarray(np.array(img)[:,:,3])
    al = al.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(0.8))
    arr = np.array(img); arr[:,:,3] = np.array(al)
    return Image.fromarray(arr)

for name in ["drop_red","drop_gold","drop_purple","drop_teal","drop_junk"]:
    p = os.path.join(SRC, name+".png")
    if not os.path.exists(p): print("skip", name); continue
    im = flood_white(Image.open(p))
    bb = im.getbbox()
    if bb:
        l,t,r,b = bb
        pad = 6
        im = im.crop((max(0,l-pad), max(0,t-pad), min(im.width,r+pad), min(im.height,b+pad)))
    sc = 128/max(im.size)
    im = im.resize((max(1,int(im.width*sc)), max(1,int(im.height*sc))), Image.LANCZOS)
    im.save(os.path.join(DST, name+".png"), optimize=True)
    print(name, im.size)

for name, q in [("bg_map", 82), ("bg_battle", 82)]:
    p = os.path.join(SRC, name+".png")
    if not os.path.exists(p): print("skip", name); continue
    im = Image.open(p).convert("RGB")
    im.save(os.path.join(DST, name+".jpg"), quality=q, optimize=True)
    print(name, im.size, os.path.getsize(os.path.join(DST, name+".jpg"))//1024, "KB")
print("DONE")
