# -*- coding: utf-8 -*-
"""hero2-5 の候補を複数シードで生成 → assets_cand/ に保存。
gen_chars.py の STYLE/NEG/build/post/wait/fetch をそのまま流用（統一感担保）。"""
import os, random, sys
import gen_chars as g

CAND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_cand")
os.makedirs(CAND, exist_ok=True)

names = sys.argv[1:] or ["hero2", "hero3", "hero4", "hero5"]
N = 3
for name in names:
    for i in range(N):
        seed = random.randint(0, 2**63 - 1)
        print(f"[{name}#{i}] seed={seed}", flush=True)
        res = g.post(g.build(seed, g.CHARS[name]))
        result = g.wait(res["prompt_id"])
        for nid, out in result.get("outputs", {}).items():
            for img in out.get("images", []):
                data = g.fetch(img["filename"], img.get("subfolder", ""), img.get("type", "output"))
                path = os.path.join(CAND, f"{name}_{i}.png")
                with open(path, "wb") as f:
                    f.write(data)
                print(" ->", path, flush=True)
print("DONE")
