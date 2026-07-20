# -*- coding: utf-8 -*-
"""任意フォルダ → 透過(外周白フラッドフィル)・トリム・256縮小 → assets/
usage: python process_any.py <srcdir> <name...>"""
import os, sys
import numpy as np
from PIL import Image
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, sys.argv[1])
DST = os.path.join(BASE, "assets")

def keyout(img, wth=225):
    a = np.array(img.convert("RGB")).astype(np.int16)
    hgt, wid = a.shape[:2]
    white = (a[:,:,0] >= wth) & (a[:,:,1] >= wth) & (a[:,:,2] >= wth)
    bg = np.zeros((hgt, wid), bool)
    dq = deque()
    for x in range(wid):
        for y in (0, hgt-1):
            if white[y,x] and not bg[y,x]: bg[y,x] = True; dq.append((y,x))
    for y in range(hgt):
        for x in (0, wid-1):
            if white[y,x] and not bg[y,x]: bg[y,x] = True; dq.append((y,x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0 <= ny < hgt and 0 <= nx < wid and white[ny,nx] and not bg[ny,nx]:
                bg[ny,nx] = True; dq.append((ny,nx))
    return Image.fromarray(np.dstack([a.clip(0,255).astype(np.uint8),
        np.where(bg, 0, 255).astype(np.uint8)]), "RGBA")

names = sys.argv[2:]
for name in names:
    fn = name if name.endswith(".png") else name + ".png"
    out = keyout(Image.open(os.path.join(SRC, fn)))
    bbox = out.getbbox()
    if bbox:
        l, t, r, b = bbox; pad = 8
        out = out.crop((max(0,l-pad), max(0,t-pad), min(out.width,r+pad), min(out.height,b+pad)))
    m = 256
    sc = min(m/out.width, m/out.height, 1.0)
    out = out.resize((max(1,int(out.width*sc)), max(1,int(out.height*sc))), Image.LANCZOS)
    path = os.path.join(DST, fn)
    out.save(path, optimize=True)
    print(fn, out.size, os.path.getsize(path)//1024, "KB")
print("DONE")
