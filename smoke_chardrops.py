# -*- coding: utf-8 -*-
"""キャラ専用ドロップ＆レリック検証:
holy(聖光)/ink(彩雫)/warcry(闘魂)/wildstar(星のしずく)/ore(魔鉱石)
prayerbook(祈祷書)/palette(パレット)/warhorn(号令)/starstaff(錫杖)/anvil(金床)
＋初期所持（剣盾回復2ずつ+専用3）"""
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

def make_group(p, idxs, t):
    for i in range(36):
        r, c = divmod(i, 6)
        base = 2 if (r + c) % 2 == 0 else 3
        p.evaluate(f"window.__test.setCellType({i}, {base})")
    for i in idxs:
        p.evaluate(f"window.__test.setCellType({i}, {t})")

def start_char(p, i):
    p.evaluate(f"window.__test.setChar({i})")
    p.evaluate("window.__test.restart()"); time.sleep(0.5)
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    p.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)  # 高HPで撃破を避ける

def wilds(s): return [i for i, c in enumerate(s["board"]) if c["w"]]

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.5)
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)

    # ―― 1) 初期所持: 専用持ちは 剣盾回復2ずつ+専用3・アルド(専用なし=聖光廃止)は3/3/3 ――
    expect = {2:"warcry", 3:"store", 4:"wildstar", 5:"ore"}
    for i, k in expect.items():
        page.evaluate(f"window.__test.setChar({i})")
        page.evaluate("window.__test.restart()"); time.sleep(0.3)
        o = st(page)["owned"]
        chk(f"char{i} owns {k}x3 + 2/2/2", o[k] == 3 and o["atk"] == 2 and o["def"] == 2 and o["heal"] == 2, str(o))

    # ―― 2) アルド: 聖光は廃止済み（3/3/3スタート・holyキー自体が存在しない） ――
    page.evaluate("window.__test.setChar(0)")
    page.evaluate("window.__test.restart()"); time.sleep(0.3)
    o = st(page)["owned"]
    chk("char0 owns 3/3/3 (holy removed)", o["atk"] == 3 and o["def"] == 3 and o["heal"] == 3, str(o))
    chk("holy key gone", "holy" not in o, str(list(o.keys())))

    # ―― 3) イリス: 彩雫は廃止済み（3/3/3スタート・inkキー自体が存在しない） ――
    start_char(page, 1)
    o = st(page)["owned"]
    chk("char1 owns 3/3/3 (ink removed)", o["atk"] == 3 and o["def"] == 3 and o["heal"] == 3, str(o))
    chk("ink key gone", "ink" not in o, str(list(o.keys())))

    # ―― 4) 虹のパレット: 6個以上の色変えで虹1個 ――
    page.evaluate("window.__test.giveRelic('palette')")
    make_group(page, [12,13,14,15,16,17], 1)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(12)"); time.sleep(0.5)
    s = st(page)
    chk("palette made 1 wild in painted group", len(wilds(s)) == 1 and wilds(s)[0] in [12,13,14,15,16,17], str(wilds(s)))

    # ―― 5) 闘魂(warcry): 強化で消すと1個につき倍率+0.2（攻撃/防御アクションでは無効果） ――
    start_char(page, 2)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_a = st(page)["tv"]["atk"]
    # 防御アクションで闘魂入りグループを消しても攻撃は変化しない（旧仕様の×1.2は廃止）
    make_group(page, [6,7,8], 0)
    page.evaluate("window.__test.setCellSpecial(6, 'warcry', false, false)")
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    s = st(page)
    chk("warcry no effect outside buff", s["tv"]["atk"] == atk_a, f"{atk_a} -> {s['tv']['atk']}")
    # 強化アクションで闘魂1個入り3個グループ → ×(1 + 0.1*3 + 0.2) = ×1.5
    page.evaluate("window.__test.resolve()"); time.sleep(1.6)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_c = st(page)["tv"]["atk"]
    make_group(page, [6,7,8], 0)
    page.evaluate("window.__test.setCellSpecial(6, 'warcry', false, false)")
    page.evaluate("window.__test.setSkillTarget('atk')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    s = st(page)
    pend5 = s["tv"].get("buffPend") or {}
    chk("warcry +0.2 in buff (pend x1.5)", abs(pend5.get("mult", 0) - 1.5) < 1e-9, str(pend5))
    page.evaluate("window.__test.resolve()"); time.sleep(2.0)  # 予約を消化して次のテストへ

    # ―― 6) 強化は「予約→攻撃直前に計算」: 後がけ・先がけの両方で倍率が乗る ――
    page.evaluate("window.__test.resolve()"); time.sleep(1.4)
    # (a) 攻撃→強化 の順: コミット時点ではtv不変・buffPendに予約される
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_b = st(page)["tv"]["atk"]
    make_group(page, [30,31,32,33], 1)  # 強化4個・対象=atk → ×1.4
    page.evaluate("window.__test.setSkillTarget('atk')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(30)"); time.sleep(0.5)
    s = st(page)
    pend = s["tv"].get("buffPend") or {}
    chk("buff pends (tv unchanged)", s["tv"]["atk"] == atk_b and abs(pend.get("mult", 0) - 1.4) < 1e-9, str(pend))
    hp0 = s["enemies"][0]["hp"]
    page.evaluate("window.__test.resolve()"); time.sleep(2.2)
    s = st(page)
    dealt = hp0 - s["enemies"][0]["hp"]
    chk("buff applied at resolve (x1.4)", dealt == int(atk_b * 1.4 + 0.5), f"dealt={dealt} want={int(atk_b*1.4+0.5)}")
    # (b) 強化→攻撃 の順でも同じく乗る（HP切れ撃破で計測が狂わないようゴーレムを湧き直す）
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
    make_group(page, [30,31,32,33], 1)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(30)"); time.sleep(0.5)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    s = st(page)
    atk_d = s["tv"]["atk"]
    hp1 = s["enemies"][0]["hp"]
    page.evaluate("window.__test.resolve()"); time.sleep(2.2)
    s = st(page)
    dealt2 = hp1 - s["enemies"][0]["hp"]
    chk("buff-first also applies (x1.4)", dealt2 == int(atk_d * 1.4 + 0.5), f"dealt={dealt2} want={int(atk_d*1.4+0.5)}")
    # (c) 号令: pend.hornに半分の倍率が入る
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
    page.evaluate("window.__test.giveRelic('warhorn')")
    make_group(page, [30,31,32,33], 1)
    page.evaluate("window.__test.setSkillTarget('def')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(30)"); time.sleep(0.5)
    pend = st(page)["tv"].get("buffPend") or {}
    chk("warhorn half in pend (1.2)", abs(pend.get("horn", 0) - 1.2) < 1e-9, str(pend))
    page.evaluate("window.__test.resolve()"); time.sleep(2.2)

    # ―― 7) 星のしずく(wildstar): ランダム1個が虹に ――
    start_char(page, 4)
    make_group(page, [0,1,2], 1)
    page.evaluate("window.__test.setCellSpecial(0, 'wildstar', false, false)")
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    s = st(page)
    chk("wildstar made 1 wild", len(wilds(s)) == 1, str(wilds(s)))

    # ―― 8) 星辰の錫杖: ターン開始時に虹がなければ1個生成 ――
    page.evaluate("window.__test.giveRelic('starstaff')")
    page.evaluate("window.__test.resolve()"); time.sleep(1.4)
    s = st(page)
    chk("starstaff keeps a wild on board", len(wilds(s)) >= 1, str(wilds(s)))

    # ―― 9) 魔鉱石(ore): 消すと素材+2（どのアクションでも） ――
    start_char(page, 5)
    make_group(page, [0,1,2], 1)
    page.evaluate("window.__test.setCellSpecial(0, 'ore', false, false)")
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    chk("ore +2 stock on atk clear", ci(page)["stock"] == 2, f"stock={ci(page)['stock']}")

    # ―― 10) 名工の金床: 補充2倍 ――
    page.evaluate("window.__test.giveRelic('anvil')")
    page.evaluate("window.__test.resolve()"); time.sleep(1.4)
    make_group(page, [6,7,8,9,10], 0)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    chk("anvil doubles stock gain (+10)", ci(page)["stock"] == 12, f"stock={ci(page)['stock']}")

    # ―― 11) 聖者の祈祷書: あふれた回復が次ターンの防御に（最大30） ――
    start_char(page, 0)
    page.evaluate("window.__test.giveRelic('prayerbook')")
    make_group(page, [0,1,2,3,4], 1)   # 防御5個=50で敵攻撃を受け切る
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    make_group(page, [6,7,8,9,10], 0)  # 回復5個（HP満タンなので全部あふれる）
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    heal_ov = st(page)["tv"]["heal"]
    php0, pmax0 = st(page)["php"], None
    make_group(page, [30,31,32], 2)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(30)"); time.sleep(1.6)
    s = st(page)
    want = min(30, heal_ov)
    chk("prayerbook overheal -> next def", s["tv"]["def"] == want, f"def={s['tv']['def']} want={want} (php was {php0})")

    chk("no page errors", len(errors) == 0, str(errors[:2]))
    b.close()

print("RESULT:", "PASS" if not fails else "FAIL " + str(fails))
