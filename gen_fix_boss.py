# -*- coding: utf-8 -*-
"""正面向きボス13体を3/4ビュー（若干左向き）に再生成 → assets_raw_fix/
威厳キープのため真横ではなく three-quarter view。既に横/座り姿勢の sphinx/vorax/toadking/reaper は対象外。
usage: python gen_fix_boss.py [name ...]  (省略時は全件。既存ファイルはスキップ)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_fix")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, strict front view, perfectly symmetrical pose")
# 威厳を残す 3/4 ビュー（真横にしない）
BOSSL = ("masterpiece, best quality, score_7, safe. "
    "fantasy game boss monster design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, imposing but slightly cute, "
    "full body, three-quarter view with the body slightly turned to the left, head facing left, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

JOBS = {
    "demon":  (BOSSL + "A demon lord boss: a muscular purple demon king with large curved horns, a small golden crown, a glowing red gem on its chest, dark bat wings, fanged confident grin.", 932001),
    "ifrit":  (BOSSL + "An ifrit fire djinn boss: a muscular flame spirit with a burning mohawk, molten cracked skin, smoke lower body, golden bracers, torso twisted 45 degrees to the left, one fist thrust forward to the left, glaring to the left.", 932102),
    "lich":   (BOSSL + "A lich king boss: an undead sorcerer in tattered deep-teal robes, a bony crowned skull face, holding a gnarled staff, a small blue soul flame floating beside him.", 932003),
    "wraith": (BOSSL + "A wraith knight boss: a ghostly knight in translucent spectral armor, hollow helmet with cold blue eyes, tattered flowing cape swept to one side, body rotated 45 degrees to the left, lunging forward to the left, thrusting a spectral blade to the left.", 932104),
    "alraune":(BOSSL + "An alraune plant queen boss: a beautiful flower monster with a giant rose-like blossom body, thorned vine arms, elegant leafy crown, the whole plant leaning and tilted to the left, vines sweeping to the left, blossom face turned to the left.", 932105),
    "fenrir": (BOSSL + "A moon wolf king boss: a giant regal wolf standing proudly, silver-white fur, golden crescent moon marking on its forehead, dark blue royal cape, fierce expression.", 932006),
    "titania":(BOSSL + "A phantom fairy queen boss: an elegant fae monarch with four moth-like wings held asymmetrically with one wing swept forward, thorn crown, flowing gown of petals and mist trailing to one side, body turned 45 degrees to the left, gazing to the left with a mischievous smile.", 932107),
    "skadi":  (BOSSL + "An ice witch boss: a frost sorceress with long white hair, crystal ice staff, snowflake tiara, gown of glacier shards, cold confident smirk.", 932008),
    "jotun":  (BOSSL + "A frost giant boss: a towering jotun with blue skin, ice beard, fur and bronze armor, huge ice club, frozen crown.", 932009),
    "behemot":(BOSSL + "A thunder behemoth boss: a colossal muscular bison-like beast with storm-grey hide, big angry face with glowing yellow eyes and tusks, lightning-bolt-shaped horns, heavy four-legged stance.", 932010),
    "bdragon":(BOSSL + "An undead bone dragon boss: a skeletal dragon with ragged wing membranes, green soul fire in ribcage and eye sockets, broken crown.", 932011),
    "noct":   (BOSSL + "A queen of night boss: a vampiric dark queen with a bat-wing cloak swept to one side, pale skin, crimson eyes, holding a black rose scepter forward, elegant gothic dress trailing to the left, body rotated 45 degrees to the left, looking to the left.", 932112),
    "demonx": (BOSSL + "A true demon lord final boss: a massive demon king with six curved horns, burning violet third eye, obsidian armor with gold trim, twin greatswords held to one side, cape of black flames streaming to the left, body turned 45 degrees to the left in a dynamic menacing stance, glaring to the left.", 932113),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_fixb"}},
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
    text, seed = JOBS[name]
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed,text))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
print("ALL_DONE")
