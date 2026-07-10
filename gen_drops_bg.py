# -*- coding: utf-8 -*-
"""ドロップ宝石5種（seed固定で形状統一）+ 背景2枚 (ComfyUI + Anima)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character")

DROP_STYLE = ("masterpiece, best quality, score_7, safe. "
    "a single round magic gem orb for a mobile puzzle game, smooth droplet shape, "
    "flat cel shading with a two-tone shadow, bold thick dark outline, "
    "one small white highlight, art style between Slay the Spire and Pokemon, "
    "centered, isolated on pure white background, game item icon, no text. ")

JOBS = {
    "drop_red":    (DROP_STYLE + "Vivid crimson red ruby colored orb.", 768, 768, 777001),
    "drop_gold":   (DROP_STYLE + "Warm amber golden topaz colored orb.", 768, 768, 777001),
    "drop_purple": (DROP_STYLE + "Rich violet purple amethyst colored orb.", 768, 768, 777001),
    "drop_teal":   (DROP_STYLE + "Fresh teal turquoise colored orb.", 768, 768, 777001),
    "drop_junk":   ("masterpiece, best quality, score_7, safe. "
        "a single cracked dull gray stone orb for a mobile puzzle game, chipped rock texture, "
        "flat cel shading, bold thick dark outline, art style between Slay the Spire and Pokemon, "
        "centered, isolated on pure white background, game item icon, gloomy, no text. ", 768, 768, 777001),
    "bg_map":      ("masterpiece, best quality, score_7, safe. "
        "hand-painted fantasy board game world map seen from above, a winding dirt road "
        "climbing from a green forest at the bottom, through rocky hills, up to a dark demon castle "
        "on a mountain at the top, muted desaturated colors, flat cel shaded illustration, "
        "bold outlines, video game level select background, dark fantasy but charming, "
        "no text, no icons, no characters. ", 768, 1024, 424242),
    "bg_battle":   ("masterpiece, best quality, score_7, safe. "
        "dark stone dungeon great hall interior, distant torches on pillars, mist on the floor, "
        "muted desaturated purple and gray palette, flat cel shaded painted illustration, bold shapes, "
        "video game battle background, empty scene, atmospheric but readable, "
        "no text, no characters. ", 1024, 576, 424242),
}

def build(seed, text, w, hgt):
    return {
        "1": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "db_asset"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["15", 0]}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["45", 0]}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["45", 0]}},
        "15": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "19": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 32, "cfg": 4.5,
            "sampler_name": "er_sde", "scheduler": "simple", "denoise": 1.0,
            "model": ["44", 0], "positive": ["11", 0], "negative": ["12", 0],
            "latent_image": ["28", 0]}},
        "28": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": hgt, "batch_size": 1}},
        "44": {"class_type": "UNETLoader", "inputs": {"unet_name": "anima-base-v1.0.safetensors", "weight_dtype": "default"}},
        "45": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_06b_base.safetensors", "type": "stable_diffusion", "device": "default"}},
    }

def post(p):
    req = urllib.request.Request(URL + "/prompt", data=json.dumps({"prompt": p}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())

def wait(pid, timeout=1500):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(URL + f"/history/{pid}", timeout=10) as r:
            hst = json.loads(r.read())
        if pid in hst:
            return hst[pid]
        time.sleep(2)
    raise TimeoutError(pid)

def fetch(fn, sub, ty):
    q = urllib.parse.urlencode({"filename": fn, "subfolder": sub, "type": ty})
    with urllib.request.urlopen(URL + "/view?" + q, timeout=30) as r:
        return r.read()

targets = sys.argv[1:] or list(JOBS.keys())
for name in targets:
    text, w, hgt, seed = JOBS[name]
    print(f"[{name}] {w}x{hgt} seed={seed}", flush=True)
    res = post(build(seed, text, w, hgt))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            data = fetch(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
            path = os.path.join(OUT, f"{name}.png")
            with open(path, "wb") as f:
                f.write(data)
            print(" ->", path, flush=True)
print("DONE")
