# -*- coding: utf-8 -*-
"""賭博師ジン リデザインv3: 白塗りジョーカー顔＋やや右向き3/4ビュー
  hero7h_a..e : キャラ候補 768px -> assets_cand/
gen_gambler.py の build/NEG_HERO を踏襲（発光・ネオン禁止・チビ体型）。
HERO は "front facing" を "three-quarter view facing right" に差し替え。
usage: python gen_gambler3.py [name ...]   (無指定なら全部)
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
os.makedirs(CAND, exist_ok=True)

# ---- gen_gambler.py と同一 ----
NEG_HERO = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, "
    "pixelated, pixel art, dithering, jagged edges, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, back view, rear view, faceless, grainy, washed out colors, pale, desaturated")
# HERO: front facing -> three-quarter view facing right（顔も体も画面右向き）
HERO = ("masterpiece, best quality, score_7, safe. "
    "fantasy game hero character design, art style between Slay the Spire and Pokemon, "
    "bold thick dark outlines, flat cel shading with subtle painted texture, vivid saturated colors, "
    "chunky readable silhouette, cute and heroic, chibi proportions, "
    "full body, three-quarter view facing right, body and head turned slightly to the right, looking toward the right side, solo, centered, plain solid white background, "
    "no text, video game sprite concept art. ")

# 白塗りジョーカー顔の共通記述（無機質マスクにせず、白塗り上に表情を出す）
FACE = ("his face fully painted with white clown greasepaint makeup like a joker, "
    "clearly visible facial features on the white face, sharp mischievous eyes, a red harlequin diamond painted around one eye, "
    "a wide cocky toothy grin with red painted lips, expressive and lively, not an inorganic mask, ")

# 主題色: #c0483f(くすんだ赤) + 黒 + 金。維持: 鈴付き二又道化帽/菱形柄/金貨指弾き/カード。
HERO_JOBS = {
    # a: hero7g_a の正統ジェスターを白塗り顔＋右向きに
    "hero7h_a": (HERO + "A mischievous fantasy jester gambler hero, wearing a two pointed jester hat with small gold bells, "
        "one half dusky red and the other half black in a harlequin diamond pattern, "
        "a dusky crimson and black harlequin diamond patterned jester coat with a gold pointed bell collar and gold trim, "
        "harlequin diamond patterned pants and curled pointed shoes, " + FACE +
        "his raised right hand flipping a big shiny gold coin off his thumb, his left hand holding a fanned playing card, "
        "short dark hair.", 974101),
    # b: フリル大襟＋菱形テールコート、白塗り顔、右向き
    "hero7h_b": (HERO + "A theatrical fantasy joker card gambler hero, "
        "a curled two pointed jester hat with drooping bell tips in dusky red and black harlequin diamonds, "
        "a ruffled harlequin collar and a dusky crimson tailcoat covered in small red and black diamonds with gold buttons, " + FACE +
        "one hand flicking a big gold coin up off the thumb, the other hand holding a joker playing card, "
        "dark hair.", 974202),
    # c: 女性ジェスター賭博師、白塗り顔、右向き
    "hero7h_c": (HERO + "A glamorous fantasy jester gambler heroine, wearing a small tilted two pointed jester hat with gold bells "
        "in dusky red and black harlequin diamonds, an ornate dusky crimson and black diamond patterned corset jacket "
        "with a gold pointed collar and a short ruffled harlequin skirt, high boots, "
        "her face painted with white clown greasepaint makeup, clearly visible sharp playful eyes, a red harlequin diamond around one eye, a bold teasing red-lipped smirk, expressive not a mask, "
        "flicking a big gold coin off her thumb, fanning playing cards in the other hand, "
        "long dark wavy hair.", 974303),
    # d: コインやや大きめ、菱形マント、白塗り顔、右向き
    "hero7h_d": (HERO + "A cunning fantasy coin jester gambler hero in a dusky crimson and black harlequin diamond patterned jester coat "
        "with gold coin shaped buttons and a gold bell collar, a two pointed red and black jester cap with bells, a short black cape lined with red diamonds, " + FACE +
        "his raised hand flipping a large gold coin off the thumb held prominently, the other hand holding a fanned playing card, "
        "a small coin pouch on the belt, dark hair.", 974404),
    # e: 中性的カードマスター道化、フリル襟、白塗り顔、右向き
    "hero7h_e": (HERO + "A charismatic fantasy card master jester gambler hero wearing a two pointed dusky red and black harlequin jester hat "
        "with gold bells, a harlequin diamond patterned dark red tailcoat with a gold ruffled cravat and gloved hands, " + FACE +
        "one gloved hand flicking a big gold coin off the thumb, the other sweeping a wide fan of playing cards, "
        "dark hair.", 974505),
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
    res = post(build(seed, text, NEG_HERO, 768, "db_gambler3_hero"))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
