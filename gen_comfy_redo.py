# -*- coding: utf-8 -*-
"""ComfyUI(animagineXL)で yeti / alraune を新デザイン生成する。
ゲーム画風: 太い黒アウトライン + フラットなセル塗り + 鮮やかな色 + 白背景（後でrembg）
出力: assets_cand/comfy_<name>_<seed>.png
"""
import json, os, sys, time, urllib.request, uuid

SRV = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "assets_cand")

CKPT = "animagineXLV31.safetensors"
COMMON_POS = ("solo, single monster, flat 2d western cartoon fantasy monster illustration, "
              "mobile game enemy art, smooth thick black outline with even line weight, "
              "flat cel shading with one simple shadow tone, clean rounded shapes, "
              "moderate saturation colors, minimal details, clear readable silhouette, "
              "full body, centered, standing on nothing, plain white background, no shadow on ground")
COMMON_NEG = ("sticker art, spiky jagged decorative outline, badge, emblem, pixel art, mosaic, "
              "anime, manga, japanese style, bishoujo, kawaii, chibi, mascot, cute, "
              "detailed rendering, intricate details, complex shading, gradients, glow effects, painterly, "
              "realistic, photo, 3d render, texture, grimdark, horror, "
              "busy background, colorful background, pattern, frame, border, symmetrical ornament, "
              "multiple characters, multiple views, character sheet, duplicate, "
              "text, watermark, signature, cropped, out of frame, extra limbs, bad anatomy")

SUBJECTS = {
    "yeti": "a big burly yeti monster, tall imposing figure about five heads tall, small head on "
            "broad shoulders, muscular torso, long powerful legs, long arms with large fists, "
            "shaggy white fur with pale blue shadow tone, jagged ice crystals growing on its shoulders, "
            "two short dark horns, angry face with sharp fangs and glaring blue eyes, "
            "in the same art style as a stone golem and werewolf from a fantasy mobile game",
    "alraune": "a rose flower monster, a tall slender adult woman about six heads tall with pale green skin, "
               "long body rising gracefully from a large red rose bloom, rose petals forming a long skirt, "
               "long dark green leaf hair, thin thorny vine tendrils curling around her arms, "
               "yellow eyes and a sly smile, green stem with thorns below, "
               "in the same art style as a fantasy mobile game enemy",
}

def q(prompt_text, neg_text, seed, w=1024, h=1024, prefix="comfy"):
    g = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt_text, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": neg_text, "clip": ["4", 1]}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "3": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 32, "cfg": 6.0, "sampler_name": "dpmpp_2m",
            "scheduler": "karras", "denoise": 1.0,
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["8", 0]}},
    }
    body = json.dumps({"prompt": g, "client_id": str(uuid.uuid4())}).encode()
    req = urllib.request.Request(f"{SRV}/prompt", data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))["prompt_id"]

def wait(pid, timeout=600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        h = json.load(urllib.request.urlopen(f"{SRV}/history/{pid}"))
        if pid in h:
            outs = h[pid]["outputs"]
            files = []
            for v in outs.values():
                for im in v.get("images", []):
                    files.append((im["filename"], im["subfolder"], im["type"]))
            return files
        time.sleep(3)
    return []

def fetch(fn, sub, typ, dest):
    url = f"{SRV}/view?filename={urllib.parse.quote(fn)}&subfolder={urllib.parse.quote(sub)}&type={typ}"
    with urllib.request.urlopen(url) as r, open(dest, "wb") as f:
        f.write(r.read())

if __name__ == "__main__":
    import urllib.parse
    names = sys.argv[1:] or ["yeti", "alraune"]
    seeds = [7701, 7702, 7703, 7704]
    for name in names:
        pos = f"{SUBJECTS[name]}, {COMMON_POS}"
        for s in seeds:
            pid = q(pos, COMMON_NEG, s, prefix=f"redo_{name}")
            files = wait(pid)
            for fn, sub, typ in files:
                dest = os.path.join(OUT, f"comfy_{name}_{s}.png")
                fetch(fn, sub, typ, dest)
                print("->", dest)
