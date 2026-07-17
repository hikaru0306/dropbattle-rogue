# -*- coding: utf-8 -*-
"""行商人キャラ＆タイトル背景をAnimaで生成 → assets_raw_ui/
merchant=チビ・セル塗り(透過用に白背景)、title=情景(背景あり・JPG想定)。
usage: python gen_merchant_title.py [name=seed ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

NEG_CHAR = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "photorealistic, realistic, 3d, cgi, render, photograph, text, watermark, signature, logo, "
    "cropped, out of frame, extra limbs, bad hands, bad anatomy, "
    "complex background, scenery, frame, border, multiple characters, "
    "cast shadow, ground shadow, drop shadow, reflection, pedestal, base")
NEG_SCENE = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "photorealistic, realistic, 3d, cgi, render, photograph, text, watermark, signature, logo, "
    "extra limbs, bad hands, bad anatomy, oversaturated, garish")

CHAR = ("masterpiece, best quality, score_7, safe. "
    "a cute chibi fantasy character, big head small body, bold thick dark outline, flat cel shading with two-tone shadow, "
    "art style between Slay the Spire and Pokemon, vivid saturated colors, ornate detailed costume, "
    "full body, standing, front view, isolated on pure white background, no text. ")
SCENE = ("masterpiece, best quality, score_7, safe. "
    "fantasy game title key art, flat vector illustration with bold clean shapes and cel shading, "
    "dramatic cinematic composition, teal and deep green twilight palette with warm gold accents, "
    "moody atmospheric, highly detailed background. ")

# name: (prompt, is_scene)
JOBS = {
    "merchant":   (CHAR + "a jolly traveling merchant peddler wearing a brown hooded traveling cloak with gold trim, "
                   "carrying a huge bulging backpack stuffed with pots bottles and wares, holding out a small coin pouch, "
                   "warm friendly smile, round cheeks, floating, hovering, nothing underneath, no shadow on the ground.", False),
    "merchant2":  (CHAR + "a mysterious hooded traveling merchant in a deep teal and purple robe with gold embroidery, "
                   "a wide-brim hat, a big pack of goods and a lantern on the back, holding a golden coin, sly friendly grin.", False),
    "title_a":    (SCENE + "a small chibi hero in a purple robe and pointed wizard hat holding an ornate staff, seen from behind on a cliff edge, "
                   "gazing across a valley at a dark demon castle with glowing red eyes atop a distant mountain, huge pale moon behind it, "
                   "pine forest and a winding glowing path, magical floating colored gem drops in the air.", True),
    "title_b":    (SCENE + "an epic dark dungeon gate glowing with magical colored gems, four tiny chibi hero silhouettes standing before it, "
                   "a towering demon king shadow looming above, swirling colored drop gems (red blue green yellow) floating around, "
                   "moonlit mountains in the background.", True),
    "title_c":    (SCENE + "a chibi hero party of four adventurers standing heroically on a hilltop at twilight, facing a distant demon castle, "
                   "colorful magic gem drops raining from the sky, dramatic clouds and a large moon, sweeping fantasy vista.", True),
}
SEED0 = 890300

def build(seed, text, neg, w, h):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_mt"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":34,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":w,"height":h,"batch_size":1}},
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
    if os.path.exists(os.path.join(OUT, f"{name}.png")):
        print("skip", name, flush=True); continue
    prompt, is_scene = JOBS[name]
    seed = int(sd) if sd else SEED0 + names.index(name)
    neg = NEG_SCENE if is_scene else NEG_CHAR
    w, h = (832, 1216) if is_scene else (768, 768)
    print(f"[{name}] seed={seed} {w}x{h}", flush=True)
    res=post(build(seed, prompt, neg, w, h))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
    print(f"  done {name}", flush=True)
print("ALL_DONE")
