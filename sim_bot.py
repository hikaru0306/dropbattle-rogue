# -*- coding: utf-8 -*-
"""難易度検証ボット: グリーディ戦略で通しプレイし勝率・到達点を測定"""
import sys, time, json
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"
SIZE = 6

def groups(board):
    """盤面(t,sp)から同色グループ一覧を返す [(size, idx, has_heart, has_atk, junk)]"""
    seen = set()
    out = []
    for i in range(36):
        if i in seen: continue
        t = board[i]["t"]
        stack = [i]; comp = []
        while stack:
            j = stack.pop()
            if j in seen or board[j]["t"] != t: continue
            seen.add(j); comp.append(j)
            r, c = divmod(j, SIZE)
            if r > 0: stack.append(j - SIZE)
            if r < 5: stack.append(j + SIZE)
            if c > 0: stack.append(j - 1)
            if c < 5: stack.append(j + 1)
        sps = [board[j]["sp"] for j in comp if board[j]["sp"]]
        out.append({"size": len(comp), "idx": comp[0], "sps": sps, "junk": t == 4})
    return sorted(out, key=lambda g: -g["size"])

PRIORITY = ["bolt","aoe","bombx","bombd","star","atkx","atk","plus","def","pierce","three","defx","heal"]
def pick_reward(page):
    time.sleep(0.4)
    try:
        texts = page.evaluate("[...document.querySelectorAll('div.pop-in button, [class*=pop-in] button')].map(b=>b.innerText)")
        best = 0
        bestrank = 99
        names = {"bolt":"サンダー","aoe":"乱れ斬り","bombx":"クロスボム","bombd":"Xボム","star":"スター","atkx":"猛攻","atk":"ソード","plus":"プラス","def":"ガード","pierce":"貫通","three":"トリプル","defx":"鉄壁","heal":"ヒール"}
        for i, t in enumerate(texts):
            for rank, k in enumerate(PRIORITY):
                if names[k] in t and rank < bestrank:
                    bestrank = rank; best = i
        page.click(f"css=[class*=pop-in] button >> nth={best}", timeout=2000)
    except Exception:
        try:
            page.click("css=[class*=pop-in] button >> nth=0", timeout=2000)
        except Exception:
            pass
    time.sleep(0.4)

def run_one(page):
    page.goto(URL, timeout=60000)
    page.wait_for_selector("text=冒険に出る", timeout=30000)
    page.click("text=冒険に出る")
    time.sleep(0.4)
    steps = 0
    while steps < 900:
        steps += 1
        s = page.evaluate("window.__test.state()")
        st = s["status"]
        if st == "clear":
            return {"result": "CLEAR", "act": s["act"] + 1, "hp": s["php"]}
        if st == "lose":
            return {"result": "LOSE", "act": s["act"] + 1, "hp": 0}
        if s.get("campfire"):
            if s["php"] < s["pmax"] * 0.7 or s["coins"] < 50:
                page.evaluate("window.__test.restHeal()")
            else:
                page.evaluate("window.__test.forge('atk')")
                time.sleep(0.3)
                if page.evaluate("window.__test.state()").get("campfire"):
                    page.evaluate("window.__test.restHeal()")
            time.sleep(0.3)
            continue
        if s.get("shop"):
            # HP半分以下でポーションが売ってたら買う
            offers = s["shop"] or []
            if s["items"].count("potion") < 2 and s["coins"] >= 45 and len(s["items"]) < 3 and "potion" in offers:
                page.evaluate("window.__test.buy('potion')")
                time.sleep(0.2)
                s = page.evaluate("window.__test.state()")
            if s["coins"] >= 120 and len(s["items"]) < 3 and "bomb" in offers:
                page.evaluate("window.__test.buy('bomb')")
                time.sleep(0.2)
            page.evaluate("window.__test.closeShop()")
            time.sleep(0.3)
            continue
        if st == "reward":
            pick_reward(page)
            continue
        if s.get("actClear"):
            page.evaluate("window.__test.nextAct()")
            time.sleep(0.4)
            continue
        if st == "map":
            sel = s["selectable"]
            if not sel:
                return {"result": "STUCK", "act": s["act"] + 1, "hp": s["php"]}
            nodes = {x["id"]: x for x in s["map"]}
            # HP低なら休憩優先、次に宝箱、それ以外は先頭
            def score(i):
                t = nodes[i]["type"]
                hp_ratio = s["php"] / s["pmax"]
                if t == "rest": return 0 if hp_ratio < 0.6 else 3
                if t == "treasure": return 1
                if t == "battle": return 2
                if t == "horde": return 4 if hp_ratio > 0.7 else 6
                if t == "elite": return 5 if hp_ratio > 0.8 else 9
                return 4
            chosen = min(sel, key=score)
            page.evaluate(f"window.__test.enter({chosen})")
            time.sleep(0.5)
            continue
        if st == "battle":
            if s.get("locked"):
                time.sleep(0.25)
                continue
            # ポーション使用
            if s["php"] < s["pmax"] * 0.4 and "potion" in s["items"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('potion')})")
                time.sleep(0.2)
            # 敵2体以上なら爆弾
            alive_n = sum(1 for e in s["enemies"] if e["alive"])
            if alive_n >= 2 and "bomb" in s["items"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('bomb')})")
                time.sleep(0.4)
            # ターゲット: ヒーラー系 > HP最低の敵
            tgt = None
            for i, e in enumerate(s["enemies"]):
                if e["alive"] and e["kind"] in ("spore", "mandra"):
                    tgt = i; break
            if tgt is None:
                aliveIdx = [(e["hp"], i) for i, e in enumerate(s["enemies"]) if e["alive"]]
                if aliveIdx: tgt = min(aliveIdx)[1]
            if tgt is not None:
                page.evaluate(f"window.__test.setTargetIdx({tgt})")
            gs = [g for g in groups(s["board"]) if not g["junk"]]
            if not gs:
                gs = groups(s["board"])
            used = set(s["used"])
            remaining = [a for a in ["atk", "def", "heal"] if a not in used]
            if not remaining:
                time.sleep(0.3)
                continue
            act = remaining[0]
            # 大きいグループ→攻撃、次→防御、最後→回復（HP高なら防御寄せの順で消化）
            gi = 3 - len(remaining)  # 0,1,2番目のグループ
            g = gs[min(gi, len(gs) - 1)]
            order = ["atk", "def", "heal"] if s["php"] > s["pmax"] * 0.5 else ["atk", "heal", "def"]
            act = [a for a in order if a in remaining][0]
            page.evaluate(f"window.__test.setAct('{act}')")
            time.sleep(0.05)
            page.evaluate(f"window.__test.commit({g['idx']})")
            time.sleep(0.35)
            continue
        time.sleep(0.25)
    return {"result": "TIMEOUT", "act": 0, "hp": 0}

N = int(sys.argv[1]) if len(sys.argv) > 1 else 6
results = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    for i in range(N):
        t0 = time.time()
        r = run_one(page)
        r["min"] = round((time.time() - t0) / 60, 1)
        results.append(r)
        print(f"run{i+1}: {r['result']} act{r['act']} hp{r['hp']} ({r['min']}min)", flush=True)
    b.close()

clears = sum(1 for r in results if r["result"] == "CLEAR")
print(f"=== {clears}/{N} clears ===")
acts = [r["act"] for r in results]
print("acts reached:", acts)
