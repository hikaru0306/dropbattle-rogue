# -*- coding: utf-8 -*-
"""場所別ウィンドウフレーム（額縁型・border-image用）をAnimaで生成 → assets_raw_ui/
中央はborder-image(fill無し)で未使用。紫紺インテリアの上に載る前提の暗めフレーム。
usage: python gen_ui_windows.py [name[=seed] ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, shiny, glossy, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, grainy, washed out colors, pale, desaturated, "
    "complex background, scenery, multiple objects, collage, "
    "cast shadow, ground shadow, drop shadow, reflection, asymmetric, tilted, perspective")

BASE = ("masterpiece, best quality, score_7, safe. "
    "a single fantasy game UI window frame, rectangular picture-frame shape filling the canvas, "
    "perfectly symmetrical, straight uniform edges, "
    "flat cel shading with bold dark outline, art style between Slay the Spire and Pokemon, "
    "completely empty plain white center, front view, flat 2d game asset, muted colors, no text. ")

JOBS = {
    # システム系（メニュー/設定/レリック/敗北）: 彫刻入りダンジョン石板
    "win_stone": BASE + "Slim carved dark grey stone frame with subtle chiseled rune-less engraving lines, weathered dungeon slab, small square corner blocks, cool dark grey with faint purple tint.",
    # ショップ/所持アイテム: 行商人の木箱・屋台
    "win_wood":  BASE + "Rustic dark brown wooden plank frame with rope lashing at the four corners and small iron nails, merchant crate style, warm dark wood grain.",
    # 報酬/章クリア/勝利/賭け: 宝箱の金具つき黒鉄フレーム
    "win_gold":  BASE + "Dark iron treasure chest trim frame with antique muted brass corner medallions and simple engraved border line, matte metal, restrained ornament.",
    # win_goldの彫り模様が縮小表示でノイズ化したため、バーは無地のクリーン版
    "win_gold2": BASE + "Dark iron treasure chest trim frame with antique muted brass square corner medallions, completely plain smooth flat iron bars with no engraving and no pattern, matte metal, clean minimal.",
    # 焚き火: 焦げた木＋残り火色の差し色
    "win_camp":  BASE + "Charred dark wooden log frame with slightly burnt blackened corners and thin warm ember-orange accent line along the inner edge, cozy campfire style.",
}
SEED0 = 953000

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_uiwin"}},
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
    hst = wait(r["prompt_id"])
    for node in hst["outputs"].values():
        for im in node.get("images", []):
            data = fetch(im["filename"], im["subfolder"], im["type"])
            fp = os.path.join(OUT, f"{name}_{seed}.png")
            open(fp, "wb").write(data)
            print("  ->", fp, flush=True)
print("done")
