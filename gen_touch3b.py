# -*- coding: utf-8 -*-
"""slime(可愛く)とdemon(世界観JRPGモンスター調・3/4左向き)を個別設定でリロール → assets_raw_touch3/
usage: python gen_touch3b.py [name ...]"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_touch3")
os.makedirs(OUT, exist_ok=True)

COMMON_NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, specular highlight, shiny plastic, gradient lighting, "
    "photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, blank hollow face, featureless, murky, "
    "ground shadow, cast shadow, drop shadow, floor shadow, shadow under feet, "
    "strict side view, full side profile, flat profile, front view, facing viewer, symmetrical pose, perfectly frontal")

# slime: 可愛さ許可(cuteをNEGに入れない)、表情はフレンドリー
SLIME_BASE = ("masterpiece, best quality, highly detailed, professional game character illustration, "
    "clear readable design, distinct expressive face, fully colored with rich flat cel shading and clean rendering, "
    "fantasy game slime enemy, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cute, charming, round and appealing, friendly little monster, chunky readable silhouette, "
    "flat matte colors, simple minimal flat cel shading, clean solid color fills, one soft shadow shape at most, "
    "full body, three-quarter view slightly turned to the left, looking to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. "
    "A cute round green slime monster with a matte flat-colored jelly body, two big round friendly eyes, a small cheerful smile with one tiny fang, a simple darker green core, tiny stubby arms, a clean rounded appealing shape, flat simple shading.")
SLIME_NEG = COMMON_NEG + ", scary, creepy, menacing grin, sharp teeth, too many eyes, ugly, glossy, shiny highlights, many highlights, wet reflections, bubbly, complex shading, soft gradient shading, ambient occlusion, busy details, noisy texture"

# demon: 世界観(cel-shaded JRPGモンスター)に合わせ、アメコミ筋肉を排除、3/4左向き
DEMON_BASE = ("masterpiece, best quality, highly detailed, professional game character illustration, "
    "clear readable design, distinct expressive face, fully colored with rich flat cel shading and clean rendering, "
    "fantasy JRPG monster boss design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, even flat lighting, "
    "cool, fierce, imposing and intimidating, regal demon lord, sharp menacing features, tall powerful build, chunky readable silhouette, "
    "full body, dynamic three-quarter view clearly turned about 45 degrees to the left, head and gaze to the left, "
    "solo, centered, plain solid white background, floating with no shadow on the ground, "
    "no text, video game sprite concept art. "
    "A demon king final-boss named Valga: a tall imposing purple-skinned demon lord with large curved horns, an ornate golden crown, "
    "a glowing red gem on its chest, dark bat wings folded to one side, sharp clawed hands, a cruel fanged sneer, a commanding intimidating pose, "
    "lean but powerful, regal and dangerous, stylized JRPG boss monster.")
DEMON_NEG = COMMON_NEG + ", american comic book style, western superhero, bodybuilder, overly muscular, bulging veiny muscles, spread wings, wings spread wide open, cute, chubby, round belly, fat, slime-like, chibi, comical, goofy, friendly, harmless"

JOBS = {
    "slime": (SLIME_BASE, SLIME_NEG, 945201),
    "demon": (DEMON_BASE, DEMON_NEG, 945202),
}

def build(seed, pos, neg):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_t3b"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":pos,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":34,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":768,"height":768,"batch_size":1}},
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
for name in targets:
    pos, neg, seed = JOBS[name]
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed, pos, neg))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
print("ALL_DONE")
