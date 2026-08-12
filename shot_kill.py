# -*- coding: utf-8 -*-
"""敵撃破時の表示を確認する（0が残って敵が居るように見える件）。"""
import time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\81200b0d-3531-47c3-9733-39ea0dda777c\scratchpad"
CHAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3  # 3=ノア

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({CHAR})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    page.evaluate("window.__test.spawn(['slime','bat','crow'])"); time.sleep(0.3)
    page.evaluate("window.__test.weaken()"); time.sleep(0.2)  # HP1にして確実に倒す

    page.evaluate("window.__test.setAct('heal')"); page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    page.evaluate("window.__test.setAct('atk')"); page.evaluate("window.__test.commit(1)"); time.sleep(0.5)
    page.evaluate("window.__test.setAct('def')"); page.evaluate("window.__test.commit(2)"); time.sleep(0.3)

    for i in range(16):
        time.sleep(0.25)
        st = page.evaluate("window.__test.state()")
        print(f"t+{0.45*(i+1):.2f}s status={st['status']} enemies={[(e['kind'], e['hp'], e['alive']) for e in st['enemies']]}")
        page.screenshot(path=f"{SHOT}\\k3_{i:02d}.png")
    print("errors:", errors)
    b.close()
