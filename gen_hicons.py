# -*- coding: utf-8 -*-
"""ヘッダーUIアイコン4種: コイン/音符/スピーカー/袋 (seed固定で画風統一)"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human")

ICON = ("masterpiece, best quality, score_7, safe. "
    "a single game map node icon, flat cel shading with two-tone shadow, bold thick dark outline, "
    "art style between Slay the Spire and Pokemon, centered, isolated on pure white background, "
    "simple readable silhouette, no text. ")

JOBS = {
    "icon_coin":    (ICON + "A single shiny gold coin with an embossed star emblem, slight 3/4 angle.", 777001),
    "icon_note":    (ICON + "A big bold golden music note symbol, thick rounded form.", 777001),
    "icon_speaker": (ICON + "A small golden megaphone loudspeaker emitting two curved sound waves.", 777001),
    "icon_bag":     (ICON + "A brown leather drawstring pouch bag with gold trim and visible stitches.", 777001),
}

def build(seed, text):
    return {
        "1": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "db_hicon"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["15", 0]}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"text": text, "clip": ["45", 0]}},
        "12": {"class_type": "CLIPTextEncode", "inputs": {"text": NEG, "clip": ["45", 0]}},
        "15": {"class_type": "VAELoader", "inputs": {"vae_name": "qwen_image_vae.safetensors"}},
        "19": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 32, "cfg": 4.5,
            "sampler_name": "er_sde", "scheduler": "simple", "denoise": 1.0,
            "model": ["44", 0], "positive": ["11", 0], "negative": ["12", 0],
            "latent_image": ["28", 0]}},
        "28": {"class_type": "EmptyLatentImage", "inputs": {"width": 768, "height": 768, "batch_size": 1}},
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
    text, seed = JOBS[name]
    print(f"[{name}]", flush=True)
    res = post(build(seed, text))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            data = fetch(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
            with open(os.path.join(OUT, f"{name}.png"), "wb") as f:
                f.write(data)
            print(" ->", name, flush=True)
print("DONE")
