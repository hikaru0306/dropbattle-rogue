# -*- coding: utf-8 -*-
"""ドロップバトル キャラ生成 (ComfyUI + Anima)
スタイル: スレスパ×ポケモンの中間。太い輪郭・セル塗り・光沢/ネオン禁止
"""
import json, os, time, random, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw")
os.makedirs(OUT, exist_ok=True)

STYLE = ("masterpiece, best quality, score_7, safe. "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, slightly cute but menacing, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, no watermark, video game sprite concept art. ")

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, shiny, glossy highlights, rim light, backlight, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, multiple characters, background scenery, "
    "human, girl, boy, cropped, out of frame")

CHARS = {
    "hero":  "A young apprentice mage adventurer wearing a deep purple pointed wizard hat and purple robe with gold trim, holding a simple wooden staff topped with a small round amber orb, brave determined expression, small satchel",
    "slime": "A round bouncy green slime monster with two big glossy round eyes and a mischievous open smile, simple blob body with one darker green gel layer inside",
    "bat":   "A plump purple cave bat monster hovering with wide ragged wings spread, big yellow eyes, tiny white fangs, fuzzy round body",
    "imp":   "A small crimson red imp devil with short cream-colored horns, pointed arrow-tipped tail, wicked toothy grin, little clawed hands raised",
    "golem": "A bulky ancient stone golem made of stacked mossy gray boulders, deep cracks across its body, two small pale blue square eyes, massive heavy fists",
    "shade": "A ghostly wraith specter floating, tattered dark indigo cloak that fades into wisps at the bottom, hollow pale white eyes, thin shadowy arms",
    "spore": "A small mushroom monster shaman with a wide brown spotted mushroom cap, sleepy gentle face, tiny body, holding a crooked twig staff with a leaf",
    "boss":  "An imposing demon lord boss monster with massive curved cream horns, small golden crown, dark violet muscular body, torn bat-like wings folded behind, magenta gem embedded in chest, cruel confident grin, clawed hands",
    "hero2": "A cheerful long-eared elf witch, holding a wooden painter palette in one hand and a paintbrush wand in the other, wearing a colorful patchwork robe splattered with rainbow paint splotches, pointed hat, playful bright expression",
    "hero3": "A heavy lion-headed beastman knight, thick ornate plate armor, holding a broad sword and a round shield, red and blue war paint stripes on the face, mane around the helmet, powerful sturdy stance",
    "hero4": "A wise nine-tailed kitsune fox scholar wearing round glasses, layered scholarly robes, holding a huge old purple spellbook under one arm and a crystal-topped staff, calm intelligent expression, fox ears and bushy tails",
    "hero5": "A noble high elf archmage of grand stature, ornate white and gold flowing robes with intricate trim, a large golden halo ring painted behind the head as flat solid gold shape, holding a luxurious tall staff, serene majestic dignified expression, looks the strongest and most powerful",
    "hero6": "A stout dwarf blacksmith with a big bushy braided brown beard, short stocky body, wearing a thick brown leather apron over a simple tunic, holding a large heavy smithing hammer resting over one shoulder, a small dark iron anvil on the ground at his feet, copper and steel-gray and warm brown color palette, sturdy confident friendly expression",
}

def build(seed, text):
    return {
        "1": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "db_char"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["19", 0], "vae": ["15", 0]}},
        "11": {"class_type": "CLIPTextEncode", "inputs": {"text": STYLE + text, "clip": ["45", 0]}},
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

def wait(pid, timeout=1200):
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

targets = sys.argv[1:] or list(CHARS.keys())
for name in targets:
    seed = random.randint(0, 2**63 - 1)
    print(f"[{name}] seed={seed}", flush=True)
    res = post(build(seed, CHARS[name]))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            data = fetch(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
            path = os.path.join(OUT, f"{name}.png")
            with open(path, "wb") as f:
                f.write(data)
            print(" ->", path, flush=True)
print("DONE")
