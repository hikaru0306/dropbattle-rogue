# -*- coding: utf-8 -*-
"""hero8（調律師カノン）の等身を少しだけ下げる: 頭・顔・肩はそのまま、
コートの裾から下（脚）だけを縦に圧縮して再合成する。
SDで作り直すと承認済みのデザインが保てないので、画像手術で等身だけ動かす
（make_hero7_squash.py と同じ手法。係数を変えれば任意の等身にできる）。
usage: python make_hero8_squash.py            → 候補を assets_cand/ に出して比較シートを作る
       python make_hero8_squash.py 0.86       → その係数で assets/hero8.png を直接更新
"""
from PIL import Image, ImageDraw
import os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets", "hero8.png")
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# カット位置: 図像の上から62%（コートの裾のあたり。顔・胸元・両手はすべて上側に残る）
CUT_AT = 0.62


def squash(im, factor):
    W, H = im.size
    x0, y0, x1, y1 = im.getbbox()
    fh = y1 - y0
    cut = y0 + int(fh * CUT_AT)
    top = im.crop((0, 0, W, cut))
    bottom = im.crop((0, cut, W, y1))
    bh = max(1, int(bottom.height * factor))
    bottom_sq = bottom.resize((W, bh), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 継ぎ目対策: 縮めた下半身を3px上に食い込ませ、その上に上半身を被せる
    canvas.alpha_composite(bottom_sq, (0, cut - 3))
    canvas.alpha_composite(top, (0, 0))
    # 再クロップ → 高さ512で正規化（頭が相対的に大きくなる＝等身が下がる）
    fig = canvas.crop(canvas.getbbox())
    sc = 512 / fig.height
    return fig.resize((max(1, int(fig.width * sc)), 512), Image.LANCZOS)


src = Image.open(SRC).convert("RGBA")

if len(sys.argv) > 1:
    f = float(sys.argv[1])
    out = squash(src, f)
    src.save(os.path.join(CAND, "hero8_prev_tall.png"))   # 元の等身を退避
    out.save(SRC, optimize=True)
    print("applied", f, "->", out.size)
    sys.exit(0)

variants = {"a": 0.90, "b": 0.84, "c": 0.78}
for name, f in variants.items():
    out = squash(src, f)
    out.save(os.path.join(CAND, f"hero8s_{name}.png"))
    print(name, f, "->", out.size)

# 比較シート（同じ高さに揃えて並べる＝頭の大きさの差がそのまま等身差に見える）
cells = [("REF", src)] + [(f"{k} x{v}", Image.open(os.path.join(CAND, f"hero8s_{k}.png"))) for k, v in variants.items()]
DH, pad = 460, 20
tiles = [(lb, img.resize((int(img.width * DH / img.height), DH), Image.LANCZOS)) for lb, img in cells]
tw = sum(t.width for _, t in tiles) + pad * (len(tiles) + 1)
sheet = Image.new("RGB", (tw, DH + pad * 2 + 20), (235, 233, 230))
d = ImageDraw.Draw(sheet)
x = pad
for lb, t in tiles:
    sheet.paste(t, (x, pad + 20), t)
    d.text((x, 6), lb, fill=(60, 60, 60))
    x += t.width + pad
sheet.save(os.path.join(CAND, "_canon_squash.png"))
print("SHEET_DONE")
