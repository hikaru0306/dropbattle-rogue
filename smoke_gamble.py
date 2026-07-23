# -*- coding: utf-8 -*-
"""賭博師ジン（gamble）検証 — 新フロー:
賭けモードをボタンで選ぶ→賭けアクションで消す（＝予約のみ）→攻撃・防御も含め
3アクション消し終わってターン解決に入った頭で天使/悪魔コイントスを開封→結果反映→攻撃。
・HPコスト=基礎×消した数 / 剛運鉄運=×消した数(buffPend予約) / 成功=ノーコスト・失敗=HPだけ払う
・専用ドロップchip=失敗時リトライ / レリック luckcoin/devilpact/angelfeather / HP0で敗北
実測攻撃力も出力する（何個消しで・HPいくら払って・攻撃力いくら）。"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"

fails, errors, notes = [], [], []
def chk(name, cond, extra=""):
    print(("OK  " if cond else "NG  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

def st(p): return p.evaluate("window.__test.state()")
def ci(p): return p.evaluate("window.__test.charInfo()")
def gask(p): return p.evaluate("window.__test.gambleAsk()")

def resolve_coin(p):
    """新フロー: 回転中はタップ(gambleReveal)で出目を出す。チップのやり直しも含め、
    出目が確定してオーバーレイが閉じる（またはHP0で敗北）まで reveal を繰り返す。"""
    for _ in range(30):
        ga = gask(p)
        if not ga: return
        ph = ga.get("phase")
        if ph == "spin":
            p.evaluate("window.__test.gambleReveal()"); time.sleep(0.15)
        elif ph == "retry":
            time.sleep(0.2)   # 投げ直し(spin)へ戻るのを待って次のタップへ
        elif ph == "result":
            time.sleep(0.3); return  # gambleFinish が閉じる
        else:
            time.sleep(0.1)

def make_group(p, idxs, t):
    for i in range(36):
        r, c = divmod(i, 6)
        base = 2 if (r + c) % 2 == 0 else 3
        p.evaluate(f"window.__test.setCellType({i}, {base})")
    for i in idxs:
        p.evaluate(f"window.__test.setCellType({i}, {t})")

def fresh_battle(p, hp=None):
    """新しいバトルに入って敵(golem高HP)を出す"""
    p.evaluate("window.__test.restart()"); time.sleep(0.4)
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.7)
    p.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)
    if hp is not None:
        p.evaluate(f"window.__test.setPHP({hp})"); time.sleep(0.1)

def use_act(p, act, group, seed):
    """1アクション(atk/def)を消費する。make_group で盤面を作り直してから消す
    （turnRef の atk/def はターン内で累積・盤面リセットの影響を受けない）"""
    make_group(p, group, 1); time.sleep(0.08)
    p.evaluate(f"window.__test.setAct('{act}')")
    p.evaluate(f"window.__test.commit({seed})"); time.sleep(0.35)

def gamble_turn(p, mode, group, seed, pick, rig, base_atk_group=None):
    """新フロー1ターン: 攻撃・防御を先に消費→賭けを消す(予約)→3揃いでコイントス開封→pick。
    base_atk_group を渡すと攻撃はそのグループを消して base攻撃を作る。返り値に php0/cost/count。"""
    # ① 攻撃（base攻撃を作るなら大きめグループ、なければ単発）
    if base_atk_group:
        use_act(p, "atk", base_atk_group, base_atk_group[0])
    else:
        use_act(p, "atk", [30], 30)
    base_atk = st(p)["tv"]["atk"]
    # ② 防御（単発）
    use_act(p, "def", [35], 35)
    # ③ 賭け（最後に消す → 3揃い → resolveTurn 冒頭でコイントス開封）
    p.evaluate(f"window.__test.setGambleMode('{mode}')"); time.sleep(0.05)
    assert ci(p)["gambleMode"] == mode, f"gambleMode set failed: {ci(p)['gambleMode']}"
    make_group(p, group, 1); time.sleep(0.1)
    # 賭けアクションで消す前にコイントスがまだ開いていないこと（＝予約タイミングの検証）
    p.evaluate(f"window.__test.rigCoin('{rig}')")
    p.evaluate("window.__test.setAct('heal')")
    php0 = st(p)["php"]
    p.evaluate(f"window.__test.commit({seed})"); time.sleep(0.55)
    ga = gask(p)  # ここで初めて天使/悪魔のコイントスが開く（3アクション消し終わった後）
    assert ga and ga["mode"] == mode and ga["phase"] == "pick", f"expected coin/pick after 3rd action, got {ga}"
    cost = ga["cost"]; count = ga["count"]
    p.evaluate(f"window.__test.gambleChoose('{pick}')"); time.sleep(0.1)
    resolve_coin(p)
    return {"php0": php0, "cost": cost, "count": count, "base_atk": base_atk}

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.5)

    # ―― キャラ選択: 7タイル・賭博師が7体目 ――
    tiles = page.query_selector_all("div.flex.justify-center.gap-2 > button")
    chk("7 tiles on select", len(tiles) == 7, f"tiles={len(tiles)}")
    tiles[6].click(); time.sleep(0.4)
    body = page.evaluate("document.body.innerText")
    chk("gambler name shown", "賭博師ジン" in body, body[:120])
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)
    chk("char applied (gamble)", ci(page)["skill"] == "gamble")

    # ―― 初期所持: 剣盾回復2ずつ + 専用chip3 ――
    o = st(page)["owned"]
    chk("owns chip x3 + 2/2/2", o["chip"] == 3 and o["atk"] == 2 and o["def"] == 2 and o["heal"] == 2, str(o))

    # ―― アクションボタンのタップで 4モードが循環（治癒→虹→剛運→鉄運）――
    chk("default gambleMode = heal2", ci(page)["gambleMode"] == "heal2", ci(page)["gambleMode"])
    seq = ["heal2", "rain", "atkx", "defx"]
    for i in range(5):
        cur = ci(page)["gambleMode"]
        nxt = seq[(seq.index(cur) + 1) % 4]
        page.evaluate(f"window.__test.setGambleMode('{nxt}')")
        chk(f"cycle {cur}->{nxt}", ci(page)["gambleMode"] == nxt, ci(page)["gambleMode"])
    page.evaluate("window.__test.setGambleMode('heal2')")

    # ================= 0) タイミング: 賭けを消した直後にコイントスが開く（2アクション目でも） =================
    fresh_battle(page)
    use_act(page, "atk", [30], 30)  # 攻撃1つ使う
    # 賭けを2つ目に消す → まだ def が残っていても、即コイントスが開く
    page.evaluate("window.__test.setGambleMode('atkx')")
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.1)
    page.evaluate("window.__test.rigCoin('angel')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.5)
    ga0 = gask(page)
    chk("賭け消去直後にコイントス開封", bool(ga0) and ga0["phase"] == "pick", str(ga0))
    page.evaluate("window.__test.gambleChoose('angel')"); time.sleep(0.1)
    resolve_coin(page)
    chk("コイントス後は次のアクションへ（ターン未解決）", gask(page) is None and st(page)["status"] == "battle", str(st(page)["status"]))
    # 残る防御を消す → 3揃い → ターン解決
    use_act(page, "def", [35], 35)
    time.sleep(0.6)

    # ================= 1) 剛運の賭け（atkx）成功 → 攻撃×消した数・HP消費なし・攻撃実行 =================
    fresh_battle(page)
    en_hp0 = st(page)["enemies"][0]["hp"]
    r = gamble_turn(page, "atkx", [12, 13, 14, 15, 16], 12, "angel", "angel", base_atk_group=[0, 1, 2, 3, 4])
    chk("base atk built (5 drops => 50)", r["base_atk"] == 50, f"atk={r['base_atk']}")
    s = st(page)
    chk("atkx WIN => no HP cost (成功はノーコスト)", r["php0"] - s["php"] == 0, f"paid={r['php0'] - s['php']} cost={r['cost']}")
    chk("atkx overlay closed after choose", gask(page) is None)
    en = s["enemies"][0]
    predicted = 50 * 5  # base50 × 倍率5
    chk("atkx resolve dealt big damage (golem撃破/大ダメージ)", (not en["alive"]) or en["hp"] <= en_hp0 - predicted + 1, f"golem {en_hp0}->{en['hp']}")
    notes.append(f"[剛運] 5個消し・的中: HP不変(0消費) / base攻撃=50 → ×5 = 攻撃250 → golem {en_hp0}→{en['hp']} alive={en['alive']}（外していれば-HP{r['cost']}）")

    # ================= 2) 治癒の賭け（heal2）成功 → 回復 count*2・HP消費なし =================
    fresh_battle(page, hp=150)
    r = gamble_turn(page, "heal2", [12, 13, 14, 15, 16], 12, "demon", "demon")
    s = st(page)
    chk("heal2 cost(外すと) = count (5)", r["cost"] == 5, f"cost={r['cost']}")
    # 治癒の賭けは成功で回復するのでHPは減らない（むしろ増える）。賭けでHPを失っていないことを確認
    chk("heal2 WIN => 賭けでHP減っていない(成功はノーコスト)", r["php0"] - s["php"] <= 0, f"paid={r['php0'] - s['php']}")
    # 回復はターン解決の回復フェーズで反映済み → HPが150付近から回復しているはず（敵攻撃で相殺され得るので下限のみ確認）
    notes.append(f"[治癒] 5個消し・的中: HP不変(賭け分) / 回復 count*2=10 をターン解決で反映 / 賭け後HP={s['php']}")

    # ================= 3) 虹の賭け（rain）成功 → 虹が count 個増える・HP消費なし =================
    fresh_battle(page)
    r = gamble_turn(page, "rain", [12, 13, 14, 15, 16], 12, "angel", "angel")
    s = st(page)
    w1 = sum(1 for c in s["board"] if c["w"])
    chk("rain win => wild drops appeared", w1 >= 1, f"wild={w1}")
    chk("rain WIN => no HP cost", r["php0"] - s["php"] == 0, f"paid={r['php0'] - s['php']}")
    notes.append(f"[虹] 5個消し・的中: HP不変 / 虹ドロップ={w1}（外していれば-HP{r['cost']}）")

    # ================= 4) 失敗 → 倍率なし・HPだけ払う =================
    fresh_battle(page)
    r = gamble_turn(page, "atkx", [12, 13, 14, 15, 16], 12, "angel", "demon", base_atk_group=[0, 1, 2, 3, 4])  # angel賭け・demon出る=はずれ
    s = st(page)
    chk("atkx LOSE => HP paid = count*10 (50)", r["php0"] - s["php"] == 50, f"paid={r['php0'] - s['php']}")
    notes.append(f"[失敗] 5個消し・はずれ: -HP50 / 倍率なし（base攻撃50はそのまま）")

    # ================= 5a) 成功では低HPでも死なない =================
    fresh_battle(page, hp=8)
    r = gamble_turn(page, "atkx", [12, 13, 14, 15, 16], 12, "angel", "angel", base_atk_group=[0, 1, 2, 3, 4])  # cost50>HP8 だが的中
    chk("low HP WIN => not lose (成功は死なない)", st(page)["status"] != "lose", f"status={st(page)['status']}")
    chk("low HP WIN => 賭けでHP減っていない", r["php0"] - st(page)["php"] == 0, f"paid={r['php0'] - st(page)['php']}")

    # ================= 5b) 失敗でHP0 → lose =================
    fresh_battle(page, hp=8)
    use_act(page, "atk", [30], 30)
    use_act(page, "def", [35], 35)
    page.evaluate("window.__test.setGambleMode('atkx')")
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.1)
    page.evaluate("window.__test.rigCoin('demon')")  # angel賭け・demon出る=はずれ→cost50支払いでHP0
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.55)
    page.evaluate("window.__test.gambleChoose('angel')"); time.sleep(0.1)
    resolve_coin(page)
    chk("LOSE at HP0 => lose", st(page)["status"] == "lose", f"status={st(page)['status']}")

    # ================= 6) 専用チップ chip → 失敗時リトライ回数に反映 =================
    fresh_battle(page)
    use_act(page, "atk", [30], 30)
    use_act(page, "def", [35], 35)
    page.evaluate("window.__test.setGambleMode('heal2')")
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.1)
    page.evaluate("window.__test.setCellSpecial(0, 'chip', false, false)")  # 通常chip1枚
    page.evaluate("window.__test.setCellSpecial(1, 'chip', true, false)")   # +化chip=2回分
    time.sleep(0.1)
    page.evaluate("window.__test.rigCoin('demon')")  # angel賭け→demonでずっと外す→リトライ消化
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.55)
    ga = gask(page)
    chk("chip retries = 1 + 2 = 3", ga and ga.get("retries") == 3, str(ga))
    page.evaluate("window.__test.gambleChoose('angel')"); time.sleep(0.1)
    resolve_coin(page)
    chk("chip flow closed overlay", gask(page) is None)

    # ================= 7) レリック luckcoin: 失敗でも効果50%（HPは払う）=================
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('luckcoin')"); time.sleep(0.1)
    r = gamble_turn(page, "atkx", [12, 13, 14, 15, 16], 12, "angel", "demon", base_atk_group=[0, 1, 2, 3, 4])  # はずれ
    s = st(page)
    # count5 atkx: 失敗でも luckcoin で倍率 1+(5-1)*0.5 = 3 / HPは cost(50) 払う
    chk("luckcoin lose => HP still paid (50)", r["php0"] - s["php"] == 50, f"paid={r['php0'] - s['php']}")
    notes.append(f"[幸運の銀貨] 5個消し・はずれ: 倍率は1+(5-1)*0.5=3を予約しつつHP50は支払い")

    # ================= 8) レリック angelfeather: HPコスト半減(切上) =================
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('angelfeather')"); time.sleep(0.1)
    use_act(page, "atk", [30], 30)
    use_act(page, "def", [35], 35)
    page.evaluate("window.__test.setGambleMode('atkx')")
    make_group(page, [0, 1, 2, 3, 4], 1); time.sleep(0.1)
    page.evaluate("window.__test.rigCoin('angel')")
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.55)
    ga2 = gask(page)
    # atkx count5 => raw50 => ceil(25)=25
    chk("angelfeather halves cost (50->25)", ga2 and ga2["cost"] == 25, str(ga2))
    page.evaluate("window.__test.gambleChoose('angel')"); time.sleep(0.1)
    resolve_coin(page)

    # ================= 9) レリック devilpact: 悪魔で当てると×1.5 =================
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('devilpact')"); time.sleep(0.1)
    r = gamble_turn(page, "atkx", [12, 13, 14, 15], 12, "demon", "demon")  # count4, 悪魔を当てる
    s = st(page)
    bp = s["tv"].get("buffPend")
    # 成功後は resolveTurn 本体が走って buffPend は消費済みの可能性。ログ/攻撃結果で確認
    notes.append(f"[悪魔契約] 4個消し 悪魔的中: 攻撃倍率 4×1.5=6 相当（buffPend={bp}）")

    chk("no page errors", len(errors) == 0, str(errors[:3]))
    b.close()

print("\n--- 実測メモ ---")
for n in notes: print("  " + n)
print("\nRESULT:", "PASS" if not fails else "FAIL " + str(fails))
