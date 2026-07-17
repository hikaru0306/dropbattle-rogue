# -*- coding: utf-8 -*-
"""レリック約53種の塗りアイコンをAnimaで生成 → assets_raw_ui/ (rl_<key>.png)
現在の絵文字/名前のモチーフに沿う。画風はgen_ui_iconsと共通。"""
import json, os, time, sys, urllib.request, urllib.parse

URL = "http://127.0.0.1:8188"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_raw_ui")
os.makedirs(OUT, exist_ok=True)

NEG = ("worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, "
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

JOBS = {
    "rl_piggy":     "A cute pink piggy bank with a coin slot on its back and a gold coin.",
    "rl_member":    "A golden VIP membership card with a small star emblem.",
    "rl_hammer":    "A blacksmith forging hammer with a brown wooden handle and steel head.",
    "rl_regen":     "A green protective amulet talisman with a glossy heart-shaped gem in the center.",
    "rl_blanket":   "A folded cozy quilted blanket bedroll, warm brown and cream stripes.",
    "rl_bento":     "A traditional wooden bento lunch box with rice and food inside, lid beside it.",
    "rl_salt":      "A small ceramic bowl overflowing with white purifying salt.",
    "rl_herb":      "A tied bundle of fresh green medicinal herbs and leaves.",
    "rl_ram":       "A battering ram, a heavy horizontal log with a bronze ram head at the tip.",
    "rl_dice":      "A pair of red gambling dice showing pips.",
    "rl_adventmap": "A rolled open parchment adventurer map with a dotted route and an X mark.",
    "rl_scale":     "A golden merchant balance scale with two pans, coins on one side.",
    "rl_blastcore": "A round orange explosive core stone crackling with an inner burst pattern.",
    "rl_crossgem":  "A bright cyan gem cut in a bold plus cross shape.",
    "rl_xgem":      "A bright magenta gem cut in a bold X cross shape.",
    "rl_redcore":   "A round glossy deep red magma core stone.",
    "rl_ambercore": "A round glossy golden amber core stone.",
    "rl_violetcore":"A round glossy violet purple crystal core stone.",
    "rl_jadecore":  "A round glossy jade green core stone.",
    "rl_swordbook": "A thick red hardcover book with two golden crossed swords forming a bold X emblem on the cover, a sword-fighting manual.",
    "rl_guardbook": "A thick blue defense manual book with a shield emblem on the cover.",
    "rl_healbook":  "A thick green herbalism manual book with a leaf emblem on the cover.",
    "rl_dragonblade":"An ornate sword with a dragon-fang shaped steel blade and gold dragon crossguard.",
    "rl_aegis_gr":  "A huge ornate golden aegis tower shield with a blue gem center.",
    "rl_saintprayer":"A pair of praying hands with a small white angel halo above, holy.",
    "rl_swordcrest":"A heraldic crest emblem shaped like a single upright silver sword on a red shield.",
    "rl_shieldcrest":"A heraldic crest emblem of a bold blue kite shield with a gold border.",
    "rl_holywater": "A small ornate vial of glowing clear holy water with a blue cross stopper.",
    "rl_warring":   "A golden ring set with a fiery red ruby, ring of battle spirit.",
    "rl_guardring": "A silver ring set with a protective blue sapphire.",
    "rl_lifefruit": "A glossy red apple fruit of life with a green leaf, a small heart shine.",
    "rl_stardust":  "A small cluster of golden sparkle stars, one big and two small.",
    "rl_starbook":  "A deep blue star-reading tome book with a golden star and moon on the cover.",
    "rl_pouch":     "A big brown leather adventurer pouch bag with a buckle flap.",
    "rl_mist":      "A flowing grey misty cloak / cape swirling with fog.",
    "rl_deathmark": "A grey skull emblem with a small scythe, mark of the reaper.",
    "rl_magnet":    "A classic red horseshoe magnet with silver poles.",
    "rl_bigstar":   "A single big brilliant golden five-pointed star, glossy.",
    "rl_prism":     "A triangular crystal prism splitting into red green blue color bands.",
    "rl_crown":     "A regal golden royal crown with red and blue gems.",
    "rl_ironwill":  "A heavy grey iron chain link, symbol of unbreakable will.",
    "rl_linegem":   "A tall vertical rainbow gemstone with an up-down arrow through it.",
    "rl_linegemh":  "A single wide horizontal faceted rainbow crystal gem bar lying flat, glossy, with a small left-right double arrow beside it.",
    "rl_gachagem":  "A round glossy rainbow orb sphere swirling with all colors.",
    "rl_warforge":  "A glowing red catalyst orb crackling with fighting spirit energy in a small dish.",
    "rl_warforge2": "A blazing orange and red catalyst flame orb, intense fighting aura.",
    "rl_storegem":  "A golden abacus counting frame with beads, accumulation ring.",
    "rl_prayerbook":"An ornate holy prayer book with prayer beads draped over it.",
    "rl_palette":   "A wooden artist palette with rainbow paint dabs and a paintbrush.",
    "rl_warhorn":   "A golden brass war horn bugle with a red tassel.",
    "rl_starstaff": "An ornate wizard staff topped with a glowing star crystal.",
    "rl_anvil":     "A black iron blacksmith anvil, sturdy.",
}
SEED0 = 892000

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_relic"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":30,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":576,"height":576,"batch_size":1}},
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
names = list(JOBS.keys())
for spec in targets:
    name, _, sd = spec.partition("=")
    if os.path.exists(os.path.join(OUT, f"{name}.png")):
        print("skip", name, flush=True); continue
    seed = int(sd) if sd else SEED0 + names.index(name)
    print(f"[{name}] seed={seed}", flush=True)
    res=post(build(seed, ICON + JOBS[name]))
    result=wait(res["prompt_id"])
    for nid,out in result.get("outputs",{}).items():
        for img in out.get("images",[]):
            open(os.path.join(OUT,f"{name}.png"),"wb").write(fetch(img["filename"],img.get("subfolder",""),img.get("type","output")))
    print(f"  done {name}", flush=True)
print("ALL_DONE")
