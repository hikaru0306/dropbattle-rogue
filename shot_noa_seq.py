# -*- coding: utf-8 -*-
"""ノアのターン解決中、攻撃/防御ボタンの表示がどう推移するかを実測する。"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\81200b0d-3531-47c3-9733-39ea0dda777c\scratchpad"
NOA = 3

def vals(p):
    return p.eval_on_selector_all("[id^='actval-']", "els => els.map(e => e.id + '=' + e.innerText.replace(/\\n/g,'|'))")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({NOA})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)

    page.evaluate("window.__test.setAct('heal')"); page.evaluate("window.__test.commit(0)"); time.sleep(0.6)
    print("蓄積後       :", vals(page))
    page.evaluate("window.__test.setAct('atk')"); page.evaluate("window.__test.commit(1)"); time.sleep(0.6)
    print("攻撃後       :", vals(page))
    page.evaluate("window.__test.setAct('def')"); page.evaluate("window.__test.commit(2)"); time.sleep(0.4)
    print("防御後(自動解決):", vals(page))

    for i in range(14):
        time.sleep(0.4)
        tv = page.evaluate("window.__test.state().tv")
        print(f"t+{0.4*(i+1):.1f}s vals={vals(page)} atk={tv['atk']} def={tv['def']}")
        if i in (1, 3, 6, 10):
            page.screenshot(path=f"{SHOT}\\noa_t{i}.png")
    b.close()
