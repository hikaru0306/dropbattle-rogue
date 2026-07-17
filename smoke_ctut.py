# -*- coding: utf-8 -*-
# キャラスキルチュートリアル(ctut)の検証
#  1) イリス(recolor): btn→cycle1→cycle2→paint(対象指定)→done。対象外タップ不可・塗りで完了フラグ
#  2) ガレス(buff): btn→toggle→clear→done
#  3) ブロム(smith): btn→mode1→mode2→mode3→clear→done（モード循環が一周して補充に戻る）
#  4) ルクス(healx): infoカード→閉じて完了フラグ
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"

fails = []
def chk(name, cond, extra=""):
    print(("OK  " if cond else "NG  ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

def st(p): return p.evaluate("window.__test.state()")
def ct(p): return p.evaluate("window.__test.ctut()")

def click_skill_btn(p):
    # 3つ目ボタン（色変え/強化/蓄積/鍛冶タイトルを持つボタン）をDOMクリック
    p.evaluate("""(() => {
      const b = [...document.querySelectorAll('button')].find(x => /色変え|強化→|蓄積→|補充|生成|強化＋/.test(x.textContent));
      if (b) b.click();
    })()""")
    time.sleep(0.3)

def start_battle_as(p, tile):
    p.evaluate("window.__test.restart()"); time.sleep(0.3)
    p.evaluate(f"window.__test.setChar({tile})")
    p.evaluate("window.__test.restart()"); time.sleep(0.3)
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); time.sleep(0.4)
    page.click("text=この仲間と冒険に出る"); time.sleep(0.6)

    # ―― 1) イリス（色変え） ――
    start_battle_as(page, 1)
    page.evaluate("window.__test.startCtut('recolor')"); time.sleep(0.3)
    chk("recolor step=btn", ct(page)["step"] == "btn")
    # btn誘導中は盤面タップ不可（commitバックドアもゲート）
    tv0 = st(page)["tv"]
    page.evaluate("window.__test.commit(14)"); time.sleep(0.4)
    chk("board locked during btn step", st(page)["tv"] == tv0)
    click_skill_btn(page)
    chk("-> cycle1", ct(page)["step"] == "cycle1")
    ink0 = page.evaluate("window.__test.charInfo()")["paint"]
    click_skill_btn(page)
    chk("-> cycle2 (ink changed)", ct(page)["step"] == "cycle2" and page.evaluate("window.__test.charInfo()")["paint"] != ink0)
    click_skill_btn(page)
    c = ct(page)
    chk("-> paint with seed", c["step"] == "paint" and c.get("seed") is not None, str(c))
    seed = c["seed"]
    # 対象グループ外はタップ不可
    s = st(page)
    grp = set(page.evaluate(f"window.__test.groupIdxs({seed})"))
    outside = next(i for i in range(36) if i not in grp)
    board0 = [x["t"] for x in s["board"]]
    page.evaluate(f"window.__test.commit({outside})"); time.sleep(0.4)
    chk("outside tap blocked", [x["t"] for x in st(page)["board"]] == board0)
    # 対象を塗る → done
    ink = page.evaluate("window.__test.charInfo()")["paint"]
    page.evaluate(f"window.__test.commit({seed})"); time.sleep(0.4)
    chk("-> finwait after paint (1秒見せる)", ct(page)["step"] == "finwait", str(ct(page)))
    time.sleep(1.4)
    chk("-> done after paint", ct(page)["step"] == "done")
    painted = st(page)["board"]
    chk("group painted to ink", all(painted[i]["t"] == ink for i in grp), str([painted[i]["t"] for i in grp]))
    chk("flag saved", page.evaluate("localStorage.getItem('db_ctut_recolor')") == "1")
    page.click("text=たたかいを続ける"); time.sleep(0.3)
    chk("ctut closed", ct(page) is None)

    # ―― 2) ガレス（強化） ――
    start_battle_as(page, 2)
    page.evaluate("window.__test.startCtut('buff')"); time.sleep(0.3)
    click_skill_btn(page)
    chk("buff -> toggle", ct(page)["step"] == "toggle")
    tgt0 = page.evaluate("window.__test.charInfo()")["target"]
    click_skill_btn(page)
    c = ct(page)
    chk("buff -> clear (target toggled)", c["step"] == "clear" and page.evaluate("window.__test.charInfo()")["target"] != tgt0, str(c))
    page.evaluate(f"window.__test.commit({c['seed']})"); time.sleep(0.6)
    chk("buff -> done", ct(page)["step"] == "done")
    chk("buff flag", page.evaluate("localStorage.getItem('db_ctut_buff')") == "1")
    page.click("text=たたかいを続ける"); time.sleep(0.3)

    # ―― 3) ブロム（鍛冶）: 補充→生成切替 → 素材+3プレゼントカード → 受け取る(粒子演出) → 生成 ――
    start_battle_as(page, 5)
    page.evaluate("window.__test.startCtut('smith')"); time.sleep(0.3)
    click_skill_btn(page)   # 選択
    chk("smith -> mode1", ct(page)["step"] == "mode1")
    stock0 = page.evaluate("window.__test.charInfo()")["stock"]
    click_skill_btn(page)   # stock->gen 切替 → プレゼントカード(gift)
    ci5 = page.evaluate("window.__test.charInfo()")
    chk("smith -> gift card (genモード・素材まだ増えない)", ct(page)["step"] == "gift" and ci5["stock"] == stock0 and ci5["smithMode"] == "gen", str(ci5))
    chk("gift card text", "素材を3個追加するね" in page.evaluate("document.body.innerText"))
    page.click("text=受け取る"); time.sleep(0.3)
    chk("gift -> giftfx", ct(page)["step"] == "giftfx")
    time.sleep(2.4)          # 粒子演出＋カウントアップ後、自動でclearへ
    c = ct(page)
    ci5b = page.evaluate("window.__test.charInfo()")
    chk("giftfx -> clear (+3素材)", c["step"] == "clear" and c.get("seed") is not None and ci5b["stock"] == stock0 + 3, f"{c} stock={ci5b['stock']}")
    grp = page.evaluate(f"window.__test.groupIdxs({c['seed']})")
    chk("seed group >= 3", len(grp) >= 3, str(len(grp)))
    page.evaluate(f"window.__test.commit({c['seed']})"); time.sleep(0.4)
    chk("smith -> finwait (生成を1秒見せる)", ct(page)["step"] == "finwait", str(ct(page)))
    time.sleep(1.4)
    ci6 = page.evaluate("window.__test.charInfo()")
    sp_in_grp = page.evaluate("(idxs => { const s = window.__test.state(); return idxs.filter(i => s.board[i].sp).length; })(" + str(grp) + ")")
    chk("smith -> done (生成済み・素材消費)", ct(page)["step"] == "done" and sp_in_grp > 0 and ci6["stock"] < ci5b["stock"], f"sp={sp_in_grp} stock={ci6['stock']}")
    chk("smith flag", page.evaluate("localStorage.getItem('db_ctut_smith')") == "1")
    page.click("text=たたかいを続ける"); time.sleep(0.3)

    # ―― 4) セレネ（info） ――
    start_battle_as(page, 4)
    page.evaluate("window.__test.startCtut('healx')"); time.sleep(0.3)
    chk("healx info card", ct(page)["step"] == "info" and "月の司祭セレネ" in page.evaluate("document.body.innerText"))
    page.click("text=了解！"); time.sleep(0.3)
    chk("healx closed + flag", ct(page) is None and page.evaluate("localStorage.getItem('db_ctut_healx')") == "1")

    b.close()

if errors:
    print("PAGE ERRORS:", errors[:3]); sys.exit(1)
print("RESULT: " + ("FAIL " + str(fails) if fails else "PASS"))
sys.exit(1 if fails else 0)
