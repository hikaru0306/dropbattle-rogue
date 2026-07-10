# -*- coding: utf-8 -*-
"""assets_raw/ → 透過・トリム・縮小 → assets/
MIDNIGHT MIRAGE の知見: rembg(isnet-anime) 後に四隅サンプル色キーイングで残り薄灰を除去"""
import os, io
import numpy as np
from PIL import Image
from rembg import remove, new_session

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(DST, exist_ok=True)
session = new_session("isnet-anime")

def corner_key(img, thresh=28):
    a = np.array(img).astype(np.int16)
    h, w = a.shape[:2]
    corners = [a[2,2,:3], a[2,w-3,:3], a[h-3,2,:3], a[h-3,w-3,:3]]
    for c in corners:
        d = np.abs(a[:,:,:3] - c).sum(axis=2)
        a[:,:,3] = np.where((d < thresh) & (a[:,:,3] > 0), 0, a[:,:,3])
    return Image.fromarray(a.clip(0,255).astype(np.uint8))

for fn in sorted(os.listdir(SRC)):
    if not fn.endswith(".png"):
        continue
    src = Image.open(os.path.join(SRC, fn)).convert("RGBA")
    out = remove(src, session=session)
    out = corner_key(out)
    bbox = out.getbbox()
    if bbox:
        pad = 8
        l, t, r, b = bbox
        out = out.crop((max(0,l-pad), max(0,t-pad), min(out.width,r+pad), min(out.height,b+pad)))
    m = 256
    sc = min(m/out.width, m/out.height, 1.0)
    out = out.resize((max(1,int(out.width*sc)), max(1,int(out.height*sc))), Image.LANCZOS)
    path = os.path.join(DST, fn)
    out.save(path, optimize=True)
    print(fn, out.size, os.path.getsize(path)//1024, "KB")
print("DONE")
