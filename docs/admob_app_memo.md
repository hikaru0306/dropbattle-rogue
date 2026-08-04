# ドロプシア アプリ版 AdMob 導入メモ（2026/8/5）

## 方針
- 広告は **AdMob に統一**。ゲーム側は `window.Ads`（ads.js）だけを見る
- Web版（GitHub Pages）は仮公開 → **ダミー広告**（ads.js が自動でダミーにフォールバック）
- アプリ公開後は Web 版を遊べなくする予定（version.json のフラグ等で対応・未実装）

## 発行済みID（iOS）
| 用途 | ID | 書く場所 |
|---|---|---|
| アプリID | `ca-app-pub-5302373872245596~5064080793` | iOS: `Info.plist` の `GADApplicationIdentifier` |
| リワード広告ユニットID | `ca-app-pub-5302373872245596/9315417079` | `ads.js` の `ADMOB_IDS.ios`（設定済み） |

Android は未発行。発行したら `ads.js` の `ADMOB_IDS.android` と `AndroidManifest.xml` の
`com.google.android.gms.ads.APPLICATION_ID` に記入。

## Capacitor セットアップ手順（アプリ化するとき）
```bash
npm init -y
npm i @capacitor/core @capacitor/cli @capacitor/ios @capacitor-community/admob
npx cap init DROPSIA com.hikaru.dropsia --web-dir .
npx cap add ios
npx cap sync
```
- `capacitor.config.json` の `webDir` はこのリポジトリ直下（index.html がある場所）
- `npx cap sync` 後、Xcode で `Info.plist` に以下を追加:
  - `GADApplicationIdentifier` = アプリID（上表）
  - `NSUserTrackingUsageDescription` = トラッキング許可の説明文（ATT。例:「広告の最適化に使用します」）
- ads.js は Capacitor ネイティブ実行を自動判定して AdMob 実装に切り替わる（コード変更不要）

## リリース前チェックリスト
- [ ] `ads.js` の `ADMOB_TESTING` を **false** に（trueの間はテスト広告）
- [ ] **app-ads.txt を設置**（ID悪用対策の本命）: AdMobコンソールでアプリをストア掲載情報と紐付け →
      指示された1行を開発者サイト（GitHub Pagesで可）のルートに `app-ads.txt` として置く →
      AdMobで検証。※広告ユニットIDは公開前提の識別子なのでコード内に書いてよい（ユーザー確認済み 2026/8/5）
- [ ] iOS ATT: 必要なら `AdMob.requestTrackingAuthorization()` を初期化前に呼ぶ（現状未実装・審査方針に合わせる）
- [ ] 実機でリワード2種（敗北復活・行商人コイン150）の視聴完了/途中キャンセル両方を確認
- [ ] Web版の停止フラグ（アプリ公開時に実装）

## ゲーム側の仕様（実装済み・index.html）
- 敗北画面「広告を見て復活」: 1冒険1回・HP40%・ターン仕切り直し。セーブv2 `adRev` で引き継ぎ
- 行商人「広告を見るとコイン+150」: 行商人1人につき1回（`shop.adUsed`）
- `window.Ads` が無い/enabled=false なら広告UIは一切出ない
- テスト: `?adstub=1` でダミー広告を強制ロード / `__test.stubAds(ok)` で成否を差し込み
  （スモーク: scratchpad smoke_ads.py 20項目）
