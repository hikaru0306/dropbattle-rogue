# -*- coding: utf-8 -*-
"""新アイテム検証: 時止め/爆裂瓶/弱体の毒/星降りの粉/不死鳥の羽/焚き火の特殊ドロップ削除"""
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
    page.click("text=冒険に出る")
    time.sleep(0.6)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)

    # 1) 時止めの砂: 敵は行動せず、パターンも進まない
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.3)
    page.evaluate("window.__test.giveItem('stun')")
    idx = st(page)["items"].index("stun")
    page.evaluate(f"window.__test.useItem({idx})")
    time.sleep(0.3)
    assert st(page)["tv"]["stun"] is True
    resolve(page)
    s = st(page)
    assert s["php"] == 300, f"stun failed php={s['php']}"
    assert s["enemies"][0]["pi"] == 0, f"stun should freeze pattern pi={s['enemies'][0]['pi']}"
    print("N1 stun OK (no damage, pattern frozen)")

    # 2) 弱体の毒: 攻撃力25%減
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.3)
    a0 = st(page)["enemyAtks"][0]
    page.evaluate("window.__test.giveItem('venom')")
    idx = st(page)["items"].index("venom")
    page.evaluate(f"window.__test.useItem({idx})")
    time.sleep(0.3)
    a1 = st(page)["enemyAtks"][0]
    assert a1 == max(1, int(a0 * 0.75 + 0.5)), f"venom: {a0} -> {a1}"
    print("N2 venom OK atk:", a0, "->", a1)

    # 3) 星降りの粉: 特殊ドロップ+3
    s0 = st(page)["specials"]
    page.evaluate("window.__test.giveItem('gemrain')")
    idx = st(page)["items"].index("gemrain")
    page.evaluate(f"window.__test.useItem({idx})")
    time.sleep(0.4)
    s1 = st(page)["specials"]
    assert s1 == s0 + 3, f"gemrain: {s0} -> {s1}"
    print("N3 gemrain OK specials:", s0, "->", s1)

    # 4) 爆裂瓶: 全体80ダメージ→とどめで勝利
    page.evaluate("window.__test.spawn(['slime','slime'])")
    time.sleep(0.3)
    page.evaluate("window.__test.giveItem('bomb')")
    idx = st(page)["items"].index("bomb")
    page.evaluate(f"window.__test.useItem({idx})")
    time.sleep(0.5)
    s = st(page)
    assert all(e["hp"] == 50 for e in s["enemies"]), f"bomb dmg: {s['enemies']}"
    print("N4 bomb 80dmg OK")
    page.evaluate("window.__test.giveItem('bomb')")
    idx = st(page)["items"].index("bomb")
    page.evaluate(f"window.__test.useItem({idx})")
    time.sleep(4.2)
    s = st(page)
    assert s["status"] == "reward", f"bomb kill-all should win: {s['status']}"
    print("N5 bomb finisher -> reward OK")
    page.click("css=[class*=pop-in] button >> nth=0")
    time.sleep(0.6)

    # 5) 不死鳥の羽: 死亡時に自動復活
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    page.evaluate("window.__test.spawn(['demon'])")
    time.sleep(0.3)
    page.evaluate("window.__test.giveItem('phoenix')")
    revived = False
    for i in range(8):
        resolve(page, 3.6)
        s = st(page)
        if s["status"] == "lose":
            break
        if "phoenix" not in s["items"] and s["php"] == 120:
            revived = True
            break
    assert revived, f"phoenix revive failed: {s['status']} php={s['php']} items={s['items']}"
    print("N6 phoenix revive OK (php=120)")

    # 6) 焚き火: 特殊ドロップ削除
    page.evaluate("window.__test.restart()")
    time.sleep(0.6)
    s = st(page)
    rest = [n for n in s["map"] if n["type"] == "rest"]
    if not rest:
        page.evaluate("window.__test.restart()"); time.sleep(0.6)
        s = st(page)
        rest = [n for n in s["map"] if n["type"] == "rest"]
    assert rest, "no rest node"
    eds = [e for e in s["edges"] if e["to"] == rest[0]["id"]]
    page.evaluate(f"window.__test.setCur({eds[0]['from']})")
    time.sleep(0.3)
    page.evaluate(f"window.__test.enter({rest[0]['id']})")
    time.sleep(0.6)
    assert st(page)["campfire"] == "menu"
    t0 = st(page)["ownedTotal"]
    page.evaluate("window.__test.restRemove('heal')")
    time.sleep(0.4)
    s = st(page)
    assert s["ownedTotal"] == t0 - 1, f"remove failed {t0} -> {s['ownedTotal']}"
    assert not s["shop"], "campfire remove should not open shop"
    print("N7 campfire remove OK owned:", t0, "->", s["ownedTotal"])
    assert st(page)["status"] == "map"
    print("N8 back to map OK")
    b.close()

if errors:
    print("ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL NEW-ITEM TESTS OK")
