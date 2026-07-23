# テクスチャ全差し替え（ChatGPT再出力）進捗メモ

2026-07-23 開始。プレイヤー(hero1〜7)とアプリアイコン(favicon/icon-192/icon-512/touch-icon)以外の全PNG 187枚が対象。
順序: 敵など大物77枚 → アイコン類110枚（retex_targets.txt の順）。

- 指示テンプレ（全画像が透過済みのため）: 「輪郭は黒い線のみにして（白い縁取りは削除）、輪郭の白のガビガビを消して、背景を透過して、見切れないように出力して。デザイン・色・画風はそのまま維持して。」（2枚目以降。ユーザーFBで黒縁指定を追加）
- 処理: DL → process_regen.py（偽透過ならrembg → トリム → 元サイズに合わせ縮小 → assets/差し替え・元はassets_backup_pre_chatgpt/へ退避）
- 生成生データ: assets_regen_raw/

## ステータス凡例
- OK: 差し替え済み・見た目維持
- RETRY→OK: 1回目で見た目が変わったため再出力して差し替え
- 要確認: 見た目が変わっている可能性あり。ユーザー確認待ち（差し替え済み or 保留を明記）
- 保留: 差し替えせず元のまま

## 進捗

（ここに1枚ずつ追記）
- alraune.png: OK（検品済み）
- banshee.png: RETRY→OK（フルカラー維持プロンプトで再生成・検品済み差し替え）
- bat.png: OK（検品済み）
- bdragon.png: OK（検品済み）
- bee.png: RETRY→OK（検品済み差し替え）
- behemot.png: OK（検品済み）
- boar.png: RETRY→OK（検品済み差し替え）
- bonek.png: OK（検品済み）
- boss.png: OK（検品済み）
- cobra.png: OK（検品済み）
- cosmo.png: OK（検品済み）
- crab.png: OK（検品済み）
- crow.png: OK（検品済み）
- demonx.png: OK（検品済み）
- djinn.png: OK（検品済み）
- dragon.png: OK（検品済み）
- drake.png: OK（検品済み）
- demon.png: ユーザー判断で適用（2026/7/24）
- dryad.png: OK（検品済み）
- eel.png: OK（検品済み）
- eye.png: OK（検品済み）
- fenrir.png: OK（検品済み）
- fgolem.png: OK（検品済み）
- fox.png: OK（検品済み）
- frost.png: OK（検品済み）
- gargo(RETRY→OK 胴体維持指示): OK（一括検品済み差し替え）
- gazer(RETRY→OK 目維持指示): OK（一括検品済み差し替え）
- ghoul(RETRY→OK 腕配色指示): OK（一括検品済み差し替え）
- golem: OK（一括検品済み差し替え）
- hound: OK（一括検品済み差し替え）
- icewolf: OK（一括検品済み差し替え）
- ifrit: OK（一括検品済み差し替え）
- ifrita: OK（一括検品済み差し替え）
- imp: OK（一括検品済み差し替え）
- knight: OK（一括検品済み差し替え）
- kslime: OK（一括検品済み差し替え）
- lich: OK（一括検品済み差し替え）
- mandra: OK（一括検品済み差し替え）
- mant: OK（一括検品済み差し替え）
- mare: OK（一括検品済み差し替え）
- merchant: OK（一括検品済み差し替え）
- moth: OK（一括検品済み差し替え）
- mudman: OK（一括検品済み差し替え）
- mummy: OK（一括検品済み差し替え）
- noct: OK（一括検品済み差し替え）
- owl: OK（一括検品済み差し替え）
- peng: OK（一括検品済み差し替え）
- jotun.png: RETRY→OK（毛皮維持指示・検品済み差し替え）
- kaos.png: RETRY→OK（目維持指示・検品済み差し替え）
- sala.png: 【要確認・保留】ChatGPTが2回とも「第三者コンテンツ類似」で生成拒否（誤判定と思われる）。元のまま維持
- pixie.png: OK（検品済み）
- scarab.png: OK（検品済み）
- scorp.png: OK（検品済み）
- reaper.png: OK（再送後・検品済み）
- raiju.png: RETRY→OK（配色指定・検品済み差し替え）
- shade.png: RETRY→OK（目維持指定・検品済み差し替え）
- skel.png: OK（検品済み）
- sludge.png: OK（検品済み）
- sphinx.png: OK（検品済み）
- skadi.png: RETRY→OK（色維持を最重要指定＋顔の線を描き直し依頼で解決・適用済み）
- slime.png: RETRY→OK（幅高比1.3の横長ドーム型を数値指定して解決・適用済み）
- snail.png: RETRY→OK（自作宣言プロンプトで通過・検品済み差し替え）

## 中断メモ (2026-07-23)
ChatGPT側で「Unusual activity has been detected from your device. Try again later.」が発生し自動操作を一時停止。残り: 大物 snail, spore, thorn, titania, toad, toadking, treant, turtle, vamp, voids, vorax, wisp, wolf, wraith, yeti + アイコン類110枚 + 保留4件(demon/sala/skadi/slime)。
- thorn.png: OK（検品済み）
- titania.png: OK（検品済み）
- toad.png: OK（検品済み）
- toadking.png: OK（検品済み）
- spore.png: RETRY→OK（表情維持指定・検品済み差し替え）
- treant.png: OK（検品済み）
- turtle.png: OK（検品済み）
- vamp.png: OK（検品済み）
- voids.png: OK（検品済み）
- vorax.png: OK（検品済み）
- wisp.png: OK（検品済み）
- wraith.png: OK（検品済み）
- yeti.png: OK（検品済み）
- wolf.png: OK（検品済み・足元にごく薄い影あり、ゲーム内では目立たないと判断）

