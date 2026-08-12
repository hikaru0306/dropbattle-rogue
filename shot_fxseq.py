# -*- coding: utf-8 -*-
"""ターン解決中に出る演出テキスト／ダメージポップを高頻度で記録し、
攻撃が2回出ていないか（ダダンと鳴る件）を調べる。"""
import time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
CHAR = int(sys.argv[1]) if len(sys.argv) > 1 else 3

JS_SNAP = """() => ({
  fx: [...document.querySelectorAll('.fx-line, .dmg-pop')].map(e => e.className + ':' + e.innerText.replace(/\\n/g,'|')),
  body: [...document.querySelectorAll('div')].filter(e => e.children.length === 0 && e.innerText && /攻撃|ダメージ|強化|蓄積/.test(e.innerText)).map(e => e.innerText.replace(/\\n/g,'|')).slice(0,4)
})"""

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
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)

    page.evaluate("window.__test.setAct('heal')"); page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    page.evaluate("window.__test.setAct('atk')"); page.evaluate("window.__test.commit(1)"); time.sleep(0.5)
    hp0 = page.evaluate("window.__test.state().enemies[0].hp")
    print("解決前の敵HP:", hp0)
    page.evaluate("window.__test.setAct('def')"); page.evaluate("window.__test.commit(2)")

    seen = []
    for i in range(40):
        time.sleep(0.12)
        snap = page.evaluate(JS_SNAP)
        key = str(snap)
        if key != (seen[-1][1] if seen else None):
            seen.append((round(0.12*(i+1), 2), key))
    for t, k in seen:
        print(f"t+{t:.2f}s {k}")
    print("解決後の敵HP:", page.evaluate("window.__test.state().enemies[0].hp"))
    print("ログ:", page.evaluate("window.__test.state()").get("log"))
    b.close()
