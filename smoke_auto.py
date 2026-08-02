# -*- coding: utf-8 -*-
"""オートモードの検証:
1. メニューに「操作設定」があり、モーダルに「オートモード／ドロップを自動で消す」がある
2. ONトグルで db_auto=1 が保存される
3. autoPick が盤面の最大グループ（細工した6連結）を指す
4. バトル中、盤面を触らずにアクションが自動消化されターンが進む
5. バトル画面の中央下に点滅バッジ「タップでオートモード解除」が出る
6. バッジタップ→確認「オートモードを解除しますか？」→いいえで継続／はいで解除・バッジ消滅
7. 賭博師: コイントスの天使/悪魔選択で止まらず、自動で天使を選んでターンが進む
"""
import os, sys, time
from playwright.sync_api import sync_playwright

EXE = os.environ.get("SMOKE_EXE", r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe")
URL = os.environ.get("SMOKE_URL", "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1")

def st(page): return page.evaluate("window.__test.state()")

def wait_status(page, want, timeout=20):
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
    page.click("text=冒険に出る")
    page.click("text=この仲間と冒険に出る")
    wait_status(page, "map")

    # 1. メニュー → 操作設定モーダル
    page.locator("button[aria-label=メニュー]").click(); time.sleep(0.3)
    assert page.locator("text=操作設定").count() >= 1, "no ctrl item in menu"
    page.click("text=操作設定"); time.sleep(0.3)
    assert page.locator("text=オートモード").count() >= 1, "no auto row"
    assert page.locator("text=ドロップを自動で消す").count() == 1, "no auto description"
    print("1 menu -> ctrl modal with auto row OK")

    # 2. トグルON → 保存
    page.locator("button[aria-label=オートモード切替]").click(); time.sleep(0.2)
    a = page.evaluate("window.__test.auto()")
    assert a["on"] is True, f"auto not on: {a}"
    assert page.evaluate("localStorage.getItem('db_auto')") == "1", "db_auto not saved"
    page.click("text=閉じる"); time.sleep(0.2)
    print("2 toggle ON persists OK")

    # 3. autoPick の採点: いったんOFFで盤面を細工し、最大グループ(行0の6連結)を指すこと
    page.evaluate("window.__test.setAuto(false)")
    s = st(page)
    battle_node = next(i for i in s["selectable"]
                       if next(n for n in s["map"] if n["id"] == i)["type"] in ("battle", "elite"))
    page.evaluate(f"window.__test.enter({battle_node})")
    wait_status(page, "battle")
    time.sleep(0.4)
    page.evaluate("""() => {
      for (let r = 0; r < 6; r++) for (let c = 0; c < 6; c++)
        window.__test.setCellType(r * 6 + c, r === 0 ? 2 : (r + c) % 2);
    }""")
    time.sleep(0.2)
    pick = page.evaluate("window.__test.autoPick()")
    assert 0 <= pick <= 5, f"autoPick={pick}, expected in row0 (0..5)"
    assert page.evaluate(f"window.__test.groupSize({pick})") == 6, "picked group is not the 6-chain"
    print("3 autoPick chooses max group OK:", pick)

    # 4. ONにして自動でターンが進む（盤面は一切クリックしない）
    page.evaluate("window.__test.setAuto(true)")
    t0 = time.time()
    while time.time() - t0 < 25:
        s = st(page)
        if s["status"] != "battle" or s["turn"] >= 2:
            break
        time.sleep(0.3)
    s = st(page)
    assert s["status"] != "battle" or s["turn"] >= 2, f"auto did not progress: turn={s['turn']} used={s['used']}"
    print("4 auto plays actions and resolves turn OK:", {"status": s["status"], "turn": s.get("turn")})

    # 5. バトル中はバッジが出る（4でバトルが終わっていたら次のバトルへ）
    if st(page)["status"] != "battle":
        if st(page)["status"] == "reward":
            page.evaluate("window.__test.declineReward()")
        wait_status(page, "map")
        s = st(page)
        battle_node = next(i for i in s["selectable"]
                           if next(n for n in s["map"] if n["id"] == i)["type"] in ("battle", "elite"))
        page.evaluate(f"window.__test.enter({battle_node})")
        wait_status(page, "battle")
    badge = page.locator("button[aria-label=オートモード解除]")
    assert badge.count() == 1, "no auto badge in battle"
    assert "タップでオートモード解除" in badge.inner_text(), "badge text mismatch"
    print("5 blinking badge shown in battle OK")

    # 6. バッジ→確認→いいえ→継続、はい→解除
    badge.click(); time.sleep(0.3)
    assert page.locator("text=オートモードを解除しますか？").count() == 1, "no confirm dialog"
    page.click("text=いいえ"); time.sleep(0.3)
    assert page.evaluate("window.__test.auto()")["on"] is True, "auto turned off by いいえ"
    assert badge.count() == 1, "badge gone after いいえ"
    badge.click(); time.sleep(0.3)
    page.click("text=はい"); time.sleep(0.3)
    assert page.evaluate("window.__test.auto()")["on"] is False, "auto still on after はい"
    assert badge.count() == 0, "badge still shown after release"
    assert page.evaluate("localStorage.getItem('db_auto')") == "0", "db_auto not cleared"
    print("6 badge -> confirm (いいえ/はい) OK")

    # 7. 賭博師: 賭けのコイントスで止まらず自動で天使を選んで進む
    page.evaluate("window.__test.setChar(6)")          # 賭博師ジンへ切替（skill=gamble）
    page.evaluate("window.__test.spawn(['golem'])")    # 高HPの敵にして途中で勝負がつかないように
    page.evaluate("window.__test.rigCoin('angel')")    # 出目を天使に固定（当たり続ける＝HP減で紛れない）
    time.sleep(0.3)
    t_start = st(page)["turn"]
    page.evaluate("window.__test.setAuto(true)")
    picked = False
    t0 = time.time()
    while time.time() - t0 < 30:
        ga = page.evaluate("window.__test.gambleAsk()")
        if ga and ga.get("pick") == "angel":
            picked = True                              # 自動選択が天使であることを目撃
        s = st(page)
        if s["status"] == "battle" and s["turn"] >= t_start + 2:
            break
        time.sleep(0.1)
    s = st(page)
    assert s["turn"] >= t_start + 2, f"gambler auto stuck: turn={s['turn']} (start={t_start}) ask={page.evaluate('window.__test.gambleAsk()')}"
    assert picked, "never observed auto angel pick"
    assert page.evaluate("window.__test.gambleAsk()") is None or st(page)["turn"] >= t_start + 2, "coin overlay left open"
    print("7 gambler coin toss auto-picks angel and turns progress OK:",
          {"turns": s["turn"] - t_start})
    page.evaluate("window.__test.setAuto(false)")

    # 8. 調律師: オートは「その手番のお題の数に一番近いグループ」を選ぶ（通常の最大化とは逆）
    page.evaluate("window.__test.setChar(7)")          # 調律師カノンへ切替（skill=resonate）
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
    for i in range(36):                                 # 市松に塗って、3個と6個のグループだけ作る
        r, c = divmod(i, 6)
        page.evaluate(f"window.__test.setCellType({i}, {2 if (r + c) % 2 == 0 else 3})")
    for i in [0, 1, 2, 3, 4, 5]:                        # 行0 = 6個
        page.evaluate(f"window.__test.setCellType({i}, 1)")
    for i in [24, 25, 26]:                              # 行4 = 3個
        page.evaluate(f"window.__test.setCellType({i}, 1)")
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.3)
    page.evaluate("window.__test.setAct('atk')"); time.sleep(0.2)   # 攻撃はお題ぴったりを狙う
    pick = page.evaluate("window.__test.autoPick()")
    assert 24 <= pick <= 26, f"resonate autoPick={pick}, expected the 3-cell group (24..26), not the biggest one"
    page.evaluate("window.__test.rigReso([6,6,6])"); time.sleep(0.2)
    pick6 = page.evaluate("window.__test.autoPick()")
    assert 0 <= pick6 <= 5, f"resonate autoPick={pick6} for quota 6, expected the 6-cell group (0..5)"
    # 調律(3つ目)は「切り取る数」以上の最小の塊を選ぶ
    page.evaluate("window.__test.rigReso([3,3,3])")
    page.evaluate("window.__test.setTuneN(3)")
    page.evaluate("window.__test.setAct('heal')"); time.sleep(0.3)
    pickT = page.evaluate("window.__test.autoPick()")
    assert 24 <= pickT <= 26, f"tune autoPick={pickT}, expected the smallest group that fits the cut (24..26)"
    page.evaluate("window.__test.setTuneN(1)")
    page.evaluate("window.__test.rigReso(null)")
    print("8 resonate autoPick matches the quota, not the max group OK:", {"t3": pick, "t6": pick6})

    browser.close()
print("ALL AUTO OK")
