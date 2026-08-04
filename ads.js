/* ===== 広告ブリッジ（AdMob統一方針・2026/8/5）=====
 * ゲーム側(index.html)は window.Ads だけを見る:
 *   Ads.enabled            … 広告ボタンを出してよいか
 *   Ads.show(name, cb)     … リワード広告を再生。視聴完了なら cb(true)、中断/失敗なら cb(false)
 *
 * 方針:
 *   ・本命はアプリ版（Capacitor + @capacitor-community/admob のリワード広告）
 *   ・Web版は仮公開なのでダミー広告（1.5秒の疑似再生→必ず視聴完了扱い）
 *   ・アプリ公開後はWeb版を遊べなくする予定（そのときは version.json 等のフラグで対応）
 * 実行環境の判定はこのファイル内で行う: Capacitorネイティブ＝AdMob / それ以外＝ダミー。
 * セットアップ手順は docs/admob_app_memo.md 参照。
 */
(function () {
  // ---- AdMob 設定（AdMobコンソールで発行したリワード広告ユニットIDを入れる）----
  var ADMOB_IDS = {
    android: "",   // Android版のリワード広告ユニットID（未発行）
    ios: "ca-app-pub-5302373872245596/9315417079"  // リワード広告ユニットID（2026/8/5発行）
  };
  // ※アプリID ca-app-pub-5302373872245596~5064080793 は広告ユニットではなく
  //   アプリ側の設定（iOS: Info.plist の GADApplicationIdentifier）に入れる → docs/admob_app_memo.md
  var ADMOB_TESTING = true; // true の間はテスト広告。ストア公開時に false へ

  var C = window.Capacitor;
  var isNative = !!(C && C.isNativePlatform && C.isNativePlatform());
  var AdMob = isNative && C.Plugins ? C.Plugins.AdMob : null;

  // ================= アプリ版: AdMob リワード広告 =================
  if (AdMob) {
    var adId = (C.getPlatform && C.getPlatform() === "ios") ? ADMOB_IDS.ios : ADMOB_IDS.android;
    if (!adId && !ADMOB_TESTING) { window.Ads = { enabled: false, show: function (n, cb) { cb(false); } }; return; }
    var ready = false, loading = false, pending = null; // pending={cb,rewarded}
    var load = function () {
      if (loading || ready) return;
      loading = true;
      AdMob.prepareRewardVideoAd({ adId: adId, isTesting: ADMOB_TESTING })
        .then(function () { ready = true; loading = false; })
        .catch(function () { loading = false; setTimeout(load, 30000); }); // 失敗したら30秒後に再ロード
    };
    var finish = function (ok) {
      var p = pending; pending = null;
      ready = false; load(); // 次の1本を先読み
      if (p) p.cb(!!ok);
    };
    AdMob.addListener("onRewardedVideoAdReward", function () { if (pending) pending.rewarded = true; });
    AdMob.addListener("onRewardedVideoAdDismissed", function () { if (pending) finish(pending.rewarded); });
    AdMob.addListener("onRewardedVideoAdFailedToShow", function () { if (pending) finish(false); });
    AdMob.initialize({}).then(load).catch(function () {});
    window.Ads = {
      enabled: true,
      show: function (name, cb) {
        if (pending) return;
        if (!ready) { load(); cb(false); return; } // 在庫なし→ゲーム側が「再生できなかった」を表示
        pending = { cb: cb, rewarded: false };
        AdMob.showRewardVideoAd().catch(function () { finish(false); });
      }
    };
    return;
  }

  // ================= Web版（仮公開）: ダミー広告 =================
  window.Ads = {
    enabled: true,
    show: function (name, cb) {
      var ov = document.createElement("div");
      ov.id = "ad-stub";
      ov.style.cssText = "position:fixed;inset:0;z-index:9999;background:#000;color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;font:bold 15px sans-serif";
      ov.innerHTML = "<div>広告（仮）を再生中…</div><div style='font-size:11px;opacity:.6'>アプリ版では本物の広告が流れます</div>";
      document.body.appendChild(ov);
      setTimeout(function () { ov.remove(); cb(true); }, 1500);
    }
  };
})();
