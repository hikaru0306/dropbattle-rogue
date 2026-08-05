# -*- coding: utf-8 -*-
"""ウィンドウフレーム素材の後処理:
外周白フラッドフィル透過 → 中央の閉領域白をゲーム内装色(30,24,42)で塗る(境界の白AAも内側デフリンジで潰す)
→ 外周デフリンジ → bboxトリム → フル解像度で assets_ui_new/ へ。
border-image "slice fill" で紙ウィンドウと同方式・暗色内装のまま使える。
枠帯の実測厚(上/右/下/左)を出力して slice 決定に使う。
usage: python process_ui_windows.py [win_stone_953000.png ...]"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_ui_new")
os.makedirs(DST, exist_ok=True)

FILL = np.array([30, 24, 42], np.int16)   # rgba(30,24,42,.98) 相当
FILL_A = 250

def process(fn):
    img = Image.open(os.path.join(SRC, fn)).convert("RGB")
    a = np.array(img).astype(np.int16)
    hgt, wid = a.shape[:2]
    white = (a[:,:,0] >= 225) & (a[:,:,1] >= 225) & (a[:,:,2] >= 225)
    lab, n = ndimage.label(white)
    edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:,0], lab[:,-1]]))) - {0}
    alpha = np.full((hgt, wid), 255, np.uint8)
    center = np.zeros((hgt, wid), bool)
    sizes = ndimage.sum(white, lab, range(1, n+1)) if n else []
    for i in range(1, n+1):
        if i in edge_labels:
            alpha[lab == i] = 0
        elif sizes[i-1] > wid*hgt*0.02:
            center |= (lab == i)
        else:
            alpha[lab == i] = 0   # セグメント間の小さな白スリットは透過（隙間として見せる）
    # 中央閉領域まわりの白AAリング: centerに隣接する near-white を反復的に取り込む
    grow = center.copy()
    for _ in range(5):
        nb = ndimage.binary_dilation(grow) & ~grow
        add = nb & (a[:,:,0] >= 190) & (a[:,:,1] >= 190) & (a[:,:,2] >= 190) & (alpha == 255)
        if not add.any(): break
        grow |= add
    a[grow] = FILL
    alpha[grow] = FILL_A
    # 外周デフリンジ
    solid = alpha > 0
    edge = solid & ~(np.roll(solid,1,0) & np.roll(solid,-1,0) & np.roll(solid,1,1) & np.roll(solid,-1,1))
    whiteish = (a[:,:,0] >= 208) & (a[:,:,1] >= 208) & (a[:,:,2] >= 208)
    alpha = np.where(edge & whiteish, 0, alpha)
    out = Image.fromarray(np.dstack([a.clip(0,255).astype(np.uint8), alpha]), "RGBA")
    bbox = out.getbbox()
    if bbox:
        out = out.crop(bbox)
    path = os.path.join(DST, fn)
    out.save(path, optimize=True)
    # 枠帯厚の実測: 中央行/列で「不透過かつ内装色でない」画素が外から連続する幅
    oa = np.array(out)
    frame = (oa[:,:,3] > 0) & ~((oa[:,:,0] == 30) & (oa[:,:,1] == 24) & (oa[:,:,2] == 42))
    hh, ww = frame.shape
    def band(v):
        i = 0
        while i < len(v) and not v[i]: i += 1
        j = i
        while j < len(v) and v[j]: j += 1
        k = len(v)-1
        while k >= 0 and not v[k]: k -= 1
        m = k
        while m >= 0 and v[m]: m -= 1
        return j - i, k - m
    lw, rw = band(frame[hh//2]); tw, bw = band(frame[:, ww//2])
    print(f"{fn} size={out.size} band T{tw} R{rw} B{bw} L{lw}")

targets = [n if n.endswith(".png") else n+".png" for n in sys.argv[1:]] or [f for f in sorted(os.listdir(SRC)) if f.startswith("win_")]
for fn in targets:
    process(fn)
print("DONE")
