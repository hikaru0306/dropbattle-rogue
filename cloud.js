// =============================================================
// ドロプシア クラウド同期 (Firebase Auth + Firestore lite)
//  - 匿名ログイン自動 → Googleアカウント連携で端末間引き継ぎ
//  - localStorage の db_* をそのまま users/{uid} にミラー保存
//  - このファイルが読めない / 設定未投入なら window.Cloud は生成されず、
//    ゲームは従来どおり localStorage のみで完全動作する
// 状態は window.Cloud.state で参照、変化は "cloud-state" CustomEvent で通知。
// =============================================================

// ▼▼ Firebaseコンソール「プロジェクトの設定 > マイアプリ」の firebaseConfig をここに貼る ▼▼
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyCzeHjUxC6uTZ_w-32pWsV94IWQM92oIVM",
  authDomain: "dropsia.firebaseapp.com",
  projectId: "dropsia",
  appId: "1:315158854448:web:3c8f6fa31b7c332ce6a6f5",
};
// ▲▲ ここまで ▲▲

const CLIENT_VERSION = "cloud-v1";
const FB = "https://www.gstatic.com/firebasejs/11.10.0/";
const Q = location.search;
const EMU = Q.indexOf("fbemu=1") >= 0;

// ?test=1(既存スモークテスト) / ?nocloud=1 では一切初期化しない
if (Q.indexOf("test=1") < 0 && Q.indexOf("nocloud=1") < 0 &&
    (EMU || FIREBASE_CONFIG.apiKey.indexOf("PASTE") !== 0)) {
  main().catch(e => console.warn("[cloud] init failed:", e));
}

