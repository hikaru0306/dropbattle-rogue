# -*- coding: utf-8 -*-
"""ルクス差し替え候補の生成（星詠みの巫女×3案+雫の聖女×1案）→ assets_cand/
画風は gen_heroes2.py（現行hero2〜5と同スタイル）を踏襲"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, cute and heroic, chibi proportions, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

JOBS = {
    # 第2弾: 既存hero5と同じ「elegant/ornate/intricate」主体の記述で細密に（第1弾はcute/young寄りでマスコット化＝安っぽくなった）
    "hero5_new_e": (HERO + "An elegant star oracle priestess heroine in flowing ornate midnight-blue and gold ceremonial robes, intricate golden constellation embroidery across layered fabrics, gold filigree trim, holding a tall ornate golden staff crowned with an elaborate star finial, long silver hair under a deep blue hood with a golden crescent diadem, serene graceful expression.", 950001),
    "hero5_new_f": (HERO + "An elegant astronomer grand sage heroine in a majestic indigo and gold robe with wide ornamented sleeves, an intricate star-chart pattern woven into the cloth, a jeweled golden tiara, holding a tall ornate staff with an elaborate golden armillary sphere and star finial, long flowing pale blonde hair, dignified gentle expression.", 950102),
    "hero5_new_g": (HERO + "An elegant moonlight priestess heroine in flowing ornate white and deep navy layered robes with intricate golden star and moon embroidery, a long celestial mantle, holding a tall ornate golden staff topped with an elaborate radiant star emblem, long white hair, calm wise expression.", 950203),
    # 雫の聖女も同路線で1枚
    "hero5_new_h": (HERO + "An elegant water saint heroine in flowing ornate teal and white ceremonial robes with intricate silver wave embroidery and layered translucent shawls, gold filigree trim, holding a tall ornate silver staff crowned with an elaborate teardrop sapphire, long aqua hair with a delicate golden circlet, serene kind expression.", 950304),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero5new"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":768,"batch_size":1}},
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

targets = sys.argv[1:] or list(JOBS.keys())
for name in targets:
    text, seed = JOBS[name]
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed,text))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
            print(" ->", name, flush=True)
print("ALL_DONE")
