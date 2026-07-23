# -*- coding: utf-8 -*-
"""ChatGPT生出力を最小限（トリム＋リサイズのみ）でassetsへ適用する。
穴埋め・フリンジ除去・rembgなどの余計な加工は一切しない。
アルファが無い画像だけ、外周から連結する白系背景を透明化する（透過にするため必須）。
usage: python apply_minimal.py <name> [name...]
src: assets_regen_raw/<name>.png  ->  assets/<name>.png
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(ROOT, "assets_regen_raw")
ASSETS = os.path.join(ROOT, "assets")

def apply(name):
    src = os.path.join(RAW, name + ".png")
    dst = os.path.join(ASSETS, name + ".png")
    im = Image.open(src).convert("RGBA")
    a = np.array(im)
    note = "as-is"
    if a[..., 3].min() >= 250:
        # 透過なし → 外周連結の白背景のみ透明化
        from scipy import ndimage
        rgb = a[..., :3].astype(int)
        mn, mx = rgb.min(2), rgb.max(2)
        bgish = (mn >= 225) & ((mx - mn) <= 14)
        lbl, n = ndimage.label(bgish)
        edge = set(lbl[0, :]) | set(lbl[-1, :]) | set(lbl[:, 0]) | set(lbl[:, -1])
        edge.discard(0)
        bg = np.isin(lbl, list(edge))
        a[..., 3][bg] = 0
        im = Image.fromarray(a)
        note = f"bgcut({int(bg.sum())}px)"
    bb = im.getbbox()
    im = im.crop(bb)
    tgt_max = max(Image.open(dst).size)
    s = tgt_max / max(im.size)
    im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    im.save(dst)
    print(f"{name:10s} {note:16s} -> {im.size}")

for n in sys.argv[1:]:
    apply(n.replace(".png", ""))
