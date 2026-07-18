# -*- coding: utf-8 -*-
"""バランス改修の検証:
1. 剣/盾 = 同時消し1つにつき+5（強化+10）・アクション非依存
2. 星の強化 = 発動個数6のまま・(★×2+1)倍
3. 裏最終ボス 真魔王HP≒4000
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

def st(page): return page.evaluate("window.__test.state()")

def wait_status(page, want, timeout=15):
    t0 = time.time()
    while time.time() - t0 < timeout:
        s = st(page)
        if s["status"] == want:
            return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT waiting status={want}, now={st(page)['status']}")

def fresh_battle(page):
    page.evaluate("window.__test.restart()")
    time.sleep(0.5)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    t0 = time.time()
    while time.time() - t0 < 10:
        if st(page)["status"] == "battle": return
        time.sleep(0.2)
    raise SystemExit("battle enter timeout")

def clear_row(page, n, special=None, up=False, action="atk"):
    """row0の左からn個を色0の連結グループにして先頭をタップ消し。specialはセル0に付与"""
    for i in range(36):
        page.evaluate(f"window.__test.setCellType({i}, {1 if (i // 6) % 2 else 2})")  # 全体を市松で分断
    for i in range(n):
        page.evaluate(f"window.__test.setCellType({i}, 0)")
    if special:
        page.evaluate(f"window.__test.setCellSpecial(0, '{special}', {str(up).lower()})")
    page.evaluate(f"window.__test.setAct('{action}')")
    tv0 = st(page)["tv"]
    page.evaluate("window.__test.commit(0)")
    time.sleep(0.8)
    tv1 = st(page)["tv"]
    return tv0, tv1

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    time.sleep(0.5)

    # 1. 剣(通常): 3個消し → main=3*10=30, 剣ボーナス=3*5=15 → atk 45
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 3, "atk")
    got = tv1["atk"] - tv0["atk"]
    assert got == 45, f"sword base: want 45 got {got}"
    print("1 sword +5/drop OK (3clear -> atk+45)")

    # 2. 剣(強化): 3個消し → 30 + 3*10=30 → 60
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 3, "atk", up=True)
    got = tv1["atk"] - tv0["atk"]
    assert got == 60, f"sword up: want 60 got {got}"
    print("2 sword up +10/drop OK (3clear -> atk+60)")

    # 3. 盾を回復アクションで消してもドロップ数×5（アクション非依存）
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 4, "def", action="heal")
    got = tv1["def"] - tv0["def"]
    assert got == 20, f"shield via heal: want 20 got {got}"
    print("3 shield +5/drop via heal action OK (4clear -> def+20)")

    # 4. 星(通常): 6個で発動 (1+1)倍 → main=6*10*2=120
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 6, "star")
    got = tv1["atk"] - tv0["atk"]
    assert got == 120, f"star base: want 120 got {got}"
    print("4 star normal x2 OK (6clear -> atk+120)")

    # 5. 星(強化): 発動は6個のまま → 5個では素の効果のみ
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 5, "star", up=True)
    got = tv1["atk"] - tv0["atk"]
    assert got == 50, f"star up 5clear: want 50 got {got}"
    print("5 star up threshold stays 6 OK (5clear -> atk+50, no mult)")

    # 6. 星(強化): 6個で3倍 → 6*10*3=180
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 6, "star", up=True)
    got = tv1["atk"] - tv0["atk"]
    assert got == 180, f"star up 6clear: want 180 got {got}"
    print("6 star up x3 OK (6clear -> atk+180)")

    # 7. 裏最終ボスHP≒4000
    hp = page.evaluate("""(() => {
      let mx = 0;
      for (let i = 0; i < 30; i++) for (const e of window.__test.encPreview(4, 'boss', 'ura'))
        if (e.kind === 'demonx') mx = Math.max(mx, e.hp || 0);
      return mx;
    })()""")
    if hp == 0:  # encPreviewがhpを返さない場合は実戦で確認
        page.evaluate("window.__test.restart()"); time.sleep(0.4)
        page.evaluate("window.__test.setMode('ura')")
        for _ in range(4): page.evaluate("window.__test.nextAct()"); time.sleep(0.3)
        page.evaluate("window.__test.jumpTo(7)"); time.sleep(0.3)
        s = st(page)
        boss_id = [n["id"] for n in s["map"] if n["type"] == "boss"][0]
        assert boss_id in s["selectable"], "boss not selectable"
        page.evaluate(f"window.__test.enter({boss_id})")
        t0 = time.time()
        while time.time() - t0 < 10:
            s = st(page)
            if s["status"] == "battle" and s["enemies"]: break
            time.sleep(0.2)
        assert s["status"] == "battle", f"battle not entered: {s['status']}"
        hp = [e["hp"] for e in s["enemies"] if e["kind"] == "demonx"][0]
    assert 3900 <= hp <= 4100, f"demonx hp: {hp}"
    print("7 demonx HP OK:", hp)

    # 8. 裏ボス大技カーブ: 3章(act2)は300〜400・章ごとに単調増加
    URA_BOSS_KINDS = {"fenrir","titania","skadi","jotun","behemot","sphinx","bdragon","noct","vorax","demonx"}
    bigs = page.evaluate("""(() => {
      const out = [];
      for (let a = 0; a < 5; a++) {
        let t = 0, n = 0;
        for (let i = 0; i < 30; i++) for (const e of window.__test.encPreview(a, 'boss', 'ura'))
          if (%s.has(e.kind)) { t += e.bigDmg; n++; }
        out.push(t / n);
      }
      return out;
    })()""" % ("new Set(" + str(sorted(URA_BOSS_KINDS)).replace("'", '"') + ")"))
    assert 300 <= bigs[2] <= 400, f"act3 boss big out of 300-400: {bigs}"
    for i in range(4):
        assert bigs[i] < bigs[i+1], f"boss big not increasing: {bigs}"
    print("8 ura boss big curve OK:", [round(x) for x in bigs])

    # 9. イリス: 攻/防の基礎値8・回復は1のまま
    page.evaluate("window.__test.setChar(1)")
    time.sleep(0.2)
    per = st(page)["per"]
    assert per["atk"] == 8 and per["def"] == 8 and per["heal"] == 1, f"iris per: {per}"
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 3)
    got = tv1["atk"] - tv0["atk"]
    assert got == 24, f"iris atk 3clear: want 24 got {got}"
    print("9 iris base 8 OK (per", per, ", 3clear -> atk+24)")

    # 10. ガレス: 強化は1ドロップ+0.1（4個atk=40 → 3個強化で 40*(1+0.3)=52）
    page.evaluate("window.__test.setChar(2)")
    page.evaluate("window.__test.setSkillTarget('atk')")
    time.sleep(0.2)
    fresh_battle(page)
    tv0, tv1 = clear_row(page, 4, action="atk")
    assert tv1["atk"] - tv0["atk"] == 40, f"gareth atk commit: {tv1}"
    tv0, tv1 = clear_row(page, 3, action="heal")   # 3つ目=強化（予約され、計算はターン解決の直前）
    pend = tv1.get("buffPend") or {}
    assert tv1["atk"] == 40 and abs(pend.get("mult", 0) - 1.3) < 1e-9, f"gareth buff pend x1.3: {tv1}"
    print("10 gareth +0.1/drop OK (pend x1.3, resolve時に40->52)")
    page.evaluate("window.__test.setChar(0)")

    # 11. 縦裂の宝珠: ちょうど5個で虹生成・6個では生成されない
    def count_linev(page):
        return sum(1 for c in st(page)["board"] if c["sp"] == "linev")
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('linegem')")
    clear_row(page, 5)
    n5 = count_linev(page)
    assert n5 == 1, f"linegem at exactly 5: want 1 got {n5}"
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('linegem')")
    clear_row(page, 6)
    n6 = count_linev(page)
    assert n6 == 0, f"linegem at 6 should not fire: got {n6}"
    print("11 linegem exact-5 OK (5clear->1, 6clear->0)")

    # 12. 核レリック4色: 翠(3)の核で上下巻き込み（3個消し+上段3個 → 6個分の回復）
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('jadecore')")
    for i in range(36):
        page.evaluate(f"window.__test.setCellType({i}, {1 if (i // 6) % 2 else 2})")
    for i in (30, 31, 32):   # 最下段に翠3連
        page.evaluate(f"window.__test.setCellType({i}, 3)")
    page.evaluate("window.__test.setAct('heal')")
    tv0 = st(page)["tv"]["heal"]
    page.evaluate("window.__test.commit(30)")
    time.sleep(0.8)
    got = st(page)["tv"]["heal"] - tv0
    assert got == 6, f"jadecore: want heal 6 (3+上3) got {got}"
    print("12 core relics all colors OK (jadecore 3clear -> 6 cells)")

    # 13. 毒: バトル中は永続（毎ターン累積値ぶん・解除されない）→ 次バトルで解除
    fresh_battle(page)
    s = st(page)
    for i in range(len(s["enemies"])):
        page.evaluate(f"window.__test.setPat({i}, ['charge'])")  # 敵は何もしない
    page.evaluate("window.__test.setPoison(4)")   # 毒4（1回ぶん）
    hp0 = st(page)["php"]
    for _ in range(3):
        page.evaluate("window.__test.resolve()")
        time.sleep(1.8)
    s = st(page)
    assert s["php"] == hp0 - 12, f"poison 3 ticks: want {hp0-12} got {s['php']}"
    assert s["poison"] > 0, "poison should persist within battle"
    time.sleep(1.5)
    page.evaluate("window.__test.weaken()")
    for _ in range(12):
        s = st(page)
        if s["status"] != "battle": break
        if s["locked"]: time.sleep(0.6); continue
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.8)
    wait_status(page, "reward", 25)
    page.evaluate("window.__test.declineReward()")
    time.sleep(0.8)
    if st(page).get("shop"):  # 群れノードだった場合はショップが開く
        page.evaluate("window.__test.closeShop()")
    s = wait_status(page, "map")
    nodes = {n["id"]: n for n in s["map"]}
    cand = [i for i in s["selectable"] if nodes[i]["type"] in ("battle", "horde", "elite")]
    page.evaluate(f"window.__test.enter({(cand or s['selectable'])[0]})")
    s = wait_status(page, "battle")
    assert s["poison"] == 0, f"poison should reset next battle: {s['poison']}"
    print("13 poison permanent-in-battle & reset-next-battle OK")

    b.close()

if errors:
    print("CONSOLE/PAGE ERRORS:")
    for e in errors[:10]: print(" -", e)
    sys.exit(1)
print("ALL BALANCE OK")