## 大物77枚 完了 (2026-07-23)
適用73枚 / 保留4枚(demon, sala, skadi, slime)。残り=アイコン類110枚（cs_/mk_/rl_/sk_/st_/icon_/intent_/node_/coin_）。

## アイコン類 方針 (2026-07-23 ユーザー指示)
- 下の楕円影は削除する
- 色違いファミリーは「ベース1枚をChatGPT生成→残りはrecolor_variant.pyで色相変換」して同一ベース化:
  - コア球: rl_redcore → rl_ambercore, rl_jadecore, rl_violetcore
  - 本: rl_guardbook → rl_healbook, rl_swordbook, rl_starbook, rl_prayerbook
  - 盾: rl_shieldcrest → rl_swordcrest(赤), rl_aegis_gr(金)
  - 瓶: cs_potion → icon_heal(緑), rl_holywater(水色)
  - 剣クロス: mk_aoe(金) → node_battle(銀)
  - linegem: rl_linegem → rl_linegemh(90度回転)
  - クロス: mk_plus → rl_crossgem(共用)
- coin_angel: stage済み
- coin_angel.png: OK / cs_aegis.png: OK（検品済み）
- coin_demon.png: RETRY→OK（黒地はローカルで穴埋め復元）
- cs_bomb.png: RETRY→OK（影削除）
- cs_colorize.png: RETRY→OK
- cs_gemrain/cs_might/cs_phoenix/cs_potion/cs_purify/cs_stun/cs_venom: OK（検品済み）
- icon_heal, rl_holywater: cs_potionからrecolor_variant.pyで色変換生成（同一ベース）

## 中断: ChatGPT画像生成の上限到達 (2026-07-23)
「You've hit the Plus plan limit for image generations requests. 上限リセットまで約10時間」
### アイコン進捗（109枚中）
- 適用済み14枚: coin_angel, coin_demon, cs_aegis, cs_bomb, cs_colorize, cs_gemrain, cs_might, cs_phoenix, cs_potion, cs_purify, cs_stun, cs_venom + 色変換2枚(icon_heal, rl_holywater)
- icon_atk: OK（検品済み適用）→適用計15枚
- 未着手: 94枚（icon_bag以降）
### 再開手順
1. retex_targets.txt の icon_bag 以降を順に処理
2. 1枚ずつ: アップ→プロンプト（影削除・白縁削除・黒アウトラインのみ・透過・フルカラー維持）→200秒待ち→DL→process_regen.py stage
3. 数枚ごとにコンタクトシートで検品→process_regen.py apply
4. 色違いファミリーはベースのみ生成し recolor_variant.py で複製（方針は上記参照）

## yeti/alraune ComfyUI一新 (2026-07-24)
- yeti: comfy_yeti_7702 採用（影はローカル除去）/ alraune: comfy_alraune_8803 採用
- 適用済み。旧ChatGPT加工版は assets_cand/{yeti,alraune}_prev_chatgpt_ver.png に退避
- ChatGPT画像生成はまだ上限中。残りアイコン94枚とNG8枚(fgolem,ghoul,imp,mant,mudman,thorn,wisp,wraith)の再加工は枠回復後にChatGPTで（影削除を毎回プロンプトに入れること）
- fgolem.png: REDO→OK（穴3箇所をfix_holes.pyで埋め・影削除）
- ghoul.png: REDO→OK
- imp.png: REDO→OK
- mant.png: REDO→OK（羽根の塗り改善）
- mudman.png: REDO→OK
- thorn.png: ユーザー判断で適用（2026/7/24）
- wisp.png: REDO→OK
- wraith.png: REDO→OK（白抜け解消）

## リテイク8枚 完了 (2026-07-24)
適用7枚: fgolem, ghoul, imp, mant, mudman, wisp, wraith（fix_holes.pyで内部穴埋め＋白フリンジ除去を全数実施）
保留1枚: thorn（尻尾先の白い花が消失）
チェックシート retex_check.html を再構築（リテイク版を最上段にまとめて表示）

## 保留解消＆sala削除 (2026-07-24)
- demon/thorn: ユーザー判断で適用
- skadi: 色維持を最重要指定＋顔の線描き直しでOK→適用
- slime: 幅高比1.3の横長ドーム型を数値指定でOK→適用
- yeti/alraune: ChatGPTで線を整え直して再適用
- sala: ゲームから完全削除（index.html の敵定義/3章light,midプール/シールド定義、docs/ゲームデータ一覧.htmlの行、画像は assets_removed/ へ）。3章lightはifritaで補充、midはbomber追加で数を維持。スモークでコンソールエラーなし

## 全89枚を最小限処理で再適用 (2026-07-24)
ユーザー指摘「ChatGPT出力そのまま使ってる？変な加工が入ってそう」→その通りだった。
- 従来: process_regen.py（rembg/トリム/リサイズ）+ fix_holes.py（内部穴埋め・白フリンジ除去）→ 画像を壊していた
- 変更: **apply_minimal.py**（トリム＋リサイズのみ。アルファが無い画像だけ外周連結の白背景を透明化）
- ChatGPT出力87枚は透過付きだったので全て as-is で再適用。作業前の状態は assets_before_minimal/ に退避
- 市松模様が焼き込まれていた2枚(alraune, skadi)はユーザーが再出力した透過PNGで差し替え→市松なし
- **今後の運用: fix_holes.py は使わない。apply_minimal.py を使う**
