# -*- coding: utf-8 -*-
"""v80 ヒーロー画像一括差し替えの前処理
- ChatGPT再出力5枚（暗背景+グロー）→ rembg isnet-anime → 低alphaグロー除去 → トリム → 高さ512
- hero5新デザイン（G案・白背景）→ 外周白フラッドフィル → フェザー → 白アンマット → トリム → 高さ512
出力は assets_cand/proc_*.png（目視確認後に assets/ へコピー）
"""
import os
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
DL = r"C:\Users\2000h\Downloads"
os.makedirs(CAND, exist_ok=True)

CHATGPT = {
    "hero":  "ChatGPT Image 2026年7月17日 17_46_14.png",  # アルド
    "hero2": "ChatGPT Image 2026年7月17日 17_48_40.png",  # イリス
    "hero3": "ChatGPT Image 2026年7月17日 17_57_10.png",  # ガレス
    "hero4": "ChatGPT Image 2026年7月17日 18_05_44.png",  # ノア
    "hero6": "ChatGPT Image 2026年7月17日 18_01_14.png",  # ブロム
}

def trim_resize(im, h=512):
    bbox = im.getbbox()
    im = im.crop(bbox)
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

def clean_glow(im, hard=200, soft=40):
    """外周グローの半透明画素を除去。輪郭AA(本体に隣接する中間alpha)は残す:
    alpha>=hard を本体とし、本体を2px膨張した範囲外の alpha<hard を全部消す。範囲内は alpha<soft のみ消す"""
    a = np.array(im)
    alpha = a[..., 3]
    core = alpha >= hard
    near = ndimage.binary_dilation(core, iterations=2)
    kill = (~near & (alpha < hard)) | (alpha < soft)
    a[kill, 3] = 0
    return Image.fromarray(a)

def unmat_white(im):
    a = np.array(im).astype(np.float64)
    al = a[..., 3:4] / 255.0
    rgb = a[..., :3]
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(al > 0, (rgb - (1 - al) * 255.0) / np.maximum(al, 1e-6), rgb)
    a[..., :3] = np.clip(out, 0, 255)
    return Image.fromarray(a.astype(np.uint8))

def cut_white_flood(path):
    """白背景素材: 外周に繋がる白(>=225)を背景として除去"""
    im = Image.open(path).convert("RGBA")
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

print("== hero5 (G案・白背景フラッドフィル) ==", flush=True)
g = cut_white_flood(os.path.join(CAND, "hero5_new_g.png"))
trim_resize(g).save(os.path.join(CAND, "proc_hero5.png"))
print("-> proc_hero5.png", flush=True)

print("== ChatGPT 5枚 (rembg isnet-anime) ==", flush=True)
sess = new_session("isnet-anime")
for name, fn in CHATGPT.items():
    im = Image.open(os.path.join(DL, fn)).convert("RGBA")
    out = remove(im, session=sess)
    out = clean_glow(out)
    out = trim_resize(out)
    out.save(os.path.join(CAND, f"proc_{name}.png"))
    print(f"-> proc_{name}.png {out.size}", flush=True)
print("ALL_DONE")
