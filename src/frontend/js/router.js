/**
 * OpenClaw GUI — Router
 *
 * SPA 路由、頁面生命週期、側邊欄管理
 */

const VIEW_IDS = ["dashboard", "configuration", "environment", "gateway", "deploy-skills", "install-plugins", "fix-plugins"];

/** 切換至指定頁面 */
function navigateTo(viewId) {
  if (!VIEW_IDS.includes(viewId)) return;

  // 觸發離開事件
  if (state.currentView && pageHooks[state.currentView]?.onLeave) {
    pageHooks[state.currentView].onLeave();
  }

  // 隱藏所有頁面
  for (const id of VIEW_IDS) {
    const el = document.getElementById(`view-${id}`);
    if (el) el.classList.add("hidden");
  }

  // 顯示目標頁面
  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.remove("hidden");

  // 更新側邊欄 active 狀態
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("nav-item-active", item.dataset.view === viewId);
  });

  state.currentView = viewId;

  // 觸發進入事件
  if (pageHooks[viewId]?.onEnter) pageHooks[viewId].onEnter();
}

/** 註冊頁面生命週期鉤子 */
function registerPage(viewId, hooks) {
  pageHooks[viewId] = hooks;
}

/* =================================================================
 * 側邊欄
 * ================================================================= */

const MODE_LABEL_KEYS = {
  "docker-windows": "mode.docker_windows",
  "docker-linux":   "mode.docker_linux",
  "native-linux":   "mode.native_linux",
  "remote-ssh":     "mode.remote_ssh",
};

/** 取得模式顯示名稱 */
function getModeLabel(mode) {
  const key = MODE_LABEL_KEYS[mode];
  return key ? t(key) : (mode || t("common.unknown"));
}

/** 更新側邊欄模式文字 */
function updateSidebarMode(mode) {
  state.currentMode = mode;
  window.__currentMode = mode;
  const el = document.getElementById("sidebar-mode");
  if (el) el.textContent = getModeLabel(mode);

  const connEl = document.getElementById("sidebar-connection");
  if (connEl) connEl.classList.toggle("hidden", mode !== "remote-ssh");
}

/** 更新連線狀態指示器 */
function updateConnectionStatus(status) {
  const dot = document.getElementById("conn-dot");
  const text = document.getElementById("conn-text");
  if (!dot || !text) return;

  const cfg = {
    connected:    { color: "bg-status-success",   label: t("status.connected"),        pulse: false },
    disconnected: { color: "bg-status-error",      label: t("status.disconnected"),     pulse: false },
    connecting:   { color: "bg-accent-secondary",  label: t("status.connecting"),       pulse: true },
    error:        { color: "bg-status-error",      label: t("status.connection_error"), pulse: true },
  };
  const c = cfg[status] || cfg.disconnected;
  dot.className = `w-2 h-2 rounded-full ${c.color}${c.pulse ? " animate-pulse" : ""}`;
  text.textContent = c.label;
}

/** 從 Bridge 取得最新連線狀態 */
async function refreshConnectionStatus() {
  try {
    const result = await window.pywebview.api.get_connection_status();
    if (result?.success) updateConnectionStatus(result.data?.status || "disconnected");
  } catch { /* Bridge 尚未就緒 */ }
}
