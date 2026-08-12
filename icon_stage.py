# -*- coding: utf-8 -*-
"""ChatGPT生出力(<name>_regen.png in ~/Downloads)を assets_regen_raw/<name>.png へ取り込み、
元assetsとの比較画像を cmp/ に作る。applyはしない（検品後に apply_minimal.py）。
usage: python icon_stage.py <name> [name...]
"""
import os, sys, shutil, glob
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
DL = os.path.expanduser("~/Downloads")
RAW = os.path.join(ROOT, "assets_regen_raw")
ASSETS = os.path.join(ROOT, "assets")
CMP = os.path.join(ROOT, "cmp_icon")
os.makedirs(RAW, exist_ok=True)
os.makedirs(CMP, exist_ok=True)

def checker(sz=64, c1=(200,200,200), c2=(245,245,245)):
    im = Image.new("RGB", (sz, sz), c1)
    px = im.load()
    for y in range(sz):
        for x in range(sz):
            if (x//8 + y//8) % 2 == 0:
                px[x, y] = c2
    return im

def on_checker(im, box=256):
    im = im.convert("RGBA")
    im.thumbnail((box, box), Image.LANCZOS)
    bg = checker().resize((box, box), Image.NEAREST).convert("RGBA")
    x = (box - im.width)//2; y = (box - im.height)//2
    bg.alpha_composite(im, (x, y))
    return bg.convert("RGB")

def stage(name):
    # Chromeは同名回避で "<name>_regen (1).png" 等を作るので最新mtimeを採用
    cands = glob.glob(os.path.join(DL, name + "_regen*.png"))
    if not cands:
        raise FileNotFoundError(name + "_regen*.png")
    dl = max(cands, key=os.path.getmtime)
    raw = os.path.join(RAW, name + ".png")
    shutil.copy(dl, raw)
    # 取り込んだら重複を掃除（次回の(n)付与を防ぐ）
    for c in cands:
        os.remove(c)
    old = Image.open(os.path.join(ASSETS, name + ".png"))
    new = Image.open(raw)
    from PIL import ImageDraw, ImageFont
    box = 256
    canvas = Image.new("RGB", (box*2, box+24), (255,255,255))
    canvas.paste(on_checker(old, box), (0, 24))
    canvas.paste(on_checker(new, box), (box, 24))
    d = ImageDraw.Draw(canvas)
    d.text((4,4), name+"  [OLD]", fill=(0,0,0))
    d.text((box+4,4), "[NEW]", fill=(180,0,0))
    canvas.save(os.path.join(CMP, name + ".png"))
    print(f"staged {name}: old{old.size} new{new.size}")

for n in sys.argv[1:]:
    stage(n.replace(".png", ""))
