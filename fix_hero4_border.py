# -*- coding: utf-8 -*-
"""ノア(hero4)の太いステッカー白フチを除去して他キャラと揃える。
元画像は「キャラ → 太い白帯 → 細い黒縁 → 背景白」の順。
背景白のフラッドフィルだけでは黒縁で止まり白帯が残るので、
アルファを外側から N px 収縮させて 黒縁＋白帯 を剥がす。
出力: assets_cand/proc_hero4_fix{N}.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
SRC = os.path.join(CAND, "pick_hero4.png")

def unmat_white(im):
    a = np.array(im).astype(np.float64)
    al = a[..., 3:4] / 255.0
    rgb = a[..., :3]
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(al > 0, (rgb - (1 - al) * 255.0) / np.maximum(al, 1e-6), rgb)
    a[..., :3] = np.clip(out, 0, 255)
    return Image.fromarray(a.astype(np.uint8))

def cut_white_flood(im):
    a = np.array(im)
    white = (a[..., 0] >= 225) & (a[..., 1] >= 225) & (a[..., 2] >= 225)
    lab, n = ndimage.label(white)
    border = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    border.discard(0)
    bg = np.isin(lab, list(border))
    a[..., 3] = np.where(bg, 0, 255).astype(np.uint8)
    return a

def erode_alpha(a, n):
    """アルファを n px 収縮（黒縁＋白帯を外側から剥がす）"""
    mask = a[..., 3] > 128
    mask = ndimage.binary_erosion(mask, iterations=n)
    a = a.copy()
    a[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    return a

def trim_resize(im, h=512):
    im = im.crop(im.getbbox())
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

im = Image.open(SRC).convert("RGBA")
base = cut_white_flood(im)
for n in [int(x) for x in (sys.argv[1:] or [8, 12, 16])]:
    a = erode_alpha(base, n)
    # 収縮後の境界を1px だけぼかして階段を消す
    alpha = Image.fromarray(a[..., 3]).filter(ImageFilter.GaussianBlur(0.8))
    a[..., 3] = np.array(alpha)
    out = trim_resize(unmat_white(Image.fromarray(a)))
    p = os.path.join(CAND, f"proc_hero4_fix{n}.png")
    out.save(p)
    print("->", os.path.basename(p), out.size)
