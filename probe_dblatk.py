# -*- coding: utf-8 -*-
"""プレイヤー攻撃が2回に見える件の調査。
 - .sp-atk-hero 要素の出現回数（アニメ再生回数）
 - 演出テキスト行の内容/DOM要素IDの推移
を高頻度サンプリングする。"""
import time, sys
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
CHAR = int(sys.argv[1]) if len(sys.argv) > 1 else 0

HOOK = """() => {
  window.__dbg = { atk: [], fx: [] };
  const t0 = performance.now();
  // sp-atk-hero の mount を MutationObserver で数える
  new MutationObserver(muts => {
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType === 1) {
          if (n.classList && n.classList.contains('sp-atk-hero'))
            window.__dbg.atk.push(Math.round(performance.now() - t0));
          n.querySelectorAll && n.querySelectorAll('.sp-atk-hero').forEach(() =>
            window.__dbg.atk.push(Math.round(performance.now() - t0)));
        }
      }
      // 演出テキストの文字変化も記録
      if (m.type === 'characterData')
        window.__dbg.fx.push([Math.round(performance.now() - t0), 'text:' + m.target.data]);
    }
  }).observe(document.body, { childList: true, subtree: true, characterData: true });
}"""

SNAP = """() => [...document.querySelectorAll('div')]
  .filter(e => e.style && e.style.animation && e.style.animation.indexOf('fxPop') >= 0)
  .map(e => e.innerText + '@' + Math.round(e.getBoundingClientRect().top))"""

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    page.goto(URL)
    page.wait_for_function("window.__test && window.__test.state", timeout=15000)
    page.evaluate(f"window.__test.setChar({CHAR})")
    page.evaluate("window.__test.restart()"); time.sleep(0.5)
    page.evaluate("window.__test.start()"); time.sleep(0.3)
    s = page.evaluate("window.__test.state()")
    page.evaluate(f"window.__test.enter({s['selectable'][0]})"); time.sleep(0.8)
    page.evaluate("window.__test.spawn(['golem'])"); time.sleep(0.4)
    page.evaluate(HOOK)

    page.evaluate("window.__test.setAct('heal')"); page.evaluate("window.__test.commit(0)"); time.sleep(0.4)
    page.evaluate("window.__test.setAct('def')");  page.evaluate("window.__test.commit(1)"); time.sleep(0.4)
    page.evaluate("window.__test.setAct('atk')");  page.evaluate("window.__test.commit(2)")

    prev = None
    for i in range(60):
        time.sleep(0.1)
        cur = page.evaluate(SNAP)
        if cur != prev:
            print(f"t+{0.1*(i+1):.1f}s  {cur}")
            prev = cur
    d = page.evaluate("window.__dbg")
    print("sp-atk-hero mount 回数:", len(d['atk']), d['atk'])
    print("テキスト差し替え(characterData)件数:", len(d['fx']))
    for row in d['fx']:
        print("   ", row)
    b.close()
