# -*- coding: utf-8 -*-
"""正面向きだった31体を『3/4左向き(約45度)』で作り直し → assets_raw_front/
方針は gen_fix_all/gen_reroll と同一: 元デザイン尊重 / 若干左向き(45度・真横にしない) /
      大人っぽくシャープ(子供向け排除) / 接地影なし / AIっぽい安物ライティング排除
対称形状(スライム/雪結晶/目玉/球体)も顔と体を左に振る。
usage: python gen_front_left.py [name ...]  (省略時は全件。既存pngはスキップ)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_front")
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
BASE = ("masterpiece, best quality, highly detailed, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, one side toward the viewer, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

JOBS = {
    # --- A群(非対称) ---
    "scorp":  ("An armored scorpion monster with a segmented blue-gray carapace, orange glowing joints, a raised curved stinger tail, sharp pincers.", 942001),
    "treant": ("An ancient treant tree monster with a gnarled brown bark body, an angry face in its trunk, mossy twisted roots for legs, small mushrooms on its branches.", 942002),
    "hound":  ("A hellhound with charcoal black fur, a fiery mane, burning eyes, bared fangs, a low prowling stance.", 942003),
    "dryad":  ("A corrupted dryad tree spirit with a small dark wooden body, dark leaves, sad glowing eyes, twisted branch arms.", 942004),
    "peng":   ("A grumpy blizzard penguin soldier holding an icicle spear, a tiny frost crown, a round body.", 942005),
    "cobra":  ("A thunder cobra snake with yellow lightning-bolt markings, a spread hood, crackling sparks on its fangs, a coiled tail.", 942006),
    "sphinx": ("A majestic sand sphinx with a golden pharaoh headdress, a lion body, folded wings, a riddling smile.", 942007),
    "golem":  ("A bulky ancient stone golem made of stacked mossy gray boulders, deep cracks, two small pale blue eyes, massive heavy fists.", 942008),
    "mudman": ("A mud golem made of dripping brown sludge, heavy fists, hollow round eyes, a lumpy body.", 942009),
    "fgolem": ("A golem made of jagged blue glacier ice blocks, a frozen core in its chest, heavy arms.", 942010),
    "ifrit":  ("A mighty ifrit fire djinn: a muscular flame spirit with a burning mohawk, molten cracked skin, a smoke lower body, golden bracers.", 942011),
    "alraune":("An alraune plant queen with a giant rose-like blossom body, thorned vine arms, an elegant leafy crown.", 942012),
    "skadi":  ("An ice witch: a frost sorceress with long white hair, a crystal ice staff, a snowflake tiara, a gown of glacier shards.", 942013),
    # --- B群(対称)。顔と体を左へ ---
    "slime":  ("A round bouncy green slime monster with two big glossy eyes and a mischievous open smile turned to the left, a blob body with a darker green gel layer inside.", 942014),
    "shade":  ("A ghostly wraith specter with a tattered dark indigo cloak fading into wisps at the bottom, hollow pale white eyes, thin shadowy arms, drifting to the left.", 942015),
    "bee":    ("A big killer bee with a striped fuzzy body, twin stingers, translucent wings, fierce eyes, hovering angled to the left.", 942016),
    "fox":    ("A mystical two-tailed fox spirit with pale cream fur, red markings around the eyes, a floating small blue flame, prowling to the left.", 942017),
    "wisp":   ("A pale blue will-o-wisp spirit flame with a small ghostly face inside looking to the left, wispy fire tendrils.", 942018),
    "crab":   ("A giant cave crab with a thick spiky shell, one oversized crushing pincer, an orange-brown carapace, angled to the left.", 942019),
    "sludge": ("A toxic sludge slime, a dark purple ooze blob with bubbles, a sickly grin turned to the left, dripping goo.", 942020),
    "bomber": ("A small bomb devil imp carrying a huge round black bomb with a lit fuse, a wicked excited grin, leaning to the left, hovering in the air with nothing beneath it.", 942121),
    "moth":   ("A dark poison moth with dusty violet wings bearing moon-like eye patterns, a fluffy body, curled antennae, angled to the left.", 942022),
    "owl":    ("A spooky spirit owl with midnight blue feathers, a crescent moon crest on its forehead, wide glaring golden eyes, body turned to the left.", 942023),
    "frost":  ("A pale ice wisp spirit, a snowflake-shaped flame with a small cold face inside looking to the left, trailing frost.", 942024),
    "scarab": ("A giant golden scarab beetle with a thick gleaming gold carapace, a gem on its back, sturdy legs, angled to the left.", 942025),
    "banshee":("A wailing banshee ghost with flowing spectral hair swept to one side, a tattered pale dress, a screaming face turned to the left.", 942026),
    "eye":    ("An evil floating eyeball monster with a big violet iris looking to the left, two large bat wings on its sides, short dark tentacles below.", 942027),
    "voids":  ("A void slime blob of dark starry goo with tiny galaxies swirling inside, a wide blank grin turned to the left.", 942028),
    "gazer":  ("A void gazer: a floating dark orb monster with one huge central eye with a violet iris looking to the left, thick crystal spikes, tiny stars on its body.", 942029),
    "bat":    ("A plump purple cave bat monster with wide ragged wings, big yellow eyes, tiny white fangs, a fuzzy round body, angled to the left.", 942030),
    "kslime": ("A giant king slime: a huge glossy green slime blob wearing a small golden crown, angry dark eyes turned to the left, jelly highlights, imposing bulk.", 942031),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_front"}},
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
