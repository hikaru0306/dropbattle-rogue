# -*- coding: utf-8 -*-
"""ユーザー提供のChatGPT出力（暗背景＋グロー）をヒーロー画像に仕上げる汎用スクリプト
  rembg isnet-anime で切り抜き → 外周グロー除去 → トリム → 高さ512
使い方: python process_hero_cg.py <出力名> <入力PNGパス> [--flip]
  例) python process_hero_cg.py hero5 "C:\\Users\\2000h\\Downloads\\ChatGPT Image ....png"
出力: assets_cand/proc_<出力名>_cg.png（確認後に assets/<出力名>.png へコピー）
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

def clean_glow(im, hard=200, soft=40):
    """外周グローの半透明画素を除去。輪郭AA(本体に隣接する中間alpha)は残す"""
    a = np.array(im)
    alpha = a[..., 3]
    core = alpha >= hard
    near = ndimage.binary_dilation(core, iterations=2)
    kill = (~near & (alpha < hard)) | (alpha < soft)
    a[kill, 3] = 0
    return Image.fromarray(a)

def trim_resize(im, h=512):
    im = im.crop(im.getbbox())
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

name, src = sys.argv[1], sys.argv[2]
flip = "--flip" in sys.argv
im = Image.open(src).convert("RGBA")
if flip:
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
out = trim_resize(clean_glow(remove(im, session=new_session("isnet-anime"))))
dst = os.path.join(CAND, f"proc_{name}_cg{'_flip' if flip else ''}.png")
out.save(dst)
print("->", os.path.basename(dst), out.size)
