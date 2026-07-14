# -*- coding: utf-8 -*-
"""レリック検証: コイン倍率/特殊+1/ポーチ/指輪/鍛冶半額/再生/磁石"""
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
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    time.sleep(0.5)

    # 1) 貯金箱+天秤: (25+0+10)*1.5 = 53
    page.evaluate("window.__test.giveRelic('piggy')")
    page.evaluate("window.__test.giveRelic('scale')")
    page.evaluate("window.__test.giveRelic('magnet')")
    time.sleep(0.3)
    s = st(page)
    assert set(s["relics"]) == {"piggy","scale","magnet"}, s["relics"]
    n0 = [n for n in s["map"] if n["id"] == s["selectable"][0]][0]
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.setPierce(true)")
    page.evaluate("window.__test.addAtk(500)")
    resolve(page, 8.0)
    s = st(page)
    assert s["status"] == "reward"
    expected = int((25 + n0["row"] * 4 + 10) * 1.5 + 0.5)  # JS Math.round
    assert s["coins"] == expected, f"coin calc: {s['coins']} != {expected}"
    print("R1 piggy+scale coins OK:", s["coins"])
    assert s["rewardPicks"] == 4, f"magnet picks: {s['rewardPicks']}"
    print("R2 magnet 4 picks OK")
    page.click("css=[class*=pop-in] button >> nth=0")
    for _ in range(20):  # reward→map遷移をポーリング（fx遅延でのフレーク対策）
        time.sleep(0.3)
        if st(page)["status"] == "map":
            break
    assert st(page)["status"] == "map", st(page)["status"]

    # 2) 星のかけら: 次の戦闘で特殊6個
    page.evaluate("window.__test.giveRelic('stardust')")
    time.sleep(0.2)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    s = st(page)
    assert s["status"] == "battle"
    assert s["specials"] == 6, f"stardust specials: {s['specials']}"
    print("R3 stardust specials=6 OK")

    # 3) 指輪: ターン開始 攻+10/防+10
    page.evaluate("window.__test.giveRelic('warring')")
    page.evaluate("window.__test.giveRelic('guardring')")
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.3)
    resolve(page)  # ターンを回して freshTurn を適用
    s = st(page)
    assert s["tv"]["atk"] == 10 and s["tv"]["def"] == 10, f"rings: {s['tv']}"
    print("R4 rings +10/+10 OK")

    # 4) 再生の護符: 被ダメ後に+2
    page.evaluate("window.__test.giveRelic('regen')")
    hp0 = s["php"]
    resolve(page)
    s = st(page)
    assert s["php"] == hp0 - (30 - 10) + 2, "regen check failed: " + str(hp0) + " -> " + str(s["php"])
    print("R5 regen +2 OK:", hp0, "->", s["php"])

    # 5) ポーチ: 4個持てる
    page.evaluate("window.__test.giveRelic('pouch')")
    for _ in range(4):
        page.evaluate("window.__test.giveItem('potion')")
    time.sleep(0.2)
    assert len(st(page)["items"]) == 4, st(page)["items"]
    print("R6 pouch cap4 OK")

    # 6) 鍛冶ハンマー: 25で鍛えられる
    page.evaluate("window.__test.restart()")
    time.sleep(0.6)
    page.evaluate("window.__test.giveRelic('hammer')")
    s = st(page)
    rest = [n for n in s["map"] if n["type"] == "rest"]
    if rest:
        eds = [e for e in s["edges"] if e["to"] == rest[0]["id"]]
        page.evaluate(f"window.__test.setCur({eds[0]['from']})")
        time.sleep(0.2)
        page.evaluate(f"window.__test.enter({rest[0]['id']})")
        time.sleep(0.5)
        page.evaluate("window.__test.addCoins(30)")
        page.evaluate("window.__test.forge('heal')")
        time.sleep(0.4)
        s = st(page)
        assert s["coins"] == 30 - 25, f"hammer cost: {s['coins']}"
        assert not s["shop"], "campfire forge should not open shop"
        print("R7 hammer 25G forge OK")
    else:
        print("R7 skipped (no rest node)")
    b.close()

if errors:
    print("ERRORS:", errors[:5]); sys.exit(1)
print("ALL RELIC TESTS OK")
