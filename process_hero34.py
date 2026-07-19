# -*- coding: utf-8 -*-
"""ガレス/ノア新画像の仕上げ: 外周の白をフラッドフィルで透過 → 白アンマット → トリム → 高さ512
使い方: python process_hero34.py hero3_a2 hero3   (assets_cand/hero3_a2.png → assets_cand/proc_hero3.png)
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")

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
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    mask = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1))
    a[..., 3] = np.array(mask)
    return unmat_white(Image.fromarray(a))

def trim_resize(im, h=512):
    im = im.crop(im.getbbox())
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

src_name, dst = sys.argv[1], sys.argv[2]
im = Image.open(os.path.join(CAND, src_name + ".png")).convert("RGBA")
out = trim_resize(cut_white_flood(im))
out.save(os.path.join(CAND, f"proc_{dst}.png"))
print("->", f"proc_{dst}.png", out.size)
