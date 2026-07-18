# -*- coding: utf-8 -*-
"""イリス（hero2）差し替え候補 第4弾（G案の詰め） → assets_cand/
FB: 第3弾Gが近い。ただし ①ハイライト/リムライトが強すぎる → 落とす ②帽子は魔女帽ではなくベレー帽
画風は引き続きアルド(hero.png)基準: アニメ調のシャープな目・グラデ付きセル塗り・黒縁＋細い白フチ・
金ライン装飾・深く濃い配色・3.5頭身・わずかに右向き
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "photorealistic, realistic, 3d, cgi, render, photograph, text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated, "
    "facing left, turned to the left, profile view, side view, "
    "tall proportions, realistic body proportions, long legs, adult proportions, teenage proportions, elongated body, "
    "western cartoon, american comic style, disney style, big round cartoon eyes, flat solid colors without shading, "
    "muted colors, pastel colors, sketch, lineart only, "
    # ① 光を落とす
    "rim light, backlight, glowing edges, cyan edge highlights, neon highlights, strong specular highlights, "
    "glossy plastic shine, bloom, glow, lens flare, shiny metallic sheen, overexposed, blown out highlights, "
    # ② 帽子はベレー
    "witch hat, pointed hat, wizard hat, wide brim hat, cone hat, tall hat")

STYLE = ("masterpiece, best quality, score_7, safe. "
    "japanese anime chibi mobile game character art, sharp angular anime eyes with small highlights, small face, "
    "soft cel shading with gentle gradients and restrained matte highlights, deep rich saturated colors, "
    "bold black outlines with a thin white outer stroke around the character, "
    "ornate layered robes with gold line trim, leather straps and small pouches, "
    "super deformed chibi, three and a half heads tall, small stubby body, short thick arms, "
    "long robe hem covering most of the legs, chunky rounded readable silhouette, "
    "full body, solo, centered, plain solid white background, "
    "body turned slightly toward the viewer's right, three-quarter view facing right, "
    "no text, video game character sprite. ")

# G案の中身（深紅×紫の重ね着・革ベルト・筆を杖のように）＋ベレー帽を明示
IRIS = ("A chibi witch painter girl, blonde hair, pointed elf ears, "
    "wearing a soft flat round crimson beret with a gold trim band, a french beret tilted on her head, ")

BODY = ("heavy layered deep crimson and dark violet robe with prominent gold line trim and gold clasps, "
    "paint-splattered mantle, leather belt with pigment pouches and a satchel strap across the chest, "
    "holding a tall ornate paintbrush like a wizard staff in one hand and a wooden paint palette in the other, ")

JOBS = {
    "hero2_g2": (STYLE + IRIS + BODY + "spirited confident expression.", 963101),
    "hero2_g3": (STYLE + IRIS + BODY + "calm confident smile.", 963202),
    "hero2_g4": (STYLE + IRIS + BODY + "cheerful determined expression, slight smile.", 963303),
    "hero2_g5": (STYLE + IRIS + BODY + "cool composed expression, sharp eyes.", 963404),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero2new4"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":34,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
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
