# -*- coding: utf-8 -*-
"""ポーズメニュー＆音量スライダーの検証:
1. ヘッダーに☰ボタンがあり、タップでメニューモーダルが開く
2. メニューに「冒険を中断してタイトルへ」がある／サウンド設定モーダルには無い
3. メニューの中断でタイトルへ戻る
4. 音量スライダー: ポインタードラッグで sfxVol/bgmVol が変わる（iOS対策の座標式）
5. BGMがGainNode経由で配線される（bgmWired）
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(page): return page.evaluate("window.__test.state()")
def snd(page): return page.evaluate("window.__test.sound()")

def wait_status(page, want, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = st(page)
        if s["status"] == want:
            return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT waiting status={want}, now={st(page)['status']}")

with sync_playwright() as pw:
    browser = pw.chromium.launch(executable_path=EXE)
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.goto(URL)
    page.wait_for_function("() => window.__test")
    # 冒険開始（タイトル→キャラ選択→マップ）
    page.click("text=冒険に出る")
    page.click("text=この仲間と冒険に出る")
    wait_status(page, "map")

    # 1. ☰ボタン→メニュー
    burger = page.locator("button[aria-label=メニュー]")
    assert burger.count() == 1, "no burger button"
    burger.click(); time.sleep(0.3)
    assert page.locator("text=冒険を中断してタイトルへ").count() == 1, "no suspend in menu"
    print("1 burger -> menu with suspend OK")

    # 2. 冒険にもどる→サウンド設定に中断が無い
    page.click("text=冒険にもどる"); time.sleep(0.3)
    page.evaluate("window.__test.openSound()"); time.sleep(0.3)
    assert page.locator("text=サウンド設定").count() >= 1, "sound modal not open"
    assert page.locator("text=冒険を中断してタイトルへ").count() == 0, "suspend still in sound modal"
    print("2 sound modal has no suspend OK")

    # 3. スライダーをポインタードラッグ（左端=0付近へ）
    sliders = page.locator("input[type=range]")
    assert sliders.count() == 2, f"sliders={sliders.count()}"
    box = sliders.nth(1).bounding_box()  # 効果音
    y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + box["width"] * 0.9, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.1, y, steps=5)
    page.mouse.up()
    v = snd(page)["sfxVol"]
    assert abs(v - 0.1) < 0.06, f"sfxVol={v}"
    box = sliders.nth(0).bounding_box()  # BGM
    y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + box["width"] * 0.5, y)
    page.mouse.down(); page.mouse.up()
    v = snd(page)["bgmVol"]
    assert abs(v - 0.5) < 0.06, f"bgmVol={v}"
    print("3 slider pointer-drag changes volumes OK:", snd(page))

    # 4. BGMのGainNode配線（音量変更がgainに反映される）
    s = snd(page)
    assert s["wired"] is True, f"wired={s}"
    assert s["gain"] is not None and abs(s["gain"] - 0.3 * s["bgmVol"]) < 0.02, f"gain mismatch: {s}"
    print("4 bgm wired via GainNode OK:", {"wired": s["wired"], "gain": s["gain"]})

    # 5. メニューから中断→タイトル
    page.click("text=閉じる"); time.sleep(0.2)
    page.locator("button[aria-label=メニュー]").click(); time.sleep(0.3)
    page.click("text=冒険を中断してタイトルへ")
    wait_status(page, "title")
    print("5 suspend from menu -> title OK")

    browser.close()
print("ALL MENU OK")
