# -*- coding: utf-8 -*-
"""イリス（hero2）差し替え候補 第3弾 → assets_cand/
FB反映: 第1・2弾は「西洋トゥーン（丸い黒目・べた塗り）」でアルドの画風から外れていた。
アルド(hero.png)の要素を明示して寄せる:
  ・アニメ調のシャープな目（ハイライト入り）／小さめの顔
  ・光沢のあるグラデ付きセル塗り（ハイライトと落ち影）
  ・太い黒縁＋キャラ外周に細い白フチ
  ・金のライン装飾が入った重ね着ローブ、斜め掛けの革ベルト＆ポーチ
  ・濃く深い配色（彩度高め・コントラスト強め）／3.5頭身のチビ体型
  ・向きはわずかに右
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
    # 画風のズレ対策（第1・2弾の失敗要因）
    "western cartoon, american comic style, disney style, cartoon network style, "
    "big round cartoon eyes, flat solid colors without shading, coloring book, sticker, "
    "muted colors, pastel colors, sketch, lineart only")

# アルドと同じ画風・同じ体型を明示
STYLE = ("masterpiece, best quality, score_7, safe. "
    "japanese anime chibi mobile game character art, sharp angular anime eyes with bright highlights, small face, "
    "glossy cel shading with smooth gradients, crisp highlights and cast shadows, deep rich saturated colors, high contrast, "
    "bold black outlines with a thin white outer stroke around the character, "
    "ornate layered robes with gold line trim, leather strap across the chest with a small pouch, "
    "super deformed chibi, three and a half heads tall, oversized headwear, small stubby body, short thick arms, "
    "long robe hem covering most of the legs, chunky rounded readable silhouette, "
    "full body, solo, centered, plain solid white background, "
    "body turned slightly toward the viewer's right, three-quarter view facing right, "
    "no text, video game character sprite. ")

IRIS = ("A chibi witch painter girl, blonde hair, pointed elf ears, big deep crimson beret with gold trim, ")

JOBS = {
    # A: 現行デザイン踏襲（赤ベレー＋カラフル絵の具＋筆＋パレット）をアルド画風で
    "hero2_f": (STYLE + IRIS +
        "layered crimson robe with gold line trim and colorful paint splashes on the sleeves, "
        "holding a tall ornate paintbrush with crimson bristles and a golden ferrule in one hand, "
        "a wooden paint palette in the other hand, confident lively expression.", 962101),
    # B: 配色をアルド寄りに深く（クリムゾン＋紫の差し色・金ライン強め）
    "hero2_g": (STYLE + IRIS +
        "heavy layered crimson and deep violet robe with prominent gold line trim and gold clasps, "
        "paint-splattered mantle, leather belt with pigment pouches, "
        "holding an ornate paintbrush like a wizard staff, wooden palette, spirited confident expression.", 962202),
    # C: 帽子を大きめ・筆を杖然と（シルエット重視）
    "hero2_h": (STYLE + IRIS +
        "oversized crimson beret with a gold band, layered crimson robe with gold trim and a colorful paint-splashed cape, "
        "gripping a tall ornate golden paintbrush staff with crimson bristles, small wooden palette, "
        "determined cheerful expression.", 962303),
    # D: 顔まわりをアルド寄せ（前髪で目元に影・シャープな目）
    "hero2_i": (STYLE + IRIS +
        "blonde hair with long side bangs shadowing the eyes, sharp confident anime eyes, "
        "layered crimson robe with gold filigree trim and vivid paint splashes, leather satchel strap, "
        "tall ornate paintbrush with a golden ferrule, wooden palette, cool confident smile.", 962404),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero2new3"}},
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
