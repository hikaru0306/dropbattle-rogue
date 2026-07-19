# -*- coding: utf-8 -*-
"""ChatGPT加工版のガレス/ノアを差し替え用に整える。
背景がグレー/黒のグラデなので白フラッドフィルは使えず、rembg(isnet-anime)で抜く。
→ トリム → 高さ512 で assets_cand/proc2_hero3.png / proc2_hero4.png
"""
import os
from PIL import Image
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
DL = r"C:\Users\2000h\Downloads"

SRC = {
    "hero3": os.path.join(DL, "ChatGPT Image 2026年7月19日 23_58_03.png"),
    "hero4": os.path.join(DL, "ChatGPT Image 2026年7月19日 23_55_54.png"),
}

session = new_session("isnet-anime")

def trim_resize(im, h=512):
    im = im.crop(im.getbbox())
    w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)

for name, path in SRC.items():
    im = Image.open(path).convert("RGBA")
    cut = remove(im, session=session)
    out = trim_resize(cut)
    p = os.path.join(CAND, f"proc2_{name}.png")
    out.save(p)
    print("->", os.path.basename(p), out.size)
