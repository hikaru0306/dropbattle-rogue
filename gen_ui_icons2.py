# -*- coding: utf-8 -*-
"""バトルUIの絵文字を塗りアイコン化する追加分をAnimaで生成 → assets_raw_ui/
画風は gen_ui_icons.py と完全共通（ICON/NEG 流用）。既存塗りアセットに無いものだけ。"""
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
    # ―― 敵ステータスバッジ ――
    "st_enrage":  "A bold emblem of two thick red arrows pointing straight upward stacked one above the other, a rising surge of power, aggressive fiery red with orange edges, arrowheads clearly pointing up.",
    "st_dcap":    "A bold circular prohibition no-entry sign, a thick glossy red ring with a strong white horizontal bar across the center, a forbidden barrier symbol, red and white with a dark outline.",
    "st_poison":  "A single large glossy green venom droplet with a small white skull mark inside it, dripping toxic ooze, sickly bright green.",
    # ―― 敵の行動予告アイコン ――
    "intent_big":    "A classic cartoon comic explosion boom, a jagged spiky burst cloud shape with bright orange yellow and red, dynamic collision blast symbol like the boom emoji.",
    "intent_charge": "A small ornate golden hourglass with bright blue sand inside, polished brass frame, symbol of charging up.",
    "intent_jam":    "A swirling dark purple whirlpool vortex, a thick concentric spiral emblem, murky violet.",
    "intent_drain":  "A single big glossy bright red blood droplet, smooth teardrop shape with a small white highlight, like the blood drop emoji.",
    "intent_curse":  "A sinister curved dark dagger with thick violet shadow flames wrapping and swirling around the entire blade, an ominous cursed weapon emblem, bold chunky purple and black shape.",
    # ―― 鍛冶キャラの3つ目ボタン ――
    "sk_stock":  "A brown cardboard shipping box closed with tape, a small three-quarter front view parcel, supply package like the package box emoji.",
    "sk_gen":    "A cluster of bright golden sparkle stars, one large four-pointed sparkle shine with two small four-pointed sparkles beside it, like the sparkles emoji.",
    "sk_forge":  "A blacksmith hammer and a pickaxe crossed together forming an X, brown wooden handles and steel heads, crafting tools emblem like the hammer and pick emoji.",
}
SEED0 = 889200

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_uiicon2"}},
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
