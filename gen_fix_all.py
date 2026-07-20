# -*- coding: utf-8 -*-
"""触った全敵42体を改善プロンプトで作り直し → assets_raw_final/
方針: 元デザインを尊重 / 若干左向き(3/4・真横にしない) / 大人っぽくシャープ(子供向け排除) /
      接地影なし / AIっぽい安物ライティング(グロー・リムライト)排除
usage: python gen_fix_all.py [name ...]  (省略時は全件。既存ファイルはスキップ=リロールは該当pngを消す)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_final")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, "
    "cute, chibi, childish, kawaii, mascot, baby, toddler, cartoon for kids, oversized head, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile")
BASE = ("masterpiece, best quality, highly detailed, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, chunky readable silhouette, "
    "full body, three-quarter view with the body only slightly turned to the left, gaze toward the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

# name: (desc, seed)   seed=94xxxx。dragon/knight/demon はパイロット採用seed。
JOBS = {
    # --- 画風が浮いていた雑魚(最初の10) ---
    "skel":  ("A skeleton soldier with chipped bone armor, a rusted short sword and a small battered round shield, a single blue soul flame in one eye socket.", 940101),
    "imp":   ("A small mischievous red imp devil with tiny bat wings, curved cream horns, an arrow-tipped tail, sharp little claws, a wicked toothy grin.", 940102),
    "kslime":("A giant king slime: a huge glossy green slime blob wearing a small golden crown, angry dark eyes, lighter green jelly highlights, imposing bulk.", 940103),
    "ifrita":("A flame mage in a flowing ember-orange hooded robe with flame patterns, a dark shadowed hood with glowing eyes, holding a floating fireball in one hand.", 940104),
    "vamp":  ("A vampire lord with a high-collared crimson and black cape spread like bat wings, pale skin, slicked dark hair, red eyes, sharp fangs, an elegant menacing pose.", 940105),
    "reaper":("A grim reaper wraith in a tattered dark violet hooded robe, a white skull face, bony hands holding a long scythe, a ragged robe hem.", 940106),
    "gazer": ("A void gazer: a floating dark orb monster with one huge central eye with a bright violet iris and a dark pupil, thick crystal spikes on its round body, tiny stars speckled on the dark body.", 940107),
    "kaos":  ("A chaos imp goblin with a big round head, one large eye and one small eye, a wide wicked grin with sharp teeth, mismatched horns, patchwork purple and black skin with stitches, clawed hands.", 940108),
    "mant":  ("A shadow mantis with sickle arms like dark blades, dark green chitin plates, a low hunting stance, narrow glowing eyes.", 940109),
    "eel":   ("A swamp eel monster rising from murky dark water, a long slick dark teal serpentine body, a pale belly, ragged fins, big yellow eyes, an open mouth with needle teeth.", 940110),
    # --- 正面顔だった雑魚(19) ---
    "bat":    ("A plump purple cave bat monster with wide ragged wings, big yellow eyes, tiny white fangs, a fuzzy round body.", 940111),
    "golem":  ("A bulky ancient stone golem made of stacked mossy gray boulders, deep cracks, two small pale blue eyes, massive heavy fists.", 940112),
    "spore":  ("A small mushroom shaman with a wide brown spotted mushroom cap, a sleepy gentle face, a tiny body, holding a crooked leaf-topped twig staff.", 940113),
    "mandra": ("A mandrake plant monster with a pale round root body, a leafy sprout on its head, an eerie blank face, thin root arms and legs.", 940114),
    "gargo":  ("A stone gargoyle with folded bat wings, a gray carved rock body, a fanged grimace, a crouching lunging pose.", 940115),
    "dragon": ("A fearsome black dragon: sleek dark scales, a deep red scaled belly and chest, large black leathery bat wings, curved horns, a fanged snarling maw, two clawed legs, a long spiked tail.", 940001),
    "boar":   ("A wild armored boar with big curved tusks, bristly brown fur, stomping hooves, angry small eyes, a charging stance.", 940117),
    "pixie":  ("A mischievous forest pixie with butterfly wings, a small grinning face, holding a tiny wand, a green tunic.", 940118),
    "toad":   ("A poisonous swamp toad with warty purple-green skin, a bloated body, dripping toxin, a wide grumpy mouth.", 940119),
    "mudman": ("A mud golem made of dripping brown sludge, heavy fists, hollow round eyes, a lumpy body.", 940120),
    "knight": ("A menacing dark knight: heavy obsidian black plate armor with crimson cloth accents, a horned helm with a single glowing slit, gauntleted hands gripping a massive greatsword.", 940002),
    "thorn":  ("A thorn-covered beast like a panther made of dark bramble vines, red berry eyes, rose thorns along its back, a prowling stance.", 940122),
    "yeti":   ("A burly yeti with shaggy white-blue fur, ice crystal shoulders, big fists, frosty breath.", 940123),
    "fgolem": ("A golem made of jagged blue glacier ice blocks, a frozen core visible in its chest, heavy arms.", 940124),
    "djinn":  ("A sand djinn with a swirling sandstorm lower body, a muscular sandy upper body, brass bracers and golden earrings, a smug grin.", 940125),
    "mummy":  ("A small mummy soldier wrapped in old bandages, one glowing eye through the wraps, holding a khopesh sword.", 940126),
    "raiju":  ("A lightning beast like a fierce weasel, white-blue fur with yellow zigzag lightning markings, a fierce grin, a crouching pose.", 940127),
    "ghoul":  ("A hunched ghoul with grey-green skin, long claws, a ragged shroud, hungry glowing eyes.", 940128),
    "bonek":  ("A bone knight built of fused skeleton armor plates, skull pauldrons, wielding a jagged bone greatsword.", 940129),
    # --- ボス(13) ---
    "demon":  ("A powerful demon lord: a muscular deep-purple demon king, large curved beige horns, a golden crown, a glowing red gem set in its chest, dark bat wings, a fanged confident grin, clawed hands.", 940003),
    "ifrit":  ("A mighty ifrit fire djinn: a muscular flame spirit with a burning mohawk, molten cracked skin, a smoke lower body, golden bracers.", 940131),
    "lich":   ("A lich king: an undead sorcerer in tattered deep-teal robes, a bony crowned skull face, holding a gnarled staff, a small blue soul flame floating beside him.", 940132),
    "wraith": ("A wraith knight: a ghostly knight in translucent spectral armor, a hollow helmet with cold blue eyes, a tattered flowing cape, holding a spectral blade.", 940133),
    "alraune":("An alraune plant queen: a beautiful flower monster with a giant rose-like blossom body, thorned vine arms, an elegant leafy crown.", 940134),
    "fenrir": ("A moon wolf king: a giant regal wolf standing proudly, silver-white fur, a golden crescent moon marking on its forehead, a dark blue royal cape, a fierce expression.", 940135),
    "titania":("A phantom fairy queen: an elegant fae monarch with four moth-like wings, a thorn crown, a flowing gown of petals and mist, a mischievous smile.", 940136),
    "skadi":  ("An ice witch: a frost sorceress with long white hair, a crystal ice staff, a snowflake tiara, a gown of glacier shards, a cold confident smirk.", 940137),
    "jotun":  ("A frost giant: a towering jotun with blue skin, an ice beard, fur and bronze armor, a huge ice club, a frozen crown.", 940138),
    "behemot":("A thunder behemoth: a colossal muscular bison-like beast with storm-grey hide, a big angry face with glowing yellow eyes and tusks, lightning-bolt-shaped horns, a heavy four-legged stance.", 940139),
    "bdragon":("An undead bone dragon: a skeletal dragon with ragged wing membranes, green soul fire in its ribcage and eye sockets, a broken crown.", 940140),
    "noct":   ("A queen of night: a vampiric dark queen with a bat-wing cloak, pale skin, crimson eyes, a black rose scepter, an elegant gothic dress.", 940141),
    "demonx": ("A true demon lord final boss: a massive demon king with six curved horns, a burning violet third eye, obsidian armor with gold trim, twin greatswords, a cape of black flames.", 940142),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_final"}},
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
