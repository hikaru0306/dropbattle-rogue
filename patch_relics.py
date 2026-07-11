# -*- coding: utf-8 -*-
"""消し方レリック4種 + 爆破巻き込み特殊ドロップの完全発動（雷の再帰対応）"""
import io, sys

p = "index.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        print("ANCHOR FAIL:", old[:90])
        sys.exit(1)
    s = s.replace(old, new)

# 1) レリック4種追加
rep('''  swordbook:  { icon:"⚔", name:"剣術指南書", desc:"攻撃ドロップ1個の効果+2", rar:1 },''',
'''  blastcore:  { icon:"💥", name:"爆心の石", desc:"1個だけで消すと、周囲3×3も爆破する", rar:2 },
  crossgem:   { icon:"✚", name:"十字晶", desc:"ちょうど4個で消すと、タップ位置から十字1列を爆破", rar:2 },
  xgem:       { icon:"❌", name:"X字晶", desc:"ちょうど5個で消すと、タップ位置から斜め4方向を爆破", rar:3 },
  redcore:    { icon:"🌋", name:"紅蓮の核", desc:"赤ドロップを消すと、消した各赤の上下も爆破", rar:2 },
  swordbook:  { icon:"⚔", name:"剣術指南書", desc:"攻撃ドロップ1個の効果+2", rar:1 },''')

# 2) 消去範囲の共通関数（パターンレリック → 爆弾連鎖 → 雷の再帰発動）
rep("const computeEffect = (act, info) => {",
"""// タップ起点の消去範囲を確定する。パターン系レリックの追加爆破と、
// 爆破に巻き込まれた特殊ドロップ（爆弾連鎖・雷）の再帰発動まで含む
const expandClear = (b, idx) => {
  const seedJunk = b[idx].type === JUNK;
  const ids0 = findGroup(b, idx);
  if (seedJunk) return { ids: ids0, seedJunk };
  const N = SIZE * SIZE;
  const addIdx = i => { if (i >= 0 && i < N) ids0.add(b[i].id); };
  const r0 = Math.floor(idx / SIZE), c0 = idx % SIZE;
  if (hasR("blastcore") && ids0.size === 1) {
    for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
      const r = r0 + dr, c = c0 + dc;
      if (r >= 0 && r < SIZE && c >= 0 && c < SIZE) addIdx(r * SIZE + c);
    }
  }
  if (hasR("crossgem") && ids0.size === 4) {
    for (let i = 0; i < SIZE; i++) { addIdx(r0 * SIZE + i); addIdx(i * SIZE + c0); }
  }
  if (hasR("xgem") && ids0.size === 5) {
    for (let d = 1; d < SIZE; d++) {
      [[r0 + d, c0 + d], [r0 + d, c0 - d], [r0 - d, c0 + d], [r0 - d, c0 - d]].forEach(rc => {
        if (rc[0] >= 0 && rc[0] < SIZE && rc[1] >= 0 && rc[1] < SIZE) addIdx(rc[0] * SIZE + rc[1]);
      });
    }
  }
  if (hasR("redcore") && b[idx].type === 0) {
    const redIdx = b.map((c, i) => (ids0.has(c.id) && c.type === 0) ? i : -1).filter(i => i >= 0);
    redIdx.forEach(i => { addIdx(i - SIZE); addIdx(i + SIZE); });
  }
  let ids = expandIds(b, ids0);
  let changed = true;
  while (changed) {
    changed = false;
    for (const c of b) {
      if (!ids.has(c.id) || c.special !== "bolt") continue;
      for (const c2 of b) {
        if (c2.type === c.type && c2.type !== JUNK && !ids.has(c2.id)) { ids.add(c2.id); changed = true; }
      }
    }
    if (changed) ids = expandIds(b, ids);
  }
  return { ids, seedJunk };
};
const computeEffect = (act, info) => {""")

# 3) commit を共通関数に置換
rep("""    const seedJunk = boardRef.current[idx].type === JUNK;
    let ids0 = findGroup(boardRef.current, idx);
    if (!seedJunk) {
      const hasBolt = boardRef.current.some(c => ids0.has(c.id) && c.special === "bolt");
      if (hasBolt) {
        const t = boardRef.current[idx].type;
        boardRef.current.forEach(c => { if (c.type === t) ids0.add(c.id); });
      }
    }
    const ids = seedJunk ? ids0 : expandIds(boardRef.current, ids0);""",
"""    const { ids, seedJunk } = expandClear(boardRef.current, idx);""")

# 4) makePreview も共通関数に（プレビュー＝実際の消去範囲）
rep("""  const makePreview = (b, idx) => {
    const seedJunk = b[idx].type === JUNK;
    let ids0 = findGroup(b, idx);
    if (!seedJunk) {
      const hasBolt = b.some(c => ids0.has(c.id) && c.special === "bolt");
      if (hasBolt) {
        const t = b[idx].type;
        b.forEach(c => { if (c.type === t) ids0.add(c.id); });
      }
    }
    const ids = seedJunk ? ids0 : expandIds(b, ids0);
    return { ids, over:true, info: groupInfo(b, ids) };
  };""",
"""  const makePreview = (b, idx) => {
    const { ids } = expandClear(b, idx);
    return { ids, over:true, info: groupInfo(b, ids) };
  };""")

io.open(p, "w", encoding="utf-8").write(s)
print("RELIC PATCH OK")
