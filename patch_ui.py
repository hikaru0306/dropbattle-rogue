# -*- coding: utf-8 -*-
"""UI統一: 絵文字UI→生成アイコン画像、パネル/トースト/ウィンドウのスタイル統一"""
import io, sys

p = "index.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        print("ANCHOR FAIL:", old[:80])
        sys.exit(1)
    s = s.replace(old, new)

# 0) インラインアイコン用ヘルパー（iOS対策: width/height属性+style両方）
rep("""const NODE_META = {""",
"""const Ic = (src, sz, extra) => h("img", { src, alt:"", draggable:false, width:sz, height:sz,
  style: Object.assign({ width:sz, height:sz, maxWidth:sz, maxHeight:sz, objectFit:"contain",
    display:"inline-block", verticalAlign:"-3px", filter:"drop-shadow(0 1px 1px rgba(0,0,0,.45))" }, extra || {}) });
const NODE_META = {""")

# 1) ヘッダー: コイン/音楽/効果音/袋
rep("""      h("span", { className:"rounded-xl px-2 py-1.5 text-sm font-bold", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #8a6f3c", color:"#e8c06a", fontVariantNumeric:"tabular-nums" } }, "💰", coins),
      h("button", { onClick: toggleBgm, className:"rounded-xl px-2 py-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450", fontSize:14, lineHeight:1, opacity: bgmOnView ? 1 : 0.45 } }, "🎵"),
      h("button", { onClick: toggleSfx, className:"rounded-xl px-2 py-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450", fontSize:14, lineHeight:1, opacity: sfxOn ? 1 : 0.45 } }, sfxOn ? "🔊" : "🔇"),
      h("button", { onClick: () => { setBagOpen(true); SFX.open(); }, className:"relative rounded-xl px-3 py-1.5 flex items-center gap-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #8a6f3c" } },
        h("span", { style:{ fontSize:15, lineHeight:1 } }, "🎒"),
        h("span", { className:"font-bold text-sm", style:{ color:"#ffcf5d", fontVariantNumeric:"tabular-nums" } }, "残", bagLeft))));""",
"""      h("span", { className:"rounded-xl px-2 py-1.5 text-sm font-bold flex items-center gap-1", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #8a6f3c", color:"#e8c06a", fontVariantNumeric:"tabular-nums" } }, Ic("assets/icon_coin.png", 15), coins),
      h("button", { onClick: toggleBgm, className:"rounded-xl px-2 py-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450", lineHeight:1 } },
        Ic("assets/icon_note.png", 15, bgmOnView ? null : { filter:"grayscale(1) drop-shadow(0 1px 1px rgba(0,0,0,.45))", opacity:0.4 })),
      h("button", { onClick: toggleSfx, className:"rounded-xl px-2 py-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #3c3450", lineHeight:1 } },
        Ic("assets/icon_speaker.png", 15, sfxOn ? null : { filter:"grayscale(1) drop-shadow(0 1px 1px rgba(0,0,0,.45))", opacity:0.4 })),
      h("button", { onClick: () => { setBagOpen(true); SFX.open(); }, className:"relative rounded-xl px-3 py-1.5 flex items-center gap-1.5", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #8a6f3c" } },
        Ic("assets/icon_bag.png", 16),
        h("span", { className:"font-bold text-sm", style:{ color:"#ffcf5d", fontVariantNumeric:"tabular-nums" } }, "残", bagLeft))));""")

