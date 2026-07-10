# -*- coding: utf-8 -*-
"""patch12: 3章制（章別マップ/ボス/背景・章クリアボーナス・吸血アクション・最大HP成長）"""
import io, sys
P = "index.html"
s = io.open(P, encoding="utf-8").read()
n = [0]
def rep(old, new, cnt=1):
    global s
    if s.count(old) < cnt:
        print("!! NOT FOUND:", old[:130].replace("\n","\\n")); sys.exit(1)
    s = s.replace(old, new, cnt); n[0] += 1

# ---------- 章定義・新ボス ----------
rep("const ATK_PER = 10, DEF_PER = 10, HEAL_PER = 2;\nconst ROWS = 8;",
"""const ATK_PER = 10, DEF_PER = 10, HEAL_PER = 2;
const ROWS = 8;
const ACTS = 3;
const ACT_NAMES = ["翠緑の森", "毒霧の沼窟", "灼熱の魔城"];
const BOSS_BY_ACT = ["kslime", "vamp", "demon"];
const MAP_BGS = ["assets/bg_map_tall.jpg", "assets/bg_map2.jpg", "assets/bg_map3.jpg"];
const BATTLE_BGS = ["assets/bg_battle.jpg", "assets/bg_battle2.jpg", "assets/bg_battle3.jpg"];
const ACT_POOLS = [
  { light:["slime","bat"], mid:["slime","bat","spore"], heavy:["imp","shade"] },
  { light:["bat","shade"], mid:["bat","shade","spore"], heavy:["imp","golem"] },
  { light:["shade","imp"], mid:["shade","imp","spore"], heavy:["golem","imp"] }
];""")
rep('''  demon: { name:"魔王ヴァルガ", hp:1050, atk:55, size:112, idle:"b", bigMul:2.4, jamN:4,
    pats:[["attack","jam","charge","bigatk"], ["jam","attack","charge","bigatk"], ["attack","charge","bigatk","jam"]] }
};''',
'''  demon: { name:"魔王ヴァルガ", hp:1050, atk:55, size:112, idle:"b", bigMul:2.4, jamN:4,
    pats:[["attack","jam","charge","bigatk"], ["jam","attack","charge","bigatk"], ["attack","charge","bigatk","jam"]] },
  kslime:{ name:"キングスライム", hp:520, atk:34, size:104, idle:"a", bigMul:2.0, jamN:3,
    pats:[["attack","jam","bigatk"]] },
  vamp:  { name:"ヴァンピール", hp:780, atk:44, size:106, idle:"f", bigMul:2.4,
    pats:[["drain","attack","charge","bigatk"]] }
};''')
rep('''  healally:{ icon:"💚", label:"なかま回復", color:"#8ce8b0" }
};''',
'''  healally:{ icon:"💚", label:"なかま回復", color:"#8ce8b0" },
  drain:   { icon:"🩸", label:"吸血",       color:"#ff9ad0" }
};''')
rep('''  const dmg = act === "attack" ? en.atk
    : act === "double" ? en.atk * 2
    : act === "bigatk" ? Math.round(en.atk * (k.bigMul || 2)) : 0;''',
'''  const dmg = act === "attack" || act === "drain" ? en.atk
    : act === "double" ? en.atk * 2
    : act === "bigatk" ? Math.round(en.atk * (k.bigMul || 2)) : 0;''')

