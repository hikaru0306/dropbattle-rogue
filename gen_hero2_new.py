# -*- coding: utf-8 -*-
"""イリス（hero2）差し替え候補の生成 → assets_cand/
ユーザー指定: 現行の雰囲気・デザインは維持しつつ ①わずかに右向きに ②ディテールをアルド（hero.png）寄りに
アルド寄せ = 厚い重ね着ローブ＋金の縁取り／細かい装飾／濃いめの配色／太い黒縁＋セル塗り＋わずかな陰影
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated, "
    "facing left, turned to the left, profile view, side view")

# 現行hero群と同じ画風＋アルド(hero.png)のディテール感を足した共通プリフィックス
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture and soft shadows, vivid saturated colors, "
    "richly detailed ornate costume, layered heavy robes with gold trim and filigree, small accessories and pouches, "
    "chunky readable silhouette, cute and heroic, chibi proportions, big expressive eyes, "
    "full body, solo, centered, plain solid white background, "
    "body turned slightly toward the viewer's right, three-quarter view facing right, looking to the right, "
    "no text, video game sprite concept art. ")

# 現行イリス: 赤ベレー帽・金髪・エルフ耳・絵の具で汚れたカラフルなコート・巨大な筆・パレット
IRIS = ("A chibi witch painter heroine, blonde hair, pointed elf ears, wearing a deep crimson beret with a gold pin, "
    "holding a tall ornate paintbrush with crimson bristles in one hand and a wooden paint palette in the other, ")

JOBS = {
    # A: 現行に最も忠実（色数そのまま）＋アルドの金縁ローブ要素
    "hero2_a": (HERO + IRIS +
        "layered crimson robe with ornate gold trim and paint-splattered colorful patchwork sleeves, "
        "leather belt with brush pouches, confident cheerful grin.", 960101),
    # B: アルド寄せを強め（重ね着・深い色・装飾多め）
    "hero2_b": (HERO + IRIS +
        "heavy layered deep crimson and violet robes with intricate gold filigree trim, ornate collar, "
        "paint-stained apron over the robe, leather satchel and brush holster, small gold buttons, "
        "spirited determined expression.", 960202),
    # C: コートの絵の具パッチを残しつつ装飾を細密に
    "hero2_c": (HERO + IRIS +
        "long ornate crimson coat with gold-embroidered hems and vivid paint-splash patches of blue, yellow and green, "
        "layered under-robe, ornate gold clasps, pouches of pigment on the belt, bright energetic smile.", 960303),
    # D: 帽子と筆をより装飾的に（アルドの杖に相当する見せ場を作る）
    "hero2_d": (HERO + IRIS +
        "ornate crimson beret with gold band and a feather, layered crimson robe with gold filigree and paint-splattered "
        "colorful mantle, holding an elaborate ornate paintbrush with a carved golden ferrule like a wizard staff, "
        "wooden palette with vivid paint blobs, lively confident expression.", 960404),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero2new"}},
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