# 2) 袋モーダル: パネル統一 + タイトルアイコン
rep("""    h("div", { className:"w-full rounded-2xl p-4 pop-in", style:{ maxWidth:360, background:"rgba(24,15,34,.98)", border:"1px solid rgba(255,221,90,.45)" }, onClick: e => e.stopPropagation() },
      h("div", { className:"flex justify-between items-center mb-1" },
        h("span", { className:"font-bold", style:{ color:"#ffcf5d", fontSize:"1.05rem" } }, "🎒 所持アイテム"),""",
"""    h("div", { className:"w-full rounded-2xl p-4 pop-in", style:{ maxWidth:360, background:"rgba(30,24,42,.98)", border:"2px solid #8a6f3c" }, onClick: e => e.stopPropagation() },
      h("div", { className:"flex justify-between items-center mb-1" },
        h("span", { className:"font-bold flex items-center gap-1.5", style:{ color:"#ffcf5d", fontSize:"1.05rem" } }, Ic("assets/icon_bag.png", 18), "所持アイテム"),""")

# 3) 焚き火: 枠を統一チャーム + タイトルは焚き火アイコン
rep("""      h("div", { className:"w-full rounded-2xl p-4 pop-in", style:{ maxWidth:370, background:"rgba(30,24,42,.98)", border:"2px solid #7cffb0" } },
        h("h2", { className:"text-center font-bold mb-1", style:{ fontSize:"1.15rem", color:"#7cffb0", textShadow:"0 2px 0 rgba(0,0,0,.6)" } }, "🔥 焚き火"),""",
"""      h("div", { className:"w-full rounded-2xl p-4 pop-in", style:{ maxWidth:370, background:"rgba(30,24,42,.98)", border:"2px solid #8a6f3c" } },
        h("h2", { className:"text-center font-bold mb-1 flex items-center justify-center gap-1.5", style:{ fontSize:"1.15rem", color:"#7cffb0", textShadow:"0 2px 0 rgba(0,0,0,.6)" } }, Ic("assets/node_rest.png", 20), "焚き火"),""")

# 4) ショップ: タイトル・所持コイン・価格ボタン
rep("""          h("span", { className:"font-bold", style:{ color:"#e8c06a", fontSize:"1.05rem" } }, "🛒 行商人"),
          h("span", { className:"text-sm font-bold", style:{ color:"#e8c06a", fontVariantNumeric:"tabular-nums" } }, "💰", coins)),""",
"""          h("span", { className:"font-bold flex items-center gap-1.5", style:{ color:"#e8c06a", fontSize:"1.05rem" } }, Ic("assets/node_treasure.png", 18), "行商人"),
          h("span", { className:"text-sm font-bold flex items-center gap-1", style:{ color:"#e8c06a", fontVariantNumeric:"tabular-nums" } }, Ic("assets/icon_coin.png", 14), coins)),""")
rep("""                border: can ? "1px solid #6e4e1a" : "1px solid #3c3450" } }, "💰", rc));""",
"""                border: can ? "1px solid #6e4e1a" : "1px solid #3c3450" } }, Ic("assets/icon_coin.png", 12), " ", rc));""")
rep("""                border: can ? "1px solid #6e4e1a" : "1px solid #3c3450" } }, "💰", priceOf(c.price)));""",
"""                border: can ? "1px solid #6e4e1a" : "1px solid #3c3450" } }, Ic("assets/icon_coin.png", 12), " ", priceOf(c.price)));""")

# 5) 報酬: タイトルをノードアイコンに / コイン獲得行
rep("""    const rTitle = rewards.kind === "treasure" ? "🎁 宝箱発見！" : rewards.kind === "elite" ? "💀 精鋭撃破！" : "🏆 勝利！";""",
"""    const rIcon = rewards.kind === "treasure" ? "assets/node_treasure.png" : rewards.kind === "elite" ? "assets/node_elite.png" : "assets/node_battle.png";
    const rTitle = rewards.kind === "treasure" ? "宝箱発見！" : rewards.kind === "elite" ? "精鋭撃破！" : "勝利！";""")
