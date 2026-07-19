# -*- coding: utf-8 -*-
"""賭博師ジン リデザイン: ジョーカー(道化師)＋コイン強調
  hero7g_a..f : キャラ候補 768px -> assets_cand/
gen_gambler.py の build/NEG_HERO/HERO を踏襲（発光・ネオン禁止・チビ体型）
usage: python gen_gambler2.py [name ...]   (無指定なら全部)
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# ---- gen_gambler.py と完全同一 ----
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

# 主題色: テーマ #c0483f (くすんだ赤) + 黒 + 金。ジョーカー(道化師)＋コイン。
HERO_JOBS = {
    # a: 王道ジェスター賭博師。二又の道化帽(鈴付)＋菱形ハーレクイン柄＋親指で大金貨を弾く
    "hero7g_a": (HERO + "A mischievous fantasy jester gambler hero, wearing a two pointed jester hat with small gold bells, "
        "one half dusky red and the other half black in a harlequin diamond pattern, "
        "a dusky crimson and black harlequin diamond patterned jester coat with a gold pointed collar and gold bell trim, "
        "flipping a big shiny gold coin up off his thumb with one hand, holding a fanned joker playing card in the other, "
        "short dark hair, a wide sly cocky grin, dark playful eyes.", 973101),
    # b: ジョーカーカードそのもの寄り。派手なフリル襟＋大金貨を指の甲でバランス
    "hero7g_b": (HERO + "A theatrical fantasy joker card gambler hero styled like the Joker playing card, "
        "a curled jester hat with three drooping points and gold bells in dusky red and black, "
        "a large ruffled harlequin collar and a dusky crimson tailcoat covered in small red and black diamonds with gold buttons, "
        "balancing a big gold coin on the back of his knuckles, other hand tossing a small gold coin, "
        "a devilish knowing smirk, dark hair.", 973202),
    # c: 女性ジェスター賭博師。ミニ二又帽＋菱形柄スカート＋親指弾き大金貨
    "hero7g_c": (HERO + "A glamorous fantasy jester gambler heroine, wearing a small tilted two pointed jester hat with gold bells "
        "in dusky red and black harlequin diamonds, an ornate dusky crimson and black diamond patterned corset jacket "
        "with a gold pointed collar and a short ruffled skirt, high boots, "
        "flipping a big gold coin off her thumb, fanning joker cards in the other hand, "
        "long dark wavy hair, a bold teasing smirk.", 973303),
    # d: ハーレクインマント＋山高帽に鈴。コイン弾き＋腰に金貨袋
    "hero7g_d": (HERO + "A flamboyant fantasy harlequin high-roller gambler hero, wearing a crimson bowler hat with a jester bell "
        "and a joker card in the band, a dusky red and black harlequin diamond patterned coat with a gold trim cape lining, "
        "gold rings, flipping a big gold coin up off his thumb, the other hand holding a joker card, "
        "a bulging coin pouch spilling a couple of gold coins on his belt, a wide daring grin.", 973404),
    # e: コイン最重視。巨大な金貨を大きく前に弾き、コイン柄の道化服
    "hero7g_e": (HERO + "A cunning fantasy coin gambler jester hero in a dusky crimson and black harlequin diamond patterned jester coat "
        "with gold coin shaped buttons and a gold bell collar, a small two pointed red and black jester cap with bells, "
        "tossing one very large gold coin high off his thumb held prominently in front, "
        "the other hand holding a fanned joker card, a coin pouch on the belt, a sharp confident smirk.", 973505),
    # f: 中性的カードマスター道化。フリル襟＋大金貨を甲にのせカード扇
    "hero7g_f": (HERO + "A charismatic fantasy card master jester gambler hero wearing a two pointed dusky red and black jester hood "
        "with gold bells, a harlequin diamond patterned dark red tailcoat with a gold ruffled cravat and gloved hands, "
        "one gloved hand sweeping a wide fan of joker playing cards, a big gold coin balanced on the other knuckles, "
        "confident narrow eyes and a crooked playful smile.", 973606),
}


def build(seed, text, neg, size, prefix):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":prefix}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":neg,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":size,"height":size,"batch_size":1}},
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

ALL = list(HERO_JOBS)
targets = sys.argv[1:] or ALL
for spec in targets:
    name, _, sd = spec.partition("=")
    text, seed = HERO_JOBS[name]
    if sd: seed = int(sd)
    dest = os.path.join(CAND, f"{name}.png")
    if os.path.exists(dest):
        print("skip", name, flush=True); continue
    print(f"[{name}] seed={seed}", flush=True)
    res = post(build(seed, text, NEG_HERO, 768, "db_gambler2_hero"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
