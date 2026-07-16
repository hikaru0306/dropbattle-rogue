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

    # ―― 1) 初期所持: 各キャラ 剣盾回復2ずつ+専用3 ――
    expect = {0:"holy", 1:"ink", 2:"warcry", 3:"store", 4:"wildstar", 5:"ore"}
    for i, k in expect.items():
        page.evaluate(f"window.__test.setChar({i})")
        page.evaluate("window.__test.restart()"); time.sleep(0.3)
        o = st(page)["owned"]
        chk(f"char{i} owns {k}x3 + 2/2/2", o[k] == 3 and o["atk"] == 2 and o["def"] == 2 and o["heal"] == 2, str(o))

    # ―― 2) 聖光(holy): 回復の50%が攻撃に。強化込みで100%上限 ――
    start_char(page, 0)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    heal0 = st(page)["tv"]["heal"]
    make_group(page, [6,7,8], 0)
    page.evaluate("window.__test.setCellSpecial(6, 'holy', false, false)")
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    s = st(page)
    atk0 = s["tv"]["atk"]
    chk("holy flag on tv", s["tv"].get("holy") == 1, str(s["tv"]))
    hp_before = s["enemies"][0]["hp"]
    page.evaluate("window.__test.commit(30)") if False else None
    # 3アクション目（防御）を消化して解決
    make_group(page, [30,31,32], 2)
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(30)"); time.sleep(1.6)
    s = st(page)
    dealt = hp_before - s["enemies"][0]["hp"]
    want = atk0 + int(heal0 * 0.5 + 0.5)  # JSのMath.roundは.5切り上げ
    chk("holy: dealt = atk + 50% of heal", dealt == want, f"dealt={dealt} want={want} (atk{atk0}+heal{heal0}/2)")

    # ―― 3) 彩雫(ink): ランダム3個を消した色に染める ――
    start_char(page, 1)
    make_group(page, [0,1,2], 1)
    page.evaluate("window.__test.setCellSpecial(0, 'ink', false, false)")
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    s = st(page)
    chk("ink painted 3 cells", s["tv"].get("inkPainted") == 3, str(s["tv"].get("inkPainted")))

    # ―― 4) 虹のパレット: 6個以上の色変えで虹1個 ――
    page.evaluate("window.__test.giveRelic('palette')")
    page.evaluate("window.__test.resolve()"); time.sleep(1.4)
    make_group(page, [12,13,14,15,16,17], 1)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(12)"); time.sleep(0.5)
    s = st(page)
    chk("palette made 1 wild in painted group", len(wilds(s)) == 1 and wilds(s)[0] in [12,13,14,15,16,17], str(wilds(s)))

    # ―― 5) 闘魂(warcry): 現在の攻/防が1.2倍 ――
    start_char(page, 2)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_a = st(page)["tv"]["atk"]
    make_group(page, [6,7,8], 0)
    page.evaluate("window.__test.setCellSpecial(6, 'warcry', false, false)")
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(6)"); time.sleep(0.5)
    s = st(page)
    chk("warcry atk x1.2", s["tv"]["atk"] == round(atk_a * 1.2), f"{atk_a} -> {s['tv']['atk']}")

    # ―― 6) 強化＆軍神の号令（3アクション消化での自動解決を避けて2アクションで検証） ――
    page.evaluate("window.__test.resolve()"); time.sleep(1.4)
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_b = st(page)["tv"]["atk"]
    make_group(page, [30,31,32,33], 1)  # 強化4個・対象=atk
    page.evaluate("window.__test.setSkillTarget('atk')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(30)"); time.sleep(0.5)
    s = st(page)
    chk("buff atk x1.4 (0.1x4)", s["tv"]["atk"] == int(atk_b * 1.4 + 0.5), f"{atk_b} -> {s['tv']['atk']}")
    # 号令: 対象=defで強化 → 反対側(atk)に半分（次のターンで検証）
    page.evaluate("window.__test.giveRelic('warhorn')")
    make_group(page, [12,13,14], 0)
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(12)"); time.sleep(1.6)  # 3アクション目→解決
    make_group(page, [0,1,2,3,4], 1)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    atk_c = st(page)["tv"]["atk"]
    make_group(page, [30,31,32,33], 1)  # 強化4個・対象=def
    page.evaluate("window.__test.setSkillTarget('def')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(30)"); time.sleep(0.5)
    s = st(page)
    chk("warhorn: atk x1.2 (half of def buff)", s["tv"]["atk"] == int(atk_c * 1.2 + 0.5), f"{atk_c} -> {s['tv']['atk']}")

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
