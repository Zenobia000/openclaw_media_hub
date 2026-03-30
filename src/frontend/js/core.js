/**
 * OpenClaw GUI — Core
 *
 * DevTools 保護、工具函式、共用全域狀態
 */

/* =================================================================
 * 0. 生產環境保護 — 停用 DevTools 快捷鍵與右鍵選單
 * ================================================================= */

document.addEventListener("keydown", (e) => {
  // F12
  if (e.key === "F12") { e.preventDefault(); return; }
  // Ctrl+Shift+I / Ctrl+Shift+J / Ctrl+Shift+C (DevTools)
  if (e.ctrlKey && e.shiftKey && ["I", "J", "C"].includes(e.key)) { e.preventDefault(); return; }
  // Ctrl+U (view source)
  if (e.ctrlKey && e.key === "u") { e.preventDefault(); return; }
});

document.addEventListener("contextmenu", (e) => e.preventDefault());

/* =================================================================
 * 1. i18n — 多國語言支援
 * ================================================================= */

/** 當前語系字典與語系 ID */
let __i18n = {};
let __i18nLocale = "zh-TW";

/** 翻譯函式 — key 不存在時回傳 key 本身 */
function t(key, params) {
  let s = __i18n[key] ?? key;
  if (params) for (const [k, v] of Object.entries(params)) s = s.replaceAll(`{${k}}`, v);
  return s;
}

/** 切換語系並重新渲染 */
function setLocale(locale) {
  const dict = locale === "en" ? window.__locale_en : window.__locale_zhTW;
  if (!dict) return;
  __i18n = dict;
  __i18nLocale = locale;
  document.documentElement.lang = locale;
  _i18nScanDOM();
  // 重建語系相關的資料結構
  if (typeof getChannelInitRegistry === "function") CHANNEL_INIT_REGISTRY = getChannelInitRegistry();
  if (window.pywebview?.api?.save_locale) window.pywebview.api.save_locale({ locale }).catch(() => {});
  if (state.currentView) navigateTo(state.currentView);
}

/** 掃描 data-i18n / data-i18n-placeholder 屬性並更新 DOM */
function _i18nScanDOM() {
  document.querySelectorAll("[data-i18n]").forEach(el => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach(el => { el.placeholder = t(el.dataset.i18nPlaceholder); });
}

/** 切換語系（zh-TW ⇄ en） */
function toggleLanguage() {
  setLocale(__i18nLocale === "zh-TW" ? "en" : "zh-TW");
}

/* =================================================================
 * 2. 工具函式
 * ================================================================= */

/** 跳脫 HTML 特殊字元 */
function esc(str) {
  if (str == null) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/** 重新初始化 Lucide 圖示 */
function refreshIcons() {
  lucide.createIcons({ nameAttr: "data-lucide" });
}

/** Toast 通知（type: "success" | "warning" | "error"） */
function showToast(message, type = "success", duration = 4000) {
  const colors = {
    success: "bg-status-success text-white",
    warning: "bg-[#f59e0b] text-white",
    error:   "bg-status-error text-white",
  };
  const icons = { success: "check-circle", warning: "alert-triangle", error: "x-circle" };
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "fixed top-4 right-4 z-[9999] flex flex-col gap-2";
    document.body.appendChild(container);
  }
  const toast = document.createElement("div");
  toast.className = `flex items-center gap-2 px-4 py-3 rounded-md shadow-lg text-sm font-medium ${colors[type] || colors.success} transition-opacity duration-300`;
  toast.innerHTML = `<i data-lucide="${icons[type] || icons.success}" class="w-4 h-4"></i><span>${esc(message)}</span>`;
  container.appendChild(toast);
  refreshIcons();
  setTimeout(() => { toast.classList.add("opacity-0"); setTimeout(() => toast.remove(), 300); }, duration);
}

/** 將 HTML 注入容器並刷新圖示 */
function renderInto(containerId, html) {
  const el = document.getElementById(containerId);
  if (el) { el.innerHTML = html; refreshIcons(); }
}

/** 更新 SectionPanel 的內容區域 */
function updatePanelContent(panelId, html) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const container = panel.querySelector(":scope > div:last-child");
  if (!container) return;
  container.innerHTML = html;
  refreshIcons();
}

/** 渲染載入中指示器 */
function renderLoading(message) {
  if (message === undefined) message = t("loading.default");
  return `<div class="flex items-center gap-3 text-text-muted py-8">
    <i data-lucide="loader" class="w-5 h-5 animate-spin"></i>
    <span class="text-sm">${esc(message)}</span>
  </div>`;
}

/** 渲染錯誤區塊 */
function renderErrorBlock({ type, message, retryAction }) {
  return `<div class="rounded-md p-4 border border-status-error" style="background: #ef444410;">
    ${type ? `<div class="flex items-center gap-2">
      <i data-lucide="alert-triangle" class="w-5 h-5 text-status-error"></i>
      <span class="text-sm font-semibold text-status-error">${esc(type)}</span>
    </div>` : ""}
    <p class="text-sm text-text-secondary ${type ? "mt-2" : ""}">${esc(message)}</p>
    ${retryAction ? `<div class="mt-3">${renderButton({ variant: "secondary", icon: "refresh-cw", label: t("common.retry"), onclick: retryAction })}</div>` : ""}
  </div>`;
}

/** 渲染計數摘要橫幅 */
function renderCountBanner({ current, total, entityName, emptySubtitle, activeSubtitle }) {
  if (current > 0) {
    return `<div class="flex items-start gap-3 p-4 rounded-md border" style="background:#4CAF5015;border-color:#4CAF5040">
      <i data-lucide="check-circle" class="w-5 h-5 text-status-success flex-shrink-0 mt-0.5"></i>
      <div>
        <div class="text-sm font-semibold text-status-success">${t("banner.x_of_y", { current, total, entity: entityName })}</div>
        <div class="text-xs text-text-secondary mt-0.5">${esc(activeSubtitle)}</div>
      </div>
    </div>`;
  }
  return `<div class="flex items-start gap-3 p-4 rounded-md border" style="background:#3b82f610;border-color:#3b82f630">
    <i data-lucide="info" class="w-5 h-5 text-status-info flex-shrink-0 mt-0.5"></i>
    <div>
      <div class="text-sm font-semibold text-status-info">${t("banner.no_entity", { entity: entityName })}</div>
      <div class="text-xs text-text-secondary mt-0.5">${esc(emptySubtitle)}</div>
    </div>
  </div>`;
}

/** 寫入剪貼簿（含非安全環境的 fallback） */
async function clipboardWrite(text) {
  try {
    if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(text); return; }
  } catch { /* 需要安全環境 — 改用 fallback */ }
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.cssText = "position:fixed;opacity:0;left:-9999px";
  document.body.appendChild(ta);
  ta.select();
  document.execCommand("copy");
  document.body.removeChild(ta);
}

/* =================================================================
 * 3. 共用全域狀態
 * ================================================================= */

/** 應用程式核心狀態 */
const state = { currentView: null, currentMode: null };

/** 頁面生命週期鉤子 { viewId: { onEnter, onLeave } } */
const pageHooks = {};
