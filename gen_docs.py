# -*- coding: utf-8 -*-
"""ゲームデータ仕様書の自動生成: index.html の実データ(__test.data())から
docs/ゲームデータ一覧.html（レリック/特殊ドロップ/敵一覧）を生成する。
usage: python gen_docs.py"""
import json, html, os
from playwright.sync_api import sync_playwright

EXE = r"C:\Users\2000h\AppData\Local\ms-playwright\chromium_headless_shell-1223\chrome-headless-shell-win64\chrome-headless-shell.exe"
URL = "file:///C:/Users/2000h/Downloads/dropbattle-rogue/index.html?test=1"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "ゲームデータ一覧.html")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=EXE)
    page = b.new_page()
    page.goto(URL)
    page.wait_for_selector("text=冒険に出る", timeout=15000)
    D = page.evaluate("window.__test.data()")
    b.close()

esc = html.escape
RAR = {1: ("コモン", "#c9bfe0"), 2: ("レア", "#7cc4ff"), 3: ("ボス級", "#ffd95c")}
CHAR_NAMES = {i: c["name"] for i, c in enumerate(D["CHARS"])}

def pat_str(pats):
    lab = {k: v["label"] for k, v in D["PATTERNS"].items()}
    return "<br>".join("→".join(lab.get(a, a) for a in pat) for pat in pats)

def enemy_row(k, boss=False):
    e = D["KINDS"][k]
    sh = D["SHIELDS"].get(k)
    shs = f"{sh['sh']}（{int(sh['c']*100)}%）" if sh else "－"
    extra = []
    if e.get("bigMul"): extra.append(f"大技×{e['bigMul']}" + ("" if boss else "（雑魚は2.4上限）"))
    if e.get("jamN"): extra.append(f"お邪魔{e['jamN']}個")
    if e.get("healMul"): extra.append(f"仲間回復×{e['healMul']}")
    return (f"<tr><td class='ic'><img src='../assets/{k}.png' loading='lazy'></td>"
        f"<td><b>{esc(e['name'])}</b><br><span class='dim'>{k}</span></td>"
        f"<td class='num'>{e['hp']}</td><td class='num'>{e['atk']}</td>"
        f"<td class='pat'>{pat_str(e['pats'])}</td>"
        f"<td class='num'>{shs}</td><td>{esc('、'.join(extra)) if extra else '－'}</td></tr>")

def enemy_table(kinds, boss=False):
    head = "<tr><th></th><th>名前</th><th>基礎HP</th><th>基礎攻撃</th><th>行動パターン（出現時に抽選）</th><th>シールド(確率)</th><th>特性</th></tr>"
    return f"<table>{head}{''.join(enemy_row(k, boss) for k in kinds)}</table>"

def pool_section(names, pools, bosses, ura):
    out = []
    for a, name in enumerate(names):
        pool = pools[a]
        seen, order = set(), []
        for role in ("light", "mid", "heavy"):
            for k in pool[role]:
                if k not in seen: seen.add(k); order.append(k)
        role_of = {k: "・".join(tag for r, tag in (("light","軽"),("mid","中"),("heavy","重")) if k in pool[r]) for k in order}
        tag = "裏" if ura else ""
        out.append(f"<h3>{tag}{a+1}章「{esc(name)}」</h3>")
        out.append("<p class='dim'>プール: " + "、".join(f"{esc(D['KINDS'][k]['name'])}({role_of[k]})" for k in order) + "（軽=群れ/序盤枠・中=中盤枠・重=強敵/終盤枠）</p>")
        out.append(enemy_table(order))
        out.append(f"<p><b>ボス候補:</b></p>" + enemy_table(bosses[a], boss=True))
    return "\n".join(out)