# ---------- エンカウント: 章対応 ----------
rep('''const encounterFor = node => {
  const r = node.row;
  const hpS = 1 + r*0.33, atkS = 1 + r*0.17;
  let list;
  if (node.type === "boss") list = [{ kind:"demon", hpM:1, atkM:1, boss:true, noScale:true }];
  else if (node.type === "elite") list = [{ kind:pick(["golem","imp"]), hpM:2.2, atkM:1.45, elite:true }];
  else if (node.type === "horde") {
    list = [0,1].map(() => ({ kind:pick(["slime","bat","shade"]), hpM:0.62, atkM:0.72 }));
    list.push({ kind: Math.random() < 0.45 ? "spore" : pick(["slime","bat","shade"]), hpM:0.62, atkM:0.72 });
  }
  else {
    if (r <= 1) list = [{ kind:pick(["slime","bat"]), hpM:1, atkM:1 }];
    else if (r <= 3) list = Math.random() < 0.5
      ? [{ kind:pick(["imp","shade","golem"]), hpM:1, atkM:1 }]
      : [0,1].map(() => ({ kind:pick(["slime","bat"]), hpM:0.85, atkM:0.85 }));
    else list = [
      { kind:pick(["slime","bat","shade","spore"]), hpM:0.9, atkM:0.9 },
      { kind:pick(["imp","shade","golem"]), hpM:0.9, atkM:0.9 }
    ];
  }''',
'''const encounterFor = (node, act) => {
  const r = node.row;
  const D = act * 5 + r; // 章をまたいで難度が伸びる
  const hpS = 1 + D * 0.26, atkS = 1 + D * 0.13;
  const pool = ACT_POOLS[act] || ACT_POOLS[0];
  let list;
  if (node.type === "boss") list = [{ kind: BOSS_BY_ACT[act] || "demon", hpM:1, atkM:1, boss:true, noScale:true }];
  else if (node.type === "elite") list = [{ kind:pick(pool.heavy), hpM:2.2, atkM:1.45, elite:true }];
  else if (node.type === "horde") {
    list = [0,1].map(() => ({ kind:pick(pool.light), hpM:0.62, atkM:0.72 }));
    list.push({ kind: Math.random() < 0.45 ? "spore" : pick(pool.light), hpM:0.62, atkM:0.72 });
  }
  else {
    if (r <= 1) list = [{ kind:pick(pool.light), hpM:1, atkM:1 }];
    else if (r <= 3) list = Math.random() < 0.5
      ? [{ kind:pick(pool.heavy), hpM:1, atkM:1 }]
      : [0,1].map(() => ({ kind:pick(pool.light), hpM:0.85, atkM:0.85 }));
    else list = [
      { kind:pick(pool.mid), hpM:0.9, atkM:0.9 },
      { kind:pick(pool.heavy), hpM:0.9, atkM:0.9 }
    ];
  }''')

# ---------- state: act / pMax / actClear ----------
rep('''  const [pHP, setPHP_] = useState(P_MAX);
  const pRef = useRef(P_MAX);
  const setPHP = v => { pRef.current = v; setPHP_(v); };''',
'''  const [pHP, setPHP_] = useState(P_MAX);
  const pRef = useRef(P_MAX);
  const setPHP = v => { pRef.current = v; setPHP_(v); };
  const [pMax, setPMax_] = useState(P_MAX);
  const pMaxRef = useRef(P_MAX);
  const setPMax = v => { pMaxRef.current = v; setPMax_(v); };
  const [act, setAct_] = useState(0);
  const actRef = useRef(0);
  const setAct = v => { actRef.current = v; setAct_(v); };
  const [actClear, setActClear] = useState(false);
  const actClearRef = useRef(false); actClearRef.current = actClear;''')

# ---------- P_MAX 実行時参照を pMax に ----------
rep('        const np = Math.min(P_MAX, before + heal);', '        const np = Math.min(pMaxRef.current, before + heal);')
rep('      const np = Math.min(P_MAX, php + heal);', '      const np = Math.min(pMaxRef.current, php + heal);')
rep('      healed = Math.min(P_MAX - pRef.current, 20);', '      healed = Math.min(pMaxRef.current - pRef.current, 20);')
rep('    const healAmt = Math.min(P_MAX - pRef.current, Math.round(P_MAX * 0.4));',
    '    const healAmt = Math.min(pMaxRef.current - pRef.current, Math.round(pMaxRef.current * 0.4));')
rep('      const np = Math.min(P_MAX, pRef.current + 80);', '      const np = Math.min(pMaxRef.current, pRef.current + 80);')
rep('          setPHP(Math.round(P_MAX * 0.4));', '          setPHP(Math.round(pMaxRef.current * 0.4));')
rep('h(Bar, { value:pHP, max:P_MAX, from:"#22c55e", to:"#7CFFB0", height:9 })', 'h(Bar, { value:pHP, max:pMax, from:"#22c55e", to:"#7CFFB0", height:9 })')
rep('h(Bar, { value:pHP, max:P_MAX, from:"#22c55e", to:"#7CFFB0", height:8 })', 'h(Bar, { value:pHP, max:pMax, from:"#22c55e", to:"#7CFFB0", height:8 })')
rep('pHP, "/", P_MAX)),\n        itemBarEl,', 'pHP, "/", pMax)),\n        itemBarEl,')
rep('} }, pHP, "/", P_MAX)),\n        // 敵', '} }, pHP, "/", pMax)),\n        // 敵')

