# -*- coding: utf-8 -*-
"""現行assetsで『閉じた領域に残った白背景』だけを追加透過する後処理 → assets/
外周フラッドフィルで抜けなかった内側の白(足の隙間・とぐろの内側等)を除去。
目・牙・白ハイライト等の小さい白は面積閾値で保護して残す。
usage: python fix_whitekey.py <name...>   (--minsize N で閾値変更, 既定40)"""
import os, sys
import numpy as np
from PIL import Image
from collections import deque

BASE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(BASE, "assets")
CAND = os.path.join(BASE, "assets_cand")

WTH = 246      # これ以上を「純白背景」とみなす
MINSIZE = 40   # この面積以上の白連結成分だけ透過(小さいのは目等として残す)
for a in sys.argv[1:]:
    if a.startswith("--minsize"):
        MINSIZE = int(a.split("=")[1]) if "=" in a else MINSIZE

def components(mask):
    h,w = mask.shape; lab = np.zeros((h,w),int); cur=0; comps=[]
    for i in range(h):
        for j in range(w):
            if mask[i,j] and lab[i,j]==0:
                cur+=1; px=[]; dq=deque([(i,j)]); lab[i,j]=cur
                while dq:
                    y,x=dq.popleft(); px.append((y,x))
                    for ny,nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                        if 0<=ny<h and 0<=nx<w and mask[ny,nx] and lab[ny,nx]==0:
                            lab[ny,nx]=cur; dq.append((ny,nx))
                comps.append(px)
    return comps

names = [a for a in sys.argv[1:] if not a.startswith("--")]
for n in names:
    fn = os.path.join(DST, n+".png")
    bak = os.path.join(CAND, n+"_prev_whitekey.png")
    if not os.path.exists(bak):
        Image.open(fn).save(bak)
    a = np.array(Image.open(fn).convert("RGBA"))
    op = a[:,:,3] > 0
    white = op & (a[:,:,0]>=WTH) & (a[:,:,1]>=WTH) & (a[:,:,2]>=WTH)
    comps = components(white)
    removed = 0; kept = 0
    for px in comps:
        if len(px) >= MINSIZE:
            for (y,x) in px: a[y,x,3] = 0
            removed += len(px)
        else:
            kept += 1
    Image.fromarray(a,"RGBA").save(fn, optimize=True)
    print(f"{n}: removed {removed}px white, kept {kept} small white blobs(目等)")
print("DONE")
