# ドロップバトル（ローグライク版 v2）

分岐マップでルートを選びながら、同色ドロップを消して敵と戦うパズルローグライク。
`index.html` をブラウザで開くだけで遊べる（単一ファイル・React UMD CDN）。

## 構成
- `index.html` — ゲーム本体
- `assets/` — キャラ透過PNG（ComfyUI + Anima 生成、256px）
- `assets_raw/` — 生成元 768px（再処理用）
- `docs/敵行動パターン仕様書.html` — 敵の行動パターン・スケーリング・アート規定の資料
- `gen_chars.py` — ComfyUI API でキャラ再生成（`python gen_chars.py [名前...]`、要 ComfyUI:8188 起動）
- `process_assets.py` — rembg(isnet-anime)+四隅キーイング → assets/ へ透過・縮小
- `smoke_db.py 〜 smoke_db7.py` — Playwright ヘッドレス実行時テスト（`?test=1` フック使用）

## v2 の主な内容
- 敵行動パターン制（毎ターン攻撃／2連撃／2ターンため→大技／お邪魔変換／仲間回復）＋行動予告表示
- お邪魔ドロップ（✖・消しても効果ゼロ）
- 攻撃はターゲット単体のみ。「貫」ドロップを消したターンだけ貫通
- 敵HP数値表示
- グラフィック一新（スレスパ×ポケモン中間・グロー廃止・フラットセル塗り）
- 待機は疑似Live2D式の全体縦スケール呼吸、攻撃/被弾/死亡アニメ付き

## v17: レリック28種
精鋭撃破・章クリア3択・ショップ販売で集めるパッシブ遺物。コイン1.5倍/火力1.1倍/特殊ドロップ+1/毎ターン回復/防御持ち越し等。詳細は docs の仕様書 §10.5。

## クレジット（BGM・すべてCC0/パブリックドメイン）
- "Awake! (Megawall-10)", "Crystal Cave (Song 18)", "Battle Theme A" — cynicmusic.com / pixelsphere.org
- "Epic Boss Battle" — Juhani Junkala
（CC0のためクレジット義務はないが感謝を込めて記載）

## アートスタイル規定（再生成時）
太い暗色アウトライン／フラットなセル塗り／発光・ネオン禁止。詳細は docs の仕様書 §7。
