# -*- coding: utf-8 -*-
"""チュートリアル・BGMトグルの検証"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    p = b.new_page(viewport={"width":420,"height":900})
    p.on("pageerror", lambda e: errors.append(str(e)))
    p.goto(URL)
    p.wait_for_selector("text=冒険に出る", timeout=15000)
    p.click("text=冒険に出る")
    time.sleep(0.5)
    s = p.evaluate("window.__test.state()")
    p.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    p.evaluate("window.__test.tutStart()")
    time.sleep(0.4)
    assert p.evaluate("window.__test.tutVal()") == 0
    p.evaluate("window.__test.tutStep()"); time.sleep(0.3)
    assert p.evaluate("window.__test.tutVal()") == 1
    p.evaluate("window.__test.tutStep()"); time.sleep(0.3)
    assert p.evaluate("window.__test.tutVal()") == 2
    p.evaluate("window.__test.tutStep()"); time.sleep(0.3)
    assert p.evaluate("window.__test.tutVal()") is None
    assert p.evaluate("localStorage.getItem('db_tut')") == "1"
    print("T1 tutorial 3steps + persist OK")
    p.click("text=🎵"); time.sleep(0.3); p.click("text=🎵"); time.sleep(0.4)
    print("T2 bgm toggle OK")
    b.close()

if errors:
    print("ERRORS:", errors[:5]); sys.exit(1)
print("ALL TUTORIAL/BGM TESTS OK")
