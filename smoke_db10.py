# -*- coding: utf-8 -*-
"""爆弾特殊ドロップ検証: 十字/斜めの巻き込み消去（お邪魔も消せる）"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(p): return p.evaluate("window.__test.state()")

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width":420,"height":900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    time.sleep(0.5)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)

    # 1) クロスボム: 隣のお邪魔ごと消す
    page.evaluate("window.__test.setCellType(13, 4)")   # 左隣をお邪魔に
    page.evaluate("window.__test.setCellSpecial(14, 'bombx')")
    time.sleep(0.2)
    assert st(page)["junk"] == 1
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.8)
    s = st(page)
    assert s["junk"] == 0, f"bombx should clear junk: junk={s['junk']}"
    assert s["tv"]["atk"] >= 30, f"bombx extra cells not counted: {s['tv']}"
    print("B1 bombx cross blast OK (junk cleared, atk", s["tv"]["atk"], ")")

    # 2) Xボム: 斜めのお邪魔を消す
    page.evaluate("window.__test.setCellType(21, 4)")   # 斜め下をお邪魔に
    page.evaluate("window.__test.setCellSpecial(14, 'bombd')")
    time.sleep(0.2)
    assert st(page)["junk"] == 1
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.8)
    s = st(page)
    assert s["junk"] == 0, f"bombd should clear diagonal junk: junk={s['junk']}"
    print("B2 bombd diagonal blast OK")

    # 2.5) 連鎖爆発: 爆弾→爆弾→その先のお邪魔まで届く
    page.evaluate("window.__test.setCellSpecial(14, 'bombx')")
    page.evaluate("window.__test.setCellSpecial(15, 'bombx')")
    page.evaluate("window.__test.setCellType(16, 4)")   # 15の右隣（14の爆風外）をお邪魔に
    time.sleep(0.2)
    assert st(page)["junk"] == 1
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.9)
    s = st(page)
    assert s["junk"] == 0, f"chain explosion failed: junk={s['junk']}"
    print("B2.5 chain explosion OK (bomb -> bomb -> junk)")

    # 3) お邪魔だけのグループは効果ゼロのまま（B2.5で3回目→ターン解決を待つ）
    time.sleep(5.5)
    page.evaluate("window.__test.setCellType(0, 4)")
    time.sleep(0.2)
    hv0 = st(page)["tv"]["heal"]
    page.evaluate("window.__test.commit(0)")   # 残アクション=回復
    time.sleep(0.8)
    s = st(page)
    assert s["tv"]["heal"] == hv0, f"junk group must be zero effect: {s['tv']}"
    print("B3 pure junk group zero effect OK")
    b.close()

if errors:
    print("ERRORS:", errors[:5]); sys.exit(1)
print("ALL BOMB TESTS OK")
