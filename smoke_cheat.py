# -*- coding: utf-8 -*-
"""隠しコード1010の検証:
1. タイトルでキーボード1010 → 全解放（u/cが全キャラ）＋バナー表示
2. ロゴ5連打 → コード入力モーダル → 1010入力で全解放 / 誤コードは無反応
3. 解放後: 選択画面で全キャラ選択可＋どのキャラでも裏トグルが出る
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)

    # --- 1. キーボード入力 ---
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.keyboard.type("1010")
    time.sleep(0.5)
    body = page.evaluate("document.body.innerText")
    assert "すべて解放された" in body, "unlock banner missing (keyboard)"
    cs = page.evaluate("window.__test.charState()")
    assert sorted(cs["u"]) == [0,1,2,3,4,5] and sorted(cs["c"]) == [0,1,2,3,4,5], f"charState: {cs}"
    print("1 keyboard 1010 unlock OK", cs)
    # 選択画面: 全キャラに裏トグル
    page.click("text=冒険に出る"); time.sleep(0.4)
    for i in range(6):
        page.click(f"css=div.flex.justify-center.gap-2 > button >> nth={i}"); time.sleep(0.25)
        body = page.evaluate("document.body.innerText")
        assert "裏の冒険" in body and "🔒 未解放" not in body, f"char {i} not fully unlocked"
    print("2 all chars selectable with ura toggle OK")
    page.close()

    # --- 2. ロゴ連打 → モーダル入力（別ページ=素の状態から） ---
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    for _ in range(5):
        page.click("css=h1.title-logo", force=True); time.sleep(0.1)
    time.sleep(0.4)
    assert "ひみつのコード" in page.evaluate("document.body.innerText"), "code modal not opened"
    # 誤コード
    page.fill("css=input", "9999")
    page.click("text=決定"); time.sleep(0.3)
    body = page.evaluate("document.body.innerText")
    assert "なにも起こらなかった" in body, "wrong-code message missing"
    # 正コード
    page.fill("css=input", "1010")
    page.click("text=決定"); time.sleep(0.5)
    body = page.evaluate("document.body.innerText")
    assert "すべて解放された" in body, "unlock banner missing (modal)"
    cs = page.evaluate("window.__test.charState()")
    assert sorted(cs["c"]) == [0,1,2,3,4,5], f"charState after modal: {cs}"
    print("3 logo-tap modal + wrong/right code OK", cs)
    page.close()
    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL CHEAT OK")
