# -*- coding: utf-8 -*-
"""装飾UIフレーム（額縁型・9-slice/border-image用）をAnimaで生成 → assets_raw_ui/
深緑×真鍮のドロプシア新パレットに合わせる。中央はborder-image(fill無し)で未使用になるため加工不要。"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

# gen_ui_icons系NEGから frame/border 除外を外したもの（今回は枠そのものを作る）
NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, grainy, washed out colors, pale, desaturated, "
    "complex background, scenery, multiple objects, collage, "
    "cast shadow, ground shadow, drop shadow, reflection, asymmetric, tilted, perspective")

BASE = ("masterpiece, best quality, score_7, safe. "
    "a single ornate fantasy game UI frame, rectangular picture-frame shape filling the canvas, "
    "perfectly symmetrical, straight uniform edges, decorative corner ornaments, "
    "flat cel shading with bold dark outline, art style between Slay the Spire and Pokemon, "
    "completely empty plain white center, front view, flat 2d game asset, no text. ")

JOBS = {
    # 深緑×真鍮の額縁（メインパネル用）
    "frame_brass": BASE + "Dark emerald green lacquered wood frame with antique brass metal trim and small brass corner medallions, subtle carved leaf pattern.",
    # 石＋蔦（ダンジョン味）
    "frame_stone": BASE + "Dark grey-green carved stone frame with moss and thin emerald vine accents wrapping the corners, weathered dungeon style.",
    # シンプル真鍮細枠
    "frame_slim": BASE + "Slim elegant antique brass frame with dark emerald inlay line, minimal corner flourish, clean and refined.",
}
SEED0 = 951000

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_uiframe"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":1024,"height":1024,"batch_size":1}},
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
    seed = int(sd) if sd else SEED0 + names.index(name)
    print(f"[{name}] seed={seed} 生成中...", flush=True)
    r = post(build(seed, JOBS[name]))
    h = wait(r["prompt_id"])
    for node in h["outputs"].values():
        for im in node.get("images", []):
            data = fetch(im["filename"], im["subfolder"], im["type"])
            fp = os.path.join(OUT, f"{name}_{seed}.png")
            open(fp, "wb").write(data)
            print("  ->", fp, flush=True)
print("done")
