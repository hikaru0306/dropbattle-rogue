# -*- coding: utf-8 -*-
"""敵シールドとモバイル幅の検証"""
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
    page.click("text=冒険に出る")
    time.sleep(0.5)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)

    # 1) シールドがダメージを吸収する
    page.evaluate("window.__test.spawn(['golem'])")
    time.sleep(0.3)
    page.evaluate("window.__test.setShd(0, 30)")
    page.evaluate("window.__test.addAtk(50)")
    resolve(page)
    s = st(page)
    assert s["enemies"][0]["hp"] == 210, f"shield absorb: {s['enemies']}"
    assert s["enemies"][0]["shd"] == 0, f"shield not consumed: {s['enemies']}"
    print("S1 shield absorb OK (50atk -> 30shd + 20hp, hp230->210)")

    # 2) シールドで完全ブロック（余りは残る）
    page.evaluate("window.__test.setShd(0, 30)")
    page.evaluate("window.__test.addAtk(20)")
    resolve(page)
    s = st(page)
    assert s["enemies"][0]["hp"] == 210, f"hp should be untouched: {s['enemies']}"
    assert s["enemies"][0]["shd"] == 10, f"shield remain: {s['enemies']}"
    print("S2 full block OK (shd 30 -> 10, hp unchanged)")

    # 3) 貫通もシールドを先に削る
    page.evaluate("window.__test.spawn(['golem','slime'])")
    time.sleep(0.3)
    page.evaluate("window.__test.setShd(0, 20)")
    page.evaluate("window.__test.addAtk(500)")
    page.evaluate("window.__test.setPierce(true)")
    resolve(page, 8.0)
    s = st(page)
    assert s["status"] == "reward", f"pierce+shield kill-all: {s['status']} {s['enemies']}"
    print("S3 pierce through shield OK")
    page.click("css=[class*=pop-in] button >> nth=0")
    time.sleep(0.6)
    b.close()

# モバイル幅チェック（横スクロールが出ないこと）
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    for w in (360, 390):
        p = b.new_page(viewport={"width":w, "height":740})
        p.goto(URL)
        p.wait_for_selector("text=冒険に出る", timeout=15000)
        sw = p.evaluate("document.documentElement.scrollWidth")
        assert sw <= w + 1, f"title overflow at {w}: {sw}"
        p.click("text=冒険に出る")
        time.sleep(0.8)
        sw = p.evaluate("document.documentElement.scrollWidth")
        assert sw <= w + 1, f"map overflow at {w}: {sw}"
        s = p.evaluate("window.__test.state()")
        p.evaluate(f"window.__test.enter({s['selectable'][0]})")
        time.sleep(0.8)
        p.evaluate("window.__test.spawn(['golem','spore','slime'])")
        time.sleep(0.5)
        sw = p.evaluate("document.documentElement.scrollWidth")
        assert sw <= w + 1, f"battle overflow at {w}: {sw}"
        if w == 390:
            p.screenshot(path="v16_mobile_battle.png")
        p.close()
        print(f"M1 no horizontal overflow at {w}px OK")
    b.close()

if errors:
    print("ERRORS:", errors[:5]); sys.exit(1)
print("ALL SHIELD/MOBILE TESTS OK")
