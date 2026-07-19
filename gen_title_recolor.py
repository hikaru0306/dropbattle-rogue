# -*- coding: utf-8 -*-
"""タイトル画のアルドを新デザイン(assets/hero.png)の配色に合わせる。
   背景・構図・線は一切触らず、キャラと杖の色相/彩度/明度だけを写像する。"""
from PIL import Image
import numpy as np
from scipy import ndimage as ndi

SRC = 'assets/bg_title2.jpg'
im = Image.open(SRC).convert('RGB')
a = np.array(im).astype(np.float32) / 255

def rgb2hsv(x):
    mx = x.max(-1); mn = x.min(-1); d = mx - mn + 1e-9
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    h = np.where(mx == r, (g - b) / d % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx

def hsv2rgb(h, s, v):
    h = h % 360
    c = v * s; x = c * (1 - abs((h / 60) % 2 - 1)); m = v - c
    z = np.zeros_like(h)
    r, g, b = [np.select(
        [h < 60, h < 120, h < 180, h < 240, h < 300, h < 361],
        pick) for pick in ([c, x, z, z, x, c], [x, c, c, x, z, z], [z, z, x, c, c, x])]
    return np.stack([r + m, g + m, b + m], -1)

h, s, v = rgb2hsv(a)
H, W = h.shape
Y, X = np.mgrid[0:H, 0:W]
out = a.copy()

char = (Y > 690) & (Y < 1000) & (X > 100) & (X < 345)   # キャラ+杖のいる範囲だけ触る

# --- 杖（連結成分で川の黄色と切り分ける） ---
orn = (h > 5) & (h < 52) & (s > 0.25) & (v > 0.2)
lab, n = ndi.label(orn, structure=np.ones((3, 3)))
staff = np.zeros_like(orn)
for i, sl in enumerate(ndi.find_objects(lab)):
    if sl is None: continue
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    if x1 < 345 and y0 > 690 and y1 < 1010 and (lab[sl] == i + 1).sum() > 100:
        staff |= (lab == i + 1)

# --- 宝珠（杖の頭の中の紫）→ オレンジ ---
head = staff.copy(); head[:700] = False; head[790:] = False
head = ndi.binary_dilation(head, np.ones((9, 9)))
gembox = (Y > 746) & (Y < 770) & (X > 288) & (X < 314)   # 杖頭の宝珠の位置
gem = gembox & (h > 240) & (h < 345) & (s > 0.08)
gem = ndi.binary_dilation(gem, np.ones((3, 3))) & gembox & (h > 235) & (h < 350)

# --- ローブ・帽子の紫 ---
robe = char & (h > 260) & (h < 345) & (s > 0.25) & (v > 0.12) & ~gem

# --- 縁取りのクリーム色（キャラに接している明るい黄白のみ） ---
near = ndi.binary_dilation(robe | staff, np.ones((7, 7)))
trim = char & near & (h > 30) & (h < 75) & (s < 0.5) & (v > 0.72)

def put(mask, nh, ns, nv):
    out[mask] = hsv2rgb(nh, ns, nv)[mask]

# ローブ: マゼンタ寄り紫 → 深い紫（陰影の差は relative に保つ）
put(robe, 271 + (h - 291) * 0.40, np.clip(s * 0.86, 0, 1), np.clip(v * 0.80, 0, 1))
# 縁取り: クリーム → 金
put(trim, 45 + (h - 52) * 0.2, np.clip(s + 0.42, 0, 0.85), np.clip(v * 0.95, 0, 1))
# 杖: フックは金（明部 H45 S.65）、暗部は茶（H29 S.92）。オレンジなのは玉だけ
# 元絵の杖の影は赤茶(H≈4)で、上の連結成分から漏れるので拾い直して茶に寄せる
staff_area = ndi.binary_dilation(staff, np.ones((3, 3)))
shadow = staff_area & ((h < 14) | (h > 350)) & (s > 0.5) & (v < 0.68) & ~gem
shadow = ndi.binary_opening(shadow, np.ones((2, 2)))   # 輪郭のノイズ画素は拾わない
staff = staff | shadow
bright = staff & (v > 0.62) & ~shadow
dark = staff & ~bright & ~gem & ~shadow
put(bright, 45 + (h - 31) * 0.10, np.clip(s * 0.9 + 0.05, 0, 0.72), np.clip(v * 0.99, 0, 1))  # フック明部 H45 S.65
put(dark, 30 + (h - 31) * 0.15, np.clip(s * 0.85, 0, 0.90), np.clip(v * 1.10, 0, 1))  # 中間は茶
put(shadow, 22 + (h % 360) * 0.02, np.clip(s * 0.92, 0, 0.95), np.clip(v * 1.02, 0, 1))  # 影は赤茶→茶（陰影の濃さは保つ）
# 宝珠: 紫 → オレンジ
put(gem, 30 + (h - 291) * 0.02, np.clip(s * 0.4 + 0.62, 0, 0.98), np.clip(v * 1.02, 0, 1))  # 玉 H30 S.98 の鮮やかなオレンジ

res = Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8))
res.save('C:/Users/2000h/AppData/Local/Temp/claude/C--Users-2000h/6e683fee-60ab-4cca-8a76-c38cb64292b9/scratchpad/title_new.jpg', quality=95, subsampling=0)
res.crop((80, 650, 420, 1000)).resize((680, 700), Image.LANCZOS).save('C:/Users/2000h/AppData/Local/Temp/claude/C--Users-2000h/6e683fee-60ab-4cca-8a76-c38cb64292b9/scratchpad/title_new_crop.png')
print('masks: robe=%d trim=%d staff=%d gem=%d' % (robe.sum(), trim.sum(), staff.sum(), gem.sum()))
