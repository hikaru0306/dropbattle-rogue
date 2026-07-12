# -*- coding: utf-8 -*-
import sys, time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\1d09642f-34d3-42f6-b80d-62863c94dfb6\scratchpad"

def st(p): return p.evaluate("window.__test.state()")
def wait_status(page, want, timeout=25):
    t0=time.time()
    while time.time()-t0<timeout:
        s=st(page)
        if s["status"]==want: return s
        time.sleep(0.25)
    raise SystemExit(f"TIMEOUT status={want} now={st(page)['status']}")

def goto_type(page, typ):
    """マップを再生成しながら typ ノードを探して直前に立つ"""
    for attempt in range(12):
        s = st(page)
        nodes = {n["id"]: n for n in s["map"]}
        cands = [n for n in s["map"] if n["type"] == typ]
        for n in cands:
            eds = [e for e in s["edges"] if e["to"] == n["id"]]
            if eds:
                page.evaluate(f"window.__test.setCur({eds[0]['from']})")
                time.sleep(0.2)
                page.evaluate(f"window.__test.enter({n['id']})")
                return n
        # 無ければリスタートして再生成
        page.evaluate("window.__test.restart()")
        time.sleep(0.5)
    raise SystemExit(f"no {typ} node found")

errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    page=b.new_page(viewport={"width":420,"height":900})
    page.on("console", lambda m: errors.append(m.text) if m.type=="error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る")
    wait_status(page,"map")

    # 群れ戦（3体）
    n=goto_type(page,"horde")
    s=wait_status(page,"battle")
    assert len(s["enemies"])==3, f"horde should be 3, got {s['enemies']}"
    time.sleep(1.2)
    page.screenshot(path=SHOT+r"\s7_horde.png")
    print("H1 horde 3 enemies OK:", [e["kind"] for e in s["enemies"]])
    page.evaluate("window.__test.weaken()")
    page.evaluate("window.__test.setPierce(true)")
    for i in range(3):
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.7)
    s=wait_status(page,"reward")
    print("H2 horde win OK")
    page.click("css=[class*=pop-in] button >> nth=0")
    time.sleep(0.6)
    assert st(page)["shop"], "horde shop should open"
    page.evaluate("window.__test.closeShop()")
    wait_status(page,"map")

    # 宝箱
    n=goto_type(page,"treasure")
    s=wait_status(page,"reward")
    page.screenshot(path=SHOT+r"\s8_treasure.png")
    page.click("css=[class*=pop-in] button >> nth=0")
    s=wait_status(page,"map")
    print("T1 treasure OK")

    # 休憩（先にHPを減らすため精鋭で1ターン受ける）
    n=goto_type(page,"elite")
    s=wait_status(page,"battle")
    assert len(s["enemies"])==1
    for _i in range(3):
        page.evaluate("window.__test.resolve()")
        time.sleep(3)
        if st(page)["php"] < 300: break
    hp1=st(page)["php"]
    assert hp1<300, "elite attack failed"
    print("E1 elite hit OK php:", hp1)
    page.evaluate("window.__test.weaken()")
    for i in range(3):
        page.evaluate("window.__test.commit(0)")
        time.sleep(0.7)
    s=wait_status(page,"reward")
    page.click("css=[class*=pop-in] button >> nth=0")
    wait_status(page,"map")
    n=goto_type(page,"rest")
    time.sleep(0.5)
    assert st(page)["campfire"] == "menu", "campfire not open"
    page.evaluate("window.__test.restHeal()")
    time.sleep(0.4)
    hp2=st(page)["php"]
    assert hp2>hp1, f"rest heal failed {hp1}->{hp2}"
    assert not st(page)["shop"], "campfire should not open shop anymore"
    assert st(page)["status"] == "map", "should return to map after rest"
    print("R1 campfire heal (no shop) OK:", hp1,"->",hp2)
    page.screenshot(path=SHOT+r"\s9_rest.png")

    # 敗北フロー（ボスの攻撃を受け続ける）
    s=st(page)
    boss=[x for x in s["map"] if x["type"]=="boss"][0]
    eds=[e for e in s["edges"] if e["to"]==boss["id"]]
    page.evaluate(f"window.__test.setCur({eds[0]['from']})")
    time.sleep(0.2)
    page.evaluate(f"window.__test.enter({boss['id']})")
    wait_status(page,"battle")
    for i in range(10):
        page.evaluate("window.__test.resolve()")
        time.sleep(2.8)
        s=st(page)
        if s["status"]=="lose": break
    assert st(page)["status"]=="lose", f"lose not reached: {st(page)}"
    page.screenshot(path=SHOT+r"\s10_lose.png")
    print("L1 lose OK")

    # 敗北→もう一度
    page.click("text=もう一度")
    s=wait_status(page,"map")
    assert s["php"]==300
    print("L2 restart OK")
    b.close()

if errors:
    print("ERRORS:")
    for e in errors[:10]: print(" -",e)
    sys.exit(1)
print("ALL SMOKE2 OK")
