# -*- coding: utf-8 -*-
"""ショップ価格の確認: 1人目=半額セール / 2人目以降=通常価格＋たまにランダム割引"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\81200b0d-3531-47c3-9733-39ea0dda777c\scratchpad"

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate("window.__test.start(0)")
    time.sleep(0.5)

    def open_shop(label):
        page.evaluate("window.__test.openShop()")
        time.sleep(2.0)  # intro 1600ms 待ち
        txt = page.inner_text("body")
        sale = "半額" in txt
        prices = page.eval_on_selector_all(
            "button", "els => els.map(e => e.innerText).filter(t => /^\\s*\\d+/.test(t))")
        print(f"{label}: sale={sale} prices={prices}")
        page.screenshot(path=f"{SHOT}\\shop_{label}.png")
        return sale

    s1 = open_shop("first")
    assert s1, "1人目は半額セールのはず"
    # 閉じて次の商人へ
    page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>e.innerText.includes('先へ進む')); if(b) b.click(); }""")
    time.sleep(0.6)
    s2 = open_shop("second")
    assert not s2, "2人目はセールではないはず"

    print("errors:", errors)
    b.close()
print("ALL SHOPPRICE OK")