# ---- レリック ----
relic_rows = []
for key, r in sorted(D["RELICS"].items(), key=lambda kv: (kv[1]["rar"], kv[0])):
    rar, color = RAR[r["rar"]]
    get = []
    if r.get("src") == "boss": get.append("ボス/精鋭報酬限定")
    if r.get("char") is not None: get.append(f"{CHAR_NAMES[r['char']]}専用")
    relic_rows.append(f"<tr><td class='em'>{r['icon']}</td><td><b>{esc(r['name'])}</b><br><span class='dim'>{key}</span></td>"
        f"<td style='color:{color}'>{rar}</td><td>{esc(r['desc'])}</td>"
        f"<td class='num'>{D['RELIC_PRICE'][str(r['rar'])] if str(r['rar']) in D['RELIC_PRICE'] else D['RELIC_PRICE'][r['rar']] if r['rar'] in D['RELIC_PRICE'] else ''}</td>"
        f"<td>{esc('、'.join(get)) if get else '通常'}</td></tr>")
relic_table = ("<table><tr><th></th><th>名前</th><th>レア度</th><th>効果</th><th>ショップ価格</th><th>入手</th></tr>"
    + "".join(relic_rows) + "</table>")

# ---- 特殊ドロップ ----
sp_rows = []
for key, it in D["ITEMS"].items():
    note = []
    if it.get("exclusive"): note.append("ノア専用（初期所持のみ・報酬に出ない）")
    sp_rows.append(f"<tr><td class='ic'><img src='../{it['img']}' loading='lazy' style='width:30px;height:30px'></td>"
        f"<td><b>{esc(it['name'])}</b><br><span class='dim'>{key}</span></td>"
        f"<td>{esc(it['desc'])}</td><td>{esc(D['DESC_UP'][key].replace('【強化】',''))}</td><td>{esc('、'.join(note)) if note else '－'}</td></tr>")
for key, g in D["RGEM"].items():
    sp_rows.append(f"<tr><td class='em'>{g['glyph']}</td><td><b>{esc(g['name'])}</b><br><span class='dim'>{key}</span></td>"
        f"<td>{esc(g['desc'])}</td><td>－</td><td>レリック（縦裂/横薙の宝珠・虹福の玉）の生成限定。袋には入らない</td></tr>")
sp_table = ("<table><tr><th></th><th>名前</th><th>通常効果</th><th>強化効果（焚き火の🔨鍛える・50G）</th><th>備考</th></tr>"
    + "".join(sp_rows) + "</table>")

consum_rows = "".join(f"<tr><td class='em'>{c['icon']}</td><td><b>{esc(c['name'])}</b></td><td>{esc(c['desc'])}</td><td class='num'>{c['price']}</td></tr>"
    for c in D["CONSUM"].values())

def _fmt(arr): return "[" + ", ".join(str(x) for x in arr) + "]"
_bigs = []
for a in range(5):
    vals = []
    for k in D["URA_BOSS_BY_ACT"][a]:
        e = D["KINDS"][k]
        vals.append(round(round(e["atk"] * D["URA_BOSSATK_ACT"][a]) * e.get("bigMul", 2)))
    _bigs.append(round(sum(vals) / len(vals)))
scaling = f"""
<div class='box'>
<b>敵のスケーリング（共通式）</b><br>
D = 章×4 ＋ 層　／　HP係数 = 1 + D×0.12　／　攻撃係数 = 1 + D×0.05（ボスは係数スケールなし・固定基礎値）<br><br>
<b>表の章倍率:</b> HP ×1 / ×1 / ×1.7（3章）、攻撃 ×1.44 / ×1.35 / ×1.6、ボスHP 3章のみ×2.5・ボス攻撃 3章のみ×1.5<br>
<b>裏の章倍率:</b> HP ×{_fmt(D['URA_HP_ACT'])}、攻撃 ×{_fmt(D['URA_ATK_ACT'])}、
ボスHP ×{_fmt(D['URA_BOSSHP_ACT'])}、ボス攻撃 ×{_fmt(D['URA_BOSSATK_ACT'])}（大技の目安 {"/".join(str(x) for x in _bigs)}）<br><br>
<b>役割倍率:</b> 強敵=HP×1.6・攻×1.3（2章以降は攻撃下限60/大技下限120、裏は65/130）／群れ=HP×0.62・攻×0.58×3体／ボスのお供=HP×0.55・攻×0.7<br>
<b>その他:</b> ボスはHP×0.72で出現・約半数が上限ダメージ持ち（最大HPの約1/4.5）／激昂=4〜6ターン毎に攻撃累積強化（裏は4〜5ターン）・3スタックで2回行動／ダメージロールは毎行動±15%
</div>"""

