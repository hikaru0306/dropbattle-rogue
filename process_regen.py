# -*- coding: utf-8 -*-
"""ChatGPT再出力画像を検品用にステージする（即差し替えはしない）。
usage:
  python process_regen.py stage <asset_name.png> <downloaded_path>
      → assets_cand/regenchk_<name> に整形済み候補、assets_cand/cmp_<name> に新旧比較画像
  python process_regen.py apply <asset_name.png>
      → 検品OK後に assets/ へ差し替え（元は assets_backup_pre_chatgpt/ に退避）
- 偽透過(市松焼き込みRGB)なら rembg(isnet-anime) で抜く
- トリム → 元アセットの最大辺に合わせて縮小
"""
import os, sys, shutil
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
mode, name = sys.argv[1], sys.argv[2]
asset = os.path.join(ROOT, "assets", name)
backup = os.path.join(ROOT, "assets_backup_pre_chatgpt", name)
staged = os.path.join(CAND, "regenchk_" + name)

if mode == "apply":
    if not os.path.exists(backup):
        shutil.copy2(asset, backup)
    shutil.copy2(staged, asset)
    print("applied ->", asset)
    sys.exit(0)

src = sys.argv[3]
im = Image.open(src).convert("RGBA")
a = np.array(im.getchannel("A"))
if not (a.min() < 128):
    from rembg import remove, new_session
    im = remove(im, session=new_session("isnet-anime"))
    note = "rembg"
else:
    note = "alpha"

im = im.crop(im.getbbox())
orig_src = backup if os.path.exists(backup) else asset
orig = Image.open(orig_src).convert("RGBA")
target_max = max(orig.size)
scale = target_max / max(im.size)
im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.LANCZOS)
im.save(staged)
shutil.copy2(src, os.path.join(ROOT, "assets_regen_raw", name))

# 新旧比較画像（グレー背景に 旧|新）
H = 256
def fit(x):
    s = H / max(x.size)
    return x.resize((max(1, round(x.width * s)), max(1, round(x.height * s))), Image.LANCZOS)
o, n = fit(orig), fit(im)
W = o.width + n.width + 30
sheet = Image.new("RGBA", (W, H + 20), (128, 128, 128, 255))
sheet.paste(o, (5, 10), o)
sheet.paste(n, (o.width + 25, 10), n)
cmp_p = os.path.join(CAND, "cmp_" + name)
sheet.convert("RGB").save(cmp_p)
print(f"staged ({note}) -> {staged} {im.size} | cmp -> {cmp_p}")
