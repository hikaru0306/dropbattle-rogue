# -*- coding: utf-8 -*-
"""正面気味に出た6体を『はっきり3/4(約45度左)』でリロール → assets_raw_reroll/
横向きすぎにはしない(45度どまり)。子供向け/影/安物ライティングは gen_fix_all と同じ排除。"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_reroll")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, "
    "cute, chibi, childish, kawaii, mascot, baby, toddler, cartoon for kids, oversized head, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile, "
    "front view, facing viewer, symmetrical pose, perfectly frontal")
# 向きを強めた版(45度どまり)。真横は上のNEGで禁止。
BASE = ("masterpiece, best quality, highly detailed, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, one shoulder toward the viewer, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

JOBS = {
    "vamp":   ("A vampire lord with a high-collared crimson and black cape flaring to one side like bat wings, pale skin, slicked dark hair, red eyes, sharp fangs, an elegant menacing pose.", 940205),
    "boar":   ("A wild armored boar with big curved tusks, bristly brown fur, stomping hooves, angry small eyes, charging with its head lowered and turned to the left.", 940217),
    "mummy":  ("A small mummy soldier wrapped in old bandages, one glowing eye through the wraps, holding a khopesh sword to one side, shambling forward.", 940226),
    "titania":("A phantom fairy queen: an elegant fae monarch with four moth-like wings held asymmetrically with one wing swept forward, a thorn crown, a flowing gown of petals and mist trailing to one side, a mischievous smile.", 940236),
    "noct":   ("A queen of night: a vampiric dark queen with a bat-wing cloak swept to one side, pale skin, crimson eyes, holding a black rose scepter forward, an elegant gothic dress trailing to one side.", 940241),
    "demonx": ("A true demon lord final boss: a massive demon king with six curved horns, a burning violet third eye, obsidian armor with gold trim, twin greatswords held to one side, a cape of black flames streaming to one side, a dynamic menacing battle stance.", 940242),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_reroll"}},
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
