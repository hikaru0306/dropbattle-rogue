# -*- coding: utf-8 -*-
"""消費アイテム10種の塗りアイコンをAnimaで生成 → assets_raw_ui/
各アイテムは現在の絵文字のモチーフに合わせる（見た目を大きく変えない）。画風はgen_ui_iconsと共通。"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, grainy, washed out colors, pale, desaturated, "
    "complex background, scenery, frame, border, multiple objects, collage, "
    "cast shadow, ground shadow, drop shadow, reflection, puddle, stand, pedestal, base")

ICON = ("masterpiece, best quality, score_7, safe. "
    "a single fantasy game UI icon, flat cel shading with simple two-tone shadow, "
    "bold thick dark outline, art style between Slay the Spire and Pokemon, "
    "vivid saturated colors, chunky readable silhouette, "
    "one object only, centered, isolated on pure white background, no text. ")

JOBS = {
    "cs_potion":   "A science test tube with a rounded bottom filled with bright red healing liquid, a small cork stopper on top, like the test tube emoji.",
    "cs_might":    "A bold flexing muscular arm making a strong bicep, red skin tone, symbol of power and strength, like the flexed biceps emoji.",
    "cs_aegis":    "A sturdy round guard shield seen from the front, deep blue steel face with a bold gold rim, like the shield emoji.",
    "cs_colorize": "An artist paint palette with dabs of red blue green and yellow paint and a paintbrush, like the artist palette emoji.",
    "cs_purify":   "A simple cleaning broom with a bundle of golden straw bristles and a brown wooden handle, like the broom emoji.",
    "cs_stun":     "An hourglass with wooden top and bottom frame and blue sand inside, like the hourglass emoji.",
    "cs_bomb":     "A round black cartoon bomb with a short lit fuse sparking at the top, like the bomb emoji.",
    "cs_venom":    "A green coiled snake with an open mouth showing fangs, poisonous serpent, like the snake emoji.",
    "cs_gemrain":  "A single brilliant cut blue gem diamond, faceted and shiny, like the gem stone emoji.",
    "cs_phoenix":  "A single curved feather colored bright orange and red like fire, a phoenix plume, like the feather emoji.",
}
SEED0 = 891000

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_consum"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":640,"height":640,"batch_size":1}},
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
    seed = int(sd) if sd else SEED0 + names.index(name)
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed, ICON + JOBS[name]))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
    print(f"  done {name}", flush=True)
print("ALL_DONE")
