# -*- coding: utf-8 -*-
"""キャラ別難易度検証ボット: 全5キャラでグリーディ通しプレイ
usage: python sim_bot_chars.py <charIdx 0-4> [N=5]
skill別戦略:
  heal/healx: 攻→防→回復（HP低時は攻→回→防）
  buff/store: 攻→強化/蓄積→防（HP低時は対象=防で 防→強化→攻）※強化は加算式なので攻撃コミット後に使う
  recolor   : 先に最大グループへ隣接グループを塗り替えて拡張→攻→防
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1&full=1"
SIZE = 6
CHAR_SKILL = ["heal", "recolor", "buff", "store", "healx", "smith"]
CHAR_NAME = ["アルド", "イリス", "ガレス", "ノア", "ルクス", "ブロム"]

def groups(board):
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
        out.append({"size": len(comp), "idx": comp[0], "cells": comp, "t": t, "junk": t == 4})
    return sorted(out, key=lambda g: -g["size"])

def recolor_plan(board):
    """最大グループLに隣接する別色グループを L の色へ塗る (paintColor, tapIdx) を返す"""
    gs = [g for g in groups(board) if not g["junk"] and not board[g["idx"]].get("w")]
    if not gs: return None
    L = gs[0]
    if L["t"] > 3: return None  # インクは0-3色のみ
    lset = set(L["cells"])
    best = None
    for g in gs[1:]:
        if g["t"] == L["t"] or g["t"] == 4: continue
        adjacent = False
        for j in g["cells"]:
            r, c = divmod(j, SIZE)
            for nb in (j - SIZE if r > 0 else -1, j + SIZE if r < 5 else -1,
                       j - 1 if c > 0 else -1, j + 1 if c < 5 else -1):
                if nb in lset: adjacent = True; break
            if adjacent: break
        if adjacent and (best is None or g["size"] > best["size"]):
            best = g
    if best: return (L["t"], best["idx"])
    # 拡張先なし: 最小グループを最大色に塗っておく（アクション消化）
    return (L["t"], gs[-1]["idx"])

PRIORITY = ["bolt","aoe","bombx","bombd","star","atkx","atk","plus","def","pierce","three","defx","heal"]
NAMES = {"bolt":"サンダー","aoe":"乱れ斬り","bombx":"クロスボム","bombd":"Xボム","star":"スター","atkx":"猛攻","atk":"ソード","plus":"プラス","def":"ガード","pierce":"貫通","three":"トリプル","defx":"鉄壁","heal":"ヒール"}
def pick_reward(page):
    time.sleep(0.4)
    try:
        texts = page.evaluate("[...document.querySelectorAll('[class*=pop-in] button')].map(b=>b.innerText)")
        best, bestrank = 0, 99
        for i, t in enumerate(texts):
            for rank, k in enumerate(PRIORITY):
                if NAMES[k] in t and rank < bestrank:
                    bestrank = rank; best = i
        page.click(f"css=[class*=pop-in] button >> nth={best}", timeout=2000)
    except Exception:
        try: page.click("css=[class*=pop-in] button >> nth=0", timeout=2000)
        except Exception: pass
    time.sleep(0.4)

def run_one(page, ci):
    skill = CHAR_SKILL[ci]
    page.goto(URL, timeout=60000)
    page.wait_for_selector("text=冒険に出る", timeout=30000)
    page.click("text=冒険に出る")
    time.sleep(0.5)
    page.click(f"css=div.flex.justify-center.gap-2 > button >> nth={ci}")
    time.sleep(0.3)
    page.click("text=この仲間と冒険に出る")
    time.sleep(0.5)
    steps = 0
    while steps < 1200:
        steps += 1
        s = page.evaluate("window.__test.state()")
        st = s["status"]
        if st == "clear": return {"result": "CLEAR", "act": s["act"] + 1, "hp": s["php"]}
        if st == "lose":  return {"result": "LOSE",  "act": s["act"] + 1, "hp": 0}
        if s.get("campfire"):
            if s["php"] < s["pmax"] * 0.7 or s["coins"] < 50:
                page.evaluate("window.__test.restHeal()")
            else:
                page.evaluate("window.__test.forge('atk')")
                time.sleep(0.3)
                if page.evaluate("window.__test.state()").get("campfire"):
                    page.evaluate("window.__test.restHeal()")
            time.sleep(0.3); continue
        if s.get("shop"):
            offers = s["shop"] or []
            if s["items"].count("potion") < 2 and s["coins"] >= 45 and len(s["items"]) < 3 and "potion" in offers:
                page.evaluate("window.__test.buy('potion')"); time.sleep(0.2)
                s = page.evaluate("window.__test.state()")
            if s["coins"] >= 120 and len(s["items"]) < 3 and "bomb" in offers:
                page.evaluate("window.__test.buy('bomb')"); time.sleep(0.2)
            page.evaluate("window.__test.closeShop()"); time.sleep(0.3); continue
        if st == "reward":
            pick_reward(page); continue
        if s.get("actClear"):
            # ボス報酬レリックは1つ受け取る（実プレイ準拠）
            try: page.click("css=[class*=pop-in] button >> nth=0", timeout=1500)
            except Exception: pass
            time.sleep(0.3)
            if page.evaluate("window.__test.state()").get("actClear"):
                page.evaluate("window.__test.nextAct()")
            time.sleep(0.4); continue
        if st == "map":
            sel = s["selectable"]
            if not sel: return {"result": "STUCK", "act": s["act"] + 1, "hp": s["php"]}
            nodes = {x["id"]: x for x in s["map"]}
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
            time.sleep(0.5); continue
        if st == "battle":
            if s.get("locked"): time.sleep(0.25); continue
            if s["php"] < s["pmax"] * 0.4 and "potion" in s["items"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('potion')})"); time.sleep(0.2)
            alive_n = sum(1 for e in s["enemies"] if e["alive"])
            if alive_n >= 2 and "bomb" in s["items"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('bomb')})"); time.sleep(0.4)
            tgt = None
            for i, e in enumerate(s["enemies"]):
                if e["alive"] and e["kind"] in ("spore", "mandra"): tgt = i; break
            if tgt is None:
                aliveIdx = [(e["hp"], i) for i, e in enumerate(s["enemies"]) if e["alive"]]
                if aliveIdx: tgt = min(aliveIdx)[1]
            if tgt is not None:
                page.evaluate(f"window.__test.setTargetIdx({tgt})")
            gs = [g for g in groups(s["board"]) if not g["junk"]] or groups(s["board"])
            used = set(s["used"])
            remaining = [a for a in ["atk", "def", "heal"] if a not in used]
            if not remaining: time.sleep(0.3); continue
            hp_ratio = s["php"] / s["pmax"]
            # --- 鍛冶: 素材4以上なら最大グループに生成→そのまま攻撃で回収、不足なら補充で貯める ---
            if skill == "smith" and "heal" not in used:
                stock = page.evaluate("window.__test.charInfo()")["stock"]
                if stock >= 4:
                    page.evaluate("window.__test.setSmithMode('gen')")
                    page.evaluate("window.__test.setAct('heal')")
                    page.evaluate(f"window.__test.commit({gs[0]['idx']})")
                    time.sleep(0.3); continue  # 次ループで特殊込みグループを攻撃
                page.evaluate("window.__test.setSmithMode('stock')")
            # --- 色変え: 3つ目は「隣接グループを最大色に塗って拡張」を最初に使う ---
            if skill == "recolor" and "heal" not in used:
                plan = recolor_plan(s["board"])
                if plan:
                    page.evaluate(f"window.__test.setPaint({plan[0]})")
                    page.evaluate("window.__test.setAct('heal')")
                    page.evaluate(f"window.__test.commit({plan[1]})")
                    time.sleep(0.3); continue  # 盤面再取得してから攻防
            # --- 使う順番とグループ配分 ---
            if skill in ("buff", "store"):
                if hp_ratio > 0.5:
                    page.evaluate("window.__test.setSkillTarget('atk')")
                    order = ["atk", "heal", "def"]   # 攻撃コミット後に強化/蓄積
                else:
                    page.evaluate("window.__test.setSkillTarget('def')")
                    order = ["def", "heal", "atk"]
            else:
                order = ["atk", "def", "heal"] if hp_ratio > 0.5 else ["atk", "heal", "def"]
            act = [a for a in order if a in remaining][0]
            rank = len(used)  # 0手目=最大グループ, 1手目=次…
            g = gs[min(rank, len(gs) - 1)]
            page.evaluate(f"window.__test.setAct('{act}')")
            time.sleep(0.05)
            page.evaluate(f"window.__test.commit({g['idx']})")
            time.sleep(0.35)
            continue
        time.sleep(0.25)
    return {"result": "TIMEOUT", "act": 0, "hp": 0}

def main():
    ci = int(sys.argv[1])
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    results = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=EXE)
        page = b.new_page(viewport={"width": 420, "height": 900})
        for i in range(N):
            t0 = time.time()
            try:
                r = run_one(page, ci)
            except Exception as e:
                r = {"result": "ERROR:" + str(e)[:60], "act": 0, "hp": 0}
            r["min"] = round((time.time() - t0) / 60, 1)
            results.append(r)
            print(f"[{CHAR_NAME[ci]}] run{i+1}: {r['result']} act{r['act']} hp{r['hp']} ({r['min']}min)", flush=True)
        b.close()
    clears = sum(1 for r in results if r["result"] == "CLEAR")
    acts = [r["act"] for r in results]
    print(f"=== {CHAR_NAME[ci]} ({CHAR_SKILL[ci]}): {clears}/{N} clears, acts {acts} ===")

if __name__ == "__main__":
    main()
