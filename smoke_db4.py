# -*- coding: utf-8 -*-
"""コイン・消費アイテム・ショップ・終了ボタン廃止の検証"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(p): return p.evaluate("window.__test.state()")
def resolve(p, w=3.4):
    p.evaluate("window.__test.resolve()"); time.sleep(w)

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width":420,"height":900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    time.sleep(0.6)
    s = st(page)
    assert s["items"] == [], f"initial items: {s['items']}"
    page.evaluate("window.__test.giveItem('potion')"); page.evaluate("window.__test.giveItem('potion')")
    import time as _t; _t.sleep(0.2)
    s = st(page)
    assert s["coins"] == 0
    print("C1 initial state OK (potion x1, 0 coins)")

    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    assert "終了▶" not in page.content(), "end-turn button still present"
    print("C2 end-turn button removed OK")

    # 敵の攻撃を受けてからポーション（お邪魔開始型の敵対策で最大3ターン回す）
    for _ in range(3):
        resolve(page)
        hp0 = st(page)["php"]
        if hp0 < 300: break
    assert hp0 < 300
    page.evaluate("window.__test.useItem(0)")
    time.sleep(0.5)
    s = st(page)
    assert s["php"] == min(300, hp0 + 80), f"potion heal: {hp0} -> {s['php']}"
    assert s["items"] == ["potion"], "potion not consumed"
    print("C3 potion OK:", hp0, "->", s["php"])

    # 剛力の薬: 攻撃2倍
    page.evaluate("window.__test.giveItem('might')")
    midx = st(page)["items"].index("might")
    page.evaluate(f"window.__test.useItem({midx})")
    time.sleep(0.3)
    assert st(page)["tv"]["atkBoost"] is True
    page.evaluate("window.__test.commit(0)")
    time.sleep(0.8)
    s = st(page)
    assert s["tv"]["atk"] >= 20, f"might not doubled: {s['tv']}"  # 基礎10×2倍=20以上（特殊ドロップ分の上乗せあり得る）
    print("C4 might x2 OK atk:", s["tv"]["atk"])

    # 浄化の書: お邪魔一掃
    page.evaluate("window.__test.spawn(['shade'])")
    time.sleep(0.3)
    resolve(page)
    s = st(page)
    assert s["junk"] >= 3
    page.evaluate("window.__test.giveItem('purify')")
    pidx = st(page)["items"].index("purify")
    page.evaluate(f"window.__test.useItem({pidx})")
    time.sleep(0.4)
    assert st(page)["junk"] == 0, "purify failed"
    print("C5 purify OK")

    # 勝利でコイン入手 → バトル報酬はショップなし
    c0 = st(page)["coins"]
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.addAtk(500)")
    resolve(page, 8.0)
    s = st(page)
    assert s["status"] == "reward"
    assert s["coins"] > c0, f"coins not gained {c0}->{s['coins']}"
    print("C6 victory coins OK:", c0, "->", s["coins"])
    page.click("css=[class*=pop-in] button >> nth=0")
    time.sleep(0.6)
    s = st(page)
    assert s["status"] == "map" and not s["shop"], "battle should not open shop"
    print("C7 battle reward -> map (no shop) OK")

    # 休憩所ショップで購入
    nodes = {n["id"]: n for n in s["map"]}
    rest = [n for n in s["map"] if n["type"] == "rest"]
    assert rest, "no rest node this map"
    eds = [e for e in s["edges"] if e["to"] == rest[0]["id"]]
    page.evaluate(f"window.__test.setCur({eds[0]['from']})")
    time.sleep(0.3)
    page.evaluate(f"window.__test.enter({rest[0]['id']})")
    time.sleep(0.8)
    s = st(page)
    assert s["campfire"] == "menu", "campfire not open"
    page.evaluate("window.__test.restHeal()")
    time.sleep(0.5)
    assert not st(page)["shop"], "campfire should not open shop"
    page.evaluate("window.__test.openShop()")
    time.sleep(0.4)
    s = st(page)
    assert s["shop"], "hook shop not open"
    page.evaluate("window.__test.addCoins(300)")
    k = s["shop"][0]
    c0 = st(page)["coins"]
    i0 = len(st(page)["items"])
    page.evaluate(f"window.__test.buy('{k}')")
    time.sleep(0.3)
    s = st(page)
    assert len(s["items"]) == i0 + 1 and s["coins"] < c0, f"buy failed {s['items']} {s['coins']}"
    print("C8 shop buy OK:", k, "coins", c0, "->", s["coins"])

    # 3個上限
    page.evaluate("window.__test.giveItem('potion')"); page.evaluate("window.__test.giveItem('potion')")
    time.sleep(0.2)
    n3 = len(st(page)["items"])
    page.evaluate(f"window.__test.buy('{k}')")
    time.sleep(0.3)
    assert len(st(page)["items"]) == min(3, n3), "cap 3 violated"
    print("C9 item cap 3 OK")
    page.evaluate("window.__test.closeShop()")
    time.sleep(0.4)
    assert st(page)["status"] == "map"
    print("C10 shop close -> map OK")
    b.close()

if errors:
    print("ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL SHOP/ITEM TESTS OK")