# ---------- 勝利: 章クリア分岐 ----------
rep('''    const node = pendingNodeRef.current;
    if (node && node.type === "boss") {
      setStatus("clear"); statusRef.current = "clear";
      SFX.win();
      return;
    }''',
'''    const node = pendingNodeRef.current;
    if (node && node.type === "boss") {
      SFX.win();
      if (actRef.current < ACTS - 1) { setActClear(true); return; }
      setStatus("clear"); statusRef.current = "clear";
      return;
    }''')

# ---------- 次章へ ----------
rep('''  // ===== ショップ（群れ勝利後・休憩所） =====''',
'''  // ===== 章クリア → 次章 =====
  const nextAct = () => {
    const na = actRef.current + 1;
    setAct(na);
    setPMax(pMaxRef.current + 50);
    setPHP(pMaxRef.current);
    setCoinsBoth(coinsRef.current + 100);
    const m = genMap();
    setMap(m); mapRef.current = m;
    setCurNodeId(null); curNodeRef.current = null;
    setVisited(new Set());
    pendingNodeRef.current = null;
    setEnemiesBoth([]);
    setActClear(false);
    setStatus("map"); statusRef.current = "map";
    setLocked(false); lockedRef.current = false;
    addLog([`― 第${na + 1}章「${ACT_NAMES[na]}」開始 ―`, "🎁 最大HP+50・全回復・💰+100"]);
    SFX.step();
  };

  // ===== ショップ（群れ勝利後・休憩所） =====''')

# ---------- enterNode: encounterForに章を渡す ----------
rep('    const ens = encounterFor(node);', '    const ens = encounterFor(node, actRef.current);')

# ---------- restart: 章リセット ----------
rep('''    setCoinsBoth(0); setItemsBoth(["potion"]); setShop(null); setCampfire(null);
    UPGRADES = initUps(); setUpsView({ ...UPGRADES });''',
'''    setCoinsBoth(0); setItemsBoth(["potion"]); setShop(null); setCampfire(null);
    UPGRADES = initUps(); setUpsView({ ...UPGRADES });
    setAct(0); setPMax(P_MAX); setActClear(false);''')
rep('''    setEnemiesBoth([]);
    setPHP(P_MAX);
    commitBoard(makeBoard(bagRef, ownedRef));''',
'''    setEnemiesBoth([]);
    setPHP(P_MAX);
    commitBoard(makeBoard(bagRef, ownedRef));
    // 章リセットは上で実施済み''')

# ---------- 吸血（drain）実行 ----------
rep('''      // 攻撃系（attack / double / bigatk）''',
'''      if (iv.act === "drain") {
        const one = iv.dmg;
        const blocked = Math.min(shield, one);
        const broke = blocked > 0 && shield - blocked <= 0 && one > blocked;
        shield -= blocked;
        const shAfter = shield;
        const through = one - blocked;
        php = Math.max(0, php - through);
        const np = php;
        const healed = Math.min(en.max - en.hp, through);
        en.hp += healed;
        const snap = ens.map(x => ({ ...x }));
        seq.push({
          text: through > 0 ? `${broke ? "防御崩壊！" : ""}${en.name}の吸血 ${through}！` : `${en.name}の吸血をガード！`,
          color: through > 0 ? "#ff9ad0" : "#7da8e8", act:"def",
          run: () => {
            setAnim(en.id, "attack");
            setTimeout(() => {
              setPHP(np); setSv(shAfter);
              if (broke) SFX.crack();
              if (through > 0) {
                setAnim("hero","hit"); SFX.hurt(); flash("player");
                if (healed > 0) setTimeout(() => { setAnim(en.id, "heal"); setEnemiesBoth(snap); SFX.heal(); }, 300);
              } else SFX.tap();
            }, 200);
          }
        });
        logs.push(through > 0 ? `🩸 ${en.name}の吸血 ${through}（${healed}回復）` : `🛡 ${en.name}の吸血を防いだ`);
        if (php <= 0) break;
        continue;
      }
      // 攻撃系（attack / double / bigatk）''')

