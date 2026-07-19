# -*- coding: utf-8 -*-
"""賭けオーバーレイの見た目を目視確認するスクショ（4択 / 天使悪魔 / 結果）"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"

def make_group(p, idxs, t):
    for i in range(36):
        r, c = divmod(i, 6)
        base = 2 if (r + c) % 2 == 0 else 3
        p.evaluate(f"window.__test.setCellType({i}, {base})")
    for i in idxs:
        p.evaluate(f"window.__test.setCellType({i}, {t})")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.5)
    tiles = page.query_selector_all("div.flex.justify-center.gap-2 > button")
    tiles[6].click(); time.sleep(0.4)
    page.screenshot(path="shot_gamble_select.png")
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.7)
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
    # HP を 40 にして「剛運=HP50が赤警告」を見せる
    page.evaluate("window.__test.setPHP(40)"); time.sleep(0.1)
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.15)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    page.screenshot(path="shot_gamble_mode.png")   # 第1段: 4択（剛運=赤）
    page.evaluate("window.__test.rigCoin('angel')")
    page.evaluate("window.__test.gamblePickMode('heal2')"); time.sleep(0.3)
    page.screenshot(path="shot_gamble_coin.png")   # 第2段: 天使/悪魔
    page.evaluate("window.__test.gambleChoose('angel')"); time.sleep(0.2)
    page.screenshot(path="shot_gamble_spin.png")   # 回転演出
    time.sleep(1.0)
    print("shots saved")
    b.close()
