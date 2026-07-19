# -*- coding: utf-8 -*-
# カード選択マップUIの検証:
#  1) マップ画面はカード(data-mapcard)が selectable と同数だけ表示される（全体マップは出ない）
#  2) 進行ドット列（ボスアイコン）がある
#  3) 近道エッジ(row+2)の行き先カードに「近道」バッジが出る
#  4) ボス手前ノードからはボスカード（説明文つき・現在地アイコン）
#  5) カードのDOMクリックでバトルに入れる
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\20e2c436-aed5-4d03-b91a-4395047d4e9d\scratchpad"

def st(page):
    return page.evaluate("window.__test.state()")

def wait_status(page, want, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = st(page)
        if s["status"] == want:
            return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT waiting status={want}, now={st(page)['status']}")

def cards(page):
    return page.evaluate("[...document.querySelectorAll('[data-mapcard]')].map(b => Number(b.dataset.mapcard))")

def body_text(page):
    return page.evaluate("document.body.innerText")

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る")
    page.click("text=この仲間と冒険に出る")
    s = wait_status(page, "map")

    # 1) カード枚数 = selectable 数（1手先読み: 全ノードは描画されない）
    ids = cards(page)
    assert sorted(ids) == sorted(s["selectable"]), f"cards {ids} != selectable {s['selectable']}"
    assert 1 <= len(ids) <= 3, f"card count {len(ids)}"
    page.screenshot(path=SHOT + r"\cm1_start.png")
    print("1 cards==selectable OK", ids)

    # 2) 進行ドット列（ボスアイコン）
    assert page.evaluate("!!document.querySelector('img[alt=\"ボス\"]')"), "no boss icon in progress dots"
    print("2 progress dots OK")

    # 3) 近道エッジは廃止: 全エッジが1層ずつ進む（row差1のみ）
    s = st(page)
    rowof = {n["id"]: n["row"] for n in s["map"]}
    bad = [e for e in s["edges"] if rowof[e["to"]] - rowof[e["from"]] != 1]
    assert not bad, f"skip edges must not exist: {bad}"
    assert "近道" not in body_text(page), "shortcut badge should be removed"
    print("3 no shortcut edges OK")

    # 4) ボス手前 → ボスカード + 現在地アイコン
    s = st(page)
    pre = [n for n in s["map"] if n["row"] == 6][0]
    page.evaluate(f"window.__test.setCur({pre['id']})")
    time.sleep(0.3)
    s = st(page)
    boss_ids = [n["id"] for n in s["map"] if n["type"] == "boss"]
    assert s["selectable"] == boss_ids, f"selectable {s['selectable']} != boss {boss_ids}"
    t = body_text(page)
    assert "主がひそむ" in t, "boss card desc missing"
    assert page.evaluate("!!document.querySelector('img[alt=\"現在地\"]')"), "no current-position icon"
    page.screenshot(path=SHOT + r"\cm3_boss.png")
    print("4 boss card OK")

    # 5) カードDOMクリックでバトルへ
    page.click(f"[data-mapcard='{boss_ids[0]}']")
    s = wait_status(page, "battle")
    assert len(s["enemyAtks"]) >= 1, "no enemies after card click"
    page.screenshot(path=SHOT + r"\cm4_battle.png")
    print("5 card click -> battle OK")

    b.close()

if errors:
    print("CONSOLE ERRORS:", errors)
    sys.exit(1)
print("ALL OK smoke_cardmap")
