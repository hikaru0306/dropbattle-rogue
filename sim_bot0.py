# -*- coding: utf-8 -*-
"""無心ボット: 何も考えず大きいグループを消すだけ（アイテム/ルート/予告 無視）"""
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
            page.evaluate("window.__test.restHeal()")
            time.sleep(0.3)
            continue
        if s.get("shop"):
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
            chosen = sel[0]  # 何も考えず先頭
            page.evaluate(f"window.__test.enter({chosen})")
            time.sleep(0.5)
            continue
        if st == "battle":
            if s.get("locked"):
                time.sleep(0.25)
                continue
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
