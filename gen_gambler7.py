# -*- coding: utf-8 -*-
"""賭博師ジン リデザインv7: hero7j_e(約3等身)基準に頭身を数値指定で3.5等身へ、seedガチャ4案
  hero7l_a..d : キャラ候補 768px -> assets_cand/
方針(coordinator指示):
  - 構図/衣装/白塗り/右向きは hero7j_e の出方を踏襲（プロンプト本文はいじりすぎない）
  - 等身は数値で直接: "3.5 heads tall proportions, youthful short stature, head slightly smaller than one third of body height"
    ・"semi-deformed"(2等身に引く)と "slender adult / tall"(7等身に引く)は使わない
  - NEG は両側をふさぐ（chibi側 と 7等身側 の両方）
  - プロンプト固定で seed のみ4種変えて拾う
維持: 白塗り顔＋表情／右向き3/4／トランプ無し・金貨のみ／鈴付き二又道化帽／ornate布質感／#c0483f＋黒金
usage: python gen_gambler7.py [name ...]
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# 両側をふさぐ NEG（chibi側＋7等身側）
NEG_HERO = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "flat vector art, sticker art, mascot, minimal shapes, graphic design, emblem, logo mascot, "
    "chibi, super deformed, two heads tall, oversized head, big head, toddler proportions, "
    "realistic adult proportions, seven heads tall, eight heads tall, tall slender fashion model, long adult legs, "
    "playing cards, playing card, card, holding cards, fan of cards, tarot card, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")

# HERO: gen_hero5_new のプリフィックスから "cute and heroic, chibi proportions" のみを
# 数値指定の頭身に差し替え（他の画風記述は維持）
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, charismatic and roguish, "
    "3.5 heads tall proportions, youthful short stature, head slightly smaller than one third of body height, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

VIEW = "Turned in a three-quarter view facing to the right, body and head angled slightly to the right. "

FACE = ("his face fully covered in smooth white greasepaint stage makeup, a red harlequin diamond painted around one eye, "
    "clearly visible mischievous eyes and a confident sly grin with red painted lips, a lively expressive face, not a blank mask, ")

# hero7j_e の本文を踏襲（showman jester・手袋・金糸クラヴァット・金貨指弾き）
BODY = ("An elegant fantasy showman jester gambler hero in an ornate dark crimson harlequin tailcoat of layered fabric with intricate gold filigree and a "
    "gold-embroidered ruffled cravat, black and red diamond patterning, gloved hands, "
    "a belled two-pointed jester hat in crimson and black with golden bells, " + FACE +
    "one gloved hand flicking a large gold coin off the thumb, the other gloved hand spread open in a showman gesture, dark hair.")

PROMPT = HERO + VIEW + BODY

# プロンプト固定・seedのみ4種
HERO_JOBS = {
    "hero7l_a": (PROMPT, 978101),
    "hero7l_b": (PROMPT, 978247),
    "hero7l_c": (PROMPT, 978389),
    "hero7l_d": (PROMPT, 978512),
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
    res = post(build(seed, text, NEG_HERO, 768, "db_gambler7_hero"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
