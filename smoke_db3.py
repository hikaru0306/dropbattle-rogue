# -*- coding: utf-8 -*-
"""行動パターン検証: 毎ターン攻撃/2連撃/2ターンため→大技/お邪魔変換/仲間回復/貫通ドロップ"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\Downloads\dropbattle-rogue"

def st(p): return p.evaluate("window.__test.state()")
def resolve(p, wait=3.2):
    p.evaluate("window.__test.resolve()")
    time.sleep(wait)

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    time.sleep(0.5)
    s = st(page)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    assert st(page)["status"] == "battle"

    # 1) シェイド: お邪魔変換 → 翌ターン攻撃
    page.evaluate("window.__test.spawn(['shade'])")
    time.sleep(0.4)
    resolve(page)
    s = st(page)
    assert s["junk"] >= 3, f"jam failed junk={s['junk']}"
    assert s["php"] == 300, f"jam should not damage php={s['php']}"
    print("P1 shade jam OK junk:", s["junk"])
    hp0 = s["php"]
    resolve(page)
    s = st(page)
    assert s["php"] < hp0, "shade attack turn failed"
    print("P2 shade attack OK php:", s["php"])

    # 2) ゴーレム: 2ターンため → 大技 (30*3.2=96)
    page.evaluate("window.__test.spawn(['golem'])")
    time.sleep(0.4)
    hp0 = st(page)["php"]
    resolve(page)
    assert st(page)["php"] == hp0, "golem charge1 should not damage"
    resolve(page)
    assert st(page)["php"] == hp0, "golem charge2 should not damage"
    print("P3 golem charge x2 OK (no damage)")
    resolve(page)
    s = st(page)
    assert hp0 - s["php"] == 72, f"golem bigatk expected 72 (bigMul cap 2.4, v47), got {hp0-s['php']}"
    print("P4 golem bigatk OK dmg:", hp0 - s["php"])

    # 3) コウモリ: 2連撃 (18x2=36)
    page.evaluate("window.__test.spawn(['bat'])")
    time.sleep(0.4)
    hp0 = st(page)["php"]
    resolve(page)
    s = st(page)
    assert hp0 - s["php"] == 36, f"bat double expected 36, got {hp0-s['php']}"
    print("P5 bat double OK dmg:", hp0 - s["php"])

    # 4) スポア: 仲間回復
    page.evaluate("window.__test.spawn(['spore','slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.hurtEnemies()")
    time.sleep(0.3)
    s0 = st(page)
    slime_hp0 = s0["enemies"][1]["hp"]
    resolve(page, 3.6)
    s = st(page)
    assert s["enemies"][1]["hp"] > slime_hp0, f"spore heal failed {slime_hp0}->{s['enemies'][1]['hp']}"
    print("P6 spore heal ally OK:", slime_hp0, "->", s["enemies"][1]["hp"])

    # 5) 攻撃は単体のみ（貫通なし）
    page.evaluate("window.__test.spawn(['slime','slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.addAtk(500)")
    resolve(page, 3.6)
    s = st(page)
    alive = [e for e in s["enemies"] if e["alive"]]
    assert len(alive) == 1 and alive[0]["hp"] == 130, f"non-pierce leak: {s['enemies']}"
    print("P7 single-target attack OK (2nd enemy untouched)")

    # 6) 貫通ドロップ効果で貫通
    page.evaluate("window.__test.spawn(['slime','slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.addAtk(500)")
    page.evaluate("window.__test.setPierce(true)")
    resolve(page, 8.0)
    s = st(page)
    assert s["status"] == "reward", f"pierce kill-all failed: {s['status']} {s['enemies']}"
    print("P8 pierce carries to 2nd enemy OK -> reward")
    page.click("css=[class*=pop-in] button >> nth=0")
    time.sleep(0.5)

    # 見た目スクショ（画像スプライト+インテント表示）
    s = st(page)
    nid = s["selectable"][0]
    page.evaluate(f"window.__test.enter({nid})")
    time.sleep(0.6)
    if st(page)["status"] == "battle":
        page.evaluate("window.__test.spawn(['golem','spore','slime'])")
        time.sleep(1.2)
        page.screenshot(path=SHOT + r"\v2_battle.png")
        print("P9 battle screenshot saved")
    b.close()

if errors:
    print("ERRORS:")
    for e in errors[:10]:
        print(" -", e)
    sys.exit(1)
print("ALL PATTERN TESTS OK")
