# -*- coding: utf-8 -*-
"""mk_chip をジョーカーマーク金貨に差し替え用の候補生成 -> assets_cand/mkchip_*.png (640px raw)
画風は gen_ui_icons.py と同一 (ICON/NEG/anima-base/qwen/er_sde/simple/cfg4.5/steps32/640)
"""
import json, os, time, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")

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

# 金貨(オレンジ寄りの金)にジョーカー(道化帽 二又+鈴)の刻印。視認性最優先。
JOBS = {
    # a: 二又ジェスター帽シルエット刻印 (hero7 の帽子に対応)
    "mkchip_a": "A single thick round gold coin seen from the front, warm orange gold metal with a darker orange rim, "
        "a bold dark embossed silhouette of a two pointed jester fool hat with two small round bells stamped in the center, "
        "clean simple emblem, flat readable design.",
    # b: 道化師の顔の刻印
    "mkchip_b": "A single thick round gold coin seen from the front, warm orange gold metal with a darker orange rim, "
        "a bold dark embossed jester clown face emblem with a wide grin and a two pointed cap stamped in the center, "
        "clean simple symbol, flat readable design.",
    # c: 三又ジェスター帽シルエット刻印
    "mkchip_c": "A single thick round gold coin seen from the front, warm orange gold metal with a darker orange rim, "
        "a bold dark embossed silhouette of a three pointed jester fool cap with small bells stamped in the center, "
        "clean simple emblem, flat readable design.",
}
SEEDS = [706011, 424242]

def build(seed, text, prefix):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":prefix}},
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

for name, text in JOBS.items():
    for si, seed in enumerate(SEEDS, 1):
        dest = os.path.join(CAND, f"{name}{si}.png")
        print(f"[{name}{si}] seed={seed}", flush=True)
        res = post(build(seed, ICON + text, "db_mkchip"))
        result = wait(res["prompt_id"])
        for nid, out in result.get("outputs", {}).items():
            for img in out.get("images", []):
                open(dest,"wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
                print("  ->", dest, flush=True)
print("ALL_DONE")
