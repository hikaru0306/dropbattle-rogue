# -*- coding: utf-8 -*-
"""鍛冶師（smith）検証: 補充で素材蓄積 / 生成は袋の中身比率で抽選した複製(extra)を配置し袋会計に影響しない / 強化で＋化 / 素材のバトル間持ち越し / 素材0はアクション消費なし"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"

fails, errors = [], []
def chk(name, cond, extra=""):
    print(("OK  " if cond else "NG  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

def st(p): return p.evaluate("window.__test.state()")
def ci(p): return p.evaluate("window.__test.charInfo()")

def fill(p, t=1):
    for i in range(36):
        p.evaluate(f"window.__test.setCellType({i}, {t})")

def make_group(p, idxs, t):
    """指定セルだけ色t、他は市松模様（縦横で隣接しない）にして孤立させる"""
    for i in range(36):
        r, c = divmod(i, 6)
        base = 2 if (r + c) % 2 == 0 else 3
        p.evaluate(f"window.__test.setCellType({i}, {base})")
    for i in idxs:
        p.evaluate(f"window.__test.setCellType({i}, {t})")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.5)

    # 選択画面: 7タイル・鍛冶師選択（6体目）
    tiles = page.query_selector_all("div.flex.justify-center.gap-2 > button")
    chk("7 tiles on select", len(tiles) == 7)
    tiles[5].click(); time.sleep(0.4)
    body = page.evaluate("document.body.innerText")
    chk("smith name/unlock shown", "鍛冶師ブロム" in body)
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)
    info = ci(page)
    chk("char applied (smith)", info["cur"] == 5 and info["skill"] == "smith" and info["smithMode"] == "stock" and info["stock"] == 0)

    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    page.evaluate("window.__test.spawn(['slime'])"); time.sleep(0.3)

    # 1) 補充: 5個消し → 素材+5・healは増えない
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.2)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.8)
    s = st(page); info = ci(page)
    chk("stock +5 on 補充", info["stock"] == 5, f"stock={info['stock']}")
    chk("heal not gained", s["tv"]["heal"] == 0)
    chk("action consumed", "heal" in s["used"])

    # 2) 生成: 別グループ(6個)に素材5で特殊5個配置（袋の中身比率で抽選した複製・袋会計に影響しない）
    page.evaluate("window.__test.resolve()"); time.sleep(1.2)
    make_group(page, [6, 7, 8, 9, 10, 11], 0); time.sleep(0.2)
    bag_before = st(page)["bagLeft"]
    owned_before = st(page)["ownedTotal"]
    sp_before = st(page)["specials"]
    page.evaluate("window.__test.setSmithMode('gen')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.6)
    s = st(page); info = ci(page)
    gen_n = s["specials"] - sp_before
    chk("gen placed 5 specials", gen_n == 5, f"gen={gen_n}")
    chk("stock spent to 0", info["stock"] == 0, f"stock={info['stock']}")
    # 袋の残数・所持数は一切変わらない（生成物は複製）
    chk("bag untouched by gen", s["bagLeft"] == bag_before, f"bag {bag_before}->{s['bagLeft']}")
    chk("owned untouched by gen", s["ownedTotal"] == owned_before, f"owned {owned_before}->{s['ownedTotal']}")
    row = [s["board"][i] for i in [6, 7, 8, 9, 10, 11]]
    chk("specials on tapped group", sum(1 for c in row if c["sp"]) == 5, str([c["sp"] for c in row]))
    chk("all gen drops flagged extra", all(c["x"] for c in row if c["sp"]), str([(c["sp"], c["x"]) for c in row]))
    chk("board not cleared (gen)", all(s["board"][i]["t"] == 0 for i in [6, 7, 8, 9, 10, 11]))

    # 3) 素材0で生成 → アクション消費なし
    page.evaluate("window.__test.resolve()"); time.sleep(1.2)
    make_group(page, [12, 13, 14], 1); time.sleep(0.2)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(12)"); time.sleep(0.4)
    s = st(page)
    chk("no-op when stock 0", "heal" not in s["used"])

    # 4) 補充で貯め直し → 強化: 特殊入りグループを＋化
    page.evaluate("window.__test.setSmithMode('stock')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(12)"); time.sleep(0.8)  # 3個消し → 素材3
    info = ci(page)
    chk("stock refilled 3", info["stock"] == 3, f"stock={info['stock']}")
    # ターンを終わらせてから強化テスト（healは1ターン1回のため）
    page.evaluate("window.__test.resolve()"); time.sleep(1.2)
    # 特殊2個入りのグループを作る
    make_group(page, [18, 19, 20, 21], 1); time.sleep(0.2)
    page.evaluate("window.__test.setCellSpecial(18, 'atk', false, false)")
    page.evaluate("window.__test.setCellSpecial(19, 'def', false, false)")
    page.evaluate("window.__test.setSmithMode('up')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(18)"); time.sleep(0.6)
    s = st(page); info = ci(page)
    chk("upgraded 2 specials", s["board"][18]["u"] and s["board"][19]["u"], str([s["board"][18], s["board"][19]]))
    chk("stock 3-2=1", info["stock"] == 1, f"stock={info['stock']}")

    # 5) 素材はバトルごとにリセット（勝利→次バトルで0に）
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.setAct('atk')")
    fillgrp = [30, 31, 32]
    make_group(page, fillgrp, 2); time.sleep(0.2)
    page.evaluate("window.__test.commit(30)"); time.sleep(0.6)
    page.evaluate("window.__test.resolve()"); time.sleep(2.5)  # 撃破→報酬
    if st(page)["status"] == "reward":
        page.evaluate("window.__test.declineReward()"); time.sleep(1.0)
    s = st(page)
    if s["status"] == "map" and s["selectable"]:
        # 休憩/宝箱はバトルにならず素材リセットが走らないため、必ずバトル系ノードを選ぶ
        types = {n["id"]: n["type"] for n in s["map"]}
        bid = next((i for i in s["selectable"] if types[i] in ("battle", "horde", "elite")), s["selectable"][0])
        page.evaluate(f"window.__test.enter({bid})"); time.sleep(0.8)
        info = ci(page)
        chk("stock resets per battle", info["stock"] == 0, f"stock={info['stock']}")

        # 6) 生成は所持特殊が全て盤面に出ていても袋比率の抽選で生成できる（複製なので枯渇の概念なし）
        page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)  # 高HPで撃破を避ける
        page.evaluate("window.__test.setSmithMode('stock')")
        make_group(page, [0, 1, 2], 1); time.sleep(0.2)
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(0)"); time.sleep(0.8)  # 素材3を確保
        chk("stock 3 for saturated test", ci(page)["stock"] == 3, f"stock={ci(page)['stock']}")
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        # make_groupで盤面の特殊を全消去してから、所持特殊を全数盤面に配置
        make_group(page, [6, 7, 8], 1); time.sleep(0.2)
        owned = st(page)["owned"]
        owned_total_before = st(page)["ownedTotal"]
        bag_before = st(page)["bagLeft"]
        cells = list(range(24, 36)); ptr = 0
        for k, v in owned.items():
            for _ in range(v):
                page.evaluate(f"window.__test.setCellSpecial({cells[ptr]}, '{k}', false, false)"); ptr += 1
        s = st(page)
        chk("all owned specials on board", s["specials"] == s["ownedTotal"], f"sp={s['specials']} owned={s['ownedTotal']}")
        page.evaluate("window.__test.setSmithMode('gen')")
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(6)"); time.sleep(0.6)
        s = st(page); info = ci(page)
        row_sp = [s["board"][i]["sp"] for i in [6, 7, 8]]
        row_x = [s["board"][i]["x"] for i in [6, 7, 8]]
        chk("gen still made 3 specials when saturated", len([x for x in row_sp if x]) == 3, str(row_sp))
        chk("saturated gen drops flagged extra", all(row_x), str(row_x))
        chk("saturated gen did not add to owned", st(page)["ownedTotal"] == owned_total_before, f"{owned_total_before}->{st(page)['ownedTotal']}")
        chk("saturated gen did not touch bag", st(page)["bagLeft"] == bag_before, f"bag {bag_before}->{st(page)['bagLeft']}")
        chk("saturated gen stock spent to 0", info["stock"] == 0, f"stock={info['stock']}")
        chk("saturated gen action consumed", "heal" in s["used"])

        # 7) 素材5で5個生成しても袋は一切減らない（全て複製・所持数でキャップされない）
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
        page.evaluate("window.__test.setSmithMode('stock')")
        make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.2)
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(0)"); time.sleep(0.8)  # 素材+5
        chk("stock>=5 for bulk test", ci(page)["stock"] >= 5, f"stock={ci(page)['stock']}")
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        make_group(page, [18, 19, 20, 21, 22], 1); time.sleep(0.2)
        bag_before = st(page)["bagLeft"]
        owned_total_before = st(page)["ownedTotal"]
        page.evaluate("window.__test.setSmithMode('gen')")
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(18)"); time.sleep(0.6)
        s = st(page)
        row = [s["board"][i] for i in [18, 19, 20, 21, 22]]
        n_gen = sum(1 for c in row if c["sp"])
        chk("bulk gen: 5 placed", n_gen == 5, f"gen={n_gen}")
        chk("bulk gen: all extra", all(c["x"] for c in row if c["sp"]), str([(c["sp"], c["x"]) for c in row]))
        chk("bulk gen: bag untouched", s["bagLeft"] == bag_before, f"bag {bag_before}->{s['bagLeft']}")
        chk("bulk gen: owned untouched", s["ownedTotal"] == owned_total_before, f"owned {owned_total_before}->{s['ownedTotal']}")
    else:
        chk("stock resets per battle (skipped: status=" + s["status"] + ")", False)

    chk("no page errors", len(errors) == 0, str(errors[:2]))
    b.close()

print("RESULT:", "PASS" if not fails else "FAIL " + str(fails))
