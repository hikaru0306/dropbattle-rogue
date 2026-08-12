# -*- coding: utf-8 -*-
"""ChatGPT最終版ノア(noa_final.png)を hero4 差し替え用に整える。
背景が市松模様(疑似透過)の焼き込みRGBなので rembg(isnet-anime) で抜く。
→ トリム → 高さ512 で assets_cand/proc_noa_final.png
"""
import os
from PIL import Image
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
SRC = r"C:\Users\2000h\Downloads\noa_final.png"

session = new_session("isnet-anime")

im = Image.open(SRC).convert("RGBA")
cut = remove(im, session=session)
cut = cut.crop(cut.getbbox())
cut = cut.resize((round(cut.width * 512 / cut.height), 512), Image.LANCZOS)
p = os.path.join(CAND, "proc_noa_final.png")
cut.save(p)
print("->", p, cut.size)
