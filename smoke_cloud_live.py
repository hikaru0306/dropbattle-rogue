# -*- coding: utf-8 -*-
# 本番Firebase(dropsia)に対する実同期スモークテスト:
#   匿名ログイン → ローカルデータをクラウドへpush → 別コンテキストでリストアを検証
import threading, functools, time, json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
ROOT = r"C:\Users\2000h\Downloads\dropbattle-rogue"
PORT = 8643

Handler = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
Handler.log_message = lambda *a, **k: None
srv = HTTPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

URL = f"http://127.0.0.1:{PORT}/index.html"
CHARS = {"u": [0, 1], "c": [0], "cu": []}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)

    # --- ctx1: ローカルにデータがある状態で起動 → 匿名ログイン+push ---
    ctx1 = b.new_context(viewport={"width": 420, "height": 900})
    pg = ctx1.new_page()
    pg.goto(URL)
    pg.evaluate(f"localStorage.setItem('db_chars', JSON.stringify({json.dumps(CHARS)}))")
    pg.reload()
    pg.wait_for_selector("text=冒険に出る", timeout=15000)
    st = None
    for _ in range(40):  # 最大20秒待って synced を確認
        st = pg.evaluate("window.Cloud ? Cloud.state : null")
        if st and st.get("status") == "synced" and st.get("lastSync"):
            break
        time.sleep(0.5)
    assert st, "Cloud not initialized"
    assert st["status"] == "synced", f"not synced: {st}"
    assert st["uid"], "no uid"
    uid = st["uid"]
    print("1 anon sign-in + push OK uid:", uid[:8] + "...", "lastSync:", st["lastSync"])

    # バッジ表示確認
    assert pg.locator("text=同期済み").count() >= 1, "sync badge missing"
    print("2 badge OK")
    ctx1.close()

    # --- ctx2: 同じ匿名uidは再現できないため、リストアは同一コンテキスト内の
    #     localStorage消去で検証（IndexedDBの認証は残る）---
    ctx2 = b.new_context(viewport={"width": 420, "height": 900})
    pg2 = ctx2.new_page()
    pg2.goto(URL)
    pg2.wait_for_selector("text=冒険に出る", timeout=15000)
    for _ in range(40):
        st2 = pg2.evaluate("window.Cloud ? Cloud.state : null")
        if st2 and st2.get("status") in ("synced", "offline"):
            break
        time.sleep(0.5)
    # 新しい匿名ユーザーなのでリモートは空 → synced(空push無し)想定
    assert st2 and st2["status"] == "synced", f"ctx2 not synced: {st2}"
    assert st2["uid"] != uid, "uid should differ in fresh context"
    print("3 fresh context = new anon user OK")

    # localStorageにクラウドの中身を消してリロード → IndexedDB認証で同一uid復帰+リストア
    pg2.evaluate(f"localStorage.setItem('db_chars', JSON.stringify({json.dumps(CHARS)}))")
    pg2.evaluate("localStorage.setItem('db_cloud_dirty','1')")
    pg2.reload()
    pg2.wait_for_selector("text=冒険に出る", timeout=15000)
    for _ in range(40):
        st3 = pg2.evaluate("window.Cloud ? Cloud.state : null")
        if st3 and st3.get("status") == "synced" and st3.get("lastSync"):
            break
        time.sleep(0.5)
    assert st3["status"] == "synced", f"push after dirty failed: {st3}"
    uid2 = st3["uid"]
    # localStorage の db_* を全消去してリロード → クラウドから自動リストアされるはず
    pg2.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('db_')).forEach(k=>localStorage.removeItem(k))")
    pg2.reload()
    time.sleep(6)  # リストア時は reload が走る
    pg2.wait_for_selector("text=冒険に出る", timeout=15000)
    restored = pg2.evaluate("JSON.parse(localStorage.getItem('db_chars')||'null')")
    assert restored and restored.get("u") == CHARS["u"], f"restore failed: {restored}"
    print("4 cloud restore OK (uid:", uid2[:8] + "...) chars:", restored)

    ctx2.close()
    b.close()
srv.shutdown()
print("ALL OK")
