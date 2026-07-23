# -*- coding: utf-8 -*-
"""ベースアイコンを色相変換して色違いバリアントを作る（numpyのみ）。
usage: python recolor_variant.py <base.png> <target.png>
"""
import os, sys, shutil
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
base_name, target_name = sys.argv[1], sys.argv[2]

def rgb_to_hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    h = np.zeros_like(mx)
    m = d > 1e-6
    idx = m & (mx == rgb[...,0]); h[idx] = ((rgb[...,1]-rgb[...,2])[idx]/d[idx]) % 6
    idx = m & (mx == rgb[...,1]) & (mx != rgb[...,0]); h[idx] = ((rgb[...,2]-rgb[...,0])[idx]/d[idx]) + 2
    idx = m & (mx == rgb[...,2]) & (mx != rgb[...,0]) & (mx != rgb[...,1]); h[idx] = ((rgb[...,0]-rgb[...,1])[idx]/d[idx]) + 4
    h = h/6 % 1.0
    s = np.where(mx>1e-6, d/np.maximum(mx,1e-6), 0)
    return h, s, mx

def hsv_to_rgb(h, s, v):
    i = np.floor(h*6).astype(int) % 6
    f = h*6 - np.floor(h*6)
    p = v*(1-s); q = v*(1-f*s); t = v*(1-(1-f)*s)
    r = np.choose(i, [v,q,p,p,t,v]); g = np.choose(i, [t,v,v,q,p,p]); b = np.choose(i, [p,p,t,v,v,q])
    return np.stack([r,g,b], -1)

def dominant_hue(path):
    a = np.array(Image.open(path).convert("RGBA")).astype(np.float32)/255.0
    rgb, alpha = a[...,:3], a[...,3]
    h, s, v = rgb_to_hsv(rgb)
    mask = (alpha>0.5) & (s>0.35) & (v>0.25)
    if mask.sum() < 20: mask = (alpha>0.5) & (s>0.15)
    ang = h[mask]*2*np.pi
    hh = (np.arctan2(np.sin(ang).mean(), np.cos(ang).mean())/(2*np.pi)) % 1.0
    return hh, float(np.median(s[mask])), float(np.median(v[mask]))

base_p = os.path.join(ROOT, "assets", base_name)
tgt_p = os.path.join(ROOT, "assets", target_name)
tgt_orig = os.path.join(ROOT, "assets_backup_pre_chatgpt", target_name)
src_for_hue = tgt_orig if os.path.exists(tgt_orig) else tgt_p
th, ts, tv = dominant_hue(src_for_hue)
bh, bs, bv = dominant_hue(base_p)

a = np.array(Image.open(base_p).convert("RGBA")).astype(np.float32)/255.0
rgb, alpha = a[...,:3], a[...,3:]
h, s, v = rgb_to_hsv(rgb)
mask = (s>0.25) & (v>0.15)
h = np.where(mask, (h + (th-bh)) % 1.0, h)
if ts > 0:
    s = np.where(mask, np.clip(s*(0.6+0.4*ts/max(bs,1e-3)), 0, 1), s)
out = hsv_to_rgb(h, s, v)
res = np.concatenate([out, alpha], 2)
img = Image.fromarray((res*255).astype(np.uint8))
if not os.path.exists(tgt_orig):
    shutil.copy2(tgt_p, tgt_orig)
orig = Image.open(src_for_hue)
sc = max(orig.size)/max(img.size)
img = img.resize((max(1,round(img.width*sc)), max(1,round(img.height*sc))), Image.LANCZOS)
img.save(tgt_p)
print(f"recolored {base_name} -> {target_name} (hue {bh:.2f}->{th:.2f})")
