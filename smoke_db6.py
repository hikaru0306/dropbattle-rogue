# -*- coding: utf-8 -*-
"""ドロップ強化（鍛える）の検証: 50Gコスト・個体単位"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(p): return p.evaluate("window.__test.state()")

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width":420,"height":900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る")
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

    # コイン不足では強化できない
    page.evaluate("window.__test.forge('heal')")
    time.sleep(0.3)
    assert page.evaluate("window.__test.ups()")["heal"] == 0, "forge should fail without coins"
    print("F1 no-coin forge blocked OK")

    # 50G払って1個だけ強化
    page.evaluate("window.__test.addCoins(120)")
    c0 = st(page)["coins"]
    page.evaluate("window.__test.forge('heal')")
    time.sleep(0.4)
    s = st(page)
    ups = page.evaluate("window.__test.ups()")
    assert ups["heal"] == 1, f"forge count: {ups}"
    assert s["coins"] == c0 - 50, f"cost: {c0} -> {s['coins']}"
    assert not s["shop"], "campfire forge should not open shop"
    print("F2 forge 1 copy for 50G OK (heal x1, coins", c0, "->", s["coins"], ")")

    # 2個目も強化できる（heal所持3個）
    page.evaluate(f"window.__test.setCur({eds[0]['from']})")
    time.sleep(0.2)
    page.evaluate(f"window.__test.enter({rest[0]['id']})")
    time.sleep(0.5)
    page.evaluate("window.__test.forge('heal')")
    time.sleep(0.4)
    assert page.evaluate("window.__test.ups()")["heal"] == 2, "2nd copy forge failed"
    print("F3 second copy forge OK (heal x2)")
    page.evaluate("window.__test.closeShop()")
    time.sleep(0.3)
    b.close()

if errors:
    print("ERRORS:", errors[:5]); sys.exit(1)
print("ALL FORGE TESTS OK")
