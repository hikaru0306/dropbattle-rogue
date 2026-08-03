# -*- coding: utf-8 -*-
"""調律師カノン（resonate）検証。

コア: 3つ目の「調律」でタップした塊をまるごと消すと、その数がそのターンの「お題」になる。
攻撃と防御で消した数の“合計”がお題ちょうどならターン成立＝攻撃・防御・回復すべてに倍率。
倍率は成功したターンが続くほど ×1.5 → ×2 → ×2.5（上限4）と伸び、外すと ×1.5 からやり直し。
調律そのものは攻撃・防御・回復を出さない。
専用ドロップ響石=ズレの許容+1(＋化+2)／レリック 音叉(許容+1)・余韻の鈴(1個ズレを救済)・
大和音の譜(倍率の上限+1)。
"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"

fails, errors, notes = [], [], []
def chk(name, cond, extra=""):
    print(("OK  " if cond else "NG  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

def st(p): return p.evaluate("window.__test.state()")
def ci(p): return p.evaluate("window.__test.charInfo()")

def make_group(p, idxs, t=1):
    """盤面を市松(2/3)に塗ってから idxs だけ色 t にする（＝ちょうど len(idxs) 個のグループ）"""
    for i in range(36):
        r, c = divmod(i, 6)
        p.evaluate(f"window.__test.setCellType({i}, {2 if (r + c) % 2 == 0 else 3})")
    for i in idxs:
        p.evaluate(f"window.__test.setCellType({i}, {t})")

def run_of(n, row=0):
    """row 行目から連続 n 個（6を超えたら次の行へ折り返して連結）"""
    idxs, r, left = [], row, n
    while left > 0:
        take = min(left, 6)
        idxs += [r * 6 + c for c in range(take)]
        left -= take; r += 1
    return idxs

def do_act(p, act, n, row=0, chord=None):
    """act を n 個の塊で1回使う。chord に (pos, up) を渡すとそのセルに響石を仕込む。
    3手目はコミット直後に自動でターン解決へ入るので、結果は同じ evaluate 内で読み取って返す。"""
    idxs = run_of(n, row)
    make_group(p, idxs); time.sleep(0.08)
    if chord is not None:
        pos, up = chord
        p.evaluate(f"window.__test.setCellSpecial({idxs[pos]}, 'chord', {str(up).lower()}, false, false)")
        time.sleep(0.1)
    p.evaluate(f"window.__test.setAct('{act}')")
    info = p.evaluate(f"(() => {{ window.__test.commit({idxs[0]}); const c = window.__test.charInfo();"
                      f" return {{ target: c.resoTarget, cnt: c.resoCnt, reso: c.reso }}; }})()")
    time.sleep(0.35)
    return info

def fresh_battle(p):
    p.evaluate("window.__test.restart()"); time.sleep(0.4)
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    p.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)

def full_turn(p, tune_n, atk_n, def_n):
    """調律 → 攻撃 → 防御 の順で1ターン回す（3手目で自動解決）。
    tune_n がお題、atk_n + def_n がそれに一致すれば成立する。
    倍率が乗ると敵を倒してしまい、次のバトルで連勝数がリセットされるので毎ターン敵を出し直す"""
    p.evaluate("window.__test.setPHP(300)")
    p.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.2)
    do_act(p, "heal", tune_n, 0)              # 調律（塊まるごと＝この数がお題）
    do_act(p, "atk", atk_n, 2)
    do_act(p, "def", def_n, 4)                # 3手目 → 自動でターン解決
    time.sleep(1.6)
    if st(p)["status"] != "battle": fresh_battle(p)

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.5)

    # ―― 1) キャラ選択: 8タイル・調律師が8体目 ――
    tiles = page.query_selector_all("div.flex.justify-center.gap-2 > button")
    chk("8 tiles on select", len(tiles) == 8, f"tiles={len(tiles)}")
    tiles[7].click(); time.sleep(0.4)
    body = page.evaluate("document.body.innerText")
    chk("canon name shown", "調律師カノン" in body, body[:140])
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)
    chk("char applied (resonate)", ci(page)["skill"] == "resonate", ci(page)["skill"])

    # ―― 2) 初期袋: 3つ目が回復でないので 剣4/盾4/回復1 + 響石3 ――
    o = st(page)["owned"]
    chk("owns chord x3 + 4/4/1", o["chord"] == 3 and o["atk"] == 4 and o["def"] == 4 and o["heal"] == 1, str(o))

    # ―― 3) 調律で消した数がそのターンのお題になる ――
    fresh_battle(page)
    chk("no target before 調律", ci(page)["resoTarget"] is None, str(ci(page)["resoTarget"]))
    r = do_act(page, "heal", 5, 0)            # 5個の塊をまるごと消す
    chk("調律 sets the turn target to the cleared count", r["target"] == 5, str(r["target"]))
    tv = st(page)["tv"]
    chk("調律 produces no atk/def/heal", tv["atk"] == 0 and tv["def"] == 0 and tv["heal"] == 0,
        str({k: tv[k] for k in ("atk", "def", "heal")}))

    # ―― 4) 本丸: 攻撃も防御も同じ数で消したら全パラメーターに倍率 ――
    per = st(page)["per"]
    do_act(page, "atk", 3, 2)                 # お題5 に対して 3 + 2 で合わせる
    idxs = run_of(2, 4)
    make_group(page, idxs); time.sleep(0.1)
    page.evaluate(f"window.__test.setCellSpecial({idxs[1]}, 'heal', false, false, false)")  # 回復にも乗ることを見る
    time.sleep(0.12)
    page.evaluate("window.__test.setAct('def')")
    raw = st(page)["tv"]
    raw_atk, raw_heal = raw["atk"], raw["heal"]
    hp0 = st(page)["enemies"][0]["hp"]
    # 3手目はコミット直後（数十ms後）に自動でターン解決へ入り、その頭で倍率が乗る。
    # 「解決に入った後・freshTurn で初期化される前」の窓で tv を読む
    page.evaluate(f"window.__test.commit({idxs[0]})")
    time.sleep(0.25)
    after = st(page)["tv"]
    chk("atk x1.5 on the first success", after["atk"] == round(raw_atk * 1.5), f"{after['atk']} vs {round(raw_atk*1.5)}")
    chk("def x1.5 on the first success", after["def"] == round(2 * per["def"] * 1.5), f"{after['def']} vs {round(2*per['def']*1.5)}")
    chk("heal x1.5 on the first success", after["heal"] == round((raw_heal + 10) * 1.5), f"{after['heal']} vs {round((raw_heal+10)*1.5)}")
    notes.append(f"お題5を 攻撃3+防御2 で成立: 攻撃 {raw_atk}→{after['atk']} / 防御 →{after['def']} / 回復 →{after['heal']}（×2）")
    time.sleep(1.6)
    dealt = hp0 - st(page)["enemies"][0]["hp"]
    chk("damage dealt matches the boosted atk", dealt == after["atk"], f"dealt={dealt} atk={after['atk']}")
    # 倍率が上がるのはターン境界（次ターンの開始）なので、ターンが終わってから連勝数を見る
    chk("streak becomes 1 at the turn boundary", ci(page)["reso"] == 1, str(ci(page)["reso"]))

    # ―― 5) 連続で成立すると ×1.5 → ×2 → ×2.5 … と伸びる ――
    fresh_battle(page)
    streaks = []
    for _ in range(4):
        full_turn(page, 5, 3, 2)
        streaks.append(ci(page)["reso"])
    chk("streak climbs 1,2,3,4 over consecutive turns", streaks == [1, 2, 3, 4], str(streaks))
    chk("multiplier after 4 wins is 3.5", page.evaluate("window.__test.resoMulNow()") == 3.5,
        str(page.evaluate("window.__test.resoMulNow()")))

    # ―― 6) 外すと ×1.5 からやり直し ――
    full_turn(page, 5, 4, 3)                  # 攻撃だけ外す
    chk("a miss resets the streak", ci(page)["reso"] == 0, str(ci(page)["reso"]))
    chk("next success is x1.5 again", page.evaluate("window.__test.resoMulNow()") == 1.5,
        str(page.evaluate("window.__test.resoMulNow()")))
    full_turn(page, 5, 3, 2)
    chk("and it climbs again from there", ci(page)["reso"] == 1, str(ci(page)["reso"]))

    # ―― 7) 調律を使わなかったターンは成立しない ――
    fresh_battle(page)
    do_act(page, "atk", 3, 0); do_act(page, "def", 3, 2)
    tv0 = st(page)["tv"]
    page.evaluate("window.__test.resolve()")
    tv1 = st(page)["tv"]
    chk("no 調律 -> no multiplier", tv1["atk"] == tv0["atk"], f"{tv1['atk']} vs {tv0['atk']}")
    chk("no 調律 -> streak stays 0", ci(page)["reso"] == 0, str(ci(page)["reso"]))
    time.sleep(1.6)

    # ―― 8) 調律: お邪魔だけの塊では決められない（アクションも消費しない） ――
    fresh_battle(page)
    make_group(page, run_of(3, 5)); time.sleep(0.1)
    page.evaluate("window.__test.setCellType(35, 4)")   # JUNK
    time.sleep(0.15)
    used0 = st(page)["used"]
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(35)"); time.sleep(0.4)
    chk("調律: a junk tap is rejected (action not spent)", st(page)["used"] == used0,
        f"{st(page)['used']} vs {used0}")
    chk("調律: a junk tap sets no target", ci(page)["resoTarget"] is None, str(ci(page)["resoTarget"]))

    # ―― 10) 響石: お題との差1個でも「ぴったり」（＋化は2個） ――
    fresh_battle(page)
    do_act(page, "heal", 5, 0)                                   # お題=5
    do_act(page, "atk", 3, 2, chord=(1, False))                  # 響石1個 → ズレ許容+1
    do_act(page, "def", 3, 4)                                    # 合計6（お題5との差1）→ 響石で成立
    time.sleep(1.6)
    chk("chord widens the tolerance (turn still succeeds)", ci(page)["reso"] == 1, str(ci(page)["reso"]))
    if st(page)["status"] != "battle": fresh_battle(page)

    # ―― 11) 専用レリック: プールに3種／他キャラでは出ない ――
    pool = page.evaluate("window.__test.relicPool()")
    for k in ("tuningfork", "echobell", "grandchord"):
        chk(f"relic {k} in canon pool", k in pool, "not in pool")
    page.evaluate("window.__test.setChar(0)"); time.sleep(0.2)
    pool0 = page.evaluate("window.__test.relicPool()")
    chk("canon relics hidden for other chars",
        not any(k in pool0 for k in ("tuningfork", "echobell", "grandchord")),
        str([k for k in ("tuningfork", "echobell", "grandchord") if k in pool0]))
    page.evaluate("window.__test.setChar(7)"); time.sleep(0.2)

    # ―― 12) 大和音の譜: 倍率が+0.5される ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('grandchord')"); time.sleep(0.2)
    for _ in range(4):
        full_turn(page, 5, 3, 2)
    chk("grandchord: +0.5 on the ladder", page.evaluate("window.__test.resoMulNow()") == 4,
        str(page.evaluate("window.__test.resoMulNow()")))

    # ―― 13) 余韻の鈴: 1つ外していても成立したことにする ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('echobell')"); time.sleep(0.2)
    full_turn(page, 5, 3, 3)                  # 合計6（お題5との差1）→ 鈴が救済
    chk("echobell rescues a 1-off sum", ci(page)["reso"] == 1, str(ci(page)["reso"]))
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('echobell')"); time.sleep(0.2)
    full_turn(page, 5, 4, 3)                  # 合計7（差2）→ 救済されない
    chk("echobell does not rescue a 2-off sum", ci(page)["reso"] == 0, str(ci(page)["reso"]))

    # ―― 14) 調律の音叉: 合計が1個ズレていても成立する ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('tuningfork')"); time.sleep(0.2)
    full_turn(page, 5, 3, 3)                  # 合計6（お題5との差1）→ 音叉で成立
    chk("tuningfork: a 1-off sum still succeeds", ci(page)["reso"] == 1, str(ci(page)["reso"]))

    # ―― 15) 中断セーブ往復でお題・連勝数が復元される ――
    fresh_battle(page)
    full_turn(page, 5, 3, 2)                  # 連勝1
    do_act(page, "heal", 4, 0)                # 次のターンでお題だけ決めておく
    tgt0, streak0 = ci(page)["resoTarget"], ci(page)["reso"]
    page.evaluate("window.__test.suspend()"); time.sleep(0.8)
    sv = page.evaluate("window.__test.saveData(7)")
    chk("save keeps the streak", sv and sv.get("reso") == streak0, str(sv.get("reso") if sv else None))
    chk("save keeps the target", sv and sv.get("tv", {}).get("resoTarget") == tgt0,
        str(sv.get("tv", {}).get("resoTarget") if sv else None))
    page.evaluate("window.__test.resumeSave(7)"); time.sleep(1.0)
    chk("resume restores the streak", ci(page)["reso"] == streak0, f"{ci(page)['reso']} vs {streak0}")
    chk("resume restores the target", ci(page)["resoTarget"] == tgt0, f"{ci(page)['resoTarget']} vs {tgt0}")

    chk("no page errors", not errors, str(errors[:3]))
    b.close()

print("\n".join(["", "― メモ ―"] + notes) if notes else "")
print(f"\n{'ALL PASS' if not fails else 'FAIL: ' + ', '.join(fails)}  ({len(fails)} failed)")
sys.exit(1 if fails else 0)
