# -*- coding: utf-8 -*-
"""消し方レリック検証: 爆心の石(3x3) / 十字晶 / 紅蓮の核 / 雷の爆破巻き込み発動"""
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1&fast=1"

def st(p): return p.evaluate("window.__test.state()")

def fill_board(p, base_type=1):
    """盤面を全て base_type で埋める（特殊なし）"""
    for i in range(36):
        p.evaluate(f"window.__test.setCellType({i}, {base_type})")

def enter_battle(p):
    s = st(p)
    p.evaluate(f"window.__test.enter({s['selectable'][0]})")
    time.sleep(0.8)
    p.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.3)

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width":420,"height":900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る")
    time.sleep(0.5)
    enter_battle(page)

    # 1) 爆心の石: 単発消しで3x3=9個
    page.evaluate("window.__test.giveRelic('blastcore')")
    fill_board(page)
    page.evaluate("window.__test.setCellType(14, 0)")  # r2c2 に孤立赤
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["atk"] == 90, f"blastcore 3x3: atk {s['tv']['atk']} != 90"
    print("K1 blastcore 3x3 -> atk90 OK")

    # 1b) 同一ターン2回目の単発消しは爆破しない（1ターン1回制限）
    fill_board(page)
    page.evaluate("window.__test.setCellType(21, 0)")
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(21)")
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["def"] == 10, f"blast once/turn: def {s['tv']['def']} != 10"
    print("K1b blastcore limited to once per turn OK")

    # 2) 十字晶: ちょうど4個消しで十字1列（4 + 行残2 + 列残5 = 11個）
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.restart()")
    time.sleep(0.8)
    if st(page)["status"] != "map":
        page.click("text=冒険に出る"); time.sleep(0.5)
    enter_battle(page)
    page.evaluate("window.__test.giveRelic('crossgem')")
    fill_board(page)
    for i in (0, 1, 2, 3):
        page.evaluate(f"window.__test.setCellType({i}, 0)")
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('def')")
    page.evaluate("window.__test.commit(0)")
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["def"] == 110, f"crossgem: def {s['tv']['def']} != 110"
    print("K2 crossgem 4-clear -> 11 cells def110 OK")

    # 3) 紅蓮の核: 赤2連結消し → 各赤の上下4個も爆破 = 6個（3アクション目でターン解決しないよう新バトルで）
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.restart()")
    time.sleep(0.8)
    if st(page)["status"] != "map":
        page.click("text=冒険に出る"); time.sleep(0.5)
    enter_battle(page)
    page.evaluate("window.__test.giveRelic('redcore')")
    fill_board(page)
    page.evaluate("window.__test.setCellType(14, 0)")
    page.evaluate("window.__test.setCellType(15, 0)")
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('heal')")
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["heal"] == 6, f"redcore: heal {s['tv']['heal']} != 6"
    print("K3 redcore red2 -> 6 cells heal6 OK")

    # 4) 雷の爆破巻き込み: 単発赤の3x3爆破が雷(黄)を巻き込み → 黄が全消し
    page.evaluate("window.__test.restart()")
    time.sleep(0.8)
    if st(page)["status"] != "map":
        page.click("text=冒険に出る"); time.sleep(0.5)
    enter_battle(page)
    page.evaluate("window.__test.giveRelic('blastcore')")
    fill_board(page)  # 全部黄(1)
    page.evaluate("window.__test.setCellType(14, 0)")   # 孤立赤
    page.evaluate("window.__test.setCellSpecial(13, 'bolt')")  # 隣の黄に雷
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(14)")
    time.sleep(0.8)
    s = st(page)
    # 赤1 + 黄35(雷で全消し) = 36個
    assert s["tv"]["atk"] == 360, f"bolt-in-blast: atk {s['tv']['atk']} != 360"
    print("K4 bolt swept by blast fires -> full board atk360 OK")

    # 5) 雷は6個未満の消去では発動しない
    page.evaluate("window.__test.spawn(['slime'])")
    time.sleep(0.4)
    page.evaluate("window.__test.restart()")
    time.sleep(0.8)
    if st(page)["status"] != "map":
        page.click("text=冒険に出る"); time.sleep(0.5)
    enter_battle(page)
    fill_board(page)  # 全部黄(1)
    for i in (0, 1, 2):
        page.evaluate(f"window.__test.setCellType({i}, 0)")
    for i in (14, 20, 30):
        page.evaluate(f"window.__test.setCellType({i}, 0)")  # 非隣接の赤
    page.evaluate("window.__test.setCellSpecial(1, 'bolt')")
    time.sleep(0.3)
    page.evaluate("window.__test.setAct('atk')")
    page.evaluate("window.__test.commit(0)")
    time.sleep(0.6)
    s = st(page)
    assert s["tv"]["atk"] == 30, f"bolt under 6: atk {s['tv']['atk']} != 30"
    print("K5 bolt inert under 6-clear OK")

    assert not errors, errors
    print("ALL CLEAR-RELIC TESTS OK")
    b.close()
