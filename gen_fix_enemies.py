# -*- coding: utf-8 -*-
"""画風が浮いていた敵10体の再生成（左向き指定）→ assets_raw_fix/
usage: python gen_fix_enemies.py [name ...]  (省略時は全件。既存ファイルはスキップ)
seed変更でリロールする場合は assets_raw_fix/<name>.png を消してから実行"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_fix")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless")
# gen_ura.py の CHAR を踏襲しつつ front facing → 左向きサイドビューに変更
CHARL = ("masterpiece, best quality, score_7, safe. "
    "fantasy game enemy character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, "
    "chunky readable silhouette, slightly cute but menacing, "
    "full body, side view facing left, looking to the left, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

JOBS = {
    # ドット絵で別画風だった
    "skel":  (CHARL + "A skeleton soldier with chipped bone armor, a rusted short sword and a small battered round shield, single blue soul flame in one eye socket, marching to the left.", 930001),
    # 絵文字風フラットだった
    "imp":   (CHARL + "A small mischievous red imp devil with tiny bat wings, curved cream horns, arrow-tipped tail, sharp little claws, wicked toothy grin.", 930002),
    # ピクセル/ディザ調だった
    "kslime":(CHARL + "A giant king slime: a huge glossy green slime blob wearing a small golden crown, angry dark eyes, lighter green jelly highlights, imposing bulk.", 930003),
    # フラットな柄塗りローブだった
    "ifrita":(CHARL + "A flame mage in a flowing ember-orange hooded robe with flame patterns, side profile walking to the left, dark shadowed hood seen from the side with one glowing eye, holding a floating fireball in the outstretched left hand.", 930104),
    # フラットポスター調だった
    "vamp":  (CHARL + "A vampire lord with a high-collared crimson and black cape spread like bat wings, pale skin, slicked dark hair, red eyes, fangs, elegant menacing pose.", 930005),
    # フラットベクター調だった
    "reaper":(CHARL + "A grim reaper wraith in a tattered dark violet hooded robe, white skull face, bony hands holding a long scythe, floating with ragged robe hem.", 930006),
    "gazer": (CHARL + "A void gazer: a floating dark orb monster with one huge central eye with a bright violet iris and a dark pupil, glaring, thick crystal spikes growing out of its round body, tiny stars speckled on its dark body.", 930007),
    "kaos":  (CHARL + "A chaos imp goblin with a big round head, one large eye and one small eye, wide wicked grin with sharp teeth, mismatched horns, patchwork purple and black skin with stitches, clawed hands raised, crouching.", 930208),
    "mant":  (CHARL + "A shadow mantis with sickle arms like dark blades, dark green chitin plates, low hunting stance, narrow glowing eyes.", 930009),
    "eel":   (CHARL + "A swamp eel monster rising from murky dark water, long slick dark teal serpentine body, pale belly, ragged fins, big yellow eyes, open mouth with needle teeth.", 930010),
}

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_fix"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
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
    if os.path.exists(os.path.join(OUT, f"{name}.png")):
        print("skip", name, flush=True); continue
    text, seed = JOBS[name]
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed,text))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
print("ALL_DONE")
