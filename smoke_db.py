# -*- coding: utf-8 -*-
import sys, time, json
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\1d09642f-34d3-42f6-b80d-62863c94dfb6\scratchpad"

def st(page):
    return page.evaluate("window.__test.state()")

def wait_status(page, want, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = st(page)
        if s["status"] == want:
            return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT waiting status={want}, now={st(page)}")

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.screenshot(path=SHOT + r"\s1_title.png")
    print("1 title OK")

    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    s = wait_status(page, "map")
    assert len(s["selectable"]) >= 1, "no selectable nodes"
    page.screenshot(path=SHOT + r"\s2_map.png")
    print("2 map OK selectable:", s["selectable"])

    # 最初のノードへ（バトル）
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    s = wait_status(page, "battle")
    assert len(s["enemies"]) >= 1
    print("3 battle OK enemies:", s["enemies"])
    page.screenshot(path=SHOT + r"\s3_battle.png")

    # 実ポインタ操作で盤面を1回消す（攻撃）
    cell = page.query_selector("[data-idx='14']")
    box = cell.bounding_box()
    page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    page.mouse.down()
    time.sleep(0.15)
    page.mouse.up()
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["atk"] > 0, f"pointer commit failed tv={s['tv']}"
    print("4 pointer commit OK tv:", s["tv"])

    # 残り2アクションはフックで消化 → ターン解決
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.commit(0)")
    time.sleep(0.7)
    page.evaluate("window.__test.commit(0)")
    s = wait_status(page, "reward", 20)
    print("5 victory->reward OK")
    page.screenshot(path=SHOT + r"\s4_reward.png")
    page.click("css=[class*=pop-in] button >> nth=0")
    s = wait_status(page, "map")
    print("6 reward picked, back to map OK")

    # 3章制: 各章のボスを倒して次章へ、最終章でクリア
    expected_boss = [("kslime","treant","alraune"), ("vamp","lich","toadking"), ("demon","dragon","ifrit","reaper")]
    for a in range(3):
        page.evaluate("window.__test.jumpTo(7)")
        time.sleep(0.3)
        s = st(page)
        boss_id = [n["id"] for n in s["map"] if n["type"] == "boss"][0]
        assert boss_id in s["selectable"], f"boss not selectable act{a}"
        page.evaluate(f"window.__test.enter({boss_id})")
        s = wait_status(page, "battle")
        assert s["enemies"][0]["kind"] in expected_boss[a], f"act{a} boss: {s['enemies']}"
        print(f"7-{a} act{a+1} boss OK:", s["enemies"][0]["kind"])
        if a == 0:
            hp_before = s["php"]
            for _t in range(3):  # ため始動のボスは数ターンでダメージ確認
                page.evaluate("window.__test.resolve()")
                time.sleep(3.5)
                s = st(page)
                if s["php"] < hp_before: break
            assert s["php"] < hp_before, f"boss attack not applied php={s['php']}"
            print("8 boss attack OK php:", s["php"])
            page.screenshot(path=SHOT + r"\s5_boss.png")
        page.evaluate("window.__test.weaken()")
        page.evaluate("window.__test.setPierce(true)")
        page.evaluate("window.__test.addAtk(5000)")
        page.evaluate("window.__test.resolve()")
        if a < 2:
            t0 = time.time()
            while time.time() - t0 < 20:
                s = st(page)
                if s["actClear"]: break
                time.sleep(0.3)
            assert s["actClear"], f"actClear not shown act{a}"
            page.evaluate("window.__test.nextAct()")
            time.sleep(0.6)
            s = st(page)
            assert s["act"] == a + 1, f"act not advanced: {s['act']}"
            assert s["php"] == s["pmax"] == 300, f"act bonus wrong php={s['php']} pmax={s['pmax']}"
            print(f"9-{a} nextAct OK act={s['act']+1} pmax={s['pmax']}")
        else:
            s = wait_status(page, "clear", 20)
            print("9 final boss defeated -> clear OK")
    page.screenshot(path=SHOT + r"\s6_clear.png")

    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]:
        print(" -", e)
    sys.exit(1)
print("ALL SMOKE OK")
