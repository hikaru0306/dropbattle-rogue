# -*- coding: utf-8 -*-
"""敵を全滅させた直後、敵エリアに残るバッジ類を全部洗い出す（0,0,10 の正体調査）。"""
import time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\81200b0d-3531-47c3-9733-39ea0dda777c\scratchpad"
CHAR = int(sys.argv[1]) if len(sys.argv) > 1 else 0

# 敵エリア(y<300)に出ている短いテキストを、色と位置つきで拾う
JS = """() => [...document.querySelectorAll('*')]
  .filter(e => e.children.length === 0 && e.innerText && e.innerText.trim().length <= 10)
  .map(e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return { t: e.innerText.trim(), x: Math.round(r.left), y: Math.round(r.top),
             bg: getComputedStyle(e.parentElement).backgroundColor, col: s.color }; })
  .filter(o => o.y < 300 && o.y > 60)
  .map(o => `"${o.t}"@x${o.x},y${o.y} col=${o.col} parentBg=${o.bg}`)"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({CHAR})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.9)
    st = page.evaluate("window.__test.state()")
    print("敵:", [(e["kind"], e["hp"], e["enr"], e["shd"], e["dcap"]) for e in st["enemies"]])

    page.evaluate("window.__test.weaken()"); time.sleep(0.2)
    for i, a in enumerate(["heal", "atk", "def"]):
        page.evaluate(f"window.__test.setAct('{a}')"); page.evaluate(f"window.__test.commit({i})"); time.sleep(0.5)

    prev = None
    for i in range(20):
        time.sleep(0.3)
        rows = page.evaluate(JS)
        st = page.evaluate("window.__test.state()")
        line = f"status={st['status']} alive={[e['kind'] for e in st['enemies'] if e['alive']]}\n    " + "\n    ".join(rows)
        if line != prev:
            print(f"--- t+{0.3*(i+1):.1f}s {line}")
            prev = line
        page.screenshot(path=f"{SHOT}\\badge_{i:02d}.png")
    b.close()
