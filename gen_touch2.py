# -*- coding: utf-8 -*-
"""ユーザー指摘の17体を作画/向き/品質改善で再生成 → assets_raw_touch2/
3/4左向き・大人っぽく・顔と色をはっきり・接地影なし。
usage: python gen_touch2.py [name ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_touch2")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, blank hollow face, featureless, murky, muddy silhouette, "
    "cute, chibi, childish, kawaii, mascot, baby, toddler, cartoon for kids, oversized head, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile, "
    "front view, facing viewer, symmetrical pose, perfectly frontal")
BASE = ("masterpiece, best quality, highly detailed, clear readable design, distinct facial features, fully colored with rich flat cel shading, "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce and menacing, sharp mature design, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, one side toward the viewer, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. ")

JOBS = {
    "slime":  ("A round bouncy green slime monster with exactly two big glossy round eyes and a wide mischievous open grin, a smooth blob body with a darker green gel core inside, turned to the left.", 944001),
    "wolf":   ("A fierce silver wolf beast with shaggy silver-white and grey fur, a wild bushy mane, glowing yellow eyes, bared white fangs, a low prowling four-legged stance.", 944002),
    "spore":  ("A mushroom shaman monster with a wide brown white-spotted mushroom cap, a small pale mushroom-stalk body, a distinct grumpy little face with two dark eyes and a frown, gripping a leaf-topped twig staff.", 944003),
    "treant": ("An ancient treant tree monster with a thick gnarled brown bark trunk body, a clear angry face on the trunk with two glowing eyes and a frowning mouth, mossy twisted root legs, leafy branch arms.", 944004),
    "turtle": ("A rocky tortoise monster with a mossy green boulder shell, a sturdy blue-grey body and limbs, a grumpy determined face, thick clawed legs.", 944005),
    "vamp":   ("A vampire lord with a high-collared crimson-lined black cape flaring to one side, pale skin, slicked-back dark hair, glowing red eyes, sharp fangs, an elegant menacing pose.", 944006),
    "demon":  ("A demon lord boss Valga: a muscular deep-purple demon king, large curved beige horns, a small golden crown, a glowing red gem in its chest, dark bat wings, a fanged confident grin, clawed hands.", 944007),
    "owl":    ("A spooky spirit owl with midnight-blue feathers, a glowing crescent-moon crest on its forehead, wide glaring golden eyes, spread feathered wings, sharp talons.", 944008),
    "snail":  ("An armored iron snail monster with a heavy spiked rocky brown shell, a soft pale grey body, two small eye stalks with a grumpy face, a glistening trail.", 944009),
    "raiju":  ("A lightning beast like a fierce weasel, white and pale-blue fur with bright yellow zigzag lightning markings and lightning-bolt-shaped ears and tail, a fierce grin, a crouching four-legged pose.", 944010),
    "mummy":  ("A mummy soldier wrapped in aged beige bandages, one glowing red eye visible through the wraps, holding a curved khopesh sword, striding forward.", 944011),
    "djinn":  ("A sand djinn with a swirling tan sandstorm lower body, a muscular sandy-orange upper body, brass arm bracers and golden earrings, a smug confident grin, arms crossed.", 944012),
    "behemot":("A thunder behemoth, a colossal muscular bison-like beast with storm-grey hide, a big angry face with glowing yellow eyes and white tusks, lightning-bolt-shaped horns, a heavy four-legged stance.", 944013),
    "mare":   ("A nightmare horse with a smoky jet-black body, a burning violet flaming mane and tail, glowing violet eyes, violet flames around its hooves, a galloping stance.", 944014),
    "noct":   ("A queen of night boss: a vampiric dark queen with a large bat-wing cloak, pale skin, crimson eyes, holding a black rose scepter, an elegant flowing gothic dress.", 944015),
    "kaos":   ("A chaos imp with a big round head, one large eye and one small eye, a wide wicked toothy grin, mismatched horns, patchwork purple and black stitched skin, sharp clawed hands.", 944016),
    "drake":  ("A void drake wyvern with dark violet scales, wing membranes like a starry night sky, a long spiked tail, sharp curved horns, a fanged maw.", 944017),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_t2"}},
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
