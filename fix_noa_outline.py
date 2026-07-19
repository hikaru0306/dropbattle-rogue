# -*- coding: utf-8 -*-
"""ノア(hero4)のステッカー白フチを、アンチエイリアスを保ったまま除去する。
前回の失敗: 二値 erosion でアルファを削り、境界がガビガビになった。
今回: 「白帯 + その外側の黒縁」をマスクとして検出し、マスクをぼかして
      アルファに連続値で掛ける（0/255 の二値化をしない）。
出力: assets_cand/proc6_hero4_d{D}.png
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
SRC = os.path.join(CAND, "proc2_hero4.png")   # rembg 済み・白フチ付き

def build(depth):
    a = np.array(Image.open(SRC).convert("RGBA")).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3]
    solid = alpha > 32

    # 輪郭からの距離（外周付近だけを対象にして、内部の白い手袋や毛を守る）
    dist = ndimage.distance_transform_edt(solid)
    outer = solid & (dist <= depth)

    mx, mn = rgb.max(axis=2), rgb.min(axis=2)
    whitish = (mn >= 150) & ((mx - mn) <= 45)      # 白帯（実測 mn≈180）
    darkish = mx <= 95                              # 白帯の外側の黒縁

    # 実測: 最外 0-3px が黒縁、その内側 3-6px が白帯、6px 以降がキャラ本体。
    # 最外の黒縁を種に、白帯まで連結を伸ばす。depth を薄く保つことでキャラ本来の
    # 黒線（もっと内側にある）へは伝播しない。
    seed = solid & darkish & (dist <= 2.5)
    band = ndimage.binary_propagation(seed, mask=outer & (darkish | whitish))

    # 二値化せずマスクをぼかして連続値で抜く → 階段状のジャギーを避ける
    m = ndimage.binary_dilation(band, iterations=1).astype(np.float32)
    m = np.array(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0

    a[..., 3] = np.clip(alpha * (1.0 - m), 0, 255)
    out = Image.fromarray(a.astype(np.uint8))
    out = out.crop(out.getbbox())
    out = out.resize((round(out.width * 512 / out.height), 512), Image.LANCZOS)
    p = os.path.join(CAND, f"proc6_hero4_d{depth}.png")
    out.save(p)
    print("->", os.path.basename(p), out.size)

for d in [int(x) for x in (sys.argv[1:] or [10, 16])]:
    build(d)