async function main() {
  const [{ initializeApp }, A, F] = await Promise.all([
    import(FB + "firebase-app.js"),
    import(FB + "firebase-auth.js"),
    import(FB + "firebase-firestore-lite.js"),
  ]);
  const app = initializeApp(EMU ? { apiKey: "demo", authDomain: "demo.firebaseapp.com", projectId: "demo-dropsia" } : FIREBASE_CONFIG);
  const auth = A.getAuth(app);
  const db = F.getFirestore(app);
  if (EMU) {
    A.connectAuthEmulator(auth, "http://127.0.0.1:9099", { disableWarnings: true });
    F.connectFirestoreEmulator(db, "127.0.0.1", 8080);
  }
  try { A.useDeviceLanguage(auth); } catch (e) {}

  const LS = window.localStorage;
  const state = {
    status: "init",            // init | syncing | synced | conflict | offline | error
    uid: null, email: null, linked: false,
    lastSync: Number(LS.getItem("db_cloud_last") || 0) || null,
    conflict: null,            // { local:{summary,time}, remote:{summary,time} }
    msg: null,
  };
  const emit = () => window.dispatchEvent(new CustomEvent("cloud-state", { detail: { ...state, conflict: state.conflict && { local: state.conflict.local, remote: state.conflict.remote } } }));

  // ---- localStorage ミラー ----
  const isGameKey = k => typeof k === "string" && k.indexOf("db_") === 0 && k.indexOf("db_cloud") !== 0 && k.indexOf("db_bak_") !== 0;
  const readLocal = () => {
    const d = {};
    for (let i = 0; i < LS.length; i++) {
      const k = LS.key(i);
      if (!isGameKey(k)) continue;
      const v = LS.getItem(k);
      if (v != null && v.length < 100000) d[k.slice(3)] = v; // 異常肥大キーは送らない
    }
    return d;
  };

  // ---- 進捗サマリ（Firestoreコンソールで一目で読める1行文字列） ----
  function buildProgress() {
    let chars = { u: [0], c: [], cu: [] }, stats = {};
    try { const j = JSON.parse(LS.getItem("db_chars")); if (j && Array.isArray(j.u)) chars = { u: j.u, c: j.c || [], cu: j.cu || [] }; } catch (e) {}
    try { const j = JSON.parse(LS.getItem("db_charstats")); if (j && typeof j === "object" && j) stats = j; } catch (e) {}
    const names = (window.TEXTS && TEXTS.chars) ? TEXTS.chars.map(c => c.name) : [];
    const nm = i => names[i] || ("キャラ" + i);
    let best = null, bestU = null;
    for (const k in stats) {
      const r = stats[k].reach, ru = stats[k].reachU;
      if (r && (!best || r[0] > best[0] || (r[0] === best[0] && r[1] > best[1]))) best = r;
      if (ru && (!bestU || ru[0] > bestU[0] || (ru[0] === bestU[0] && ru[1] > bestU[1]))) bestU = ru;
    }
    const deep = bestU ? ("裏" + (bestU[0] + 1) + "章" + bestU[1] + "F") : best ? ((best[0] + 1) + "章" + best[1] + "F") : "—";
    let totalClears = 0, totalUra = 0;
    for (const k in stats) { totalClears += stats[k].clears || 0; totalUra += stats[k].uraClears || 0; }
    const summary = "解放" + chars.u.length + "/7｜表:" + (chars.c.map(nm).join(",") || "—") +
      "｜裏:" + (chars.cu.map(nm).join(",") || "—") + "｜最深:" + deep;
    return { summary: summary.slice(0, 400), progress: {
      unlocked: chars.u.length, clearedOmote: chars.c, clearedUra: chars.cu,
      totalClears, totalUraClears: totalUra, perChar: stats,
    } };
  }

  // ---- Push（ローカル → クラウド）----
  let pushTimer = null;
  async function push() {
    const user = auth.currentUser;
    if (!user) return;
    clearTimeout(pushTimer); pushTimer = null;
    const now = Date.now();
    const p = buildProgress();
    state.status = "syncing"; emit();
    try {
      await F.setDoc(F.doc(db, "users", user.uid), {
        v: 1, updatedAt: now, svTime: F.serverTimestamp(), clientVersion: CLIENT_VERSION,
        linked: state.linked, summary: p.summary, progress: p.progress, data: readLocal(),
      });
      try { LS.setItem("db_cloud_last", String(now)); LS.removeItem("db_cloud_dirty"); } catch (e) {}
      state.lastSync = now; state.status = "synced"; emit();
    } catch (e) {
      console.warn("[cloud] push failed:", e);
      state.status = "offline"; emit();
    }
  }
  function markDirty() {
    if (state.conflict) return;
    try { LS.setItem("db_cloud_dirty", "1"); } catch (e) {}
    if (!auth.currentUser) return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(() => push(), 5000);
  }
  function flush() {
    if (LS.getItem("db_cloud_dirty") === "1" && auth.currentUser && !state.conflict) push();
  }
  window.addEventListener("pagehide", flush);
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden") flush(); });

  // ---- Restore（クラウド → ローカル、reloadで反映）----
  function restore(remote, backupLocal) {
    window.__dbRestoring = true;
    try {
      const kill = [];
      for (let i = 0; i < LS.length; i++) { const k = LS.key(i); if (isGameKey(k)) kill.push(k); }
      kill.forEach(k => { if (backupLocal) { try { LS.setItem("db_bak_" + k.slice(3), LS.getItem(k)); } catch (e) {} } LS.removeItem(k); });
      const d = remote.data || {};
      for (const k in d) { if (typeof d[k] === "string") LS.setItem("db_" + k, d[k]); }
      LS.setItem("db_cloud_last", String(remote.updatedAt || Date.now()));
      LS.removeItem("db_cloud_dirty");
    } finally { window.__dbRestoring = false; }
    location.reload(); // タイトル画面でしか起きないので無害。stateの再読込を確実にする
  }

  // ---- Pull & 突き合わせ（起動時・ログイン/連携直後）----
  // ミラー同士の完全一致（キー集合と全値が同じ）。pushはreadLocal()をそのまま送るので
  // 値はどちらも文字列
  const sameData = (a, b) => {
    a = a || {}; b = b || {};
    const ka = Object.keys(a);
    return ka.length === Object.keys(b).length && ka.every(k => a[k] === b[k]);
  };
  let conflictDoc = null;
  async function reconcile() {
    const user = auth.currentUser;
    if (!user) return;
    state.status = "syncing"; emit();
    let snap;
    try { snap = await F.getDoc(F.doc(db, "users", user.uid)); }
    catch (e) { console.warn("[cloud] pull failed:", e); state.status = "offline"; emit(); return; }
    const remote = snap.exists() ? snap.data() : null;
    const local = readLocal();
    // 実プレイの痕跡（音量やチュートリアルフラグだけなら「空」扱い）
    const hasLocal = Object.keys(local).some(k => k === "chars" || k === "charstats" || k.indexOf("save_") === 0);
    const last = Number(LS.getItem("db_cloud_last") || 0);
    const dirty = LS.getItem("db_cloud_dirty") === "1";
    if (!remote) { if (Object.keys(local).length) await push(); else { state.status = "synced"; emit(); } return; }
    if (!hasLocal) { restore(remote, false); return; }                    // 新端末 → 無言リストア
    if ((remote.updatedAt || 0) <= last) {                                // ローカルが同等以上
      if (dirty) await push(); else { state.status = "synced"; emit(); }
      return;
    }
    // 中身が完全に同じなら分岐ではない（pagehide中のpushでクラウド保存は届いたが
    // db_cloud_last更新前にページが落ちた等）→ クラウドの時刻を取り込んで同期済みに
    if (sameData(remote.data, local)) {
      try { LS.setItem("db_cloud_last", String(remote.updatedAt || Date.now())); LS.removeItem("db_cloud_dirty"); } catch (e) {}
      state.lastSync = remote.updatedAt || null; state.status = "synced"; emit();
      return;
    }
    if (!dirty && last > 0) { restore(remote, false); return; }           // クラウドだけ進んでいる
    // 両側が分岐（または一度も同期していない端末にローカルデータあり）→ ユーザー選択
    conflictDoc = remote;
    state.conflict = {
      local:  { summary: buildProgress().summary, time: last || null },
      remote: { summary: remote.summary || "(サマリなし)", time: remote.updatedAt || null },
    };
    state.status = "conflict"; emit();
  }

  // 競合解決: "local"=この端末を採用 / "remote"=クラウドを採用
  function resolveConflict(choice) {
    if (!state.conflict || !conflictDoc) return;
    const docBak = conflictDoc;
    state.conflict = null; conflictDoc = null;
    if (choice === "remote") {
      restore(docBak, true);                                              // 負けた側は db_bak_* に退避
    } else {
      try { LS.setItem("db_bak_remote", JSON.stringify(docBak.data || {})); } catch (e) {}
      LS.setItem("db_cloud_dirty", "1");
      push();
    }
  }

  // ---- 認証 ----
  function readUser(user) {
    state.uid = user.uid;
    state.linked = (user.providerData || []).some(p => p.providerId === "google.com");
    state.email = user.email || ((user.providerData || [])[0] || {}).email || null;
  }
  async function handleLinkError(e, provider) {
    const code = e && e.code || "";
    if (code === "auth/credential-already-in-use" || code === "auth/email-already-in-use") {
      // このGoogleアカウントは既に別データに紐付いている → そちらのユーザーに切り替え
      const cred = A.GoogleAuthProvider.credentialFromError(e);
      if (cred) {
        try { LS.removeItem("db_cloud_last"); } catch (e2) {}             // 旧uidの同期時刻は無効
        await A.signInWithCredential(auth, cred);                        // onAuthStateChanged → reconcile（必要なら競合モーダル）
        return { ok: true, switched: true };
      }
    }
    if (code === "auth/popup-blocked" || code === "auth/operation-not-supported-in-this-environment") {
      try { await A.linkWithRedirect(auth.currentUser, provider); return { ok: true, redirect: true }; }
      catch (e2) { return { ok: false, msg: "このブラウザでは連携できませんでした。別のブラウザでお試しください" }; }
    }
    if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") return { ok: false, msg: "キャンセルされました" };
    console.warn("[cloud] link failed:", e);
    return { ok: false, msg: "連携に失敗しました (" + (code || e) + ")" };
  }
  async function linkGoogle() {
    const user = auth.currentUser;
    const provider = new A.GoogleAuthProvider();
    if (!user) return signInGoogle();
    try {
      await A.linkWithPopup(user, provider);
      readUser(auth.currentUser); emit();
      LS.setItem("db_cloud_dirty", "1"); await push();
      return { ok: true };
    } catch (e) { return handleLinkError(e, provider); }
  }
  async function signInGoogle() {
    const provider = new A.GoogleAuthProvider();
    try {
      try { LS.removeItem("db_cloud_last"); } catch (e) {}
      await A.signInWithPopup(auth, provider);                            // onAuthStateChanged → reconcile
      return { ok: true };
    } catch (e) { return handleLinkError(e, provider); }
  }

  let prevUid = null, booted = false;
  A.onAuthStateChanged(auth, async user => {
    if (!user) {
      try { await A.signInAnonymously(auth); }                            // 初回: 匿名ユーザー自動作成
      catch (e) { console.warn("[cloud] anon sign-in failed:", e); state.status = "offline"; emit(); }
      return;
    }
    if (prevUid && prevUid !== user.uid) { try { LS.removeItem("db_cloud_last"); } catch (e) {} }
    prevUid = user.uid;
    readUser(user);
    await reconcile();
  });
  try { await A.getRedirectResult(auth); }                                // リダイレクト連携の戻り
  catch (e) { await handleLinkError(e, new A.GoogleAuthProvider()); }

  window.__dbDirty = markDirty;                                           // head のStorageパッチと接続
  window.Cloud = {
    get state() { return { ...state, conflict: state.conflict && { ...state.conflict } }; },
    linkGoogle, signInGoogle, resolveConflict, pushNow: push,
  };
  if (!booted) { booted = true; emit(); }
}
