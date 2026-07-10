# -*- coding: utf-8 -*-
"""patch27: バトル画面を1画面に収める（ログ撤去/行統合/高さ自動調整）"""
import io, sys
P = "index.html"
s = io.open(P, encoding="utf-8").read()
n = [0]
def rep(old, new, cnt=1):
    global s
    if s.count(old) < cnt:
        print("!! NOT FOUND:", old[:140].replace("\n","\\n")); sys.exit(1)
    s = s.replace(old, new, cnt); n[0] += 1

# CSS: シーン高さの自動調整
rep('''.pop-in{animation:popIn .28s cubic-bezier(.3,1.4,.6,1)}''',
'''.scene-h{height:176px}
@media (max-height:800px){.scene-h{height:150px}}
@media (max-height:700px){.scene-h{height:132px}}
.pop-in{animation:popIn .28s cubic-bezier(.3,1.4,.6,1)}''')

# ヘッダーを薄く
rep('''  const header = h("div", { className:"flex items-center justify-between mb-2 rounded-xl px-3 py-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450" } },''',
'''  const header = h("div", { className:"flex items-center justify-between mb-1 rounded-xl px-3 py-1", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450" } },''')

# アイテムスロットを部品化（マップ用バーはそのまま、バトルは統合行）
rep('''  const itemBarEl = h("div", { className:"flex items-center gap-2 mb-1" },
    h("span", { className:"text-[10px] font-bold", style:{ color:"#c9bfe0", width:44 } }, "アイテム"),
    Array.from({ length: itemCap() }).map((_, i) => {
      const k = items[i];
      const c = k ? CONSUM[k] : null;
      return h("button", { key:i, onClick: () => useItem(i), disabled: !k,
        title: c ? `${c.name}：${c.desc}` : "空きスロット",
        className:"rounded-xl flex items-center justify-center",
        style:{ width:44, height:44, background: k ? "rgba(30,24,42,.92)" : "rgba(20,16,28,.7)",
          border: `2px solid ${k ? "#8a6f3c" : "#2c2740"}`, fontSize:"1.25rem",
          opacity: k ? 1 : 0.45, cursor: k ? "pointer" : "default" } },
        c ? c.icon : "");
    }),
    h("span", { className:"text-[9px]", style:{ opacity:0.55, marginLeft:2 } }, "タップで使用（最大", itemCap(), "個）"));''',
'''  const itemSlots = sz => Array.from({ length: itemCap() }).map((_, i) => {
    const k = items[i];
    const c = k ? CONSUM[k] : null;
    return h("button", { key:i, onClick: () => useItem(i), disabled: !k,
      title: c ? `${c.name}：${c.desc}` : "空きスロット",
      className:"rounded-xl flex items-center justify-center",
      style:{ width:sz, height:sz, background: k ? "rgba(30,24,42,.92)" : "rgba(20,16,28,.7)",
        border: `2px solid ${k ? "#8a6f3c" : "#2c2740"}`, fontSize: sz > 40 ? "1.25rem" : "1.05rem",
        opacity: k ? 1 : 0.45, cursor: k ? "pointer" : "default" } },
      c ? c.icon : "");
  });
  const itemBarEl = h("div", { className:"flex items-center gap-2 mb-1" },
    h("span", { className:"text-[10px] font-bold", style:{ color:"#c9bfe0", width:44 } }, "アイテム"),
    itemSlots(44),
    h("span", { className:"text-[9px]", style:{ opacity:0.55, marginLeft:2 } }, "タップで使用（最大", itemCap(), "個）"));''')

