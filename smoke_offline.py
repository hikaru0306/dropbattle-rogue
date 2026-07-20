# -*- coding: utf-8 -*-
# クラウド遮断スモークテスト:
#   Firebase/gstatic への通信を全ブロックした状態で http 配信し、
#   ゲームが従来どおり動くこと（タイトル表示・フッター・各モーダル）を検証する。
import threading, functools, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
ROOT = r"C:\Users\2000h\Downloads\dropbattle-rogue"
PORT = 8642

Handler = functools.partial(SimpleHTTPRequestHandler, directory=ROOT)
Handler.log_message = lambda *a, **k: None
srv = HTTPServer(("127.0.0.1", PORT), Handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()

errors = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page(viewport={"width": 420, "height": 900})
    # Firebase 関連を全遮断（cloud.js の import 自体を失敗させる）
    page.route("**/*gstatic.com/**", lambda r: r.abort())
    page.route("**/*googleapis.com/**", lambda r: r.abort())
    page.route("**/*firebaseapp.com/**", lambda r: r.abort())
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" and "ERR_FAILED" not in m.text and "Failed to load resource" not in m.text else None)

    # ?fbemu=1 で cloud.js の初期化を強制（configがプレースホルダでも通信を試みさせる）→ 遮断で失敗しても無害なこと
    page.goto(f"http://127.0.0.1:{PORT}/index.html?fbemu=1")
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    print("1 title OK (firebase blocked)")

    assert page.evaluate("typeof window.Cloud") == "undefined", "Cloud should be absent when blocked"
    print("2 Cloud absent OK")

    # フッターのリンクが表示されている
    for t in ["アカウント", "クレジット", "利用規約", "プライバシー"]:
        assert page.locator(f"text={t}").count() >= 1, f"footer link missing: {t}"
    print("3 footer links OK")

    # クレジットモーダル
    page.click("text=クレジット")
    page.wait_for_selector("text=cynicmusic", timeout=5000)
    page.click("text=閉じる")
    print("4 credits modal OK")

    # アカウントモーダル（クラウド不在時は準備中表示）
    page.click("text=アカウント")
    page.wait_for_selector("text=準備中", timeout=5000)
    page.click("text=閉じる")
    print("5 account modal OK")

    # ゲーム開始できること
    page.click("text=冒険に出る")
    page.wait_for_selector("text=この仲間と冒険に出る", timeout=10000)
    print("6 char select OK")

    b.close()
srv.shutdown()

if errors:
    print("ERRORS:")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("ALL OK")
