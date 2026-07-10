# -*- coding: utf-8 -*-
"""UI素材: アクションアイコン3種(seed固定) / タイトル背景 / 全体背景テクスチャ"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character")

ICON = ("masterpiece, best quality, score_7, safe. "
    "a single game skill icon, flat cel shading with two-tone shadow, bold thick dark outline, "
    "art style between Slay the Spire and Pokemon, centered, isolated on pure white background, "
    "simple readable silhouette, no text. ")

JOBS = {
    "icon_atk":  (ICON + "A sturdy short sword pointing upward, steel blade, gold crossguard, red leather grip.", 768, 768, 777001),
    "icon_def":  (ICON + "A round kite shield, blue steel with gold rim and a small emblem.", 768, 768, 777001),
    "icon_heal": (ICON + "A small glass healing potion bottle with bright green liquid and a cork.", 768, 768, 777001),
    "bg_title":  ("masterpiece, best quality, score_7, safe. "
        "vertical fantasy game title screen background, ominous demon castle on a distant mountain peak "
        "under a dark night sky with a large pale moon, pine forest silhouettes in the foreground, "
        "a winding road leading toward the castle, muted desaturated colors, "
        "flat cel shaded painted illustration, bold shapes, atmospheric, "
        "empty middle area for logo, no text, no characters. ", 768, 1024, 515151),
    "bg_texture": ("masterpiece, best quality, score_7, safe. "
        "very dark seamless stone brick wall texture, extremely subtle, low contrast, "
        "flat muted dark gray purple, tileable game UI background pattern, "
        "no text, no objects. ", 768, 768, 515151),
}

def build(seed, text, w, hgt):
    return {
        "1": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "db_ui"}},
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
    print(f"[{name}] {w}x{hgt}", flush=True)
    res = post(build(seed, text, w, hgt))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            data = fetch(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
            with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
                f.write(data)
            print(" ->", name, flush=True)
print("DONE")
