# -*- coding: utf-8 -*-
"""BGM遷移の検証（ボス戦後の切り替え仕様）:
1. ボス戦中は boss
2. 中間章ボス撃破 → 章クリア画面は bossclear
3. レリック選択後の報酬画面も bossclear のまま（result を鳴らさない）
4. 報酬確定 → 次章マップで map
5. 最終章ボス撃破 → clear 画面は result（bossclear を挟まない）
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(p): return p.evaluate("window.__test.state()")
def track(p): return p.evaluate("window.__test.sound()")["track"]

def wait_status(page, want, timeout=25):
    t0=time.time()
    while time.time()-t0<timeout:
        s=st(page)
        if s["status"]==want: return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT status={want} now={st(page)['status']}")

def wait_actclear(page, timeout=25):
    t0=time.time()
    while time.time()-t0<timeout:
        if st(page)["actClear"]: return
        time.sleep(0.25)
    raise SystemExit("TIMEOUT actClear")

def enter_boss(page):
    s = st(page)
    boss = [n for n in s["map"] if n["type"] == "boss"][0]
    eds = [e for e in s["edges"] if e["to"] == boss["id"]]
    page.evaluate(f"window.__test.setCur({eds[0]['from']})")
    time.sleep(0.2)
    page.evaluate(f"window.__test.enter({boss['id']})")
    return wait_status(page, "battle")

def kill_all(page):
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.setPierce(true)")
    for i in range(4):
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.7)
        s = st(page)
        if s["actClear"] or s["status"] in ("reward", "clear"): return
        if s["status"] == "battle" and not any(e["alive"] for e in s["enemies"]): return

errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    page=b.new_page(viewport={"width":420,"height":900})
    page.on("console", lambda m: errors.append(m.text) if m.type=="error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    wait_status(page,"map")
    assert track(page) == "map", f"map bgm: {track(page)}"

    # 1. 中間章（1章）ボス戦 → boss
    enter_boss(page)
    time.sleep(0.5)
    assert track(page) == "boss", f"boss bgm: {track(page)}"
    print("B1 boss bgm OK")

    # 2. 撃破 → 章クリア画面は bossclear
    kill_all(page)
    wait_actclear(page)
    time.sleep(0.3)
    assert track(page) == "bossclear", f"actclear bgm: {track(page)}"
    print("B2 actclear bossclear OK")

    # 3. レリックを受け取らずに進む → 報酬画面でも bossclear のまま（result禁止）
    page.click("text=レリックを受け取らずに進む")
    wait_status(page, "reward")
    time.sleep(0.5)
    assert track(page) == "bossclear", f"boss reward bgm should stay bossclear: {track(page)}"
    print("B3 reward keeps bossclear (no result) OK")

    # 4. 報酬確定 → 次章マップで map
    page.click("css=[class*=pop-in] button >> nth=0")
    wait_status(page, "map")
    time.sleep(0.3)
    s = st(page)
    assert s["act"] == 1, f"act: {s['act']}"
    assert track(page) == "map", f"act2 map bgm: {track(page)}"
    print("B4 next act map bgm OK")

    # 5. 最終章（3章）へジャンプ → ボス撃破 → clear 画面は result（bossclearを挟まない）
    page.evaluate("window.__test.nextAct()")
    wait_status(page, "map")
    assert st(page)["act"] == 2, f"act: {st(page)['act']}"
    enter_boss(page)
    time.sleep(0.5)
    assert track(page) == "boss", f"final boss bgm: {track(page)}"
    kill_all(page)
    wait_status(page, "clear")
    time.sleep(0.3)
    assert not st(page)["actClear"], "final boss must not show actClear"
    assert track(page) == "result", f"clear bgm should be result: {track(page)}"
    print("B5 final clear result OK")
    b.close()

if errors:
    print("ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL SMOKE_BGM OK")
