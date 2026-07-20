# -*- coding: utf-8 -*-
"""裏ステージのスモークテスト:
1. 表クリア前は裏トグル非表示 / setClearedで表示
2. 裏開始 → mode=ura・ヘッダー「裏・第1章」
3. 裏1章の敵プール・表より高い火力(encPreviewサンプリング)
4. 全5章のボスを順に撃破 → 真魔王 → クリア → cu記録
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\8337b61f-2136-4d04-9cc7-403904522f1d\scratchpad"

URA_POOL0_LIGHT = {"moth", "owl", "mant", "fox", "crow"}
URA_BOSSES = [("fenrir", "titania"), ("skadi", "jotun"), ("behemot", "sphinx"),
              ("bdragon", "noct", "vorax"), ("demonx",)]

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

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)

    # 1. 表クリア前: 裏トグルなし
    page.click("text=冒険に出る")
    time.sleep(0.5)
    body = page.evaluate("document.body.innerText")
    assert "表の冒険" not in body, "ura toggle should be hidden before omote clear"
    print("1 ura hidden before clear OK")

    # 2. 表クリア済みにする → トグル出現 → 裏を選んで開始
    # （賭博師6はTEST_MODE初期状態で解放済みなので、裏クリアでの解放検証用に一旦ロック）
    page.evaluate("window.__test.lockChar(6)")
    time.sleep(0.2)
    assert 6 not in page.evaluate("window.__test.charState()")["u"], "lockChar(6) failed"
    page.evaluate("window.__test.setCleared(0)")
    time.sleep(0.4)
    body = page.evaluate("document.body.innerText")
    assert "表の冒険" in body, "ura toggle missing after setCleared"
    page.click("text=裏の冒険")
    time.sleep(0.3)
    page.screenshot(path=SHOT + r"\u1_select_ura.png")
    page.click("text=裏の世界へ挑む")
    s = wait_status(page, "map")
    assert s["mode"] == "ura", f"mode={s['mode']}"
    body = page.evaluate("document.body.innerText")
    assert "裏・第1章" in body, "ura header missing"
    page.screenshot(path=SHOT + r"\u2_map_ura.png")
    print("2 ura start OK mode:", s["mode"])

    # 3. 裏の敵は表より強い（同条件でatk平均を20回サンプリング）
    avg = page.evaluate("""(() => {
      const s = (m) => { let t = 0, n = 0;
        for (let i = 0; i < 20; i++) for (const e of window.__test.encPreview(0, 'battle', m)) { t += e.atk; n++; }
        return t / n; };
      return { omote: s(undefined), ura: s('ura') };
    })()""")
    assert avg["ura"] > avg["omote"] * 1.1, f"ura not harder: {avg}"
    print(f"3 ura atk avg {avg['ura']:.1f} > omote {avg['omote']:.1f} OK")

    # 4. 裏1章のバトル: 敵が裏プール
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    s = wait_status(page, "battle")
    for e in s["enemies"]:
        assert e["kind"] in URA_POOL0_LIGHT, f"unexpected ura act0 enemy: {e['kind']}"
    print("4 ura act0 enemies OK:", [e["kind"] for e in s["enemies"]])
    page.screenshot(path=SHOT + r"\u3_battle_ura.png")
    page.evaluate("window.__test.weaken()")
    for _ in range(3):
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.7)
    s = wait_status(page, "reward", 20)
    page.evaluate("window.__test.declineReward()")
    s = wait_status(page, "map")
    print("5 ura battle victory OK")

    # 5. 全5章: 各章ボス撃破 → 最終は真魔王 → クリア
    for a in range(5):
        page.evaluate("window.__test.jumpTo(7)")
        time.sleep(0.3)
        s = st(page)
        boss_id = [n["id"] for n in s["map"] if n["type"] == "boss"][0]
        assert boss_id in s["selectable"], f"boss not selectable act{a}"
        page.evaluate(f"window.__test.enter({boss_id})")
        s = wait_status(page, "battle")
        boss = [e for e in s["enemies"]]
        assert boss[0]["kind"] in URA_BOSSES[a], f"ura act{a} boss: {boss[0]['kind']}"
        assert len(boss) == 3, f"ura boss should have 2 minions: {len(boss)}"
        print(f"6-{a} ura act{a+1} boss OK:", boss[0]["kind"])
        if a == 4:
            page.screenshot(path=SHOT + r"\u4_lastboss.png")
        page.evaluate("window.__test.weaken()")
        page.evaluate("window.__test.setPierce(true)")
        page.evaluate("window.__test.addAtk(9999)")
        page.evaluate("window.__test.resolve()")
        if a < 4:
            t0 = time.time()
            while time.time() - t0 < 20:
                s = st(page)
                if s["actClear"]: break
                time.sleep(0.3)
            assert s["actClear"], f"actClear not shown ura act{a}"
            page.evaluate("window.__test.nextAct()")
            time.sleep(0.6)
            s = st(page)
            assert s["act"] == a + 1 and s["mode"] == "ura", f"advance fail act={s['act']} mode={s['mode']}"
            print(f"7-{a} ura nextAct OK -> act{s['act']+1}")
        else:
            s = wait_status(page, "clear", 20)
            body = page.evaluate("document.body.innerText")
            assert "真魔王討伐" in body, "ura clear text missing"
            print("8 ura final boss defeated -> clear OK")
    page.screenshot(path=SHOT + r"\u5_clear_ura.png")

    # 6. 裏クリアが cu に記録される＋賭博師ジン(6)が解放される
    cs = page.evaluate("window.__test.charState()")
    assert 0 in cs["cu"], f"ura clear not recorded: {cs}"
    print("9 ura clear recorded cu:", cs["cu"])
    assert 6 in cs["u"], f"gambler not unlocked by ura clear: {cs}"
    print("10 gambler unlocked by ura clear OK u:", cs["u"])

    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]:
        print(" -", e)
    sys.exit(1)
print("ALL URA SMOKE OK")
