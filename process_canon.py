# -*- coding: utf-8 -*-
"""assets_raw_canon/ を仕上げて assets_cand/canon_*.png に出す（確認後 assets/ へコピー）
  白背景フラッドフィル透過 → 白フチのデフリンジ → 閉領域の白除去 → アルファ境界トリム
  hero8 は高さ512、mk_/rl_ は 96px（既存アイコンと同じ規格）
usage: python process_canon.py [name ...]
"""
import os, sys
import numpy as np
from PIL import Image
from collections import deque
from scipy import ndimage

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "assets_raw_canon")
DST = os.path.join(ROOT, "assets_cand")
os.makedirs(DST, exist_ok=True)

def keyout(img, wth=225):
    """外周から繋がった白だけを透過（本体内部の白＝目/ハイライトは守る）"""
    a = np.array(img.convert("RGB")).astype(np.int16)
    hgt, wid = a.shape[:2]
    white = (a[:,:,0] >= wth) & (a[:,:,1] >= wth) & (a[:,:,2] >= wth)
    bg = np.zeros((hgt, wid), bool)
    dq = deque()
    for x in range(wid):
        for y in (0, hgt-1):
            if white[y,x] and not bg[y,x]: bg[y,x] = True; dq.append((y,x))
    for y in range(hgt):
        for x in (0, wid-1):
            if white[y,x] and not bg[y,x]: bg[y,x] = True; dq.append((y,x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
            if 0 <= ny < hgt and 0 <= nx < wid and white[ny,nx] and not bg[ny,nx]:
                bg[ny,nx] = True; dq.append((ny,nx))
    return Image.fromarray(np.dstack([a.clip(0,255).astype(np.uint8),
        np.where(bg, 0, 255).astype(np.uint8)]), "RGBA")

def defringe(im):
    a = np.array(im)
    alpha = a[:,:,3]
    solid = alpha > 0
    edge = solid & ~(np.roll(solid,1,0) & np.roll(solid,-1,0) & np.roll(solid,1,1) & np.roll(solid,-1,1))
    whiteish = (a[:,:,0] >= 208) & (a[:,:,1] >= 208) & (a[:,:,2] >= 208)
    a[:,:,3] = np.where(edge & whiteish, 0, alpha)
    return Image.fromarray(a)

def kill_closed_white(im, wth=246, minarea=40):
    """足の隙間など閉領域に残った純白を面積ベースで除去（小さい白＝目/牙は残す）"""
    a = np.array(im)
    pure = (a[:,:,0] >= wth) & (a[:,:,1] >= wth) & (a[:,:,2] >= wth) & (a[:,:,3] > 0)
    lab, n = ndimage.label(pure)
    if n:
        for i in range(1, n+1):
            m = lab == i
            if m.sum() >= minarea: a[:,:,3][m] = 0
    return Image.fromarray(a)

def trim(im, pad=1):
    """アルファ境界でタイトにトリム＋1px余白（今回のアイコンサイズ統一と同じ規格）"""
    bb = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bb: return im
    c = im.crop(bb)
    out = Image.new("RGBA", (c.width + pad*2, c.height + pad*2), (0,0,0,0))
    out.paste(c, (pad, pad))
    return out

targets = [n if n.endswith(".png") else n + ".png" for n in sys.argv[1:]] or sorted(os.listdir(SRC))
for fn in targets:
    if not fn.endswith(".png"): continue
    src = os.path.join(SRC, fn)
    if not os.path.exists(src): print("missing", fn); continue
    im = keyout(Image.open(src))
    im = defringe(im)
    im = kill_closed_white(im)
    im = trim(im)
    name = fn[:-4]
    if name.startswith("hero"):
        sc = 512 / im.height
        im = im.resize((max(1,int(im.width*sc)), 512), Image.LANCZOS)
    else:
        m = 96
        sc = min(m/im.width, m/im.height, 1.0)
        im = im.resize((max(1,int(im.width*sc)), max(1,int(im.height*sc))), Image.LANCZOS)
    path = os.path.join(DST, "canon_" + fn)
    im.save(path, optimize=True)
    print(fn, im.size, os.path.getsize(path)//1024, "KB")
print("DONE")
