# -*- coding: utf-8 -*-
"""hero7（賭博師）の低等身化: 頭〜襟〜手はそのまま、コート下部〜脚だけ縦に圧縮して再合成"""
from PIL import Image
import os

SRC = r"C:\Users\2000h\Downloads\dropbattle-rogue\assets\hero7.png"  # 376x512 透過（基準画像処理済み）
OUT = r"C:\Users\2000h\Downloads\dropbattle-rogue\assets_cand"

im = Image.open(SRC).convert("RGBA")
W, H = im.size
bbox = im.getbbox()
x0, y0, x1, y1 = bbox
fh = y1 - y0  # 図像の高さ

# カット位置: 図像の上から58%（ボタン列の下・コートの広がり始め。手とコインは上側に残る）
cut = y0 + int(fh * 0.58)

variants = {"a": 0.80, "b": 0.72, "c": 0.64}
for name, f in variants.items():
    top = im.crop((0, 0, W, cut))
    bottom = im.crop((0, cut, W, y1))
    bh = int(bottom.height * f)
    bottom_sq = bottom.resize((W, bh), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 継ぎ目対策: 縮めた下半身を3px上に食い込ませて置き、その上に上半身を被せる
    canvas.alpha_composite(bottom_sq, (0, cut - 3))
    canvas.alpha_composite(top, (0, 0))
    # 再クロップ→高さ512で正規化（頭が相対的に大きくなる＝低等身）
    nb = canvas.getbbox()
    fig = canvas.crop(nb)
    scale = 512 / fig.height
    fig = fig.resize((int(fig.width * scale), 512), Image.LANCZOS)
    fig.save(os.path.join(OUT, f"hero7s_{name}.png"))
    print(name, f, "->", fig.size)

# 比較シート: 元(左端) + 3案、同じ高さで並べる（頭の大きさの違い＝等身差が見える）
cells = [("REF", Image.open(SRC).convert("RGBA"))]
for name in variants:
    cells.append((f"s_{name} x{variants[name]}", Image.open(os.path.join(OUT, f"hero7s_{name}.png"))))
DH = 480
pad = 20
tiles = []
for label, img in cells:
    s = DH / img.height
    tiles.append((label, img.resize((int(img.width * s), DH), Image.LANCZOS)))
tw = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
sheet = Image.new("RGB", (tw, DH + pad * 2 + 20), (235, 233, 230))
x = pad
from PIL import ImageDraw
d = ImageDraw.Draw(sheet)
for label, t in tiles:
    sheet.paste(t, (x, pad + 20), t)
    d.text((x, 6), label, fill=(60, 60, 60))
    x += t.width + pad
sheet.save(os.path.join(OUT, "_gambler9_squash.png"))
print("SHEET_DONE")
