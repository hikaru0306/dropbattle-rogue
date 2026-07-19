# -*- coding: utf-8 -*-
"""ガレス(hero3)・ノア(hero4) 画風寄せ差し替え候補 → assets_cand/
キャラのデザイン（ライオンの重騎士／狐の賢者）は現状維持のまま、
書き込み・塗りをアルド(hero.png)・イリス(hero2.png)基準に寄せる:
  アニメ調のシャープな目 / グラデ付きセル塗り / 黒縁＋細い白フチ /
  金ライン装飾・革ベルト・小物の書き込み / 深く濃い配色 / 4頭身前後
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "photorealistic, realistic, 3d, cgi, render, photograph, text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated, "
    "tall proportions, realistic body proportions, adult proportions, elongated body, "
    "western cartoon, american comic style, disney style, mascot logo, sticker art, "
    "big round cartoon eyes, flat solid colors without shading, simple flat shading, no shading, "
    "thick uniform outlines, coloring book style, plain undetailed clothing, "
    "muted colors, pastel colors, sketch, lineart only, "
    "rim light, backlight, glowing edges, neon highlights, strong specular highlights, "
    "glossy plastic shine, bloom, glow, lens flare, overexposed, blown out highlights")

STYLE = ("masterpiece, best quality, score_7, safe. "
    "japanese anime chibi mobile game character art, sharp angular anime eyes with small highlights, "
    "soft cel shading with gentle gradients and restrained matte highlights, deep rich saturated colors, "
    "bold black outlines with a thin white outer stroke around the character, "
    "highly detailed ornate equipment with gold line trim, leather straps, buckles and small pouches, "
    "fine painted detail on every surface, layered depth, "
    "chibi proportions, four heads tall, compact sturdy body, chunky readable silhouette, "
    "full body, solo, centered, facing the viewer, plain solid white background, "
    "no text, video game character sprite. ")

# ガレス: ライオン頭の重騎士（現デザイン踏襲: 鋼色の重鎧・大剣を地に突く・盾を背負う・茶金のたてがみ）
GARETH = ("A chibi anthropomorphic lion heavy knight, proud lion head with a thick golden brown mane, "
    "fierce determined anime eyes, wearing heavy steel plate armor in deep blue steel and gunmetal with "
    "gold filigree trim, engraved pauldrons, chainmail at the joints, a dark blue tabard with gold edging, "
    "leather belts and buckles over the armor, "
    "both gauntleted hands resting on the pommel of a huge greatsword planted point down in front of him, "
    "a large round shield strapped on his back, ")

# ノア: 狐の賢者（現デザイン踏襲: 薄紫の毛・丸眼鏡・本と杖・紫×赤のローブ・二又の尻尾）
NOA = ("A chibi anthropomorphic fox sage, soft lavender white fur, round wire rimmed glasses, "
    "gentle intelligent anime eyes, two big fluffy fox tails, "
    "wearing a heavy layered deep violet and dark plum scholar robe with crimson lining and gold line trim, "
    "gold clasps, a leather book strap and small pouches across the chest, "
    "holding an open ancient tome with visible pages in one hand and a gnarled wooden staff with a "
    "faceted crystal on top in the other hand, ")

JOBS = {
    "hero3_a1": (STYLE + GARETH + "brave dignified expression, slight roar.", 771101),
    "hero3_a2": (STYLE + GARETH + "calm stoic expression, sharp eyes.", 771202),
    "hero3_a3": (STYLE + GARETH + "confident fierce expression.", 771303),
    "hero3_a4": (STYLE + GARETH + "noble commanding expression.", 771404),
    "hero4_a1": (STYLE + NOA + "calm gentle smile.", 882101),
    "hero4_a2": (STYLE + NOA + "thoughtful scholarly expression.", 882202),
    "hero4_a3": (STYLE + NOA + "kind confident expression, slight smile.", 882303),
    "hero4_a4": (STYLE + NOA + "wise composed expression.", 882404),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero34"}},
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
