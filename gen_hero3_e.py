# -*- coding: utf-8 -*-
"""ガレス(hero3) 第5弾 → assets_cand/
FB: ①まだ微妙 ②AI絵特有の光りすぎ（金属テカリ・ハイライト）を抑える ③見て右向きが理想
維持: 兜あり / 4.5頭身 / アルド・イリス基準の画風（黒縁＋細白フチ・セル塗り・金ライン装飾）
向き: イリス(hero2)と同じく生成後に左右反転して右向きに揃える運用（process_hero34.py --flip）
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "photorealistic, realistic, 3d, cgi, render, photograph, text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated, "
    "western cartoon, american comic style, disney style, mascot logo, sticker art, "
    "big round cartoon eyes, flat solid colors without shading, simple flat shading, no shading, "
    "thick uniform outlines, coloring book style, plain undetailed clothing, "
    "muted colors, pastel colors, sketch, lineart only, "
    # ② 光りすぎ対策（AI絵特有のテカリを重点的に潰す）
    "shiny metallic sheen, polished chrome, mirror finish armor, specular highlights, strong highlights, "
    "glossy plastic shine, wet look, oily sheen, glossy surface, high contrast lighting, "
    "rim light, backlight, glowing edges, neon highlights, bloom, glow, lens flare, god rays, "
    "overexposed, blown out highlights, white glare spots, big round highlight blobs on armor, "
    "shimmering, iridescent, gradient rainbow reflections, "
    # 等身
    "super deformed, two heads tall, three heads tall, oversized head, huge head, big head, "
    "head as wide as the shoulders, mane wider than the shoulders, "
    "short stubby legs, no neck, squat body, baby proportions, toddler proportions, kawaii mascot, "
    "six heads tall, seven heads tall, realistic adult body proportions, tall slender figure, thin limbs, "
    "bare head, bareheaded, no helmet, hood, uncovered head, "
    # ③ 向き
    "front view, facing the viewer, symmetrical frontal pose, straight-on view, profile view, side view")

STYLE = ("masterpiece, best quality, score_7, safe. "
    "japanese anime mobile game character art, sharp angular anime eyes with small highlights, "
    "soft cel shading with gentle gradients, matte finish, hand painted flat matte surfaces, "
    "restrained subtle shading, low contrast lighting, no shiny highlights, brushed unpolished metal, "
    "deep rich saturated colors, "
    "bold black outlines with a thin white outer stroke around the character, "
    "detailed ornate equipment with gold line trim, leather straps, buckles and small pouches, "
    "fine painted detail on every surface, layered depth, "
    "chibi proportions but slightly taller, four and a half heads tall, small head relative to the body, "
    "visible neck, broad shoulders wider than the head, sturdy compact torso, legs a bit longer, "
    "chunky readable silhouette, "
    "full body from head to toe, solo, centered, plain solid white background, "
    "clearly turned toward the viewer's right, three-quarter pose, shoulders and hips rotated to the right, "
    "head and gaze directed to the right side of the frame, "
    "no text, video game character sprite. ")

GARETH = ("A stalwart anthropomorphic lion heavy knight, "
    "wearing an ornate steel great helm with a golden lion crest on the crown and cheek guards, "
    "the open visor reveals his fierce lion eyes and muzzle, "
    "a golden brown mane flows out from under the helmet around his neck, "
    "fierce determined anime eyes, heavy steel plate armor in deep blue steel and gunmetal with "
    "gold filigree trim, engraved pauldrons, chainmail at the joints, a dark blue tabard with gold edging, "
    "leather belts and buckles over the armor, armored greaves, "
    "both gauntleted hands resting on the pommel of a huge greatsword planted point down, "
    "a large round shield strapped on his back, ")

JOBS = {
    "hero3_e1": (STYLE + GARETH + "calm stoic expression, sharp eyes.", 771501),
    "hero3_e2": (STYLE + GARETH + "brave dignified expression.", 771602),
    "hero3_e3": (STYLE + GARETH + "noble commanding expression.", 771703),
    "hero3_e4": (STYLE + GARETH + "confident fierce expression.", 771804),
    "hero3_e5": (STYLE + GARETH + "quiet resolute expression.", 771905),
    "hero3_e6": (STYLE + GARETH + "steady watchful expression.", 772006),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_hero3e"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":34,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":704,"height":832,"batch_size":1}},
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
