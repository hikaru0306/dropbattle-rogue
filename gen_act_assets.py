# -*- coding: utf-8 -*-
"""3章制用アセット: ボス2体 + マップ背景2枚 + バトル背景2枚"""
import json, os, time, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame")
CHAR = ("masterpiece, best quality, score_7, safe. "
    "fantasy game boss monster design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, imposing but slightly cute, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

JOBS = {
    "kslime": (CHAR + "A giant royal king slime boss: a huge green slime wearing a small golden crown, "
        "big confident eyes, smaller slime bumps around its base, wide imposing blob body.", 768, 768, 890001),
    "vamp": (CHAR + "A vampire bat lord boss: an elegant aristocratic bat monster wrapped in a crimson-and-black "
        "cape like folded wings, pale face, small sharp fangs, glaring red eyes, high collar.", 768, 768, 890002),
    "bg_map2": ("masterpiece, best quality, score_7, safe. "
        "very tall vertical hand-painted fantasy board game world map seen from above, "
        "one long winding wooden plank path climbing through a dark misty swamp with glowing mushrooms, "
        "twisted dead trees, murky green water, cave entrances, reaching a bone gate at the very top, "
        "muted desaturated teal and olive colors, flat cel shaded illustration, bold outlines, "
        "video game level select background, no text, no icons, no characters. ", 576, 1536, 890003),
    "bg_map3": ("masterpiece, best quality, score_7, safe. "
        "very tall vertical hand-painted fantasy board game world map seen from above, "
        "one long winding obsidian road climbing through scorched volcanic wasteland with lava rivers, "
        "black jagged rocks, ash clouds, reaching a huge dark demon citadel at the very top, "
        "muted desaturated dark red and charcoal colors, flat cel shaded illustration, bold outlines, "
        "video game level select background, no text, no icons, no characters. ", 576, 1536, 890004),
    "bg_battle2": ("masterpiece, best quality, score_7, safe. "
        "dark swamp cavern interior, giant glowing mushrooms, hanging vines, shallow murky water floor, "
        "muted desaturated teal and olive palette, flat cel shaded painted illustration, bold shapes, "
        "video game battle background, empty scene, atmospheric but readable, no text, no characters. ", 1024, 576, 890005),
    "bg_battle3": ("masterpiece, best quality, score_7, safe. "
        "demon castle throne hall interior, tall dark pillars, torn red banners, braziers with embers, "
        "obsidian floor, muted desaturated dark red and charcoal palette, flat cel shaded painted illustration, "
        "bold shapes, video game battle background, empty scene, atmospheric but readable, no text, no characters. ", 1024, 576, 890006),
}

def build(seed, text, w, hgt):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_act"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":w,"height":hgt,"batch_size":1}},
      "44":{"class_type":"UNETLoader","inputs":{"unet_name":"anima-base-v1.0.safetensors","weight_dtype":"default"}},
      "45":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}}}

def post(p):
    req = urllib.request.Request(URL+"/prompt", data=json.dumps({"prompt":p}).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())

def wait(pid):
    t0 = time.time()
    while time.time()-t0 < 1800:
        with urllib.request.urlopen(URL+f"/history/{pid}", timeout=10) as r: hst = json.loads(r.read())
        if pid in hst: return hst[pid]
        time.sleep(2)
    raise TimeoutError(pid)

def fetch(fn, sub, ty):
    q = urllib.parse.urlencode({"filename":fn,"subfolder":sub,"type":ty})
    with urllib.request.urlopen(URL+"/view?"+q, timeout=30) as r: return r.read()

for name,(text,w,hgt,seed) in JOBS.items():
    print(f"[{name}]", flush=True)
    res = post(build(seed,text,w,hgt))
    result = wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
            print(" ->", name, flush=True)
print("DONE")
