# -*- coding: utf-8 -*-
"""作り直した全敵を実機バトル画面でスクショ確認（エラー監視込み）"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\655ffa77-2d1b-427e-9090-1795fb6dd0f7\scratchpad"

ALL = "skel imp kslime ifrita vamp reaper gazer kaos mant eel bat golem spore mandra gargo dragon boar pixie toad mudman knight thorn yeti fgolem djinn mummy raiju ghoul bonek wolf mare drake demon ifrit lich wraith alraune fenrir titania skadi jotun behemot bdragon noct demonx".split()
GROUPS = [(f"a{i//3+1}", ALL[i:i+3]) for i in range(0, len(ALL), 3)]

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    t0 = time.time()
    while time.time() - t0 < 15:
        s = page.evaluate("window.__test.state()")
        if s["status"] == "map": break
        time.sleep(0.25)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    t0 = time.time()
    while time.time() - t0 < 15:
        s = page.evaluate("window.__test.state()")
        if s["status"] == "battle": break
        time.sleep(0.25)
    for label, kinds in GROUPS:
        page.evaluate(f"window.__test.spawn({kinds!r})")
        time.sleep(0.5)
        page.screenshot(path=SHOT + rf"\shot_all_{label}.png")
    print("groups:", len(GROUPS))
    b.close()
print("errors:", errors if errors else "none")
print("DONE")
