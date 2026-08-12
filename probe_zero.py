# -*- coding: utf-8 -*-
"""画面上に出る「0」だけの表示を、位置つきで洗い出す（敵の頭上に0が残る件の特定用）。"""
import time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
CHAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3

# 敵エリア（画面上部 y<300）に出ている短いテキストを全部拾う
JS_ZEROS = """() => [...document.querySelectorAll('*')]
  .filter(e => e.children.length === 0 && e.innerText && e.innerText.trim().length <= 8)
  .map(e => { const r = e.getBoundingClientRect(); return { t: e.innerText.trim(), x: Math.round(r.left), y: Math.round(r.top), c: String(e.className).slice(0,16) }; })
  .filter(o => o.y < 300)
  .map(o => `${o.t}@x${o.x},y${o.y}${o.c ? '.' + o.c : ''}`)"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({CHAR})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)

    prev = None
    for i in range(6):
        time.sleep(0.2)
        z = page.evaluate(JS_ZEROS)
        st = page.evaluate("window.__test.state()")
        alive = [e["kind"] for e in st["enemies"] if e["alive"]]
        line = f"alive={alive} zeros={z}"
        if line != prev:
            print(f"t+{0.2*(i+1):.1f}s {line}")
            prev = line
    b.close()
