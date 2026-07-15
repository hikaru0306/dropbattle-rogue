# -*- coding: utf-8 -*-
"""裏モード検証ボット: 脅威対応型＋盤面ビルド（つなげ役）
usage: python sim_bot_ura.py <charIdx 0-5> [N=5]

戦略（グリーディボットからの強化点）:
- 敵の攻撃予告(intents)を合計し、致死級/大ダメージ級なら最大グループを防御に回す
- 攻撃は常に残り最大グループ（大きく消す）
- 余ったアクションは「ビルド」: 小グループを消したとき重力落下後に
  最大グループがどれだけ育つかを盤面シミュレーションで評価し、最良の一手を選ぶ
- HP低下時はポーション、ショップでポーション/守護の薬を補充
- 報酬は剣/盾(+5/強化+10)を高優先で取得、焚き火では剣を強化
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1&full=1"
SIZE = 6
JUNK = 4
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
        out.append({"size": len(comp), "idx": comp[0], "cells": comp, "t": t, "junk": t == JUNK})
    return sorted(out, key=lambda g: -g["size"])

def max_group_after(board, removed):
    """removedを消して重力落下させた後の（既知セルのみの）最大グループサイズ"""
    grid = [[None] * SIZE for _ in range(SIZE)]  # grid[r][c] = 色 or None(未知)
    for c in range(SIZE):
        stack = [board[r * SIZE + c]["t"] for r in range(SIZE - 1, -1, -1) if r * SIZE + c not in removed]
        for k, t in enumerate(stack):  # 下から詰める
            grid[SIZE - 1 - k][c] = t
    seen = set(); best = 0
    for r in range(SIZE):
        for c in range(SIZE):
            t = grid[r][c]
            if t is None or t == JUNK or (r, c) in seen: continue
            stack = [(r, c)]; n = 0
            while stack:
                y, x = stack.pop()
                if (y, x) in seen or not (0 <= y < SIZE and 0 <= x < SIZE) or grid[y][x] != t: continue
                seen.add((y, x)); n += 1
                stack += [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
            best = max(best, n)
    return best

def builder_move(board, gs, exclude):
    """size<=3の小グループから「消すと次の最大グループが最も育つ」ものを選ぶ"""
    base = max((g["size"] for g in gs if not g["junk"]), default=0)
    best, gain = None, 0
    for g in gs:
        if g["idx"] in exclude or g["size"] > 3: continue
        after = max_group_after(board, set(g["cells"]))
        d = after - base
        if d > gain or (best is None and g["junk"] and g["size"] >= 2):
            gain = d; best = g
    return best, gain

# 剣/盾は+5/強化+10になったため高優先
PRIORITY = ["bolt", "atk", "def", "aoe", "star", "bombx", "bombd", "atkx", "plus", "pierce", "defx", "three", "heal"]
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

def cur_row(s):
    if s.get("cur") is None: return 0
    for n in s["map"]:
        if n["id"] == s["cur"]: return n["row"]
    return 0

def run_one(page, ci, mode="ura"):
    page.goto(URL, timeout=60000)
    page.wait_for_selector("text=冒険に出る", timeout=30000)
    page.click("text=冒険に出る")
    time.sleep(0.5)
    page.click("text=この仲間と冒険に出る")
    time.sleep(0.4)
    page.evaluate(f"window.__test.setChar({ci})")
    page.evaluate(f"window.__test.setMode('{mode}')")
    page.evaluate("window.__test.restart()")  # 指定モードで最初から
    time.sleep(0.5)
    assert page.evaluate("window.__test.state()")["mode"] == mode
    steps = 0
    forged = 0
    while steps < 2500:
        steps += 1
        s = page.evaluate("window.__test.state()")
        st = s["status"]
        row = cur_row(s)
        if st == "clear": return {"result": "CLEAR", "act": s["act"] + 1, "row": row, "hp": s["php"]}
        if st == "lose":
            kinds = [e["kind"] for e in s["enemies"] if e["alive"]]
            return {"result": "LOSE", "act": s["act"] + 1, "row": row, "hp": 0, "killer": kinds}
        if s.get("campfire"):
            if s["php"] < s["pmax"] * 0.65 or s["coins"] < 50:
                page.evaluate("window.__test.restHeal()")
            else:
                key = "atk" if forged % 2 == 0 else "def"
                page.evaluate(f"window.__test.forge('{key}')")
                forged += 1
                time.sleep(0.3)
                if page.evaluate("window.__test.state()").get("campfire"):
                    page.evaluate("window.__test.restHeal()")
            time.sleep(0.3); continue
        if s.get("shop"):
            offers = s["shop"] or []
            for want, cost in (("potion", 45), ("aegis", 55)):
                s2 = page.evaluate("window.__test.state()")
                if want in offers and s2["items"].count(want) < 2 and s2["coins"] >= cost + 45 and len(s2["items"]) < 3:
                    page.evaluate(f"window.__test.buy('{want}')"); time.sleep(0.2)
            page.evaluate("window.__test.closeShop()"); time.sleep(0.3); continue
        if st == "reward":
            pick_reward(page); continue
        if s.get("actClear"):
            try: page.click("css=[class*=pop-in] button >> nth=0", timeout=1500)
            except Exception: pass
            time.sleep(0.3)
            if page.evaluate("window.__test.state()").get("actClear"):
                page.evaluate("window.__test.nextAct()")
            time.sleep(0.4); continue
        if st == "map":
            sel = s["selectable"]
            if not sel: return {"result": "STUCK", "act": s["act"] + 1, "row": row, "hp": s["php"]}
            nodes = {x["id"]: x for x in s["map"]}
            hp_ratio = s["php"] / s["pmax"]
            def score(i):
                t = nodes[i]["type"]
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
            hp_ratio = s["php"] / s["pmax"]
            incoming = sum((iv or {}).get("dmg", 0) for iv in s["intents"])
            # --- アイテム: 致死予告 or 低HPでポーション、致死予告で守護の薬(防御2倍) ---
            if "potion" in s["items"] and (hp_ratio < 0.45 or incoming >= s["php"]):
                page.evaluate(f"window.__test.useItem({s['items'].index('potion')})"); time.sleep(0.2)
                s = page.evaluate("window.__test.state()")
                hp_ratio = s["php"] / s["pmax"]
            if "aegis" in s["items"] and incoming >= s["php"] * 0.8 and "def" not in s["used"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('aegis')})"); time.sleep(0.2)
            alive_n = sum(1 for e in s["enemies"] if e["alive"])
            if alive_n >= 2 and "bomb" in s["items"]:
                page.evaluate(f"window.__test.useItem({s['items'].index('bomb')})"); time.sleep(0.4)
            # --- ターゲット: ヒーラー優先 → 低HP ---
            tgt = None
            for i, e in enumerate(s["enemies"]):
                if e["alive"] and e["kind"] in ("spore", "mandra", "dryad"): tgt = i; break
            if tgt is None:
                aliveIdx = [(e["hp"], i) for i, e in enumerate(s["enemies"]) if e["alive"]]
                if aliveIdx: tgt = min(aliveIdx)[1]
            if tgt is not None:
                page.evaluate(f"window.__test.setTargetIdx({tgt})")
            gs = [g for g in groups(s["board"]) if not g["junk"]] or groups(s["board"])
            used = set(s["used"])
            remaining = [a for a in ["atk", "def", "heal"] if a not in used]
            if not remaining: time.sleep(0.3); continue
            per_def = max(1, s["per"]["def"])
            shield_now = s["tv"].get("def", 0)
            danger = incoming - shield_now
            lethal = danger >= s["php"]
            def_est = gs[0]["size"] * per_def if gs else 0
            # --- アクション割当て: 基本は攻め。致死ターンで「防御が実際に受け切れる」時だけ大防御 ---
            # (v42教訓: 守り優先はテンポ損で負ける。人間の勝ち筋=普段は攻め・致死ターンだけ大防御+ポーション)
            if lethal and "def" in remaining and def_est >= danger * 0.6:
                act, g = "def", gs[0]                       # 大防御で受ける価値がある
            elif "atk" in remaining:
                act, g = "atk", gs[0]                       # 常に攻めが最優先・最大グループ
            elif "def" in remaining and danger > 0:
                # 2手目以降の防御: 不足分をカバーできる最小グループ。届かないなら最大で軽減
                need = max(1, -(-danger // per_def))
                fit = [x for x in gs if x["size"] >= need]
                act, g = "def", (min(fit, key=lambda x: x["size"]) if fit else gs[0])
            elif "heal" in remaining and hp_ratio < 0.75:
                act, g = "heal", gs[0]
            else:
                # 余りアクション = ビルド: 次の盤面の最大グループを育てる一手
                act = remaining[0]
                bm, gain = builder_move(s["board"], groups(s["board"]), exclude=set())
                g = bm if (bm is not None and gain >= 2) else gs[min(len(used), len(gs) - 1)]
            page.evaluate(f"window.__test.setAct('{act}')")
            time.sleep(0.05)
            page.evaluate(f"window.__test.commit({g['idx']})")
            time.sleep(0.35)
            continue
        time.sleep(0.25)
    return {"result": "TIMEOUT", "act": s["act"] + 1, "row": 0, "hp": 0}

def main():
    ci = int(sys.argv[1])
    N = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    mode = sys.argv[3] if len(sys.argv) > 3 else "ura"
    tag = "裏" if mode == "ura" else "表"
    results = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=EXE)
        page = b.new_page(viewport={"width": 420, "height": 900})
        for i in range(N):
            t0 = time.time()
            try:
                r = run_one(page, ci, mode)
            except Exception as e:
                r = {"result": "ERROR:" + str(e)[:60], "act": 0, "row": 0, "hp": 0}
            r["min"] = round((time.time() - t0) / 60, 1)
            results.append(r)
            print(f"[{tag}/{CHAR_NAME[ci]}] run{i+1}: {r['result']} {tag}{r['act']}章{r.get('row',0)+1}層 hp{r['hp']}"
                  + (f" killer={r['killer']}" if r.get("killer") else "") + f" ({r['min']}min)", flush=True)
        b.close()
    clears = sum(1 for r in results if r["result"] == "CLEAR")
    prog = [f"{r['act']}-{r.get('row',0)+1}" for r in results]
    print(f"=== {tag}/{CHAR_NAME[ci]}: {clears}/{N} clears, 到達(章-層) {prog} ===")

if __name__ == "__main__":
    main()
