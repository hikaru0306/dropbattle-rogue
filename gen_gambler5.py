# -*- coding: utf-8 -*-
"""賭博師ジン リデザインv5: 世界観・塗り質感を既存ロスターに合わせる
  hero7j_a..e : キャラ候補 768px -> assets_cand/
方針:
  - 画風記述は gen_hero5_new.py の HERO プリフィックスを一字も変えず流用（front facing含む）
  - 視点/等身は HERO の後に追記でオーバーライド（やや右向き3/4・3〜4頭身）。プリフィックスは削らない
  - 衣装は ornate/intricate/layered fabric/gold filigree 系の布質感語彙で記述（マスコット化回避）
  - NEG にマスコット/フラットベクター/カード禁止語を追加
  - 維持: 白塗り顔＋表情はっきり／トランプ無し・金貨のみ／鈴付き二又道化帽／#c0483f＋黒金
usage: python gen_gambler5.py [name ...]
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# gen_hero5_new.py の NEG に、マスコット化防止＋トランプ禁止を追加
NEG_HERO = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "flat vector art, sticker art, mascot, minimal shapes, graphic design, emblem, logo mascot, "
    "playing cards, playing card, card, holding cards, fan of cards, tarot card, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")

# ★ gen_hero5_new.py の HERO を一字も変えずコピー ★
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, cute and heroic, chibi proportions, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

# HERO の後に追記して視点・等身をオーバーライド（プリフィックスは削らない）
VIEW = "Drawn at 3 to 4 heads tall proportions. Turned in a three-quarter view facing to the right, body and head angled slightly to the right. "

# 白塗り顔（表情はっきり・無機質マスクにしない）
FACE = ("his face fully covered in smooth white greasepaint stage makeup, a red harlequin diamond painted around one eye, "
    "clearly visible mischievous eyes and a confident sly grin with red painted lips, a lively expressive face, not a blank mask, ")

# 衣装は ornate/intricate/layered fabric/gold filigree 語彙（hero2/hero5/hero6の質感に寄せる）
HERO_JOBS = {
    # a: 王道の宮廷道化賭博師。層になった布・金糸刺繍・ベルベット
    "hero7j_a": (HERO + VIEW +
        "An elegant fantasy court jester gambler hero in an ornate crimson and black harlequin diamond costume of layered velvet fabric "
        "with intricate gold filigree trim and gold thread embroidery, a scalloped gold-trimmed collar, "
        "a belled two-pointed jester hood in dusky crimson and black with golden bells, harlequin diamond patterned leggings and curled pointed shoes, " + FACE +
        "flipping a large ornate gold coin off his thumb, the other hand resting confidently on his hip, short dark hair.", 976101),
    # b: 華やかなハイローラー道化。フリル襟・金ボタン列・厚手コート
    "hero7j_b": (HERO + VIEW +
        "An elegant fantasy high-roller jester gambler hero in an ornate dusky crimson tailcoat densely patterned with small black and red harlequin diamonds, "
        "intricate gold filigree edging, a row of gold buttons, a layered ruffled harlequin collar of rich fabric, "
        "a belled two-pointed jester hat in crimson and black with golden bells, " + FACE +
        "flicking a large gold coin up off his thumb, the other gloved hand gesturing outward, dark hair.", 976202),
    # c: 女性の宮廷道化賭博師。コルセット×層スカート・金刺繍
    "hero7j_c": (HERO + VIEW +
        "An elegant fantasy court jester gambler heroine in an ornate crimson and black harlequin diamond costume, a fitted embroidered corset bodice "
        "with intricate gold filigree, a layered ruffled harlequin skirt of rich fabric, a scalloped gold collar, high boots, "
        "a small tilted belled two-pointed jester hat in crimson and black, "
        "her face fully covered in smooth white greasepaint makeup, a red harlequin diamond around one eye, a bold teasing red-lipped smirk, expressive not a mask, "
        "flipping a large gold coin off her thumb, the other hand on her hip, long dark wavy hair.", 976303),
    # d: 重厚なマント付き。厚手ベルベット・金糸・コイン袋
    "hero7j_d": (HERO + VIEW +
        "An elegant fantasy trickster gambler hero in an ornate dusky crimson and black harlequin diamond doublet of heavy velvet with intricate gold filigree, "
        "gold coin-shaped buttons, a scalloped gold bell collar, a short layered cape lined with red diamond fabric, "
        "a belled two-pointed jester hat in crimson and black, an embroidered coin pouch on the belt, " + FACE +
        "flipping a large gold coin off his thumb held up prominently, the other hand relaxed at his side, dark hair.", 976404),
    # e: 手袋の見世物師風。金糸クラヴァット・層フリル
    "hero7j_e": (HERO + VIEW +
        "An elegant fantasy showman jester gambler hero in an ornate dark crimson harlequin tailcoat of layered fabric with intricate gold filigree and a "
        "gold-embroidered ruffled cravat, black and red diamond patterning, gloved hands, "
        "a belled two-pointed jester hat in crimson and black with golden bells, " + FACE +
        "one gloved hand flicking a large gold coin off the thumb, the other gloved hand spread open in a showman gesture, dark hair.", 976505),
}


def build(seed, text, neg, size, prefix):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":prefix}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":size,"height":size,"batch_size":1}},
      "44":{"class_type":"UNETLoader","inputs":{"unet_name":"anima-base-v1.0.safetensors","weight_dtype":"default"}},
      "45":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}}}

def post(p):
    req = urllib.request.Request(URL+"/prompt", data=json.dumps({"prompt":p}).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

def wait(pid):
    t0=time.time()
    while time.time()-t0<1800:
        with urllib.request.urlopen(URL+f"/history/{pid}", timeout=10) as r: hst=json.loads(r.read())
        if pid in hst: return hst[pid]
        time.sleep(2)
    raise TimeoutError(pid)

def fetch(fn,sub,ty):
    q=urllib.parse.urlencode({"filename":fn,"subfolder":sub,"type":ty})
    with urllib.request.urlopen(URL+"/view?"+q, timeout=30) as r: return r.read()

ALL = list(HERO_JOBS)
targets = sys.argv[1:] or ALL
for spec in targets:
    name, _, sd = spec.partition("=")
    text, seed = HERO_JOBS[name]
    if sd: seed = int(sd)
    dest = os.path.join(CAND, f"{name}.png")
    if os.path.exists(dest):
        print("skip", name, flush=True); continue
    print(f"[{name}] seed={seed}", flush=True)
    res = post(build(seed, text, NEG_HERO, 768, "db_gambler5_hero"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
