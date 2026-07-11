# -*- coding: utf-8 -*-
"""宝箱パズルモード: 3手でちょうど目標個数を消すとレリック（個数毎に別レリック）、外すとアイテム"""
import io, sys

p = "index.html"
s = io.open(p, encoding="utf-8").read()

def rep(old, new):
    global s
    if s.count(old) != 1:
        print("ANCHOR FAIL:", old[:90])
        sys.exit(1)
    s = s.replace(old, new)

# 1) state
rep("""  const [rewards, setRewards] = useState(null); // {picks, kind:'battle'|'elite'|'treasure'|'horde', healed}""",
"""  const [rewards, setRewards] = useState(null); // {picks, kind:'battle'|'elite'|'treasure'|'horde', healed}
  const [puzzle, setPuzzle] = useState(null); // {target, moves, cleared, relics:[3], done}
  const puzzleRef = useRef(null);""")

# 2) パズル開始/タップ/終了（enterNodeの直前に定義）
rep("""  // ===== ノード進入 =====""",
"""  // ===== 宝箱パズル =====
  const startPuzzle = () => {
    const bd = Array.from({ length: 36 }, () => ({ id: UID++, type: Math.floor(Math.random() * 4), special: false }));
    commitBoard(bd);
    // 盤面から目標を算出: 上位3グループ合計から2〜4引く（＝最大消しではぴったりにならない）
    const seen = new Set(); const sizes = [];
    bd.forEach((c, i) => {
      if (seen.has(c.id)) return;
      const g = findGroup(bd, i);
      g.forEach(id => seen.add(id));
      sizes.push(g.size);
    });
    sizes.sort((a, b) => b - a);
    const maxSum = (sizes[0] || 0) + (sizes[1] || 0) + (sizes[2] || 0);
    const target = Math.max(10, maxSum - 2 - Math.floor(Math.random() * 3));
    const relics = pickRelics(3);
    const pz = { target, moves: 3, cleared: 0, relics, done: null };
    setPuzzle(pz); puzzleRef.current = pz;
    setClearing(new Set()); setPreview(null); setPops({}); setArmed(null);
    setStatus("puzzle"); statusRef.current = "puzzle";
    setLocked(false); lockedRef.current = false;
    SFX.open();
  };
  const puzzleTap = idx => {
    const pz = puzzleRef.current;
    if (!pz || pz.moves <= 0 || pz.done) return;
    const ids = findGroup(boardRef.current, idx);
    const count = ids.size;
    const next = boardRef.current.map(c => ids.has(c.id) ? { id: UID++, type: Math.floor(Math.random() * 4), special: false } : c);
    SFX.clear();
    setClearing(new Set(ids));
    setLocked(true); lockedRef.current = true;
    const cleared = pz.cleared + count, moves = pz.moves - 1;
    setTimeout(() => {
      commitBoard(next);
      setClearing(new Set());
      let done = null;
      if (moves <= 0) {
        const diff = cleared - pz.target;
        const rk = Math.abs(diff) <= 1 ? pz.relics[diff + 1] : null;
        if (rk) {
          addRelic(rk);
          done = { kind: "relic", relic: rk, cleared };
          SFX.coin();
        } else {
          const k = pick(Object.keys(CONSUM));
          if (itemsRef.current.length < itemCap()) {
            setItemsBoth([...itemsRef.current, k]);
            done = { kind: "item", item: k, cleared };
          } else {
            setCoinsBoth(coinsRef.current + 40);
            done = { kind: "coins", coins: 40, cleared };
          }
          SFX.pick();
        }
      }
      const npz = { ...pz, cleared, moves, done };
      setPuzzle(npz); puzzleRef.current = npz;
      setLocked(false); lockedRef.current = false;
    }, FAST ? 40 : 240);
  };
  puzzleTapRef.current = puzzleTap;
  const closePuzzle = () => {
    setPuzzle(null); puzzleRef.current = null;
    SFX.step();
    finishNode();
  };

  // ===== ノード進入 =====""")

# 3) puzzleTapRef 宣言
rep("""  const commitRef = useRef(() => {});""",
"""  const commitRef = useRef(() => {});
  const puzzleTapRef = useRef(() => {});""")