# 吸血も攻撃系チップ扱い
rep('            const isDmgIntent = iv.act === "attack" || iv.act === "double" || iv.act === "bigatk";',
    '            const isDmgIntent = iv.act === "attack" || iv.act === "double" || iv.act === "bigatk" || iv.act === "drain";')

# ---------- 背景を章別に ----------
rep('h("img", { src:"assets/bg_map_tall.jpg", alt:"", draggable:false, className:"absolute pointer-events-none", style:{ left:0, top:0, width:"100%", height:"100%", objectFit:"cover", opacity:.9 } }),',
    'h("img", { src:MAP_BGS[act] || MAP_BGS[0], alt:"", draggable:false, className:"absolute pointer-events-none", style:{ left:0, top:0, width:"100%", height:"100%", objectFit:"cover", opacity:.9 } }),')
rep('h("img", { src:"assets/bg_battle.jpg", alt:"", draggable:false, className:"absolute pointer-events-none", style:{ left:0, top:0, width:"100%", height:"100%", objectFit:"cover", objectPosition:"center bottom", opacity:.92 } }),',
    'h("img", { src:BATTLE_BGS[act] || BATTLE_BGS[0], alt:"", draggable:false, className:"absolute pointer-events-none", style:{ left:0, top:0, width:"100%", height:"100%", objectFit:"cover", objectPosition:"center bottom", opacity:.92 } }),')

# ---------- ヘッダー: 章表示 ----------
rep('''      "ドロップバトル ",
      h("span", { style:{ fontSize:"0.74rem", color:"#ffcf5d" } }, progRow, "/", ROWS, "層")),''',
'''      "ドロップバトル ",
      h("span", { style:{ fontSize:"0.74rem", color:"#ffcf5d" } }, "第", act + 1, "章 ", progRow, "/", ROWS)),''')

# ---------- 章クリアオーバーレイ ----------
rep('''  if (status === "clear" || status === "lose") {''',
'''  if (actClear) {
    overlays.push(h("div", { key:"actclear", className:"fixed inset-0 flex items-center justify-center px-6 fade-in", style:{ background:"rgba(8,4,14,.88)", zIndex:56 } },
      h("div", { className:"text-center pop-in rounded-2xl p-5 w-full", style:{ maxWidth:360, background:"rgba(30,24,42,.98)", border:"2px solid #8a6f3c" } },
        h("div", { className:"font-bold", style:{ fontSize:"1.6rem", color:"#f2e6c8", textShadow:"0 3px 0 rgba(0,0,0,.55)" } }, "🎉 第", act + 1, "章 クリア！"),
        h("p", { className:"my-2 text-sm", style:{ opacity:0.85 } }, "「", ACT_NAMES[act], "」を制覇した！"),
        h("div", { className:"rounded-xl py-2 px-3 mb-3 text-xs", style:{ background:"rgba(232,192,106,.1)", border:"1px solid rgba(216,168,72,.4)", color:"#e8d8a8", lineHeight:1.9 } },
          "🎁 章クリアボーナス", h("br"), "最大HP +50 ／ HP全回復 ／ 💰 +100"),
        h("button", { onClick: nextAct, className:"w-full rounded-xl py-3 font-bold tracking-widest",
          style:{ background:"linear-gradient(180deg,#e8c06a,#b8862e)", color:"#2c2030", border:"2px solid #6e4e1a", boxShadow:"0 3px 0 #6e4e1a" } },
          "第", act + 2, "章「", ACT_NAMES[act + 1] || "", "」へ ▶"))));
  }
  if (status === "clear" || status === "lose") {''')

# クリア文言
rep('status === "clear" ? "全8層を踏破し、魔王ヴァルガを打ち倒した！" : `${progRow}層で冒険は終わった…`',
    'status === "clear" ? "全3章を踏破し、魔王ヴァルガを打ち倒した！" : `第${act + 1}章 ${progRow}層で冒険は終わった…`')

# ---------- テストフック ----------
rep('''        campfire: campfireRef.current,''',
'''        campfire: campfireRef.current,
        act: actRef.current, pmax: pMaxRef.current, actClear: actClearRef.current,''')
rep('''      tutStart: () => setTut(0),''',
'''      tutStart: () => setTut(0),
      nextAct: () => nextAct(),''')

io.open(P, "w", encoding="utf-8").write(s)
print(f"PATCH12 OK: {n[0]} replacements")
