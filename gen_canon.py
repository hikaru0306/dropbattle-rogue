# -*- coding: utf-8 -*-
"""8人目「調律師カノン」一式をAnimaで生成 → assets_raw_canon/
  hero8        : 立ち絵（既存hero*と同じ画風・約3.5等身）
  mk_chord     : 専用ドロップ「響石」の盤面マーク
  rl_tuningfork / rl_echobell / rl_grandchord : 専用レリック3種
画風は gen_chars.py（キャラ）/ gen_relics.py（アイコン）の確定プロンプトを踏襲。
使い方: python gen_canon.py [name[=seed] ...]   （引数なしで全部）
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_canon")
os.makedirs(OUT, exist_ok=True)
SEED0 = 960100

# ―― キャラ立ち絵（gen_chars.py の STYLE/NEG を踏襲）――
CHAR_STYLE = ("masterpiece, best quality, score_7, safe. "
    "anime style JRPG hero character design, about three and a half heads tall, "
    "large head with big expressive anime eyes, small compact body, short limbs, "
    "wide chunky readable silhouette, voluminous flaring costume with lots of layered fabric, "
    "bold thick black outline, rich smooth gradient cel shading, vivid saturated colors, "
    "ornate fantasy costume with heavy gold trim, "
    "full body, three-quarter view clearly turned to the right, body and gaze toward the right side, "
    "solo, centered, plain solid white background, even lighting, no shadow on the ground, "
    "no text, no watermark, mobile game character art. ")
CHAR_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, neon colors, lens flare, shiny, glossy highlights, rim light, backlight, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, multiple characters, character sheet, multiple views, duplicate, "
    "background scenery, cropped, out of frame, ground shadow, cast shadow, "
    "tall adult proportions, five heads tall, eight heads tall, slim narrow figure, "
    "long thin legs, thin silhouette, high heels, plain tights, "
    "dull desaturated colors, washed out, dark muddy colors, "
    "modern clothing, business suit, tuxedo, sci-fi, mecha, teal green robe, cream robe")

# ―― アイコン（gen_relics.py の ICON/NEG を踏襲）――
ICON = ("masterpiece, best quality, score_7, safe. "
    "a single fantasy game relic icon, flat cel shading with simple two-tone shadow, "
    "bold thick dark outline, art style between Slay the Spire and Pokemon, "
    "vivid saturated colors, chunky readable silhouette, "
    "one object only, centered, isolated on pure white background, no text. ")
ICON_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, grainy, washed out colors, pale, desaturated, "
    "complex background, scenery, frame, border, multiple objects, collage, "
    "cast shadow, ground shadow, drop shadow, reflection, puddle, stand, pedestal, base")

JOBS = {
    # name: (kind, prompt)
    "hero8": ("char",
        "A small genius tuner girl scholar with silver white hair in a short side ponytail, "
        "big pale blue eyes behind round gold-rimmed glasses, a calm knowing smile, "
        "wearing a voluminous royal blue long coat with wide flaring skirt and heavy gold embroidery, "
        "a big white ruffled cravat at the collar, wide gold-trimmed cuffs, sturdy brown boots, "
        "holding a tall wooden staff topped with a large brass tuning fork, the staff taller than she is, "
        "a big antique brass pocket watch hanging on a chain at her hip, "
        "vivid royal blue, warm gold, ivory and silver white color palette"),
    "mk_chord": ("icon",
        "A single smooth teal green resonance stone, a rounded polished gem with three concentric "
        "ring grooves carved on its face like sound waves, warm gold rim around the edge"),
    "rl_tuningfork": ("icon",
        "A large bronze tuning fork seen from the front, a thick U shape with two straight parallel prongs "
        "pointing up and a short stubby handle at the bottom, warm brass and gold color, "
        "a deep indigo blue cord tied around the handle, wide sturdy proportions"),
    "rl_echobell": ("icon",
        "A small round golden hand bell with a dark wooden handle, a deep indigo blue ribbon tied to "
        "the handle, the bell mouth facing down"),
    "rl_grandchord": ("icon",
        "An open old parchment music score sheet with bold black musical notes on staff lines, "
        "ivory parchment with worn edges, gold corner fittings and a deep indigo blue ribbon bookmark"),
}

def build(seed, text, neg, size, steps):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_canon"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":steps,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":size,"height":size,"batch_size":1}},
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
names = list(JOBS.keys())
for spec in targets:
    name, _, sd = spec.partition("=")
    dst = os.path.join(OUT, f"{name}.png")
    if os.path.exists(dst) and not sd:
        print("skip", name, flush=True); continue
    kind, prompt = JOBS[name]
    seed = int(sd) if sd else SEED0 + names.index(name)
    style, neg, size, steps = (CHAR_STYLE, CHAR_NEG, 768, 32) if kind == "char" else (ICON, ICON_NEG, 576, 30)
    print(f"[{name}] kind={kind} seed={seed}", flush=True)
    res = post(build(seed, style + prompt, neg, size, steps))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dst, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
    print(f"  done {name}", flush=True)
print("ALL_DONE")
