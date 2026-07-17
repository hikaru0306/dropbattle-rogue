# -*- coding: utf-8 -*-
"""鍛冶師（smith）検証: 補充で素材蓄積 / 生成で袋から特殊配置 / 強化で＋化 / 素材のバトル間持ち越し / 素材0はアクション消費なし / 出せる特殊が尽きたら魔鉱石を生成"""
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

    # 選択画面: 6タイル・鍛冶師選択
    tiles = page.query_selector_all("div.flex.justify-center.gap-2 > button")
    chk("6 tiles on select", len(tiles) == 6)
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

    # 2) 生成: 別グループ(6個)に素材5で特殊5個配置（袋から引く）
    page.evaluate("window.__test.resolve()"); time.sleep(1.2)
    make_group(page, [6, 7, 8, 9, 10, 11], 0); time.sleep(0.2)
    bag_before = st(page)["bagLeft"]
    sp_before = st(page)["specials"]
    page.evaluate("window.__test.setSmithMode('gen')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.6)
    s = st(page); info = ci(page)
    gen_n = s["specials"] - sp_before
    chk("gen placed 5 specials", gen_n == 5, f"gen={gen_n}")
    chk("stock spent to 0", info["stock"] == 0, f"stock={info['stock']}")
    # 生成しても所持数を超えない（袋+盤面 <= 所持合計 = 複製なし）
    chk("no duplication (bag+board<=owned)", s["bagLeft"] + s["specials"] <= s["ownedTotal"], f"bag{s['bagLeft']}+sp{s['specials']} vs owned{s['ownedTotal']}")
    row_sp = [s["board"][i]["sp"] for i in [6, 7, 8, 9, 10, 11]]
    chk("specials on tapped group", sum(1 for x in row_sp if x) == 5, str(row_sp))
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

        # 6) 生成の枯渇フォールバック: 所持特殊が全て盤面に出ている（リロードしても出せない）
        #    → 剣20%/盾20%/魔鉱石60%で追加生成（extra=所持外・袋会計に影響しない）
        page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)  # 高HPで撃破を避ける
        page.evaluate("window.__test.setSmithMode('stock')")
        make_group(page, [0, 1, 2], 1); time.sleep(0.2)
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(0)"); time.sleep(0.8)  # 素材3を確保
        chk("stock 3 for fallback test", ci(page)["stock"] == 3, f"stock={ci(page)['stock']}")
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        # make_groupで盤面の特殊を全消去してから、所持特殊を全数(9個)盤面に配置
        make_group(page, [6, 7, 8], 1); time.sleep(0.2)
        owned = st(page)["owned"]
        owned_total_before = st(page)["ownedTotal"]
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
        chk("gen fallback made 3 specials in {atk,def,ore}", len([x for x in row_sp if x]) == 3 and all(x in ("atk", "def", "ore") for x in row_sp), str(row_sp))
        chk("fallback drops flagged extra", all(row_x), str(row_x))
        chk("fallback did not add to owned", st(page)["ownedTotal"] == owned_total_before, f"{owned_total_before}->{st(page)['ownedTotal']}")
        chk("fallback stock spent to 0", info["stock"] == 0, f"stock={info['stock']}")
        chk("fallback action consumed", "heal" in s["used"])

        # 7) 部分フォールバック: 所持のうち盤面外が2つ + 素材5 → 袋2 + 追加3 の計5生成（袋数でキャップされない）
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
        page.evaluate("window.__test.setSmithMode('stock')")
        make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.2)
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(0)"); time.sleep(0.8)  # 素材+5
        chk("stock>=5 for partial test", ci(page)["stock"] >= 5, f"stock={ci(page)['stock']}")
        page.evaluate("window.__test.resolve()"); time.sleep(1.2)
        # 5個の生成対象グループ + 所持特殊を7個だけ盤面に配置(availLeft = 9-7 = 2)
        make_group(page, [18, 19, 20, 21, 22], 1); time.sleep(0.2)
        owned = st(page)["owned"]
        flat = []
        for k, v in owned.items(): flat += [k] * v
        for c, k in zip([24, 25, 26, 27, 28, 29, 30], flat[:7]):
            page.evaluate(f"window.__test.setCellSpecial({c}, '{k}', false, false)")
        time.sleep(0.1)
        page.evaluate("window.__test.setSmithMode('gen')")
        page.evaluate("window.__test.setAct('heal')")
        page.evaluate("window.__test.commit(18)"); time.sleep(0.6)
        s = st(page)
        row = [s["board"][i] for i in [18, 19, 20, 21, 22]]
        n_extra = sum(1 for c in row if c["x"])
        n_bag = sum(1 for c in row if c["sp"] and not c["x"])
        chk("partial gen: 5 total (袋数でキャップされない)", n_extra + n_bag == 5, f"bag={n_bag} extra={n_extra}")
        chk("partial gen: 袋2 + 追加3", n_bag == 2 and n_extra == 3, f"bag={n_bag} extra={n_extra}")
    else:
        chk("stock resets per battle (skipped: status=" + s["status"] + ")", False)

    chk("no page errors", len(errors) == 0, str(errors[:2]))
    b.close()

print("RESULT:", "PASS" if not fails else "FAIL " + str(fails))