# 4) enterNode: 宝箱の一部をパズル化（TEST_MODEでは常に従来型＝決定性維持）
rep("""    if (node.type === "treasure") {
      const picks = shuffle(ITEM_KEYS.slice()).slice(0, hasR("magnet") ? 4 : 3);
      setRewards({ picks, kind:"treasure", healed:0 });
      setStatus("reward"); statusRef.current = "reward";
      return;
    }""",
"""    if (node.type === "treasure") {
      if (!TEST_MODE && Math.random() < 0.45) { startPuzzle(); return; } // 不思議な宝箱（パズル）
      const picks = shuffle(ITEM_KEYS.slice()).slice(0, hasR("magnet") ? 4 : 3);
      setRewards({ picks, kind:"treasure", healed:0 });
      setStatus("reward"); statusRef.current = "reward";
      return;
    }""")

# 5) commit: パズル時はpuzzleTapへ
rep("""  const commit = useCallback(idx => {
    if (lockedRef.current || statusRef.current !== "battle") return;""",
"""  const commit = useCallback(idx => {
    if (lockedRef.current) return;
    if (statusRef.current === "puzzle") { puzzleTapRef.current(idx); return; }
    if (statusRef.current !== "battle") return;""")

# 6) onDown: パズル中も反応（アクション条件はバトルのみ）
rep("""  const onDown = (e, idx) => {
    if (lockedRef.current || statusRef.current !== "battle") return;
    if (!actionRef.current || usedRef.current.has(actionRef.current)) return;""",
"""  const onDown = (e, idx) => {
    if (lockedRef.current || (statusRef.current !== "battle" && statusRef.current !== "puzzle")) return;
    if (statusRef.current === "battle" && (!actionRef.current || usedRef.current.has(actionRef.current))) return;""")

# 7) 盤面JSXを boardEl として抽出
rep("""      // 盤面
      h("div", { className:"relative rounded-2xl board-wrap", style:{ padding:5, background:"rgba(19,14,28,.8)", border:"2px solid #3c3450", marginBottom:4 } },""",
"""      // 盤面
      boardEl,
      overlays));
}

  var root = RD.createRoot(document.getElementById('root'));
  root.render(h(DropBattle));
})();
PUZZLE_SPLIT_MARKERh("div", { className:"relative rounded-2xl board-wrap", style:{ padding:5, background:"rgba(19,14,28,.8)", border:"2px solid #3c3450", marginBottom:4 } },""")
# 分割: 旧盤面ブロック（マーカー以降に残っている）を回収して boardEl 定義に転用
head, tail = s.split("PUZZLE_SPLIT_MARKER")
board_block_end = tail.index("          }))),\n      overlays));")
board_block = tail[:board_block_end] + "          })));"
rest = tail[board_block_end + len("          }))),\n      overlays));"):]
# rest には旧 return 終端の "}\n\n  var root = ..." が残る → 除去して head と結合
s = head.rstrip()
# 旧末尾の後始末: rest から余計な旧フッタを削除（"}"とroot.render部分）
import re
rest_clean = re.sub(r"^\s*\}\s*var root = RD\.createRoot[\s\S]*?\)\(\);\s*", "", rest, count=1)
if "root.render" in rest_clean:
    print("TAIL CLEAN FAIL"); sys.exit(1)
s = s + "\n" + rest_clean
# boardEl 定義をマップ画面の直前に挿入
rep("""  if (status === "map" || (status === "reward" && pendingNodeRef.current && pendingNodeRef.current.type === "treasure")) {""",
"""  const boardEl = """ + board_block + """

  // ===== 宝箱パズル画面 =====
  if (status === "puzzle" && puzzle) {
    return h("div", { style: rootStyle, className:"w-full flex justify-center px-3 py-2" },
      h("div", { key:"scr-puzzle", className:"w-full fade-in", style:{ maxWidth:440 } },
        header,
        h("div", { className:"rounded-2xl px-3 py-2 mb-1 text-center", style:{ background:"rgba(30,24,42,.92)", border:"2px solid #8a6f3c" } },
          h("div", { className:"flex items-center justify-center gap-2 font-bold", style:{ color:"#ffd95c", fontSize:"1.02rem" } }, Ic("assets/node_treasure.png", 20), "不思議な宝箱"),
          h("p", { className:"text-[11px] mt-0.5", style:{ opacity:0.85 } },
            "3回の消去で 合計ぴったり ", h("b", { style:{ color:"#ffd95c", fontSize:"0.9rem" } }, puzzle.target), " 個（±1個OK）消すと…"),
          h("div", { className:"flex justify-center gap-1.5 mt-1 text-[10px]", style:{ flexWrap:"wrap" } },
            [-1, 0, 1].map(d => h("span", { key:d, className:"rounded-full px-2 py-0.5", style:{ background:"rgba(232,192,106,.1)", border:"1px solid rgba(216,168,72,.4)", color:"#e8d8a8" } },
              (puzzle.target + d) + "個 → " + (puzzle.relics[d + 1] ? RELICS[puzzle.relics[d + 1]].icon + RELICS[puzzle.relics[d + 1]].name : "アイテム"))),
          h("div", { className:"flex justify-center gap-5 mt-1.5 text-sm font-bold" },
            h("span", { style:{ color:"#c9bfe0" } }, "消した数 ", h("span", { style:{ color:"#7cffb0", fontSize:"1.1rem", fontVariantNumeric:"tabular-nums" } }, puzzle.cleared)),
            h("span", { style:{ color:"#c9bfe0" } }, "残り ", h("span", { style:{ color:"#e8c06a", letterSpacing:2 } }, "●".repeat(puzzle.moves) + "○".repeat(3 - puzzle.moves))))),
        boardEl,
        h("p", { className:"text-center text-[10px]", style:{ opacity:0.6 } }, "外れても アイテム or コインは貰える"),
        overlays));
  }

  if (status === "map" || (status === "reward" && pendingNodeRef.current && pendingNodeRef.current.type === "treasure")) {""")

