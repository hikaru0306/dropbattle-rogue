# -*- coding: utf-8 -*-
"""品質/向きが微妙な9体をタッチアップ再生成 → assets_raw_touch/
各キャラの実体(顔・輪郭)をはっきりさせ、3/4左向き・大人っぽく・影なしを維持。
usage: python gen_touchup.py [name ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_touch")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, blank hollow face, featureless, murky, muddy silhouette, "
    "cute, chibi, childish, kawaii, mascot, baby, toddler, cartoon for kids, oversized head, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile, "
    "front view, facing viewer, symmetrical pose, perfectly frontal")
BASE = ("masterpiece, best quality, highly detailed, clear readable design, distinct facial features, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, one side toward the viewer, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

JOBS = {
    # 品質改善: 顔・実体をはっきり
    "mandra": ("A mandrake plant monster: a pale round turnip-like root body, a leafy green sprout on top of its head, a distinct creepy face with two dark oval eyes and a small frowning mouth, thin knobby root arms and legs.", 943001),
    "mudman": ("A mud golem: a humanoid figure made of thick wet brown mud, a lumpy muscular body, two clearly visible glowing pale eyes on its head, thick dripping arms and fists.", 943002),
    "alraune": ("An alraune plant queen: a large fully-bloomed pink rose forming her head and upper body with clearly visible layered rose petals, a small elegant face peeking from the rose center, thorned green vine arms, a few green leaves at the base.", 943003),
    "banshee": ("A banshee ghost: a spectral female wraith with a clearly visible wailing screaming face, flowing pale spectral hair swept to one side, a tattered ghostly white dress fading into wisps, floating.", 943004),
    "voids":  ("A void slime: a blob of dark starry night-sky goo with a clearly visible wide white grinning mouth and two glowing white eyes, tiny galaxies and stars swirling inside its dark body.", 943005),
    "titania":("A phantom fairy queen, fully colored with rich flat cel shading: an elegant slender fae woman with pale skin and a clearly visible beautiful face as the main focus, long lavender hair, a green thorn crown, a flowing gown of blue and violet petals, four translucent pale-blue moth-like wings held gracefully to one side and not too large, a mischievous smile.", 943106),
    # 向き改善
    "toadking":("A giant royal toad king: a massive fat toad with warty emerald-green skin, a golden crown, a huge pale belly, holding a lily-pad scepter, sitting and turned to the left.", 943007),
    "fgolem": ("An ice golem made of jagged translucent blue glacier ice blocks, angular icy limbs and heavy fists, a bright glowing frozen core in its chest, two glowing pale eyes, clearly turned to the left.", 943008),
    "jotun":  ("A frost giant: a towering muscular jotun with pale blue skin, a big frosty beard, fur and bronze shoulder armor, a frozen crown, hoisting a huge ice club to one side, clearly turned to the left.", 943009),
    "spore":  ("A mushroom shaman monster with a wide brown spotted mushroom cap, a small pale round body, a distinct grumpy little face with two dark eyes and a small frown, both tiny hands gripping a crooked twig staff topped with a leaf, clearly turned to the left.", 943010),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_touch"}},
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
    if os.path.exists(os.path.join(OUT, f"{name}.png")):
        print("skip", name, flush=True); continue
    desc, seed = JOBS[name]
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed, BASE + desc))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
print("ALL_DONE")