# バトル: アイテム+被ダメ予測を1行に統合、ログ撤去
rep('''      itemBarEl,
      h("div", { className:"flex items-center justify-end mb-1", style:{ fontSize:11, gap:4 } },
        h("span", { style:{ opacity:0.75 } }, "次の被ダメ予測"),
        h("b", { style:{ color: incomingPreview > 0 ? "#ff8a80" : "#7cffb0", fontSize:15, fontVariantNumeric:"tabular-nums", textShadow:"0 1px 2px #000" } }, incomingPreview),
        tv.def > 0 && h("span", { className:"flex items-center", style:{ gap:2, fontSize:10, color:"#9db8e8" } },
          "（", h("img", { src:"assets/icon_def.png", alt:"", draggable:false, style:{ width:11, height:11, objectFit:"contain" } }), tv.def, " で軽減後）")),''',
'''      h("div", { className:"flex items-center justify-between mb-1" },
        h("div", { className:"flex items-center gap-1.5" }, itemSlots(38)),
        h("div", { className:"flex items-center", style:{ fontSize:11, gap:4 } },
          h("span", { style:{ opacity:0.75 } }, "被ダメ予測"),
          h("b", { style:{ color: incomingPreview > 0 ? "#ff8a80" : "#7cffb0", fontSize:15, fontVariantNumeric:"tabular-nums", textShadow:"0 1px 2px #000" } }, incomingPreview),
          tv.def > 0 && h("span", { className:"flex items-center", style:{ gap:2, fontSize:10, color:"#9db8e8" } },
            "（", h("img", { src:"assets/icon_def.png", alt:"", draggable:false, style:{ width:11, height:11, objectFit:"contain" } }), tv.def, "）"))),''')

# シーン: 高さをCSSクラスで
rep('''      h("div", { key:"scn" + shakeSeq, className:"relative w-full mb-1" + (shakeSeq > 0 ? " scene-shake" : ""), style:{ height:192, borderRadius:16, overflow:"hidden", border:"2px solid #453b5c", background:"#191424" } },''',
'''      h("div", { key:"scn" + shakeSeq, className:"relative w-full mb-1 scene-h" + (shakeSeq > 0 ? " scene-shake" : ""), style:{ borderRadius:16, overflow:"hidden", border:"2px solid #453b5c", background:"#191424" } },''')

# アクションボタンを薄く
rep('''          style:{ height:72,''', '''          style:{ height:62,''')
rep('''          h("img", { src:a.img, alt:a.label, draggable:false, style:{ height:26, width:26, objectFit:"contain", opacity: isUsed && !lit ? 0.35 : 1, filter:"drop-shadow(0 2px 1px rgba(0,0,0,.45))" } }),''',
'''          h("img", { src:a.img, alt:a.label, draggable:false, style:{ height:22, width:22, objectFit:"contain", opacity: isUsed && !lit ? 0.35 : 1, filter:"drop-shadow(0 2px 1px rgba(0,0,0,.45))" } }),''')

# 盤面フレームを薄く
rep('''      h("div", { className:"relative rounded-2xl", style:{ padding:6, background:"rgba(19,14,28,.8)", border:"2px solid #3c3450", marginBottom:6 } },''',
'''      h("div", { className:"relative rounded-2xl", style:{ padding:5, background:"rgba(19,14,28,.8)", border:"2px solid #3c3450", marginBottom:4 } },''')

# バトル画面からログを撤去（マップは残す）
rep('''              cell.type === JUNK ? h("img", { src:"assets/mk_skull.png"''', '''              cell.type === JUNK ? h("img", { src:"assets/mk_skull.png"''')  # 位置確認用no-op
rep('''                 : h("span", { style:{ width:"32%", height:"24%", borderRadius:"50%", background:"rgba(255,255,255,.30)", position:"absolute", top:"11%", left:"13%", pointerEvents:"none" } }));
          }))),
      logBox,
      overlays));''',
'''                 : h("span", { style:{ width:"32%", height:"24%", borderRadius:"50%", background:"rgba(255,255,255,.30)", position:"absolute", top:"11%", left:"13%", pointerEvents:"none" } }));
          }))),
      overlays));''')

# レリックバーを小さく
rep('''      className:"rounded-lg", style:{ width:30, height:30, fontSize:"1rem", background:"rgba(30,24,42,.92)", border:"1px solid #6e5a3c", lineHeight:"28px" } }, RELICS[k].icon)));''',
'''      className:"rounded-lg", style:{ width:26, height:26, fontSize:"0.85rem", background:"rgba(30,24,42,.92)", border:"1px solid #6e5a3c", lineHeight:"24px" } }, RELICS[k].icon)));''')

io.open(P, "w", encoding="utf-8").write(s)
print(f"PATCH27 OK: {n[0]}")