# 8) パズル結果オーバーレイ
rep("""  if (restMsg) overlays.push(""",
"""  if (puzzle && puzzle.done) {
    const d = puzzle.done;
    const hit = d.kind === "relic";
    overlays.push(h("div", { key:"pzdone", className:"fixed inset-0 flex items-center justify-center px-6 fade-in", style:{ background:"rgba(8,4,14,.88)", zIndex:56 } },
      h("div", { className:"text-center pop-in rounded-2xl p-4 w-full", style:{ maxWidth:340, background:"rgba(30,24,42,.98)", border:"2px solid #8a6f3c" } },
        h("div", { className:"font-bold", style:{ fontSize:"1.3rem", color: hit ? "#ffd95c" : "#c9bfe0", textShadow:"0 2px 0 rgba(0,0,0,.55)" } },
          hit ? "ぴったり！" : "おしい…"),
        h("p", { className:"my-1 text-sm", style:{ opacity:0.85 } }, "合計 ", h("b", { style:{ color:"#7cffb0" } }, d.cleared), " 個（目標 ", puzzle.target, " 個）"),
        hit && h("div", { className:"flex items-center justify-center gap-2 rounded-xl px-3 py-2 my-2", style:{ background:"rgba(232,192,106,.1)", border:"1px solid rgba(216,168,72,.5)" } },
          h("span", { style:{ fontSize:"1.5rem" } }, RELICS[d.relic].icon),
          h("span", { className:"text-left" },
            h("span", { className:"font-bold text-sm block", style:{ color:"#e8c06a" } }, "レリック獲得: ", RELICS[d.relic].name),
            h("span", { className:"block text-[10px]", style:{ opacity:0.8 } }, RELICS[d.relic].desc))),
        d.kind === "item" && h("p", { className:"my-2 text-sm font-bold", style:{ color:"#8ce8b0" } }, CONSUM[d.item].icon, " ", CONSUM[d.item].name, " を獲得"),
        d.kind === "coins" && h("p", { className:"my-2 text-sm font-bold flex items-center justify-center gap-1", style:{ color:"#e8c06a" } }, Ic("assets/icon_coin.png", 14), "+", d.coins),
        h("button", { onClick: closePuzzle, className:"w-full rounded-xl py-2.5 font-bold mt-1",
          style:{ background:"linear-gradient(180deg,#e8c06a,#b8862e)", color:"#2c2030", border:"1px solid #6e4e1a" } }, "先へ進む ▶"))));
  }
  if (restMsg) overlays.push(""")

# 9) テストフック: puzzle状態 + 強制開始
rep("""        selectable: statusRef.current === "map" ? selectableIds() : [],""",
"""        puzzle: puzzleRef.current ? { target: puzzleRef.current.target, moves: puzzleRef.current.moves, cleared: puzzleRef.current.cleared, done: puzzleRef.current.done ? puzzleRef.current.done.kind : null } : null,
        selectable: statusRef.current === "map" ? selectableIds() : [],""")
rep("""      restart: """,
"""      startPuzzle: () => startPuzzle(),
      restart: """)

io.open(p, "w", encoding="utf-8").write(s)
print("PUZZLE PATCH OK")
