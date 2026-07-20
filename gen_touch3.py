# -*- coding: utf-8 -*-
"""品質不足の5体をキャラ特徴ベースで高品質再生成 → assets_raw_touch3/
元デザインは踏襲しない。特徴が合っていて高品質・3/4左向き・大人っぽく・影なしであればよい。
usage: python gen_touch3.py [name ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_touch3")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, blank hollow face, featureless, murky, muddy silhouette, "
    "flat empty shapes, undetailed, plain, boring, stiff pose, "
    "cute, chibi, childish, kawaii, mascot, baby, toddler, cartoon for kids, oversized head, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile, "
    "front view, facing viewer, symmetrical pose, perfectly frontal")
BASE = ("masterpiece, best quality, highly detailed, intricate details, professional game character illustration, "
    "clear readable design, distinct expressive face, fully colored with rich flat cel shading and clean rendering, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, dynamic pose, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, one side toward the viewer, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

JOBS = {
    "slime":  ("A glossy plump green slime monster, a translucent jelly blob body with a visible darker inner gel core and soft light reflections, two big expressive glossy eyes and a wide cheeky fanged grin, small stubby jelly arms, bouncing playfully to the left.", 945001),
    "demon":  ("A mighty demon lord named Valga, a powerfully muscular deep-purple demon king with large sweeping curved horns, an ornate golden crown, a glowing crimson gem embedded in his broad chest, huge dark leathery bat wings, sharp black claws, a commanding fanged grin, an imposing regal boss stance.", 945002),
    "behemot":("A colossal thunder behemoth beast, a massive muscular bison-like monster with thick storm-grey armored hide, a fierce face with glowing yellow eyes and long curved white tusks, huge crackling lightning-bolt-shaped horns, powerful clawed legs, a heavy imposing four-legged stance.", 945003),
    "mare":   ("A demonic nightmare stallion, a sleek jet-black horse with a wild flowing mane and tail made of violet flames, glowing violet eyes, bared fangs, hooves wreathed in purple fire, a dynamic rearing gallop.", 945004),
    "noct":   ("An elegant queen of the night boss, a beautiful vampiric dark sorceress-queen with a clearly visible pale regal face and flowing black hair, large ornate bat-wing cloak, crimson eyes, holding a black rose scepter, a fitted elegant gothic gown, a graceful commanding pose.", 945005),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_t3"}},
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
