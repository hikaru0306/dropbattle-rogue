# -*- coding: utf-8 -*-
"""賭博師ジン 最終調整: 基準画像 db_gambler2_hero_00002_(=hero7g_b) の雰囲気そのまま、頭身だけ3〜3.5等身へ
  hero7m_a..d : キャラ候補 768px -> assets_cand/
方針(coordinator指示):
  - gen_gambler2.py の2番目のジョブ(hero7g_b)のプロンプト/NEGを一字も変えない
  - 末尾に頭身の語だけ追加: "Drawn at 3 heads tall, youthful short stature."（tall系語は無いので除去不要）
  - seed のみ4種で拾う。白塗り/金襟巻き/赤黒帽/コインを手に浮かべる/シルエットは維持
usage: python gen_gambler8.py [name ...]
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# ★ gen_gambler2.py の NEG_HERO を一字も変えずコピー ★
NEG_HERO = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")

# ★ gen_gambler2.py の HERO を一字も変えずコピー ★
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, cute and heroic, chibi proportions, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

# ★ gen_gambler2.py の hero7g_b 本文を一字も変えずコピー ★
BODY = ("A theatrical fantasy joker card gambler hero styled like the Joker playing card, "
    "a curled jester hat with three drooping points and gold bells in dusky red and black, "
    "a large ruffled harlequin collar and a dusky crimson tailcoat covered in small red and black diamonds with gold buttons, "
    "balancing a big gold coin on the back of his knuckles, other hand tossing a small gold coin, "
    "a devilish knowing smirk, dark hair.")

# 頭身の語だけ追加（これ以外は基準と同一）
SHORT = " Drawn at 3 heads tall, youthful short stature."

PROMPT = HERO + BODY + SHORT

HERO_JOBS = {
    "hero7m_a": (PROMPT, 979101),
    "hero7m_b": (PROMPT, 979263),
    "hero7m_c": (PROMPT, 979418),
    "hero7m_d": (PROMPT, 979574),
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
    res = post(build(seed, text, NEG_HERO, 768, "db_gambler8_hero"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
