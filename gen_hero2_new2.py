# -*- coding: utf-8 -*-
"""イリス（hero2）差し替え候補 第2弾 → assets_cand/
第1弾のFB: 「アルドと等身が合っていない」→ 3頭身のずんぐりチビ体型（アルド hero.png と同じ）に寄せる。
・頭（帽子込み）が大きく、胴と手足は短く太い / 裾が床まで届いて足はほとんど見えない
・向きは引き続き「わずかに右向き」
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
    "facing left, turned to the left, profile view, side view, "
    # 等身ズレ対策
    "tall proportions, realistic body proportions, long legs, slender legs, adult proportions, teenage proportions, "
    "long torso, thin limbs, elongated body, high heels, model pose")

# アルドと同じ超デフォルメ体型を強く指定
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture and soft shadows, vivid saturated colors, "
    "richly detailed ornate costume, layered heavy robes with gold trim and filigree, small pouches and accessories, "
    "super deformed chibi, three heads tall, very large head with oversized headwear, small stubby round body, "
    "short thick arms, tiny hands, very short legs almost hidden under a floor-length robe, "
    "chunky rounded readable silhouette, cute and heroic, big expressive eyes, "
    "full body, solo, centered, plain solid white background, "
    "body turned slightly toward the viewer's right, three-quarter view facing right, looking to the right, "
    "no text, video game sprite concept art. ")

IRIS = ("A chibi witch painter heroine, blonde hair, pointed elf ears, wearing a big deep crimson beret with a gold pin, "
    "holding a tall ornate paintbrush with crimson bristles in one hand and a wooden paint palette in the other, ")

JOBS = {
    # 第1弾A（現行に最も近い案）を3頭身で
    "hero2_a2": (HERO + IRIS +
        "layered crimson robe with ornate gold trim and paint-splattered colorful patchwork sleeves, "
        "leather belt with brush pouches, confident cheerful grin.", 961101),
    "hero2_a3": (HERO + IRIS +
        "layered crimson robe with ornate gold trim and paint-splattered colorful patchwork sleeves, "
        "leather belt with brush pouches, confident cheerful grin.", 961202),
    # 第1弾D（帽子と筆が装飾的）を3頭身で
    "hero2_d2": (HERO + IRIS +
        "ornate crimson beret with a gold band, layered crimson robe with gold filigree and paint-splattered colorful mantle, "
        "an elaborate ornate paintbrush with a carved golden ferrule like a wizard staff, "
        "wooden palette with vivid paint blobs, lively confident expression.", 961303),
    # さらにずんぐり（アルド最寄せ）: 裾が地面につくローブ・帽子特大
    "hero2_e2": (HERO + IRIS +
        "oversized crimson beret almost as wide as her body, heavy floor-length crimson robe with thick gold-trimmed hem "
        "and colorful paint splashes, wide sleeves, small leather satchel, cheerful determined face.", 961404),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero2new2"}},
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
