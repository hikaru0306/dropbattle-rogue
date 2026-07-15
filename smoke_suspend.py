# -*- coding: utf-8 -*-
"""中断セーブ＆BGM切替の検証:
1. 戦闘勝利→マップ到達で自動保存される
2. 中断→タイトル→キャラ選択で「続きから」モーダル→再開で状態復元
3. 「最初から」で中断データ削除＆新規開始
4. BGM: ボス死亡後も雑魚が残ればbossのまま／リザルト=result
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&resume=1"

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

def win_battle(page):
    page.evaluate("window.__test.weaken()")
    for _ in range(12):
        s = st(page)
        if s["status"] != "battle": break
        if s["locked"]: time.sleep(0.6); continue
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.8)
    wait_status(page, "reward", 25)

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.evaluate("window.__test.clearSave(0)")  # 前回実行の残骸を掃除
    page.click("text=冒険に出る"); time.sleep(0.4)
    page.click("text=この仲間と冒険に出る")
    s = wait_status(page, "map")
    assert not page.evaluate("window.__test.hasSave(0)"), "no save before progress"
    print("1 fresh start, no premature save OK")

    # バトル1勝 → マップ到達 → 自動保存
    nodes = {n["id"]: n for n in s["map"]}
    battle_id = [i for i in s["selectable"] if nodes[i]["type"] == "battle"][0]
    page.evaluate(f"window.__test.enter({battle_id})")
    wait_status(page, "battle")
    page.evaluate("window.__test.giveRelic('piggy')")
    win_battle(page)
    assert snd(page)["track"] == "result", f"reward bgm: {snd(page)['track']}"
    print("2 reward BGM=result OK")
    page.evaluate("window.__test.declineReward()")
    time.sleep(0.8)
    if st(page).get("shop"): page.evaluate("window.__test.closeShop()")
    s = wait_status(page, "map")
    assert page.evaluate("window.__test.hasSave(0)"), "autosave missing after node clear"
    sv = page.evaluate("window.__test.saveData(0)")
    coins0, cur0 = s["coins"], s["cur"]
    assert sv["coins"] == coins0 and sv["cur"] == cur0 and "piggy" in sv["relics"], f"save content: {sv}"
    print("3 autosave on map OK:", {"coins": sv["coins"], "cur": sv["cur"]})

    # 中断 → タイトル → 続きから
    page.evaluate("window.__test.suspend()")
    s = wait_status(page, "title")
    page.click("text=冒険に出る"); time.sleep(0.4)
    page.click("text=この仲間と冒険に出る"); time.sleep(0.5)
    body = page.evaluate("document.body.innerText")
    assert "中断中のデータがあります" in body and "続きから進めますか" in body, "resume modal missing"
    page.click("text=▶ 続きから")
    s = wait_status(page, "map")
    assert s["coins"] == coins0 and s["cur"] == cur0 and "piggy" in s["relics"], f"resume mismatch: {s['coins']},{s['cur']},{s['relics']}"
    assert len(s["selectable"]) >= 1, "no selectable after resume"
    print("4 suspend -> resume OK (coins/cur/relics restored)")

    # もう一度中断 → 最初から
    page.evaluate("window.__test.suspend()")
    wait_status(page, "title")
    page.click("text=冒険に出る"); time.sleep(0.4)
    page.click("text=この仲間と冒険に出る"); time.sleep(0.5)
    page.click("text=最初から（中断データを削除）")
    s = wait_status(page, "map")
    assert s["coins"] == 0 and s["act"] == 0 and s["relics"] == [], f"fresh start dirty: {s['coins']},{s['relics']}"
    assert not page.evaluate("window.__test.hasSave(0)"), "save should be deleted on fresh start"
    print("5 fresh-start deletes save OK")

    # BGM: ボス死亡後も雑魚残りは boss のまま
    page.evaluate("window.__test.jumpTo(7)")
    time.sleep(0.3)
    s = st(page)
    boss_id = [n["id"] for n in s["map"] if n["type"] == "boss"][0]
    page.evaluate(f"window.__test.enter({boss_id})")
    s = wait_status(page, "battle")
    assert snd(page)["track"] == "boss", f"boss bgm: {snd(page)['track']}"
    # ボスだけ倒す（取り巻きは残す）
    page.evaluate("window.__test.weaken()")
    bidx = [i for i, e in enumerate(s["enemies"]) if e["kind"] in ("kslime","treant","alraune")][0]
    page.evaluate(f"window.__test.setTargetIdx({bidx})")
    for _ in range(3):
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.8)
    time.sleep(3.0)
    s = st(page)
    alive = [e for e in s["enemies"] if e["alive"]]
    if s["status"] == "battle" and alive:  # 取り巻きが残っている状況
        assert all(e["kind"] not in ("kslime","treant","alraune") for e in alive), f"boss still alive: {alive}"
        assert snd(page)["track"] == "boss", f"bgm after boss death: {snd(page)['track']}"
        print("6 boss BGM persists with minions alive OK:", [e["kind"] for e in alive])
    else:
        print("6 (skip) minions died too — actClear path, track:", snd(page)["track"])

    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL SUSPEND OK")
