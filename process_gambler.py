# -*- coding: utf-8 -*-
"""ギャンブラー一式の仕上げ（system python: rembg 2.0.69 / isnet-anime）
  hero7   : assets_cand/hero7_a.png -> rembg+corner_key -> 高さ512 -> assets/hero7.png
                                     -> 768原画を assets_raw/hero7.png へ
  coins   : assets_raw_ui/coin_*_b   -> 白フラッドフィル透過 -> 384角の対称ペア -> assets/coin_{angel,demon}.png
  icons   : mk_chip / rl_*           -> 白フラッドフィル透過 -> 96px（mk_ore等と同規格）-> assets/*.png
"""
import os, shutil
import numpy as np
from PIL import Image, ImageFilter
from collections import deque
from rembg import remove, new_session

ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
RAWUI = os.path.join(ROOT, "assets_raw_ui")
RAW = os.path.join(ROOT, "assets_raw")
DST = os.path.join(ROOT, "assets")
os.makedirs(RAW, exist_ok=True)

# ---------- hero: rembg isnet-anime + 四隅キー（process_assets.py 踏襲） ----------
def corner_key(img, thresh=28):
    a = np.array(img).astype(np.int16)
    h, w = a.shape[:2]
    corners = [a[2,2,:3], a[2,w-3,:3], a[h-3,2,:3], a[h-3,w-3,:3]]
    for c in corners:
        d = np.abs(a[:,:,:3] - c).sum(axis=2)
        a[:,:,3] = np.where((d < thresh) & (a[:,:,3] > 0), 0, a[:,:,3])
    return Image.fromarray(a.clip(0,255).astype(np.uint8))

def process_hero(src_name, out_name, h=512):
    src = Image.open(os.path.join(CAND, src_name)).convert("RGBA")
    shutil.copyfile(os.path.join(CAND, src_name), os.path.join(RAW, out_name))  # 768原画保存
    session = new_session("isnet-anime")
    out = remove(src, session=session)
    out = corner_key(out)
    bbox = out.getbbox()
    if bbox:
        pad = 8; l,t,r,b = bbox
        out = out.crop((max(0,l-pad), max(0,t-pad), min(out.width,r+pad), min(out.height,b+pad)))
    w = round(out.width * h / out.height)
    out = out.resize((w, h), Image.LANCZOS)
    out.save(os.path.join(DST, out_name), optimize=True)
    print("hero ->", out_name, out.size)

# ---------- icons/coins: 白フラッドフィル透過（process_ui.py 踏襲） ----------
def keyout(img, wth=225):
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

def defringe(img):
    a = np.array(img)
    alpha = a[:,:,3]; solid = alpha > 0
    edge = solid & ~(np.roll(solid,1,0) & np.roll(solid,-1,0) & np.roll(solid,1,1) & np.roll(solid,-1,1))
    whiteish = (a[:,:,0] >= 208) & (a[:,:,1] >= 208) & (a[:,:,2] >= 208)
    a[:,:,3] = np.where(edge & whiteish, 0, alpha)
    return Image.fromarray(a)

def trim(img, pad=6):
    out = defringe(keyout(img))
    bbox = out.getbbox()
    if bbox:
        l,t,r,b = bbox
        out = out.crop((max(0,l-pad), max(0,t-pad), min(out.width,r+pad), min(out.height,b+pad)))
    return out

def process_icon(src_name, out_name, m=96):
    out = trim(Image.open(os.path.join(RAWUI, src_name)))
    sc = min(m/out.width, m/out.height, 1.0)
    out = out.resize((max(1,int(out.width*sc)), max(1,int(out.height*sc))), Image.LANCZOS)
    out.save(os.path.join(DST, out_name), optimize=True)
    print("icon ->", out_name, out.size)

def process_coin(src_name, out_name, canvas=384, fill=0.94):
    """対称ペア用: トリム後、正方キャンバス中央に同一直径で配置"""
    out = trim(Image.open(os.path.join(RAWUI, src_name)), pad=2)
    m = int(canvas * fill)
    sc = min(m/out.width, m/out.height)
    out = out.resize((max(1,int(out.width*sc)), max(1,int(out.height*sc))), Image.LANCZOS)
    c = Image.new("RGBA", (canvas, canvas), (0,0,0,0))
    c.alpha_composite(out, ((canvas-out.width)//2, (canvas-out.height)//2))
    c.save(os.path.join(DST, out_name), optimize=True)
    print("coin ->", out_name, c.size)

if __name__ == "__main__":
    process_hero("hero7_a.png", "hero7.png")
    process_coin("coin_angel_b.png", "coin_angel.png")
    process_coin("coin_demon_b.png", "coin_demon.png")
    process_icon("mk_chip.png", "mk_chip.png", 96)
    process_icon("rl_luckcoin.png", "rl_luckcoin.png", 96)
    process_icon("rl_devilpact.png", "rl_devilpact.png", 96)
    process_icon("rl_angelfeather.png", "rl_angelfeather.png", 96)
    print("DONE")