rep("""        h("h2", { className:"text-center font-bold mb-1", style:{ fontSize:"1.25rem", color:"#e0b45c", textShadow:"0 2px 0 rgba(0,0,0,.6)" } }, rTitle),""",
"""        h("h2", { className:"text-center font-bold mb-1 flex items-center justify-center gap-2", style:{ fontSize:"1.25rem", color:"#e0b45c", textShadow:"0 2px 0 rgba(0,0,0,.6)" } }, Ic(rIcon, 22), rTitle),""")
rep("""        rewards.coins > 0 && h("p", { className:"text-center text-xs mb-1", style:{ color:"#e8c06a", fontWeight:800 } }, "💰 コイン +", rewards.coins),""",
"""        rewards.coins > 0 && h("p", { className:"text-center text-xs mb-1", style:{ color:"#e8c06a", fontWeight:800 } }, Ic("assets/icon_coin.png", 13), " コイン +", rewards.coins),""")

# 6) 鍛冶: コスト表示
rep("""            h("span", { className:"text-sm font-bold", style:{ color: coins >= forgeCost() ? "#e8c06a" : "#f0a8a0" } }, "💰", forgeCost())),""",
"""            h("span", { className:"text-sm font-bold flex items-center gap-1", style:{ color: coins >= forgeCost() ? "#e8c06a" : "#f0a8a0" } }, Ic("assets/icon_coin.png", 13), forgeCost())),""")
rep("""          h("p", { className:"text-center text-[11px] mb-2", style:{ opacity:0.75 } }, "鍛える特殊ドロップを1つ選ぶ（💰", forgeCost(), " ／ 所持 💰", coins, "）"),""",
"""          h("p", { className:"text-center text-[11px] mb-2", style:{ opacity:0.75 } }, "鍛える特殊ドロップを1つ選ぶ（", Ic("assets/icon_coin.png", 11), forgeCost(), " ／ 所持 ", Ic("assets/icon_coin.png", 11), coins, "）"),""")

# 7) 章クリア: ボーナス行のコイン
rep(""""🎁 章クリアボーナス", h("br"), "最大HP +", hasR("crown") ? 80 : 50, " ／ HP全回復 ／ 💰 +100"),""",
""""章クリアボーナス", h("br"), "最大HP +", hasR("crown") ? 80 : 50, " ／ HP全回復 ／ ", Ic("assets/icon_coin.png", 12), " +100"),""")

# 8) 休憩トースト: パネル系と同じチャームに
rep("""  if (restMsg) overlays.push(h("div", { key:"rest", className:"fixed pop-in", style:{ top:18, left:"50%", transform:"translateX(-50%)", zIndex:70, background:"rgba(20,40,26,.95)", border:"1px solid rgba(124,255,176,.6)", color:"#c8ffdd", borderRadius:12, padding:"10px 18px", fontSize:"0.85rem", fontWeight:800, boxShadow:"0 3px 8px rgba(0,0,0,.5)" } }, restMsg));""",
"""  if (restMsg) overlays.push(h("div", { key:"rest", className:"fixed pop-in", style:{ top:18, left:"50%", transform:"translateX(-50%)", zIndex:70, background:"rgba(30,24,42,.97)", border:"2px solid #3c5a48", color:"#c8ffdd", borderRadius:12, padding:"10px 18px", fontSize:"0.85rem", fontWeight:800, boxShadow:"0 3px 8px rgba(0,0,0,.5)" } }, restMsg));""")

# 9) マップのHPバー: 🧙→勇者画像
rep("""          h("span", { style:{ fontSize:"0.9rem" } }, "🧙"),""",
"""          Ic("assets/hero.png", 20),""")

# 10) タイトルの操作ヒント: 絵文字→アクションアイコン画像
rep("""          "⚔攻撃 / 🛡防御 / ✚回復 を選んで同色ドロップをタップ。3回消すと敵のターン。")));""",
"""          Ic("assets/icon_atk.png", 13), "攻撃 / ", Ic("assets/icon_def.png", 13), "防御 / ", Ic("assets/icon_heal.png", 13), "回復 を選んで同色ドロップをタップ。3回消すと敵のターン。")));""")

io.open(p, "w", encoding="utf-8").write(s)
print("UI PATCH OK")
