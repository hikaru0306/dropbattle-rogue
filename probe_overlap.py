# -*- coding: utf-8 -*-
"""ため攻撃(charge)中の敵の頭上に、どのバッジがどの位置で出ているかを列挙する。
「攻撃予告の後ろに何か重なって表示されている」件の特定用。"""
import time
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\81200b0d-3531-47c3-9733-39ea0dda777c\scratchpad"

# 敵エリアにある「絶対配置の小さな枠」を全部、重なり判定つきで拾う
JS = """() => {
  // 攻撃予告バッジ（スプライト上の絶対配置の小枠）を探し、それに重なる要素を列挙する
  const cands = [...document.querySelectorAll('span')].filter(e => {
    const s = getComputedStyle(e); const r = e.getBoundingClientRect();
    return s.position === 'absolute' && r.top > 60 && r.top < 200 && r.width > 20 && r.width < 120 && s.zIndex === '2';
  });
  const badge = cands[0];
  if (!badge) return ['(予告バッジが見つからない)'];
  const b = badge.getBoundingClientRect();
  const hit = [];
  document.querySelectorAll('*').forEach(e => {
    if (e === badge || e.contains(badge) || badge.contains(e)) return;
    const r = e.getBoundingClientRect();
    if (r.width === 0 || r.width > 300) return;
    if (r.left < b.right + 4 && r.right > b.left - 4 && r.top < b.bottom + 4 && r.bottom > b.top - 4) {
      const s = getComputedStyle(e);
      hit.push(e.tagName + ' "' + (e.innerText || e.getAttribute('alt') || e.getAttribute('src') || '').slice(0,26) + '" @x' + Math.round(r.left) + ',y' + Math.round(r.top) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + ' z=' + s.zIndex);
    }
  });
  return ['予告バッジ "' + badge.innerText.trim() + '" @x' + Math.round(b.left) + ',y' + Math.round(b.top) + ' ' + Math.round(b.width) + 'x' + Math.round(b.height), '--- 重なっている要素 ---'].concat(hit);
}"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.9)
    # ため攻撃 + シールド + 激昂 を同時に持たせて、画像と同じ状況を作る
    page.evaluate("window.__test.setPat(0, ['bigatk'])")
    page.evaluate("window.__test.setShd(0, 20)")
    page.evaluate("window.__test.setEnrEvery(0, 1)")
    time.sleep(0.6)
    st = page.evaluate("window.__test.state()")
    print("敵:", [(e["kind"], e["hp"], e["enr"], e["shd"]) for e in st["enemies"]])
    print("intent:", st.get("intents"))
    for row in page.evaluate(JS):
        print("   ", row)
    page.screenshot(path=f"{SHOT}\\overlap.png")
    b.close()
