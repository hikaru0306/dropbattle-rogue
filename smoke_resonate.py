# -*- coding: utf-8 -*-
"""調律師カノン（resonate）検証。

コア: 毎ターン「お題」が3つ出る。1手目・2手目・3手目をその数ちょうどで消すと、
そのアクションの効果に倍率がかかる。倍率は合わせるたびに0.5ずつ上がり
（×1.5 → ×2 → ×2.5 → ×3 → ×3.5 → ×4・上限4）、バトル中はターンをまたいで伸び続ける。
外すと ×1.5 からやり直し。
倍率は消した瞬間に確定する（＝手応えが即わかる）。外しても他の手には影響しない。
3つ目の「調律」はボタンのタップで切り取る数を1〜4から選び、その数だけを塊から切り取る。
専用ドロップ響石=許容差±1(＋化±2)／レリック 音叉(お題3〜6)・余韻の鈴(1回だけ救済)・大和音の譜(倍率+1段)。
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
    """act を n 個消しで1回使う。chord に (pos, up) を渡すとそのセルに響石を仕込む。
    3手目はコミット直後に自動でターン解決へ入って resoHit が freshTurn で消えるので、
    判定結果は「同じ evaluate の中で」読み取って返す。"""
    idxs = run_of(n, row)
    make_group(p, idxs); time.sleep(0.08)
    if chord is not None:
        pos, up = chord
        p.evaluate(f"window.__test.setCellSpecial({idxs[pos]}, 'chord', {str(up).lower()}, false, false)")
        time.sleep(0.1)
    p.evaluate(f"window.__test.setAct('{act}')")
    hits = p.evaluate(f"(() => {{ window.__test.commit({idxs[0]}); return window.__test.charInfo().resoHit; }})()")
    time.sleep(0.35)
    return hits

def fresh_battle(p):
    p.evaluate("window.__test.restart()"); time.sleep(0.4)
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    p.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)

def roll_quotas(p, n):
    """アクションを消さずにターン解決だけ回して、お題の抽選値を集める"""
    seen = set()
    for _ in range(n):
        if st(p)["status"] != "battle": break
        seen.update(ci(p)["resoQuota"])
        p.evaluate("window.__test.setPHP(300)")
        p.evaluate("window.__test.resolve()"); time.sleep(0.75)
    return seen

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

    # ―― 2) 初期袋: 3つ目が「調律」で回復でないので 剣4/盾4/回復1 + 響石3 ――
    o = st(page)["owned"]
    chk("owns chord x3 + 4/4/1", o["chord"] == 3 and o["atk"] == 4 and o["def"] == 4 and o["heal"] == 1, str(o))

    fresh_battle(page)

    # ―― 3) お題は3つ・毎ターン引き直し・2〜7 ――
    page.evaluate("window.__test.rigReso(null)")
    q = ci(page)["resoQuota"]
    chk("quota has 3 numbers", isinstance(q, list) and len(q) == 3, str(q))
    seen = roll_quotas(page, 18)
    chk("quota values in 2..7", all(2 <= v <= 7 for v in seen), str(sorted(seen)))
    chk("quota re-rolled (>2 distinct)", len(seen) > 2, str(sorted(seen)))

    # ―― 4) 本丸: 1手目 4個 → 攻撃×2 / 2手目 2個 → 防御×3 / 3手目 3個 → 回復×4 ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([4,2,3])"); time.sleep(0.1)
    chk("rigReso fixes quota", ci(page)["resoQuota"] == [4, 2, 3], str(ci(page)["resoQuota"]))
    per = st(page)["per"]
    do_act(page, "atk", 4, 0)                        # 1手目 ぴったり → ×1.5
    tv1 = st(page)["tv"]
    chk("hit1: atk = 4 x per x1.5", tv1["atk"] == round(4 * per["atk"] * 1.5), f"{tv1['atk']} vs {round(4*per['atk']*1.5)}")
    chk("hit1 recorded as x1.5", ci(page)["resoHit"][0] == 1.5, str(ci(page)["resoHit"]))
    do_act(page, "def", 2, 2)                        # 2手目 ぴったり → ×2
    tv2 = st(page)["tv"]
    chk("hit2: def = 2 x per x2", tv2["def"] == 2 * per["def"] * 2, f"{tv2['def']} vs {2*per['def']*2}")
    chk("hit2 recorded as x2", ci(page)["resoHit"][1] == 2, str(ci(page)["resoHit"]))
    hp0 = st(page)["enemies"][0]["hp"]
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    hit3 = do_act(page, "heal", 5, 4)                # 3手目=調律。5個の塊から3個を切り取る（お題3）→ ×2.5
    chk("hit3 (調律) recorded as x2.5 (perfect)", hit3 == [1.5, 2, 2.5], str(hit3))
    notes.append(f"お題4・2・3を全部ぴったり: 攻撃{tv1['atk']}（×1.5）/ 防御{tv2['def']}（×2）/ 調律×2.5")
    time.sleep(1.6)
    dealt = hp0 - st(page)["enemies"][0]["hp"]
    chk("damage dealt matches the boosted atk", dealt == tv1["atk"], f"dealt={dealt} tv.atk={tv1['atk']}")

    # ―― 5) 外した手は等倍。倍率のはしごは「合わせた回数」で進む ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([4,2,3])"); time.sleep(0.1)
    do_act(page, "atk", 5, 0)                        # 1手目 外し（4に対して5個）
    tvm = st(page)["tv"]
    chk("miss: atk is plain", tvm["atk"] == 5 * per["atk"], f"{tvm['atk']} vs {5*per['atk']}")
    chk("miss recorded as 0", ci(page)["resoHit"][0] == 0, str(ci(page)["resoHit"]))
    do_act(page, "def", 2, 2)                        # 2手目 ぴったり → はしごは最初なので ×1.5
    tvm2 = st(page)["tv"]
    chk("after a miss, the next hit is x1.5", tvm2["def"] == round(2 * per["def"] * 1.5), f"{tvm2['def']} vs {round(2*per['def']*1.5)}")
    chk("hit ladder counts hits, not slots", ci(page)["resoHit"] == [0, 1.5, None], str(ci(page)["resoHit"]))

    # ―― 5b) 伸ばしたはしごも、外した瞬間に×1.5へ巻き戻る ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    do_act(page, "atk", 3, 0); do_act(page, "def", 3, 2)
    chk("ladder climbed to 2 hits", ci(page)["reso"] == 2, str(ci(page)["reso"]))
    do_act(page, "heal", 5, 4)                       # 3手目=調律(3個)でお題3を達成 → 3段目
    time.sleep(1.6)
    if st(page)["status"] != "battle": fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    chk("ladder is at 3 across the turn", ci(page)["reso"] == 3, str(ci(page)["reso"]))
    do_act(page, "atk", 5, 0)                        # 外す → 巻き戻る
    chk("a miss resets the ladder to the start", ci(page)["reso"] == 0, str(ci(page)["reso"]))
    do_act(page, "def", 3, 2)                        # 次の的中は ×1.5 から
    chk("after the reset the next hit is x1.5 again", ci(page)["resoHit"][1] == 1.5, str(ci(page)["resoHit"]))

    # ―― 6) お題・達成状況はターン開始でリセットされる ――
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    do_act(page, "heal", 5, 4)
    time.sleep(1.6)
    if st(page)["status"] != "battle": fresh_battle(page)
    chk("resoHit cleared on the new turn", all(v is None for v in ci(page)["resoHit"]), str(ci(page)["resoHit"]))
    chk("ladder itself survives the turn (still climbing)", ci(page)["reso"] >= 2, str(ci(page)["reso"]))

    # ―― 7) 響石: お題との差1個でも「ぴったり」（＋化は2個） ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([4,4,4])"); time.sleep(0.1)
    do_act(page, "atk", 5, 0, chord=(1, False))      # 5個（差1）＋響石1個 → 的中
    chk("chord: |5-4|=1 counts as a hit", ci(page)["resoHit"][0] == 1.5, str(ci(page)["resoHit"]))
    do_act(page, "def", 6, 2, chord=(1, True))       # 6個（差2）＋＋化響石 → 的中
    chk("chord+: |6-4|=2 counts as a hit", ci(page)["resoHit"][1] == 2, str(ci(page)["resoHit"]))
    page.evaluate("window.__test.setTuneN(4)"); time.sleep(0.1)
    h3 = do_act(page, "heal", 6, 4)                  # 3手目=調律。切り取り数4=お題4 → 達成
    chk("調律 with a matching cut fulfils the quota", h3[2] == 2.5, str(h3))
    time.sleep(1.6)

    # ―― 8) 専用レリック: プールに3種／他キャラでは出ない ――
    if st(page)["status"] != "battle": fresh_battle(page)
    pool = page.evaluate("window.__test.relicPool()")
    for k in ("tuningfork", "echobell", "grandchord"):
        chk(f"relic {k} in canon pool", k in pool, "not in pool")
    page.evaluate("window.__test.setChar(0)"); time.sleep(0.2)
    pool0 = page.evaluate("window.__test.relicPool()")
    chk("canon relics hidden for other chars",
        not any(k in pool0 for k in ("tuningfork", "echobell", "grandchord")),
        str([k for k in ("tuningfork", "echobell", "grandchord") if k in pool0]))
    page.evaluate("window.__test.setChar(7)"); time.sleep(0.2)

    # ―― 9) 大和音の譜: 倍率が ×3 → ×4 → ×5 に底上げ ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('grandchord')"); time.sleep(0.2)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    do_act(page, "atk", 3, 0); do_act(page, "def", 3, 2)
    hg = do_act(page, "heal", 5, 4)
    chk("grandchord: ladder starts at 2 (+0.5)", hg == [2, 2.5, 3], str(hg))
    time.sleep(1.6)

    # ―― 10) 余韻の鈴: 1ターンに1回だけ外しを救済する ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('echobell')"); time.sleep(0.2)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    do_act(page, "atk", 5, 0)                        # 外し → 鈴が救済して的中扱い
    chk("echobell saves the first miss", ci(page)["resoHit"][0] == 1.5, str(ci(page)["resoHit"]))
    do_act(page, "def", 5, 2)                        # 2度目の外しは救済されない
    chk("echobell works once per turn", ci(page)["resoHit"][1] == 0, str(ci(page)["resoHit"]))
    chk("echobell: the saved miss did not reset the ladder, the real miss did", ci(page)["reso"] == 0, str(ci(page)["reso"]))
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    do_act(page, "heal", 5, 4)
    time.sleep(1.6)
    if st(page)["status"] != "battle": fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    ladder0 = ci(page)["reso"]
    do_act(page, "atk", 5, 0)                        # 次のターンは鈴が復活している
    chk("echobell recharges next turn", ci(page)["resoHit"][0] > 0, str(ci(page)["resoHit"]))
    time.sleep(0.2)

    # ―― 11) 調律の音叉: お題が3〜6に狭まる ――
    fresh_battle(page)
    page.evaluate("window.__test.giveRelic('tuningfork')"); time.sleep(0.2)
    page.evaluate("window.__test.rigReso(null)"); time.sleep(0.1)
    page.evaluate("window.__test.resolve()"); time.sleep(1.2)
    seen2 = roll_quotas(page, 16)
    chk("tuningfork: quota in 3..6", all(3 <= v <= 6 for v in seen2), str(sorted(seen2)))

    # ―― 12) 中断セーブ往復でお題と達成状況が復元される ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([4,2,3])"); time.sleep(0.1)
    do_act(page, "atk", 4, 0)
    q_before, hit_before = ci(page)["resoQuota"], ci(page)["resoHit"]
    page.evaluate("window.__test.suspend()"); time.sleep(0.8)
    sv = page.evaluate("window.__test.saveData(7)")
    chk("save keeps the quota", sv and sv.get("tv", {}).get("resoQuota") == q_before, str(sv.get("tv", {}).get("resoQuota") if sv else None))
    page.evaluate("window.__test.resumeSave(7)"); time.sleep(1.0)
    chk("resume restores the quota", ci(page)["resoQuota"] == q_before, f"{ci(page)['resoQuota']} vs {q_before}")
    chk("resume restores the hits", ci(page)["resoHit"] == hit_before, f"{ci(page)['resoHit']} vs {hit_before}")

    # ―― 13) 調律: お題ぶんだけ切り取る／足りない塊は使えない／攻防回は出ない ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    # 3つ目を先頭へ持ってきて1手目に調律を使う
    page.evaluate("window.__test.setAct('heal')"); time.sleep(0.15)
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    make_group(page, run_of(2, 5)); time.sleep(0.15)          # 切り取り3に対して2個 = 足りない
    used0 = st(page)["used"]
    page.evaluate("window.__test.commit(30)"); time.sleep(0.4)
    chk("調律: too-small group is rejected (action not spent)", st(page)["used"] == used0, f"{st(page)['used']} vs {used0}")
    # 最下段に6個の塊を作る。切り取った穴は上（市松の2/3）から落ちてくるので、
    # 最下段に残る色1の数＝「切り取らずに残った数」を決定的に数えられる
    make_group(page, run_of(6, 5)); time.sleep(0.15)
    page.evaluate("window.__test.setAct('heal')")
    hits = page.evaluate("(() => { window.__test.commit(30); return window.__test.charInfo().resoHit; })()")
    time.sleep(0.6)
    tv1 = st(page)["tv"]
    chk("調律: fulfils the quota (x1.5 on a fresh ladder)", hits[0] == 1.5, str(hits))
    chk("調律: produces no atk/def/heal", tv1["atk"] == 0 and tv1["def"] == 0 and tv1["heal"] == 0, str({k: tv1[k] for k in ("atk", "def", "heal")}))
    left = sum(1 for c in st(page)["board"][30:36] if c["t"] == 1)
    chk("調律: cuts exactly the chosen count and leaves the rest", left == 3, f"left={left} (expected 6-3)")

    # ―― 14) 調律の切り取り数はボタンのタップで 1→2→3→4 と循環し、お題とズラすこともできる ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    page.evaluate("window.__test.setTuneN(1)"); time.sleep(0.1)
    seq = []
    for _ in range(5):
        seq.append(ci(page)["tuneN"])
        page.evaluate("""(() => { const b = [...document.querySelectorAll('button')].find(x => /調律/.test(x.textContent)); if (b) b.click(); })()""")
        time.sleep(0.25)
    chk("調律: tapping cycles 1→2→3→4→1", seq == [1, 2, 3, 4, 1], str(seq))
    # お題3に対して切り取り2 = わざと外して盤面だけ整える
    page.evaluate("window.__test.setTuneN(2)"); time.sleep(0.1)
    make_group(page, run_of(6, 5)); time.sleep(0.15)
    page.evaluate("window.__test.setAct('heal')")
    hits2 = page.evaluate("(() => { window.__test.commit(30); return window.__test.charInfo().resoHit; })()")
    time.sleep(0.6)
    chk("調律: a deliberate mismatch does not fulfil the quota", hits2[0] == 0, str(hits2))
    chk("調律: a deliberate mismatch also resets the ladder", ci(page)["reso"] == 0, str(ci(page)["reso"]))
    left2 = sum(1 for c in st(page)["board"][30:36] if c["t"] == 1)
    chk("調律: a mismatch still cuts the chosen count", left2 == 4, f"left={left2} (expected 6-2)")

    # ―― 15) はしごは 1.5,2,2.5 / 3,3.5,4 とターンをまたいで伸び、×4で頭打ち ――
    fresh_battle(page)
    page.evaluate("window.__test.rigReso([3,3,3])"); time.sleep(0.1)
    page.evaluate("window.__test.setTuneN(3)"); time.sleep(0.1)
    got = []
    for _ in range(3):                                   # 3ターン×3手=9回ぶん見る
        do_act(page, "atk", 3, 0); got.append(ci(page)["resoHit"][0])
        do_act(page, "def", 3, 2); got.append(ci(page)["resoHit"][1])
        h = do_act(page, "heal", 5, 4); got.append(h[2])  # 3手目=調律（切り取り3=お題3）
        time.sleep(1.6)
        if st(page)["status"] != "battle": break
    chk("ladder climbs 1.5,2,2.5 / 3,3.5,4 across turns and caps at 4",
        got[:9] == [1.5, 2, 2.5, 3, 3.5, 4, 4, 4, 4], str(got))
    notes.append("はしご実測: " + " → ".join(str(v) for v in got))

    chk("no page errors", not errors, str(errors[:3]))
    b.close()

print("\n".join(["", "― メモ ―"] + notes) if notes else "")
print(f"\n{'ALL PASS' if not fails else 'FAIL: ' + ', '.join(fails)}  ({len(fails)} failed)")
sys.exit(1 if fails else 0)
