# -*- coding: utf-8 -*-
"""裏ステージ用ロースター生成: 雑魚25 + ボス10（計35体） → assets_raw_ura/"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ura")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless")
CHAR = ("masterpiece, best quality, score_7, safe. "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, slightly cute but menacing, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")
BOSSC = CHAR.replace("enemy character", "boss monster").replace("slightly cute but menacing", "imposing but slightly cute")

JOBS = {
    # ---- 裏1章 月影の森 ----
    "moth":   (CHAR + "A dark poison moth with dusty violet wings bearing moon-like eye patterns, fluffy body, curled antennae.", 920001),
    "thorn":  (CHAR + "A thorn-covered beast like a panther made of dark bramble vines, red berry eyes, rose thorns along its back.", 920002),
    "owl":    (CHAR + "A spooky spirit owl with midnight blue feathers, crescent moon crest on forehead, wide glaring golden eyes.", 920003),
    "dryad":  (CHAR + "A corrupted dryad tree spirit, small wooden body with dark leaves, sad glowing eyes, twisted branch arms.", 920004),
    "mant":   (CHAR + "A shadow mantis with sickle arms like dark blades, dark green chitin, low hunting stance.", 920005),
    # ---- 裏2章 氷晶の霊窟 ----
    "yeti":   (CHAR + "A burly yeti with shaggy white-blue fur, ice crystal shoulders, big fists, frosty breath.", 920011),
    "icewolf":(CHAR + "A frost wolf with pale blue fur, icicle mane, freezing mist from its mouth, sharp icy claws.", 920012),
    "fgolem": (CHAR + "A golem made of jagged blue glacier ice blocks, frozen core visible in chest, heavy arms.", 920013),
    "peng":   (CHAR + "A grumpy blizzard penguin soldier with an icicle spear, tiny crown of frost, round body.", 920014),
    "frost":  (CHAR + "A pale ice wisp spirit, floating snowflake-shaped flame with a small cold face inside, trailing frost sparkles.", 920015),
    # ---- 裏3章 雷鳴の砂海 ----
    "djinn":  (CHAR + "A sand djinn with a swirling sandstorm lower body, muscular sandy upper body, brass bracers and golden earrings, smug grin.", 920221),
    "cobra":  (CHAR + "A thunder cobra snake with yellow lightning bolt markings, spread hood, crackling sparks on fangs.", 920022),
    "scarab": (CHAR + "A giant golden scarab beetle with a thick gleaming gold carapace, gem embedded on its back, sturdy legs.", 920023),
    "mummy":  (CHAR + "A small mummy soldier wrapped in old bandages, one glowing eye through the wraps, khopesh sword.", 920024),
    "raiju":  (CHAR + "A lightning beast raiju like a fierce weasel, white-blue fur with yellow zigzag lightning-shaped markings painted on its fur, fierce grin, crouching pose.", 920225),
    # ---- 裏4章 奈落の霊廟 ----
    "ghoul":  (CHAR + "A hunched ghoul with grey-green skin, long claws, ragged shroud, hungry glowing eyes.", 920031),
    "banshee":(CHAR + "A wailing banshee ghost with flowing spectral hair, tattered pale dress, screaming face, floating.", 920032),
    "bonek":  (CHAR + "A bone knight built of fused skeleton armor plates, skull pauldrons, jagged bone greatsword.", 920033),
    "eye":    (CHAR + "An evil floating eyeball monster with a big violet iris, two large bat wings attached to its sides, short dark tentacles hanging below, smooth clean thick lineart.", 920234),
    "mare":   (CHAR + "A nightmare ghost horse with smoky black body, burning violet mane, glowing hoofprints.", 920035),
    # ---- 裏5章 星淵の魔殿 ----
    "voids":  (CHAR + "A void slime blob of dark starry goo with tiny galaxies swirling inside, wide blank grin.", 920041),
    "cosmo":  (CHAR + "A cosmic beast like a bison made of deep night sky, constellation lines on its body, star-tipped horns.", 920042),
    "gazer":  (CHAR + "A void gazer: a floating dark orb monster with one huge central eye with a bright violet iris and a dark pupil, glaring, thick crystal spikes growing out of its round body, smooth clean thick lineart.", 920343),
    "kaos":   (CHAR + "A chaos imp facing the viewer with a wide wicked grinning face, mismatched horns, patchwork purple and black skin, clawed hands raised.", 920244),
    "drake":  (CHAR + "A void drake wyvern with dark violet scales, wing membranes like the night sky full of stars, sharp tail.", 920045),
    # ---- 裏ボス10種 ----
    "fenrir": (BOSSC + "A moon wolf king boss: a giant regal wolf standing proudly, silver-white fur, golden crescent moon marking on its forehead, dark blue royal cape, fierce expression.", 920251),
    "titania":(BOSSC + "A phantom fairy queen boss: an elegant fae monarch with four moth-like wings, thorn crown, flowing gown of petals and mist, mischievous smile.", 920052),
    "skadi":  (BOSSC + "An ice witch boss: a frost sorceress with long white hair, crystal ice staff, snowflake tiara, gown of glacier shards, cold confident smirk.", 920053),
    "jotun":  (BOSSC + "A frost giant boss: a towering jotun with blue skin, ice beard, fur and bronze armor, huge ice club, frozen crown.", 920054),
    "behemot":(BOSSC + "A thunder behemoth boss: a colossal muscular bison-like beast with storm-grey hide, big angry face with glowing yellow eyes and tusks, lightning-bolt-shaped horns, heavy four-legged stance.", 920255),
    "sphinx": (BOSSC + "A sand sphinx boss: a majestic sphinx with a golden headdress, lion body, folded wings, riddle-smile, sitting on a sand dune.", 920056),
    "bdragon":(BOSSC + "An undead bone dragon boss: a skeletal dragon with ragged wing membranes, green soul fire in ribcage and eye sockets, broken crown.", 920057),
    "noct":   (BOSSC + "A queen of night boss: a vampiric dark queen with bat-wing cloak, pale skin, crimson eyes, black rose scepter, elegant gothic dress.", 920058),
    "vorax":  (BOSSC + "A star-devourer dragon boss: a huge dragon with dark indigo scales sprinkled with tiny stars, pale cream belly plates, glowing white eyes, galaxy-pattern wing membranes, jaws biting a small golden star, ancient curved horns.", 920159),
    "demonx": (BOSSC + "A true demon lord final boss: a massive demon king with six curved horns, burning violet third eye, obsidian armor with gold trim, twin greatswords, cape of black flames.", 920060),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_ura"}},
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
