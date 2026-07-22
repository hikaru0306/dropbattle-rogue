# -*- coding: utf-8 -*-
"""隠しコード1010の検証:
1. タイトルでキーボード1010 → キャラ全解放（uが全キャラ・cは変えない）＋バナー表示
2. ロゴ5連打 → コード入力モーダル → 1010入力で解放 / 誤コードは無反応
3. 解放後: 選択画面で全キャラ選択可。未クリアなので裏トグルは出ない
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

ALL = [0, 1, 2, 3, 4, 5, 6]

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
    assert sorted(cs["u"]) == ALL, f"u not all unlocked: {cs}"
    assert cs["c"] == [], f"c must stay untouched (fresh profile): {cs}"
    print("1 keyboard 1010 unlock-only OK", cs)
    # 0101: 実績のないクリア印だけ掃除（実績ありの本物クリアと解放は維持）
    page.evaluate("window.__test.setCleared(0); window.__test.setCleared(2); window.__test.recordStats(0, 500, 100)")
    cs = page.evaluate("window.__test.charState()")
    assert sorted(cs["c"]) == [0, 2], f"setCleared failed: {cs}"
    page.keyboard.type("0101")
    time.sleep(0.5)
    body = page.evaluate("document.body.innerText")
    assert "クリア印を掃除した" in body, "reset banner missing"
    cs = page.evaluate("window.__test.charState()")
    assert sorted(cs["u"]) == ALL, f"u lost after 0101: {cs}"
    assert cs["c"] == [0], f"real clear (with stats) must survive, fake removed: {cs}"
    print("1b keyboard 0101 cleanup keeps real clear OK", cs)
    # 選択画面: 全キャラ選択可・未クリアなので裏トグルは出ない
    page.click("text=冒険に出る"); time.sleep(0.4)
    for i in range(len(ALL)):
        page.click(f"css=div.flex.justify-center.gap-2 > button >> nth={i}"); time.sleep(0.25)
        body = page.evaluate("document.body.innerText")
        assert "🔒 未解放" not in body, f"char {i} still locked"
        if i == 0:  # 1bで本物クリアを維持したキャラは裏トグルが出るのが正しい
            assert "裏の冒険" in body, "char 0 (real clear) must show ura toggle"
        else:
            assert "裏の冒険" not in body, f"char {i} shows ura toggle without clear"
    print("2 all chars selectable, ura toggle only on real clear OK")
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
    assert sorted(cs["u"]) == ALL and cs["c"] == [], f"charState after modal: {cs}"
    print("3 logo-tap modal + wrong/right code OK", cs)
    page.close()
    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL CHEAT OK")
