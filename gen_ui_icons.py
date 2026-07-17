# -*- coding: utf-8 -*-
"""UIアイコン全27種をAnimaで統一スタイル再生成 → assets_raw_ui/
（icon_*=ヘッダー/アクション, mk_*=盤面特殊マーク, node_*=マップノード）
モチーフは現行を踏襲、画風を敵/キャラと同じ「スレスパ×ポケモン・太アウトライン・セル塗り」に統一"""
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
    "a single fantasy game UI icon, flat cel shading with simple two-tone shadow, "
    "bold thick dark outline, art style between Slay the Spire and Pokemon, "
    "vivid saturated colors, chunky readable silhouette, "
    "one object only, centered, isolated on pure white background, no text. ")

JOBS = {
    # ―― ヘッダー/アクションアイコン ――
    "icon_atk":     "A sturdy short sword pointing straight up, polished steel blade, ornate gold crossguard, red leather wrapped grip.",
    "icon_def":     "A round shield seen from the front, deep blue steel face, bold gold rim, small gold center boss.",
    "icon_heal":    "A small rounded glass potion bottle filled with bright green liquid, brown cork stopper.",
    "icon_coin":    "A single thick gold coin with an embossed six-pointed star stamp, slightly tilted.",
    "icon_bag":     "A plump brown leather drawstring pouch tied at the top with a rope.",
    "icon_note":    "A single golden musical note symbol with a round note head and a curved flag on the stem, flat bold design.",
    "icon_speaker": "An ornate golden brass horn megaphone held sideways, wide bell opening facing left, hovering, nothing underneath.",
    # ―― 盤面特殊ドロップのマーク ――
    "mk_star":   "A classic bold five-pointed golden star shape, flat yellow gold fill with an orange bottom shade, single star symbol.",
    "mk_plus":   "A bold bright teal plus cross symbol with slightly rounded ends.",
    "mk_three":  "Three glossy bright orange round orbs arranged in a pyramid triangle, touching each other, hovering, nothing underneath.",
    "mk_pierce": "A bold silver arrow with a wide triangular arrowhead and thick shaft pointing to the upper right, chunky cartoon proportions, short red feather fletching.",
    "mk_skull":  "A cute round cartoon skull, pale grey white, simple eye sockets.",
    "mk_aoe":    "Two short crossed steel swords forming a clean X shape, gold crossguards.",
    "mk_gold":   "Three shiny thick gold coins in a small stack, top coin slightly offset, each with visible rim edge.",
    "mk_bolt":   "A bold bright yellow lightning bolt symbol, sharp clean zigzag shape with a pointed bottom tip.",
    "mk_bombx":  "A round dark iron bomb with a short lit fuse, a bold bright orange plus cross emblem painted on its body.",
    "mk_bombd":  "A round dark purple iron bomb with a short lit fuse, a bold bright violet X cross emblem painted on its body.",
    "mk_atkx":   "A sword pointing straight up completely engulfed in bright vivid orange and yellow flames, red leather grip.",
    "mk_defx":   "A gold heater shield with a flat top and pointed bottom, a large glossy round red gem set in the center.",
    "mk_heart":  "A glossy bright green heart.",
    "mk_store":  "A closed purple magic tome book with gold trim and a small gold plus emblem on the cover.",
    # ―― キャラ専用特殊ドロップのマーク ――
    "mk_holy":     "A radiant golden sun symbol, a bright yellow circle surrounded by bold triangular sun rays.",
    "mk_ink":      "A flat paint splat symbol, a magenta paint splash blob with wavy edges and two small droplets, top view.",
    "mk_warcry":   "A bold red clenched fist symbol pointing upward, thick outline, powerful.",
    "mk_sigil":    "A small grey stone tablet engraved with a single bright cyan glowing rune letter.",
    "mk_stardust": "A cluster of golden five-pointed stars, one large star with two small stars beside it.",
    "mk_ore":      "A chunk of rough dark grey rock with steel blue crystal shards growing from it.",
    # ―― マップノード ――
    "node_battle":   "Two crossed steel swords forming an X, gold crossguards, red grips.",
    "node_boss":     "A menacing dark demon king crown, deep purple black metal with jagged spikes and small red gems.",
    "node_elite":    "A dark purple demonic dragon head emblem with curved horns, facing forward, fierce.",
    "node_horde":    "A tattered orange war banner flag hanging from a horizontal wooden pole, dark beast paw emblem on the cloth.",
    "node_rest":     "A cozy campfire, bright orange flames over a few crossed brown logs and small grey stones.",
    "node_treasure": "A closed sturdy wooden treasure chest with gold metal trim, gold lock, slightly tilted front view.",
}
SEED0 = 888100

def build(seed, text):
    return {"1":{"class_type":"SaveImage","inputs":{"images":["8",0],"filename_prefix":"db_uiicon"}},
      "8":{"class_type":"VAEDecode","inputs":{"samples":["19",0],"vae":["15",0]}},
      "11":{"class_type":"CLIPTextEncode","inputs":{"text":text,"clip":["45",0]}},
      "12":{"class_type":"CLIPTextEncode","inputs":{"text":NEG,"clip":["45",0]}},
      "15":{"class_type":"VAELoader","inputs":{"vae_name":"qwen_image_vae.safetensors"}},
      "19":{"class_type":"KSampler","inputs":{"seed":seed,"steps":32,"cfg":4.5,"sampler_name":"er_sde","scheduler":"simple","denoise":1.0,"model":["44",0],"positive":["11",0],"negative":["12",0],"latent_image":["28",0]}},
      "28":{"class_type":"EmptyLatentImage","inputs":{"width":640,"height":640,"batch_size":1}},
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
print("ALL_DONE")
