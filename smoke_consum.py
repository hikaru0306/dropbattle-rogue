# -*- coding: utf-8 -*-
import time
from playwright.sync_api import sync_playwright
EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
SHOT = r"C:\Users\2000h\AppData\Local\Temp\claude\C--Users-2000h\5fa01898-a7fd-44b5-bb24-da1f2a31a8a1\scratchpad"
errs=[]
def st(page): return page.evaluate("window.__test.state()")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width":420,"height":900})
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=20000)
    page.click("text=冒険に出る"); page.click("text=この仲間と冒険に出る")
    t0=time.time()
    while time.time()-t0<20:
        if st(page)["status"]=="map": break
        time.sleep(0.2)
    while page.evaluate('!!document.querySelector("[data-actintro]")'): time.sleep(0.05)
    s=st(page); page.evaluate(f"window.__test.enter({s['selectable'][0]})")
    t0=time.time()
    while time.time()-t0<20:
        if st(page)["status"]=="battle": break
        time.sleep(0.2)
    # 空の状態
    page.click("[aria-label=メニュー]"); time.sleep(0.4)
    page.click("text=所持アイテム確認"); time.sleep(0.4)
    assert "アイテムを持っていない" in page.inner_text("body"), "empty state missing"
    page.screenshot(path=SHOT+r"\consum_empty.png")
    print("1 空の状態 OK")
    page.click("text=閉じる"); time.sleep(0.3)
    # アイテムを3個渡す
    for k in ["potion","bomb","stun"]:
        page.evaluate("window.__test.giveItem('%s')" % k)
    time.sleep(0.4)
    page.click("[aria-label=メニュー]"); time.sleep(0.4)
    page.click("text=所持アイテム確認"); time.sleep(0.4)
    page.screenshot(path=SHOT+r"\consum_list.png")
    n = page.locator("button:text-is('捨てる')").count()
    assert n == 3, "捨てるボタンが3つない: %d" % n
    print("2 一覧3件 OK")
    # 1回目のタップでは消えない（確認待ち）
    page.locator("button:text-is('捨てる')").first.click(); time.sleep(0.3)
    assert page.evaluate("window.__test.state().items.length") == 3, "1タップで消えてしまった"
    assert page.locator("button:text-is('本当に捨てる？')").count() == 1, "確認表示が出ていない"
    page.screenshot(path=SHOT+r"\consum_armed.png")
    print("3 1タップ目は確認のみ OK")
    # 2回目で削除
    page.locator("button:text-is('本当に捨てる？')").click(); time.sleep(0.4)
    items = page.evaluate("window.__test.state().items")
    assert len(items) == 2 and "potion" not in items, "捨てられていない: %s" % items
    print("4 2タップ目で削除 OK:", items)
    # 3秒放置で確認解除
    page.locator("button:text-is('捨てる')").first.click(); time.sleep(3.4)
    assert page.locator("button:text-is('本当に捨てる？')").count() == 0, "確認が自動解除されない"
    assert len(page.evaluate("window.__test.state().items")) == 2, "放置で消えた"
    print("5 3秒で確認解除 OK")
    print("errors:", errs)
    b.close()
print("ALL CONSUM OK")
