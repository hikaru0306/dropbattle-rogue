# -*- coding: utf-8 -*-
"""依頼書/宝の地図風のボロ紙パネル素材をAnimaで生成 → assets_raw_ui/
border-image(fill)で行き先カード等に使う。中央は無地であること。"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, "
    "glow, bloom, neon, lens flare, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, letters, writing, runes, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, "
    "map lines, drawings, illustration inside, ink marks, stains in center, pattern in center, "
    "complex background, scenery, multiple objects, collage, cast shadow, drop shadow, "
    "rolled paper, scroll rod, ribbon, wax seal, fold lines")

BASE = ("masterpiece, best quality, score_7, safe. "
    "a single sheet of aged parchment paper filling the canvas, fantasy RPG quest board notice style, "
    "rough tattered torn edges all around, slightly burnt darkened corners, warm beige aged paper, "
    "completely plain empty center with no markings, subtle worn texture only near the edges, "
    "flat cel shading with soft dark outline, flat 2d game asset, front view, no text. ")

JOBS = {
    "paper_quest": BASE + "Portrait orientation sheet, like a monster hunting request poster.",
    "paper_map":   BASE + "Landscape treasure map sheet, corners slightly curled and ripped.",
    "paper_strip": BASE + "Wide short horizontal banner strip of parchment, like an old signboard label.",
}
SEED0 = 952000

def build(seed, text, w, h):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_uipaper"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":w,"height":h,"batch_size":1}},
      "44":{"class_type":"UNETLoader","inputs":{"unet_name":"anima-base-v1.0.safetensors","weight_dtype":"default"}},
      "45":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}}}

SIZES = { "paper_quest": (832, 1024), "paper_map": (1024, 832), "paper_strip": (1024, 512) }

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
names = list(JOBS.keys())
for spec in targets:
    name, _, sd = spec.partition("=")
    seed = int(sd) if sd else SEED0 + names.index(name)
    w,h = SIZES[name]
    print(f"[{name}] seed={seed} {w}x{h} 生成中...", flush=True)
    r = post(build(seed, JOBS[name], w, h))
    hst = wait(r["prompt_id"])
    for node in hst["outputs"].values():
        for im in node.get("images", []):
            data = fetch(im["filename"], im["subfolder"], im["type"])
            fp = os.path.join(OUT, f"{name}_{seed}.png")
            open(fp, "wb").write(data)
            print("  ->", fp, flush=True)
print("done")
