# -*- coding: utf-8 -*-
"""ステージ済み候補の内部透明穴を周囲色で埋め、白フリンジを除去する。
usage: python fix_holes.py <name.png> [more...]
対象: assets_cand/regenchk_<name>
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")

def fix(name):
    p = os.path.join(CAND, "regenchk_" + name)
    a = np.array(Image.open(p).convert("RGBA"))
    al = a[..., 3]
    solid = al > 200
    filled = ndimage.binary_fill_holes(solid)
    holes = filled & ~solid
    nfix = int(holes.sum())
    if nfix:
        # 最近傍の不透明画素の色で埋める
        idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
        for c in range(3):
            ch = a[..., c]
            ch[holes] = ch[idx[0][holes], idx[1][holes]]
        a[..., 3][holes] = 255
    # 輪郭付近の白フリンジ除去（半透明の白い縁）
    rgb = a[..., :3].astype(int)
    mx, mn = rgb.max(2), rgb.min(2)
    whitish = (mn >= 215) & ((mx - mn) <= 20)
    edge = (al > 0) & (al < 240)
    fr = whitish & edge
    nfr = int(fr.sum())
    if nfr:
        a[..., 3][fr] = 0
    Image.fromarray(a).save(p)
    print(f"{name}: holes_filled={nfix} fringe_cleared={nfr}")

for n in sys.argv[1:]:
    fix(n if n.endswith(".png") else n + ".png")
