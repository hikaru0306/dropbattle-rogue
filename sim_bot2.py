# -*- coding: utf-8 -*-
"""スマートボット: 敵の予告ダメージに合わせて防御量を調整して通しプレイ"""
import sys, time, json
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1&full=1"
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
                if t == "rest": return 0 if hp_ratio < 0.7 else 3
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
            # ポーション使用: 予告ダメージで落ちる圏内なら合わせて飲む
            incoming_now = sum(iv["dmg"] for iv in (s.get("intents") or []) if iv)
            danger = s["php"] - max(0, incoming_now - s["tv"]["def"]) < s["pmax"] * 0.15
            enr_threat = any(e["alive"] and e["enr"] >= 2 for e in s["enemies"])
            if (s["php"] < s["pmax"] * (0.6 if enr_threat else 0.45) or danger) and "potion" in s["items"]:
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
            # 攻め主体+致死ターンだけ大防御（人間的な受け）: 普段は凡と同配分でテンポ維持
            incoming = sum(iv["dmg"] for iv in (s.get("intents") or []) if iv)
            need = max(0, incoming - s["tv"]["def"])
            dper = (s.get("per") or {}).get("def", 10)
            need_drops = (need + dper - 1) // dper
            plan = {}
            pool = list(range(len(gs)))
            hp_after_leak = s["php"] - max(0, need - (len(gs) > 1 and gs[1]["size"] or 0) * dper)
            danger_turn = need > 0 and (hp_after_leak < s["pmax"] * 0.25)
            if danger_turn and "def" in remaining and pool:
                cand = [i for i in pool if gs[i]["size"] * dper >= need]
                plain = [i for i in cand if not gs[i]["sps"]]
                di = min(plain or cand, key=lambda i: gs[i]["size"]) if cand else max(pool, key=lambda i: gs[i]["size"])
                plan["def"] = di; pool.remove(di)
            if "atk" in remaining and pool:
                BONUS = {"aoe": 5, "bolt": 4, "bombx": 3, "bombd": 3, "star": 3, "atkx": 4, "atk": 2, "plus": 2, "pierce": 2}
                ai = max(pool, key=lambda i: (gs[i]["size"], sum(BONUS.get(sp, 1) for sp in gs[i]["sps"])))
                plan["atk"] = ai; pool.remove(ai)
            if "def" in remaining and "def" not in plan and pool:
                if need_drops > 0:
                    cand = [i for i in pool if gs[i]["size"] >= need_drops]
                    plain = [i for i in cand if not gs[i]["sps"]]
                    di = min(plain or cand, key=lambda i: gs[i]["size"]) if cand else max(pool, key=lambda i: gs[i]["size"])
                else:
                    plain = [i for i in pool if not gs[i]["sps"]] or pool
                    di = min(plain, key=lambda i: gs[i]["size"])
                plan["def"] = di; pool.remove(di)
            if "heal" in remaining and pool:
                hi = min(pool, key=lambda i: gs[i]["size"])
                plan["heal"] = hi; pool.remove(hi)
            act = next(a for a in ["def", "atk", "heal"] if a in remaining)
            g = gs[plan.get(act, 0)] if act in plan else gs[0]
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
