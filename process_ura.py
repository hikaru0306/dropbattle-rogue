# -*- coding: utf-8 -*-
"""assets_raw_ura/ → 透過・トリム・縮小 → assets/
この画風（白背景フラットイラスト）には rembg より外周白フラッドフィルが確実:
外周から繋がった白だけ透過し、輪郭内の白（毛・ハイライト等）は保持される。
usage: python process_ura.py [name ...]  (省略時は全ファイル)"""
import os, sys
import numpy as np
from PIL import Image
from collections import deque

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ura")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

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

targets = [n if n.endswith(".png") else n + ".png" for n in sys.argv[1:]] or sorted(os.listdir(SRC))
for fn in targets:
    if not fn.endswith(".png"): continue
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
