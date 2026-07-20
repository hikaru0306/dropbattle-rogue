# -*- coding: utf-8 -*-
import time
from playwright.sync_api import sync_playwright
EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\655ffa77-2d1b-427e-9090-1795fb6dd0f7\scratchpad"
ALL="slime wolf spore treant turtle vamp demon owl snail raiju mummy djinn behemot mare noct kaos drake".split()
GROUPS=[(f"u{i//3+1}", ALL[i:i+3]) for i in range(0,len(ALL),3)]
errors=[]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=EXE)
    page=b.new_page(viewport={"width":420,"height":900})
    page.on("console", lambda m: errors.append(m.text) if m.type=="error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL); page.wait_for_selector("text=冒険に出る",timeout=15000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    t0=time.time()
    while time.time()-t0<15:
        s=page.evaluate("window.__test.state()")
        if s["status"]=="map": break
        time.sleep(0.25)
    page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    t0=time.time()
    while time.time()-t0<15:
        s=page.evaluate("window.__test.state()")
        if s["status"]=="battle": break
        time.sleep(0.25)
    for label,kinds in GROUPS:
        page.evaluate(f"window.__test.spawn({kinds!r})"); time.sleep(0.5)
        page.screenshot(path=SHOT+rf"\shot_u_{label}.png")
    b.close()
print("groups:",len(GROUPS),"errors:", errors if errors else "none")
