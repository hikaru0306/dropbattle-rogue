# -*- coding: utf-8 -*-
"""新キャラ「ギャンブラー」一式をAnimaで生成
  hero7_*  : キャラ候補 768px    -> assets_cand/
  coin_*   : コイントス用 768px  -> assets_raw_ui/
  mk_chip  : 専用ドロップマーク  -> assets_raw_ui/
  rl_*     : レリックアイコン    -> assets_raw_ui/
画風は gen_hero5_new.py / gen_relics.py / gen_ui_icons.py を踏襲（発光・ネオン禁止）
usage: python gen_gambler.py [name ...]   (無指定なら全部)
"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
ROOT = os.path.dirname(os.path.abspath(__file__))
CAND = os.path.join(ROOT, "assets_cand")
RAWUI = os.path.join(ROOT, "assets_raw_ui")
os.makedirs(CAND, exist_ok=True)
os.makedirs(RAWUI, exist_ok=True)

# ---- キャラ用（gen_hero5_new.py と同一） ----
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

# ---- アイコン用（gen_relics.py / gen_ui_icons.py と同一） ----
NEG_ICON = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
    "glow, bloom, neon, lens flare, rim light, backlight, photorealistic, realistic, 3d, cgi, render, photograph, "
    "text, watermark, signature, logo, cropped, out of frame, human, character, face, "
    "pixelated, pixel art, dithering, floating particles, sparkles, magic aura, energy effects, "
    "floating debris, disconnected parts, grainy, washed out colors, pale, desaturated, "
    "complex background, scenery, frame, border, multiple objects, collage, "
    "cast shadow, ground shadow, drop shadow, reflection, puddle, stand, pedestal, base")
ICON = ("masterpiece, best quality, score_7, safe. "
    "a single fantasy game relic icon, flat cel shading with simple two-tone shadow, "
    "bold thick dark outline, art style between Slay the Spire and Pokemon, "
    "vivid saturated colors, chunky readable silhouette, "
    "one object only, centered, isolated on pure white background, no text. ")
# コインは「正円・対で同寸」を強制するため専用の枕詞
COIN = ("masterpiece, best quality, score_7, safe. "
    "a single large fantasy game coin medallion icon, viewed perfectly flat from the front, "
    "a perfect circle disc with a thick rim edge, "
    "flat cel shading with simple two-tone metal shading, bold thick dark outline, "
    "art style between Slay the Spire and Pokemon, vivid saturated colors, "
    "one coin only, centered, fills the frame, isolated on pure white background, no text. ")

# 主題色: テーマ #c0483f (くすんだ赤)
HERO_JOBS = {
    # 山高帽＋派手コートの正統派賭博師
    "hero7_a": (HERO + "A confident fantasy gambler rogue hero, wearing a tall dusky red top hat with a playing card tucked in the band, "
        "an ornate dusky crimson long tailcoat with gold trim and a black waistcoat, a gold pocket watch chain, "
        "fanning a hand of playing cards in one hand, flipping a gold coin with the other, "
        "short dark hair, a cocky smirk with one eyebrow raised.", 970001),
    # バイザー＋ディーラー風、ダイス主体
    "hero7_b": (HERO + "A sly fantasy casino dealer hero, wearing a green dealer visor and a dusky crimson vest over a white shirt with rolled sleeves, "
        "black arm garters, a long dark red coat draped on the shoulders, "
        "holding a pair of red dice ready to throw, a stack of casino chips in the other hand, "
        "messy dark hair, a mischievous confident grin.", 970102),
    # 女性版・華やかな勝負師
    "hero7_c": (HERO + "A glamorous fantasy gambler heroine, wearing a small tilted dusky red top hat with a card in the band, "
        "an ornate crimson and black gambler coat with gold buttons and a long tailcoat hem, high boots, "
        "fanning playing cards in one raised hand, gold coins in the other, "
        "long dark wavy hair, a bold teasing smirk.", 970203),
    # 派手コート＋マント、豪華ハイローラー
    "hero7_d": (HERO + "A flamboyant fantasy high-roller gambler hero, wearing an extravagant dusky red long coat with a heavy gold-embroidered collar "
        "and a black cape lining, a wide-brimmed crimson hat with a card and a feather, many gold rings, "
        "one hand spreading a fan of playing cards, the other resting on a pile of gambling chips, "
        "a wide daring grin, dark eyes.", 970304),
    # ダイス＋コインを大きく、シルエット強め
    "hero7_e": (HERO + "A cunning fantasy fortune gambler hero in a dusky crimson double breasted gambler coat with gold trim, "
        "a black bowler hat with a red band and a playing card, a patterned scarf, "
        "tossing a big gold coin up in one hand, holding two large red dice in the other, "
        "a small leather chip pouch on the belt, a sharp knowing smirk.", 970405),
    # 中性的・カードマスター寄り
    "hero7_f": (HERO + "A charismatic fantasy card master gambler hero wearing a tall crimson top hat, "
        "an ornate dark red tailcoat with gold filigree and a black cravat, gloved hands, "
        "one arm sweeping a wide fan of playing cards outward, a gold coin balanced on the other knuckles, "
        "confident narrow eyes and a crooked smile, dice and chips on the belt pouch.", 970506),
}

COIN_JOBS = {
    "coin_angel_a": (COIN + "A bright polished gold angel coin: a perfect circle gold disc with a thick beaded rim, "
        "a pair of spread white feathered angel wings embossed across the face and a bold ring halo above them, "
        "warm bright yellow gold with light cream highlights and a darker gold shadow on the lower half, "
        "clean symmetrical heraldic emblem, holy and lucky.", 971001),
    "coin_demon_a": (COIN + "A dark blood red and black demon coin: a perfect circle metal disc with a thick spiked rim, "
        "a pair of curved demon horns embossed across the face with a sharp barbed tail motif below, "
        "deep dark red and blackened iron with dull crimson highlights and near black shadow on the lower half, "
        "clean symmetrical heraldic emblem, sinister and cursed.", 971002),
    "coin_angel_b": (COIN + "A bright gold angel coin: a perfect circle thick gold disc with a smooth wide rim border, "
        "a single large ring halo embossed in the center flanked by two symmetrical folded feathered wings, "
        "bright golden yellow with pale cream top shading and amber lower shading, flat clean design, holy.", 971103),
    "coin_demon_b": (COIN + "A dark demon coin: a perfect circle thick blackened iron disc with a smooth wide rim border, "
        "a single large ram skull with two big curved horns embossed in the center, symmetrical, "
        "dark crimson red and black with dull red top shading and black lower shading, flat clean design, sinister.", 971104),
}

ICON_JOBS = {
    # mk_* は盤面ドロップのマーク規格（mk_store / mk_ore と同規格）
    "mk_chip": "A single casino gambling chip disc seen at a slight tilt, bright orange body with white dashed edge segments "
        "around the rim and a white inner ring, a small orange center circle, thick chunky disc with a visible side edge.",
    "rl_luckcoin": "A large lucky gold coin with a four leaf clover embossed on its face, thick beaded rim, warm gold, "
        "slightly tilted, a small second coin behind it.",
    "rl_devilpact": "An unrolled aged parchment contract scroll with dark red blood written signature lines and a black feather quill pen "
        "laid across it, a dark red wax seal with a small horned demon mark at the bottom corner.",
    "rl_angelfeather": "A single large pure white angel feather, softly curved, with a fine golden quill shaft and a small gold ring halo behind its tip.",
}
ICON_SEED0 = 972000


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


def spec_for(name):
    """name -> (prompt, seed, neg, size, outdir, prefix)"""
    if name in HERO_JOBS:
        t, s = HERO_JOBS[name]
        return t, s, NEG_HERO, 768, CAND, "db_gambler_hero"
    if name in COIN_JOBS:
        t, s = COIN_JOBS[name]
        return t, s, NEG_ICON, 768, RAWUI, "db_gambler_coin"
    if name in ICON_JOBS:
        seed = ICON_SEED0 + list(ICON_JOBS).index(name)
        return ICON + ICON_JOBS[name], seed, NEG_ICON, 576, RAWUI, "db_gambler_icon"
    raise KeyError(name)

ALL = list(HERO_JOBS) + list(COIN_JOBS) + list(ICON_JOBS)
targets = sys.argv[1:] or ALL
for spec in targets:
    name, _, sd = spec.partition("=")
    text, seed, neg, size, outdir, prefix = spec_for(name)
    if sd: seed = int(sd)
    dest = os.path.join(outdir, f"{name}.png")
    if os.path.exists(dest):
        print("skip", name, flush=True); continue
    print(f"[{name}] seed={seed} size={size}", flush=True)
    res = post(build(seed, text, neg, size, prefix))
    result = wait(res["prompt_id"])
    for nid, out in result.get("outputs", {}).items():
        for img in out.get("images", []):
            open(dest, "wb").write(fetch(img["filename"], img.get("subfolder",""), img.get("type","output")))
            print("  ->", dest, flush=True)
print("ALL_DONE")
