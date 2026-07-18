# -*- coding: utf-8 -*-
"""イリス新画像(hero2_g5)の仕上げ:
  左右反転（右向きにする）→ 外周の白をフラッドフィルで透過 → 白アンマット → トリム → 高さ512
出力: assets_cand/proc_hero2.png（目視確認後に assets/hero2.png へコピー）
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
SRC = os.path.join(CAND, "hero2_g5.png")

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

im = Image.open(SRC).convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)  # 右向きに
out = trim_resize(cut_white_flood(im))
out.save(os.path.join(CAND, "proc_hero2.png"))
print("-> proc_hero2.png", out.size)
