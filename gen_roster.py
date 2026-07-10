# -*- coding: utf-8 -*-
"""大量ロースター生成: 雑魚20 + ボス4（計24体）"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human")
CHAR = ("masterpiece, best quality, score_7, safe. "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, slightly cute but menacing, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")
BOSSC = CHAR.replace("enemy character", "boss monster").replace("slightly cute but menacing", "imposing but slightly cute")

JOBS = {
    # ---- 第1章 翠緑の森 ----
    "boar":   (CHAR + "A wild armored boar with big curved tusks, bristly brown fur, stomping hoof, angry small eyes.", 910001),
    "bee":    (CHAR + "A big killer bee with striped fuzzy body, twin stingers, translucent fast wings, fierce eyes.", 910002),
    "pixie":  (CHAR + "A mischievous forest pixie with butterfly wings, tiny grinning face, holding a small wand, green tunic.", 910003),
    "snail":  (CHAR + "A giant armored snail with a rocky iron-like spiral shell, sturdy eyestalks, slime trail.", 910004),
    "fox":    (CHAR + "A mystical two-tailed fox spirit with pale cream fur, red markings around the eyes, floating small blue flame.", 910005),
    "crow":   (CHAR + "A sinister night crow with ragged black feathers, one gleaming yellow eye, sharp beak, perched pose.", 910006),
    # ---- 第2章 毒霧の沼窟 ----
    "toad":   (CHAR + "A poisonous swamp toad with warty purple-green skin, bloated body, dripping toxin, wide grumpy mouth.", 910007),
    "eel":    (CHAR + "A swamp electric eel rising from murky water, slick dark blue body, glowing small spots, needle teeth.", 910008),
    "mudman": (CHAR + "A mud golem made of dripping brown sludge, heavy fists, hollow round eyes, lumpy body.", 910009),
    "wisp":   (CHAR + "A pale blue will-o-wisp spirit flame with a small ghostly face inside, wispy fire tendrils.", 910010),
    "crab":   (CHAR + "A giant cave crab with thick spiky shell, one oversized crushing pincer, orange-brown carapace.", 910011),
    "sludge": (CHAR + "A toxic sludge slime, dark purple ooze blob with bubbles, sickly grin, dripping goo.", 910012),
    "turtle": (CHAR + "A rock turtle with a boulder-like mossy shell, stout legs, calm stubborn face.", 910013),
    # ---- 第3章 灼熱の魔城 ----
    "sala":   (CHAR + "A fire salamander lizard with ember-orange scales, flame patterns, small flames on its tail.", 910014),
    "bomber": (CHAR + "A small bomb devil imp carrying a huge round black bomb with a lit fuse, wicked excited grin.", 910015),
    "knight": (CHAR + "A dark knight in obsidian black armor with red cloth accents, heavy sword planted, glowing visor slit.", 910016),
    "hound":  (CHAR + "A hellhound with charcoal black fur, fiery mane, burning eyes, bared fangs, low prowling stance.", 910017),
    "ifrita": (CHAR + "A flame mage imp wearing a small wizard robe of fire pattern, casting a fireball, floating.", 910018),
    "skel":   (CHAR + "A skeleton soldier with a rusty sword and cracked round shield, missing a few teeth, old helmet.", 910019),
    "wraith": (CHAR + "A ghostly wraith knight, translucent spectral armor, hollow helmet with cold blue eyes, tattered cape.", 910020),
    # ---- ボス4種 ----
    "alraune": (BOSSC + "An alraune plant queen boss: a beautiful flower monster with a giant rose-like blossom body, thorned vine arms, elegant leafy crown.", 910021),
    "toadking":(BOSSC + "A giant toad king boss: a massive royal toad with a golden crown, warty emerald skin, huge belly, holding a lily-pad scepter.", 910022),
    "ifrit":  (BOSSC + "An ifrit fire djinn boss: a muscular flame spirit with burning mohawk, molten cracked skin, smoke lower body, golden bracers.", 910023),
    "reaper": (BOSSC + "A grim reaper boss: a hooded skeletal death spirit with a giant scythe, tattered black robe, cold violet inner glow, floating.", 910024),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_roster"}},
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
    print(f"[{name}]", flush=True)
    res=post(build(seed,text))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
print("ALL_DONE")
