# -*- coding: utf-8 -*-
"""ノアの蓄積が「消した瞬間」ではなく「ターン解決の攻撃直前」に攻防へ乗ることを確認する。
ガレスの強化(buffPend)と同じ挙動になっているかを見る。
"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
NOA = 3  # CHARS: 0=アルド 1=イリス 2=ガレス 3=ノア

errors = []
def st(p): return p.evaluate("window.__test.state()")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({NOA})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.3)  # 高HPで撃破を避ける

    # 蓄積アクションでドロップを消す
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(0)"); time.sleep(0.6)
    s = st(page)
    tv = s["tv"]
    print("蓄積を消した直後: atk=%s def=%s storePend=%s" % (tv["atk"], tv["def"], tv.get("storePend")))
    assert tv.get("storePend"), "蓄積は予約(storePend)されているはず"
    add = tv["storePend"]["add"]
    # 蓄積は攻防の両方に乗る仕様。乗っていれば atk も増えるので atk で判定する
    assert tv["atk"] == 0, "この時点ではまだ攻撃に乗らないはず"
    def_before = tv["def"]

    # 攻撃を積んでからターン解決 → 蓄積が攻防に乗る
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(1)"); time.sleep(0.6)
    before = st(page)["tv"]
    print("攻撃を積んだ後: atk=%s def=%s" % (before["atk"], before["def"]))
    assert before["storePend"], "解決前はまだ予約のまま"

    page.evaluate("window.__test.resolve()"); time.sleep(0.35)
    mid = st(page)["tv"]   # 解決の攻撃直前＝ここで初めて蓄積が乗る
    print("解決直後: atk=%s def=%s storePend=%s" % (mid["atk"], mid["def"], mid.get("storePend")))
    assert mid["atk"] == before["atk"] + add, "攻撃に蓄積が乗るはず"
    assert mid["def"] == before["def"] + add, "防御にも蓄積が乗るはず"
    time.sleep(2.5)
    after = st(page)["tv"]
    print("ターン解決後(次ターン): atk=%s def=%s storePend=%s" % (after["atk"], after["def"], after.get("storePend")))
    assert not after.get("storePend"), "解決で予約は消えるはず"
    print("蓄積量:", add)
    print("errors:", errors)
    assert not errors, errors
    b.close()
print("ALL STOREPEND OK")
