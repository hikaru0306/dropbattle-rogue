# -*- coding: utf-8 -*-
"""hero7 賭博師ジン img2img 清書: 低等身のまま自然に描き直す
入力: assets_cand/_hero7_i2i_input.png (768 白背景)
出力: assets_cand/hero7n_a..f.png (768px)
設定は gen_gambler2.py と同一 (anima-base / qwen_3_06b / qwen_image_vae / er_sde / simple / cfg4.5 / steps32)
denoise 0.35/0.45/0.55 x seed 2種 = 6案
"""
import json, os, time, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
INPUT_LOCAL = os.path.join(CAND, "_hero7_i2i_input.png")

# gen_gambler2.py と完全同一
NEG_HERO = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, cute and heroic, chibi proportions, "
    "full body, front facing, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")
# hero7g_b (gen_gambler2.py の2番目ジョブ) 本文 + 低等身追記
POS = (HERO + "A theatrical fantasy joker card gambler hero styled like the Joker playing card, "
    "a curled jester hat with three drooping points and gold bells in dusky red and black, "
    "a large ruffled harlequin collar and a dusky crimson tailcoat covered in small red and black diamonds with gold buttons, "
    "balancing a big gold coin on the back of his knuckles, other hand tossing a small gold coin, "
    "a devilish knowing smirk, dark hair. 3 heads tall, youthful short stature.")
NEG = NEG_HERO + ", chibi, super deformed, two heads tall, oversized head, realistic adult proportions"

def upload(path):
    fn = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    boundary = "----i2iBoundary7"
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{fn}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + data + (f"\r\n--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"overwrite\"\r\n\r\ntrue\r\n--{boundary}--\r\n").encode()
    req = urllib.request.Request(URL+"/upload/image", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        res = json.loads(r.read())
    print("uploaded:", res, flush=True)
    return res["name"]

def build(seed, denoise, image_name, prefix):
    return {
      "1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":prefix}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":POS,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":denoise,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["30",0]}},
      "30":{"class_type":"VAEEncode","inputs":{"pixels":["31",0],"vae":["15",0]}},
      "31":{"class_type":"LoadImage","inputs":{"image":image_name}},
      "44":{"class_type":"UNETLoader","inputs":{"unet_name":"anima-base-v1.0.safetensors","weight_dtype":"default"}},
      "45":{"class_type":"CLIPLoader","inputs":{"clip_name":"qwen_3_06b_base.safetensors","type":"stable_diffusion","device":"default"}}}

def post(p):
    req = urllib.request.Request(URL+"/prompt", data=json.dumps({"prompt":p}).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
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

img_name = upload(INPUT_LOCAL)

SEED1, SEED2 = 973202, 424242
# a..f: (seed, denoise)
JOBS = {
    "hero7n_a": (SEED1, 0.35),
    "hero7n_b": (SEED1, 0.45),
    "hero7n_c": (SEED1, 0.55),
    "hero7n_d": (SEED2, 0.35),
    "hero7n_e": (SEED2, 0.45),
    "hero7n_f": (SEED2, 0.55),
}
for name,(seed,dn) in JOBS.items():
    dest = os.path.join(CAND, f"{name}.png")
    print(f"[{name}] seed={seed} denoise={dn}", flush=True)
    res = post(build(seed, dn, img_name, "db_gambler_i2i"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest,"wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
