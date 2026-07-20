# -*- coding: utf-8 -*-
"""正面顔だった雑魚敵19体を左向きに再生成 → assets_raw_fix/
usage: python gen_fix_enemies2.py [name ...]  (省略時は全件。既存ファイルはスキップ)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_fix")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, front view, facing viewer")
CHARL = ("masterpiece, best quality, score_7, safe. "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, slightly cute but menacing, "
    "full body, side view facing left, head turned to the left, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

JOBS = {
    "bat":    (CHARL + "A plump purple cave bat monster hovering with wide ragged wings, big yellow eyes, tiny white fangs, fuzzy round body, seen from the side facing left.", 931001),
    "golem":  (CHARL + "A bulky ancient stone golem made of stacked mossy gray boulders, deep cracks, two small pale blue eyes, massive fists, striding to the left.", 931002),
    "spore":  (CHARL + "A small mushroom shaman with a wide brown spotted cap, sleepy gentle face in profile, tiny body, holding a crooked leaf-topped twig staff, walking to the left.", 931003),
    "mandra": (CHARL + "A mandrake plant monster with a pale round root body, leafy sprout on its head, eerie blank face turned left, thin root arms and legs, hopping to the left.", 931004),
    "gargo":  (CHARL + "A stone gargoyle with folded bat wings, gray carved rock body, fanged grimace, crouching and lunging to the left, seen from the side.", 931005),
    "dragon": (CHARL + "A black dragon wyrm with dark leathery bat wings, deep red scaled underbelly, two curved horns, fanged snarling maw, clawed limbs, side profile lunging to the left.", 931006),
    "boar":   (CHARL + "A wild armored boar with big curved tusks, bristly brown fur, stomping hooves, angry small eyes, charging to the left in side view.", 931007),
    "pixie":  (CHARL + "A mischievous forest pixie with butterfly wings, tiny grinning face, holding a small wand, green tunic, flying to the left in profile.", 931008),
    "toad":   (CHARL + "A poisonous swamp toad with warty purple-green skin, bloated body, dripping toxin, wide grumpy mouth, side view facing left.", 931009),
    "mudman": (CHARL + "A mud golem made of dripping brown sludge, heavy fists, hollow round eyes, lumpy body, lurching to the left in side view.", 931010),
    "knight": (CHARL + "A dark knight in obsidian black armor with red cloth accents, glowing visor slit, holding a heavy sword, striding to the left in side view.", 931011),
    "thorn":  (CHARL + "A thorn-covered beast like a panther made of dark bramble vines, red berry eyes, rose thorns along its back, prowling to the left in side profile.", 931012),
    "yeti":   (CHARL + "A burly yeti with shaggy white-blue fur, ice crystal shoulders, big fists, frosty breath, lumbering to the left in side view.", 931013),
    "fgolem": (CHARL + "A golem made of jagged blue glacier ice blocks, frozen core visible in chest, heavy arms, stepping to the left in side view.", 931014),
    "djinn":  (CHARL + "A sand djinn with a swirling sandstorm lower body, muscular sandy upper body, brass bracers and golden earrings, smug grin, body turned to the left.", 931015),
    "mummy":  (CHARL + "A small mummy soldier wrapped in old bandages, one glowing eye through the wraps, holding a khopesh sword, shambling to the left in side view.", 931016),
    "raiju":  (CHARL + "A lightning beast like a fierce weasel, white-blue fur with yellow zigzag lightning markings, fierce grin, crouching and creeping to the left in side profile.", 931017),
    "ghoul":  (CHARL + "A hunched ghoul with grey-green skin, long claws, ragged shroud, hungry glowing eyes, creeping to the left in side view.", 931018),
    "bonek":  (CHARL + "A bone knight built of fused skeleton armor plates, skull pauldrons, wielding a jagged bone greatsword, advancing to the left in side view.", 931019),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_fix2"}},
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