html_doc = f"""<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ドロプシア ゲームデータ一覧</title>
<style>
body{{font-family:'Hiragino Kaku Gothic ProN','Yu Gothic',sans-serif;background:#14101e;color:#ece7f2;margin:0;padding:24px;line-height:1.7}}
h1{{color:#e8c06a;border-bottom:3px solid #8a6f3c;padding-bottom:8px}}
h2{{color:#e8c06a;margin-top:44px;border-left:6px solid #8a6f3c;padding-left:10px}}
h3{{color:#cf9af8;margin-top:28px}}
table{{border-collapse:collapse;width:100%;margin:10px 0;font-size:13px;background:rgba(30,24,42,.6)}}
th,td{{border:1px solid #3c3450;padding:6px 8px;text-align:left;vertical-align:middle}}
th{{background:#241d33;color:#e8d8a8;white-space:nowrap}}
td.ic{{width:44px;text-align:center;background:#1b1528}}
td.ic img{{width:40px;height:40px;object-fit:contain;vertical-align:middle}}
td.em{{font-size:22px;text-align:center;width:44px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
td.pat{{font-size:12px}}
.dim{{opacity:.55;font-size:11px}}
.box{{background:rgba(30,24,42,.85);border:2px solid #3c3450;border-radius:12px;padding:14px 16px;font-size:13px;margin:12px 0}}
</style></head><body>
<h1>ドロプシア ゲームデータ一覧</h1>
<p class='dim'>index.html の実データから自動生成（python gen_docs.py で再生成）。基礎HP/攻撃は倍率適用前の値。</p>

<h2>1. レリック一覧（{len(D['RELICS'])}種）</h2>
<p>入手: 精鋭報酬（1個）／章クリア3択（ボス級枠あり）／ショップ（コモン90・レア130・ボス級180、会員証で20%引）／宝箱パズル</p>
{relic_table}

<h2>2. 特殊ドロップ一覧（{len(D['ITEMS'])}種＋虹2種）</h2>
<p>初期の袋: 剣3・盾3・回復3（ノアのみ 剣2・盾2・回復2・蓄積石3）。その他は勝利報酬・虹福などで獲得。<br>
剣/盾の値は同時に消したドロップ数に比例（1個につき+5、強化+10）。</p>
{sp_table}
<h3>消費アイテム（最大3個・ポーチで4個）</h3>
<table><tr><th></th><th>名前</th><th>効果</th><th>価格</th></tr>{consum_rows}</table>

<h2>3. 敵一覧</h2>
{scaling}
<h2>表の世界（全3章・雑魚{len(set(sum([p['light']+p['mid']+p['heavy'] for p in D['ACT_POOLS']], [])))}種＋ボス{len(sum(D['BOSS_BY_ACT'], []))}種）</h2>
{pool_section(D['ACT_NAMES'], D['ACT_POOLS'], D['BOSS_BY_ACT'], False)}
<h2>裏の世界（全5章・雑魚{len(set(sum([p['light']+p['mid']+p['heavy'] for p in D['URA_POOLS']], [])))}種＋ボス{len(sum(D['URA_BOSS_BY_ACT'], []))}種）</h2>
<p class='dim'>各キャラで表3章クリア→そのキャラで挑戦可能。最終章のボスは真魔王ヴァルガ固定。</p>
{pool_section(D['URA_ACT_NAMES'], D['URA_POOLS'], D['URA_BOSS_BY_ACT'], True)}
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(html_doc)
print("WROTE", OUT, len(html_doc), "bytes")
