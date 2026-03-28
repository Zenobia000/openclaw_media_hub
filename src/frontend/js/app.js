/**
 * OpenClaw GUI — 前端應用程式
 *
 * SPA 路由、UI 元件、Bridge 整合
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
 * 1. 工具函式
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
function renderLoading(message = "Loading...") {
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
    ${retryAction ? `<div class="mt-3">${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Retry", onclick: retryAction })}</div>` : ""}
  </div>`;
}

/** 渲染計數摘要橫幅 */
function renderCountBanner({ current, total, entityName, emptySubtitle, activeSubtitle }) {
  if (current > 0) {
    return `<div class="flex items-start gap-3 p-4 rounded-md border" style="background:#4CAF5015;border-color:#4CAF5040">
      <i data-lucide="check-circle" class="w-5 h-5 text-status-success flex-shrink-0 mt-0.5"></i>
      <div>
        <div class="text-sm font-semibold text-status-success">${current} of ${total} ${esc(entityName)}</div>
        <div class="text-xs text-text-secondary mt-0.5">${esc(activeSubtitle)}</div>
      </div>
    </div>`;
  }
  return `<div class="flex items-start gap-3 p-4 rounded-md border" style="background:#3b82f610;border-color:#3b82f630">
    <i data-lucide="info" class="w-5 h-5 text-status-info flex-shrink-0 mt-0.5"></i>
    <div>
      <div class="text-sm font-semibold text-status-info">No ${esc(entityName)} yet</div>
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
 * 2. 全域狀態
 * ================================================================= */

/** 應用程式核心狀態 */
const state = { currentView: null, currentMode: null };

/** 頁面生命週期鉤子 { viewId: { onEnter, onLeave } } */
const pageHooks = {};

/** 設定精靈 — 第一步 */
const configState = {
  step: 1,
  selectedMode: null,
  sshTestPassed: false,
  sshTestResult: null,
  sshAuthMethod: "key",
  rendered: false,
  formValues: {},
};

/** 設定精靈 — 第二步 */
const step2State = {
  cachedProviders: null,
  cachedModels: null,
  checkedProviders: new Set(),
  checkedModels: {},
  primaryModel: null,
  keyValues: {},
};

/** 設定精靈 — 第三步（初始化） */
const initState = {
  running: false,
  gatewayToken: null,
  tokenRevealed: false,
  deviceApprovalLoading: false,
  failedStep: null,
  failedError: null,
};

/** 儀表板 */
const dashboardState = { pollTimer: null, actionPending: false };

/** Gateway 頁面 */
const gatewayState = {
  origins: [],
  allowAll: false,
  devices: { pending: [], paired: [] },
  deviceNotes: {},
  info: null,
  loading: false,
  tokenRevealed: false,
  settingsDirty: false,
  pendingBind: null,
  pendingControlUi: null,
};

/* =================================================================
 * 3. SPA 路由
 * ================================================================= */

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
 * 4. 側邊欄
 * ================================================================= */

const MODE_LABELS = {
  "docker-windows": "Docker \u00b7 Windows",
  "docker-linux": "Docker \u00b7 Linux/WSL2",
  "native-linux": "Native \u00b7 Linux (systemd)",
  "remote-ssh": "Remote \u00b7 SSH",
};

/** 更新側邊欄模式文字 */
function updateSidebarMode(mode) {
  state.currentMode = mode;
  window.__currentMode = mode;
  const el = document.getElementById("sidebar-mode");
  if (el) el.textContent = MODE_LABELS[mode] || mode || "Unknown";

  const connEl = document.getElementById("sidebar-connection");
  if (connEl) connEl.classList.toggle("hidden", mode !== "remote-ssh");
}

/** 更新連線狀態指示器 */
function updateConnectionStatus(status) {
  const dot = document.getElementById("conn-dot");
  const text = document.getElementById("conn-text");
  if (!dot || !text) return;

  const cfg = {
    connected:    { color: "bg-status-success",   label: "Connected",        pulse: false },
    disconnected: { color: "bg-status-error",      label: "Disconnected",     pulse: false },
    connecting:   { color: "bg-accent-secondary",  label: "Connecting...",     pulse: true },
    error:        { color: "bg-status-error",      label: "Connection Error", pulse: true },
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

/* =================================================================
 * 5. UI 元件
 * ================================================================= */

/* ---------- 5.1 按鈕 ---------- */

/** 渲染按鈕 (Primary / Secondary / Danger) */
function renderButton({ variant = "primary", icon, label, disabled = false, loading = false, id, onclick, size = "md" }) {
  const base = "inline-flex items-center justify-center gap-2 font-medium rounded-sm transition-colors cursor-pointer select-none";
  const sizing = size === "sm" ? "px-3 py-1.5 text-xs" : "px-4 py-2.5 text-sm";
  const variants = {
    primary:   "bg-accent-primary text-text-on-accent hover:bg-[#e64d4d]",
    secondary: "bg-bg-card text-text-secondary border border-border-default hover:bg-bg-input",
    danger:    "bg-status-error text-text-on-accent hover:bg-[#dc2626]",
  };
  const disabledCls = disabled || loading ? "opacity-50 pointer-events-none" : "";
  const iconName = loading ? "loader" : icon;
  const iconCls = loading ? "animate-spin" : "";
  const idAttr = id ? `id="${id}"` : "";
  const onclickAttr = onclick && !disabled ? `onclick="${onclick}"` : "";

  return `<button ${idAttr} class="${base} ${sizing} ${variants[variant] || variants.primary} ${disabledCls}" ${disabled ? "disabled" : ""} ${onclickAttr}>
    ${iconName ? `<i data-lucide="${iconName}" class="w-4 h-4 ${iconCls}"></i>` : ""}
    <span>${label}</span>
  </button>`;
}

/* ---------- 5.2 輸入框 ---------- */

/** 渲染表單輸入框 */
function renderInput({ id, label, icon, placeholder = "", type = "text", value = "", error, required = false }) {
  const errorBorder = error ? "border-status-error" : "border-border-default focus-within:border-accent-primary";
  const reqMark = required ? '<span class="text-accent-primary ml-0.5">*</span>' : "";
  const passwordToggle = type === "password"
    ? `<button type="button" class="pwd-toggle absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary" onclick="togglePassword('${id}')"><i data-lucide="eye-off" class="w-4 h-4"></i></button>`
    : "";

  return `<div class="flex flex-col gap-1.5">
    ${label ? `<label for="${id}" class="text-xs font-medium text-text-secondary">${label}${reqMark}</label>` : ""}
    <div class="relative">
      ${icon ? `<i data-lucide="${icon}" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"></i>` : ""}
      <input id="${id}" name="${id}" type="${type}" value="${esc(value)}" placeholder="${esc(placeholder)}"
        class="w-full bg-bg-input border ${errorBorder} rounded-sm text-sm text-text-primary placeholder:text-text-muted ${icon ? "pl-10" : "pl-3"} ${type === "password" ? "pr-10" : "pr-3"} py-2.5 outline-none transition-colors" />
      ${passwordToggle}
    </div>
    ${error ? `<span class="text-xs text-status-error">${error}</span>` : ""}
  </div>`;
}

/** 切換密碼可見性 */
function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPassword = input.type === "password";
  input.type = isPassword ? "text" : "password";
  const btn = input.parentElement.querySelector(".pwd-toggle i");
  if (btn) btn.setAttribute("data-lucide", isPassword ? "eye" : "eye-off");
  refreshIcons();
}

/* ---------- 5.3 狀態標籤 ---------- */

/** 渲染狀態標籤 (圓點 + 文字) */
function renderStatusBadge({ status, text }) {
  const colors = {
    success: { dot: "bg-status-success", bg: "bg-[#22c55e18]", txt: "text-status-success" },
    error:   { dot: "bg-status-error",   bg: "bg-[#ef444418]", txt: "text-status-error" },
    warning: { dot: "bg-[#eab308]",      bg: "bg-[#eab30818]", txt: "text-[#eab308]" },
    info:    { dot: "bg-status-info",     bg: "bg-[#3b82f618]", txt: "text-status-info" },
  };
  const c = colors[status] || colors.info;
  return `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full ${c.bg} ${c.txt} text-xs font-medium">
    <span class="w-1.5 h-1.5 rounded-full ${c.dot}"></span>
    ${esc(text)}
  </span>`;
}

/* ---------- 5.4 統計卡片 ---------- */

/** 渲染統計卡片 */
function renderStatCard({ icon, iconColor = "text-accent-primary", value, label, status }) {
  const badge = status ? renderStatusBadge({ status, text: status }) : "";
  return `<div class="bg-bg-card border border-border-default rounded-md p-5 flex-1 min-w-0">
    <div class="flex items-center justify-between mb-3">
      <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center">
        <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
      </div>
      ${badge}
    </div>
    <div class="text-2xl font-bold">${esc(value)}</div>
    <div class="text-xs text-text-muted mt-1">${esc(label)}</div>
  </div>`;
}

/* ---------- 5.5 環境檢查卡片 ---------- */

/** 渲染環境檢查卡片 */
function renderCheckCard({ icon, iconColor = "text-status-info", name, version, status }) {
  const isOk = status === "installed" || status === "running";
  const badgeStatus = isOk ? "success" : "error";
  const badgeText = isOk ? (version || "Installed") : "Not Found";
  return `<div class="bg-bg-card border border-border-default rounded-md p-4 flex items-center gap-3 min-w-[200px] flex-1">
    <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">${esc(name)}</div>
      ${version ? `<div class="text-xs text-text-muted mt-0.5">${esc(version)}</div>` : ""}
    </div>
    ${renderStatusBadge({ status: badgeStatus, text: badgeText })}
  </div>`;
}

/* ---------- 5.6 區段面板 ---------- */

/** 渲染區段面板（圖示、標題、內容） */
function renderSectionPanel({ icon, iconColor = "text-accent-primary", title, description, children = "", id, flexFill = false }) {
  const idAttr = id ? `id="${id}"` : "";
  const outerFlex = flexFill ? " flex-1 min-h-0 flex flex-col" : "";
  const innerFlex = flexFill ? " flex-1 min-h-0 flex flex-col" : "";
  return `<div ${idAttr} class="bg-bg-card border border-border-default rounded-md${outerFlex}">
    <div class="px-5 pt-5 pb-4 flex items-start gap-3 flex-shrink-0">
      <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0 mt-0.5">
        <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
      </div>
      <div>
        <h3 class="text-base font-semibold">${esc(title)}</h3>
        ${description ? `<p class="text-[13px] text-text-secondary mt-0.5">${esc(description)}</p>` : ""}
      </div>
    </div>
    <div class="px-5 pb-5${innerFlex}">${children}</div>
  </div>`;
}

/* ---------- 5.7 步驟指示器 ---------- */

/** 渲染水平步驟指示器 */
function renderStepIndicator({ steps, currentStep, completedSteps = [] }) {
  const items = steps.map((label, i) => {
    const num = i + 1;
    const isCompleted = completedSteps.includes(num);
    const isActive = num === currentStep;
    const isPending = !isCompleted && !isActive;

    let circle;
    if (isCompleted) {
      circle = `<div class="w-8 h-8 rounded-full bg-status-success flex items-center justify-center flex-shrink-0">
        <i data-lucide="check" class="w-4 h-4 text-white"></i></div>`;
    } else if (isActive) {
      circle = `<div class="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center flex-shrink-0">
        <span class="text-sm font-bold text-white">${num}</span></div>`;
    } else {
      circle = `<div class="w-8 h-8 rounded-full border-2 border-border-default flex items-center justify-center flex-shrink-0">
        <span class="text-sm font-medium text-text-muted">${num}</span></div>`;
    }

    const labelCls = isActive ? "text-sm font-semibold text-text-primary"
      : isPending ? "text-sm text-text-muted" : "text-sm text-text-secondary";

    const line = i > 0
      ? `<div class="flex-1 h-0.5 ${completedSteps.includes(num) || isActive ? "bg-status-success" : "bg-border-default"}"></div>`
      : "";

    return `${line}<div class="flex items-center gap-2">${circle}<span class="${labelCls}">${esc(label)}</span></div>`;
  });

  return `<div class="flex items-center gap-3">${items.join("")}</div>`;
}

/* ---------- 5.8 進度項目 ---------- */

/** 渲染進度項目（初始化 / 部署步驟） */
function renderProgressItem({ name, description, status, icon, error }) {
  const cfg = {
    done:    { circleClass: "bg-status-success", icon: "check",  iconClass: "text-white", textClass: "text-status-success", label: "Done" },
    running: { circleClass: "bg-accent-primary", icon: "loader", iconClass: "text-white animate-spin", textClass: "text-accent-primary", label: "Running..." },
    pending: { circleClass: "border-2 border-border-default bg-transparent", icon: null, iconClass: "", textClass: "text-text-muted", label: "Pending" },
    failed:  { circleClass: "bg-status-error",   icon: "x",      iconClass: "text-white", textClass: "text-status-error", label: "Failed" },
  };
  const c = cfg[status] || cfg.pending;
  const circleContent = c.icon ? `<i data-lucide="${c.icon}" class="w-3.5 h-3.5 ${c.iconClass}"></i>` : "";
  const prefix = icon ? `<span class="text-base mr-2">${icon}</span>` : "";

  const errorBlock = (status === "failed" && error) ? `
    <div class="bg-red-500/10 rounded-lg p-3 mt-2" data-error-text="${esc(`[${name}] ${error}`)}">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-1.5">
          <i data-lucide="triangle-alert" class="w-3.5 h-3.5 text-status-error"></i>
          <span class="text-xs font-semibold text-status-error">Error Details</span>
        </div>
        <button onclick="copyProgressError(this)" class="p-1 rounded bg-red-500/15 hover:bg-red-500/25 transition-colors" title="Copy error">
          <i data-lucide="copy" class="w-3 h-3 text-status-error"></i>
        </button>
      </div>
      <pre class="text-xs text-red-400 font-mono whitespace-pre-wrap max-h-[120px] overflow-y-auto leading-relaxed">${esc(error)}</pre>
      <div class="flex items-center gap-2 mt-3">
        <button onclick="retryFromFailedStep()" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-status-error hover:bg-red-600 text-white text-xs font-medium transition-colors">
          <i data-lucide="rotate-ccw" class="w-3 h-3"></i>Retry
        </button>
        <span class="text-xs text-text-muted">Retry from this step</span>
      </div>
    </div>` : "";

  return `<div class="py-3 border-b border-border-default last:border-b-0">
    <div class="flex items-center gap-3">
      <div class="w-7 h-7 rounded-full ${c.circleClass} flex items-center justify-center flex-shrink-0">${circleContent}</div>
      ${prefix}
      <div class="flex-1 min-w-0">
        <div class="text-sm font-medium">${esc(name)}</div>
        ${description ? `<div class="text-xs text-text-secondary mt-0.5">${esc(description)}</div>` : ""}
      </div>
      <span class="text-xs font-medium ${c.textClass}">${c.label}</span>
    </div>${errorBlock}
  </div>`;
}

/* =================================================================
 * 6. 勾選清單頁面工廠
 * ================================================================= */

/** 外掛分類與顏色 */
const PLUGIN_CATEGORIES = [
  { key: "providers", label: "Providers", color: "#8B5CF6" },
  { key: "channels",  label: "Channels",  color: "#3B82F6" },
  { key: "tools",     label: "Tools",     color: "#F59E0B" },
  { key: "infrastructure", label: "Infrastructure", color: "#10B981" },
];
const PLUGIN_COLORS = Object.fromEntries(PLUGIN_CATEGORIES.map(c => [c.key, c.color]));

/** Channel 初始化 Registry（資料驅動，新增 Channel 只需加條目） */
const CHANNEL_INIT_REGISTRY = {
  line: {
    label: "LINE",
    icon: "L",
    iconColor: "#06C755",
    steps: ["Credentials", "Webhook Setup", "DM Policy"],
    fields: [
      { id: "LINE_CHANNEL_ACCESS_TOKEN", label: "Channel Access Token", type: "password", required: true },
      { id: "LINE_CHANNEL_SECRET", label: "Channel Secret", type: "password", required: true },
    ],
    webhookInstructions: [
      "Open LINE Developers Console and select your Messaging API channel",
      "Go to the Messaging API tab",
      "Paste the Webhook URL into the Webhook URL field",
      "Click Verify to test the connection",
      "Enable the Use webhook toggle",
      "In LINE Official Account Manager, go to Chat settings and disable Auto-reply messages",
    ],
    helpSteps: [
      "Go to LINE Official Account Manager, disable Auto-reply messages in Chat settings",
      "Click Message API to enable Messaging API",
      "Go to LINE Developers Console, select your Provider and Messaging API Channel",
      "In Basic settings, copy the Channel Secret",
      "In Messaging API tab, click Issue to generate Channel Access Token",
    ],
    dmPolicyOptions: [
      { value: "pairing", label: "Pairing (Recommended)", desc: "New users receive a pairing code, must be approved before chatting" },
      { value: "allowlist", label: "Allowlist", desc: "Only pre-approved LINE User IDs can send messages" },
      { value: "open", label: "Open", desc: "Any LINE user can send messages directly" },
      { value: "disabled", label: "Disabled", desc: "Direct messages are disabled for this channel" },
    ],
    defaultDmPolicy: "pairing",
    consoleUrl: "https://developers.line.biz/console/",
  },
};

/** Channel 初始化精靈狀態 */
const channelInitState = {
  active: false,
  channelName: null,
  step: 1,
  fieldValues: {},
  dmPolicy: "pairing",
  saving: false,
  webhookData: null,
  existingCredentials: {},
  existingConfig: {},
  fieldVisible: {},
};

/**
 * 建立勾選清單頁面（技能部署 / 外掛安裝共用工廠）
 *
 * 回傳的函式須綁定至 window，供 HTML onclick 使用。
 */
function createChecklistPage(cfg) {
  const ps = { data: [], selected: new Set(), tab: "", busy: false, progressMap: {}, rendered: false };

  const getId = (item) => item[cfg.idField];

  // 渲染頁面
  function renderPage() {
    const activeCount = ps.data.filter(d => d[cfg.installedField]).length;

    renderInto(cfg.badgeId,
      activeCount > 0
        ? renderStatusBadge({ status: "success", text: `${activeCount} ${cfg.activeCountLabel}` })
        : renderStatusBadge({ status: "info", text: `0 ${cfg.activeCountLabel}` })
    );

    const bannerHtml = renderCountBanner({
      current: activeCount,
      total: ps.data.length,
      entityName: `${cfg.entityNamePlural} ${cfg.activeCountLabel}`,
      activeSubtitle: cfg.activeSubtitle,
      emptySubtitle: cfg.emptySubtitle,
    });

    const checklistHtml = renderSectionPanel({
      icon: cfg.icon,
      iconColor: cfg.iconColor,
      title: cfg.panelTitle,
      description: cfg.panelDescription,
      id: cfg.panelId,
      flexFill: true,
      children: renderTabs() + renderList(),
    });

    renderInto(cfg.contentId, `<div class="flex-shrink-0">${bannerHtml}</div>` + checklistHtml);
    renderActionBar();
  }

  // 渲染頁籤
  function renderTabs() {
    const tabCls = (active) => active
      ? `px-4 py-2 text-sm font-semibold text-${cfg.tabAccentColor} border-b-2 border-${cfg.tabAccentColor} cursor-pointer`
      : "px-4 py-2 text-sm font-medium text-text-muted hover:text-text-primary cursor-pointer";

    const tabs = cfg.tabs.map(t => {
      const count = ps.data.filter(t.filterFn).length;
      return `<div class="${tabCls(ps.tab === t.key)}" onclick="${cfg.switchTabFn}('${t.key}')">${t.label} (${count})</div>`;
    }).join("");

    return `<div class="flex border-b border-border-default mb-3 flex-shrink-0">${tabs}</div>`;
  }

  // 渲染清單
  function renderList() {
    const tabDef = cfg.tabs.find(t => t.key === ps.tab);
    const filtered = tabDef ? ps.data.filter(tabDef.filterFn) : [];

    if (filtered.length === 0) {
      return `<div class="py-8 text-center text-sm text-text-muted">No items found in this category.</div>`;
    }

    const allIds = filtered.map(getId);
    const allSelected = allIds.length > 0 && allIds.every(id => ps.selected.has(id));

    const selectAllHtml = `<div class="flex items-center gap-3 px-4 py-2.5 border-b border-border-default flex-shrink-0">
      <input type="checkbox" ${allSelected ? "checked" : ""}
        class="w-4 h-4 rounded accent-accent-primary cursor-pointer"
        onchange="${cfg.toggleAllFn}()" id="${cfg.panelId}-select-all" />
      <label for="${cfg.panelId}-select-all" class="text-sm font-medium text-text-secondary cursor-pointer select-none">Select All</label>
    </div>`;

    const rowsHtml = filtered.map(item => renderRow(item)).join("");
    return selectAllHtml + `<div class="flex-1 min-h-0 overflow-y-auto">${rowsHtml}</div>`;
  }

  // 渲染單列
  function renderRow(item) {
    const itemId = getId(item);
    const checked = ps.selected.has(itemId) ? "checked" : "";
    const isActive = item[cfg.installedField];
    const badge = isActive
      ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-medium bg-[#4CAF5015] text-status-success border border-[#4CAF5040]">${cfg.activeLabel}</span>`
      : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-medium bg-bg-input text-text-muted border border-border-default">${cfg.inactiveLabel}</span>`;

    const iconHtml = cfg.renderRowIcon(item);
    const displayName = cfg.getDisplayName(item);
    const rawDesc = cfg.getDescription(item);
    const desc = rawDesc && rawDesc.length > 80 ? rawDesc.slice(0, 80) + "..." : (rawDesc || "");

    const configAction = (cfg.renderConfigAction && cfg.renderConfigAction(item)) || "";

    return `<div class="flex items-center gap-3 px-4 py-3.5 border-b border-border-default last:border-b-0 hover:bg-bg-input transition-colors cursor-pointer"
      onclick="${cfg.toggleFn}('${esc(itemId)}')">
      <input type="checkbox" ${checked}
        class="w-4 h-4 rounded accent-accent-primary cursor-pointer flex-shrink-0"
        onclick="event.stopPropagation(); ${cfg.toggleFn}('${esc(itemId)}')" />
      ${iconHtml}
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-text-primary">${esc(displayName)}</div>
        <div class="text-xs text-text-secondary mt-0.5 truncate">${esc(desc)}</div>
      </div>
      <div class="flex items-center gap-2 flex-shrink-0">${badge}${configAction}</div>
    </div>`;
  }

  // 渲染動作列
  function renderActionBar() {
    const bar = document.getElementById(cfg.actionBarId);
    if (!bar) return;

    const count = ps.selected.size;
    const hasUnactive = ps.data.some(d => ps.selected.has(getId(d)) && !d[cfg.installedField]);
    const hasActive = ps.data.some(d => ps.selected.has(getId(d)) && d[cfg.installedField]);

    if (count === 0 && !ps.busy) { bar.classList.add("hidden"); return; }
    bar.classList.remove("hidden");

    bar.innerHTML = `<div class="flex items-center justify-between">
      <span class="text-sm text-text-secondary">${count} ${cfg.entityName}${count !== 1 ? "s" : ""} selected</span>
      <div class="flex items-center gap-3">
        ${renderButton({ variant: "danger", icon: cfg.removeIcon, label: cfg.removeLabel, disabled: !hasActive || ps.busy, onclick: cfg.handleRemoveFn + "()", size: "sm" })}
        ${renderButton({ variant: "primary", icon: cfg.deployIcon, label: cfg.deployLabel, disabled: !hasUnactive || ps.busy, onclick: cfg.handleDeployFn + "()", size: "sm" })}
      </div>
    </div>`;
    refreshIcons();
  }

  // 渲染進度覆蓋
  function renderProgressOverlay() {
    const names = Object.keys(ps.progressMap);
    const allDone = names.length > 0 && names.every(n => {
      const s = ps.progressMap[n].status;
      return s === "done" || s === "failed";
    });

    let itemsHtml = names.map(name => {
      const p = ps.progressMap[name];
      const item = ps.data.find(d => getId(d) === name);
      return renderProgressItem({
        name: name,
        description: p.message,
        status: p.status,
        icon: item ? cfg.getProgressIcon(item) : "?",
      });
    }).join("");

    if (allDone) {
      // 檢測已安裝的 Channel 外掛，顯示 Configure CTA
      let configCtas = "";
      if (cfg.renderConfigAction) {
        const channelNames = names.filter(n => {
          const item = ps.data.find(d => getId(d) === n);
          return item && item.category === "channels" && CHANNEL_INIT_REGISTRY[item.id]
            && ps.progressMap[n]?.status === "done";
        });
        configCtas = channelNames.map(n => {
          const item = ps.data.find(d => getId(d) === n);
          const reg = CHANNEL_INIT_REGISTRY[item.id];
          return renderButton({ variant: "primary", icon: "settings", label: `Configure ${reg.label}`, onclick: `openChannelInitWizard('${item.id}')` });
        }).join(" ");
      }
      itemsHtml += `<div class="mt-4 flex justify-end gap-3">
        ${configCtas}
        ${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Done", onclick: cfg.reloadFn + "()" })}
      </div>`;
    }

    updatePanelContent(cfg.panelId, itemsHtml);
  }

  // 切換選取
  function toggle(id) {
    if (ps.busy) return;
    ps.selected.has(id) ? ps.selected.delete(id) : ps.selected.add(id);
    updatePanelContent(cfg.panelId, renderTabs() + renderList());
    renderActionBar();
  }

  // 全選 / 全不選
  function toggleAll() {
    if (ps.busy) return;
    const tabDef = cfg.tabs.find(t => t.key === ps.tab);
    const filtered = tabDef ? ps.data.filter(tabDef.filterFn) : [];
    const allIds = filtered.map(getId);
    const allSelected = allIds.every(id => ps.selected.has(id));

    if (allSelected) allIds.forEach(id => ps.selected.delete(id));
    else allIds.forEach(id => ps.selected.add(id));

    updatePanelContent(cfg.panelId, renderTabs() + renderList());
    renderActionBar();
  }

  // 切換頁籤
  function switchTab(tab) {
    ps.tab = tab;
    updatePanelContent(cfg.panelId, renderTabs() + renderList());
  }

  // 部署/安裝
  async function handleDeploy() {
    const toDeploy = ps.data.filter(d => ps.selected.has(getId(d)) && !d[cfg.installedField]).map(getId);
    if (toDeploy.length === 0) return;

    ps.busy = true;
    ps.progressMap = {};
    toDeploy.forEach(id => { ps.progressMap[id] = { status: "pending", message: "Waiting..." }; });
    renderProgressOverlay();
    renderActionBar();

    try { await window.pywebview.api[cfg.deployApi](toDeploy); } catch { /* 進度覆蓋已顯示個別狀態 */ }

    ps.busy = false;
    renderProgressOverlay();
    renderActionBar();
  }

  // 移除/解除安裝
  async function handleRemove() {
    const toRemove = ps.data.filter(d => ps.selected.has(getId(d)) && d[cfg.installedField]).map(getId);
    if (toRemove.length === 0) return;
    if (!confirm(cfg.confirmRemoveMessage(toRemove.length))) return;

    ps.busy = true;
    ps.progressMap = {};
    toRemove.forEach(id => { ps.progressMap[id] = { status: "pending", message: "Waiting..." }; });
    renderProgressOverlay();
    renderActionBar();

    try { await window.pywebview.api[cfg.removeApi](toRemove); } catch { /* 進度覆蓋已顯示個別狀態 */ }

    ps.busy = false;
    renderProgressOverlay();
    renderActionBar();
  }

  // 重新載入資料
  async function reload() {
    ps.progressMap = {};
    ps.busy = false;
    try {
      const result = await window.pywebview.api[cfg.listApi]();
      if (result?.success && result.data) {
        ps.data = result.data;
        ps.selected = new Set(ps.data.filter(d => d[cfg.installedField]).map(getId));
      }
    } catch { /* 保留現有資料 */ }
    renderPage();
  }

  // 進度回呼
  window[cfg.progressCallback] = function (id, status, message) {
    ps.progressMap[id] = { status, message };
    renderProgressOverlay();
  };

  // 頁面生命週期
  registerPage(cfg.pageId, {
    onEnter: async () => {
      if (ps.rendered && !ps.busy) { await reload(); return; }

      if (!ps.rendered) renderInto(cfg.contentId, renderLoading(`Loading ${cfg.entityNamePlural}...`));

      try {
        const result = await window.pywebview.api[cfg.listApi]();
        if (result?.success && result.data) {
          ps.data = result.data;
          ps.selected = new Set(ps.data.filter(d => d[cfg.installedField]).map(getId));
          ps.tab = cfg.defaultTab(ps.data);
          renderPage();
          ps.rendered = true;
        } else {
          renderInto(cfg.contentId, `<div class="text-center py-16">
            ${renderErrorBlock({ message: result?.error?.message || "Unknown error", retryAction: cfg.reloadFn + "()" })}
          </div>`);
        }
      } catch {
        renderInto(cfg.contentId, `<div class="text-center py-16">
          ${renderErrorBlock({ message: "Failed to load data", retryAction: cfg.reloadFn + "()" })}
        </div>`);
      }
    },
    onLeave: () => { ps.busy = false; },
  });

  return { toggle, toggleAll, switchTab, handleDeploy, handleRemove, reload, state: ps };
}

/* ---------- 技能部署頁面實例 ---------- */

const skillsPage = createChecklistPage({
  pageId: "deploy-skills", contentId: "deploy-skills-content", badgeId: "deploy-skills-badge",
  panelId: "skills-checklist-panel", actionBarId: "deploy-skills-action-bar",
  entityName: "skill", entityNamePlural: "skills", activeCountLabel: "deployed",
  icon: "zap", iconColor: "text-accent-primary",
  panelTitle: "Available Skills",
  panelDescription: "Scanned from module_pack/ (custom modules) and openclaw/skills/ (community skills)",
  listApi: "list_skills", deployApi: "deploy_skills", removeApi: "remove_skills",
  progressCallback: "updateDeployProgress",
  tabs: [
    { key: "custom", label: "Custom Modules", filterFn: s => s.source === "module_pack" },
    { key: "community", label: "Community Skills", filterFn: s => s.source === "community" },
  ],
  idField: "name", installedField: "installed",
  activeLabel: "Deployed", inactiveLabel: "Available",
  deployLabel: "Deploy Selected", removeLabel: "Remove Selected",
  deployIcon: "upload", removeIcon: "trash-2",
  activeSubtitle: "Select skills below to deploy or remove",
  emptySubtitle: "Select skills below and click Deploy to get started",
  renderRowIcon: s => `<span class="text-base flex-shrink-0">${s.emoji}</span>`,
  getDisplayName: s => s.name,
  getDescription: s => s.description,
  getProgressIcon: s => s.emoji || "\u{1F4E6}",
  confirmRemoveMessage: n => `Remove ${n} skill(s)? This will delete the deployed files.`,
  defaultTab: data => data.some(s => s.source === "module_pack") ? "custom" : "community",
  tabAccentColor: "accent-primary",
  // onclick 全域函式名
  toggleFn: "toggleSkill", toggleAllFn: "toggleAllSkills", switchTabFn: "switchSkillsTab",
  handleDeployFn: "handleDeploySkills", handleRemoveFn: "handleRemoveSkills", reloadFn: "reloadSkillsPage",
});

window.toggleSkill = skillsPage.toggle;
window.toggleAllSkills = skillsPage.toggleAll;
window.switchSkillsTab = skillsPage.switchTab;
window.handleDeploySkills = skillsPage.handleDeploy;
window.handleRemoveSkills = skillsPage.handleRemove;
window.reloadSkillsPage = skillsPage.reload;

/* ---------- 外掛安裝頁面實例 ---------- */

const pluginsPage = createChecklistPage({
  pageId: "install-plugins", contentId: "install-plugins-content", badgeId: "install-plugins-badge",
  panelId: "plugins-checklist-panel", actionBarId: "install-plugins-action-bar",
  entityName: "plugin", entityNamePlural: "plugins", activeCountLabel: "installed",
  icon: "puzzle", iconColor: "text-accent-secondary",
  panelTitle: "Available Plugins",
  panelDescription: "Extensions from openclaw/extensions/ — install by modifying openclaw.json plugins config",
  listApi: "list_plugins", deployApi: "install_plugins", removeApi: "uninstall_plugins",
  progressCallback: "updatePluginProgress",
  tabs: PLUGIN_CATEGORIES.map(c => ({
    key: c.key, label: c.label, filterFn: p => p.category === c.key,
  })),
  idField: "id", installedField: "installed",
  activeLabel: "Installed", inactiveLabel: "Available",
  deployLabel: "Install Selected", removeLabel: "Uninstall Selected",
  deployIcon: "download", removeIcon: "trash-2",
  activeSubtitle: "Select plugins below to install or uninstall",
  emptySubtitle: "Select plugins below and click Install to get started",
  renderRowIcon: p => {
    const color = PLUGIN_COLORS[p.category] || "#6B7280";
    const letter = p.id.charAt(0).toUpperCase();
    return `<div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold text-white" style="background:${color}">${letter}</div>`;
  },
  getDisplayName: p => (p.category === "channels" && p.channel_label) ? p.channel_label : p.id,
  getDescription: p => (p.category === "channels" && p.channel_blurb) ? p.channel_blurb : p.description,
  getProgressIcon: p => p.id.charAt(0).toUpperCase(),
  confirmRemoveMessage: n => `Uninstall ${n} plugin(s)? This will remove them from openclaw.json.`,
  defaultTab: data => PLUGIN_CATEGORIES.map(c => c.key).find(k => data.some(p => p.category === k)) || "providers",
  tabAccentColor: "accent-secondary",
  toggleFn: "togglePlugin", toggleAllFn: "toggleAllPlugins", switchTabFn: "switchPluginsTab",
  handleDeployFn: "handleInstallPlugins", handleRemoveFn: "handleUninstallPlugins", reloadFn: "reloadPluginsPage",
  renderConfigAction: p => {
    if (p.category === "channels" && p.installed && CHANNEL_INIT_REGISTRY[p.id]) {
      return `<button onclick="event.stopPropagation(); openChannelInitWizard('${esc(p.id)}')"
        class="inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-bg-secondary transition-colors"
        title="Configure ${esc(CHANNEL_INIT_REGISTRY[p.id].label)} channel">
        <i data-lucide="settings" class="w-3.5 h-3.5"></i>
      </button>`;
    }
    return "";
  },
});

window.togglePlugin = pluginsPage.toggle;
window.toggleAllPlugins = pluginsPage.toggleAll;
window.switchPluginsTab = pluginsPage.switchTab;
window.handleInstallPlugins = pluginsPage.handleDeploy;
window.handleUninstallPlugins = pluginsPage.handleRemove;
window.reloadPluginsPage = pluginsPage.reload;

/* =================================================================
 * 6a. Channel Init Wizard — Modal 初始化精靈
 * ================================================================= */

/** 開啟 Channel 初始化精靈 */
window.openChannelInitWizard = async function (channelName) {
  const reg = CHANNEL_INIT_REGISTRY[channelName];
  if (!reg) return;

  channelInitState.active = true;
  channelInitState.channelName = channelName;
  channelInitState.step = 1;
  channelInitState.fieldValues = {};
  channelInitState.dmPolicy = reg.defaultDmPolicy || "pairing";
  channelInitState.saving = false;
  channelInitState.webhookData = null;
  channelInitState.existingCredentials = {};
  channelInitState.existingConfig = {};
  channelInitState.fieldVisible = {};

  renderChannelInitModal();

  // 非同步載入既有設定與 webhook URL
  try {
    const [cfgRes, whRes] = await Promise.all([
      window.pywebview.api.get_channel_config(channelName),
      window.pywebview.api.get_webhook_url(channelName),
    ]);
    if (cfgRes?.success && cfgRes.data) {
      channelInitState.existingCredentials = cfgRes.data.credentials || {};
      channelInitState.existingConfig = cfgRes.data.config || {};
      if (cfgRes.data.config?.dmPolicy) {
        channelInitState.dmPolicy = cfgRes.data.config.dmPolicy;
      }
    }
    if (whRes?.success && whRes.data) {
      channelInitState.webhookData = whRes.data;
    }
  } catch { /* 使用預設值 */ }

  renderChannelInitModal();
};

/** 關閉 Channel 初始化精靈 */
window.closeChannelInitWizard = function () {
  channelInitState.active = false;
  const modal = document.getElementById("channel-init-modal");
  if (modal) modal.remove();
};

/** Step 導航 */
window.channelInitNav = function (direction) {
  const reg = CHANNEL_INIT_REGISTRY[channelInitState.channelName];
  if (!reg) return;

  if (direction === 1 && channelInitState.step === 1) {
    // Step 1 驗證: 全新設定時金鑰必填
    for (const field of reg.fields) {
      const val = (channelInitState.fieldValues[field.id] || "").trim();
      const existing = channelInitState.existingCredentials[field.id];
      if (!val && !(existing && existing.has_value)) {
        showToast(`${field.label} is required`, "error");
        return;
      }
    }
  }

  const totalSteps = reg.steps.length;
  const next = channelInitState.step + direction;
  if (next < 1 || next > totalSteps) return;
  channelInitState.step = next;
  renderChannelInitModal();
};

/** 設定 DM Policy */
window.setChannelInitDmPolicy = function (value) {
  channelInitState.dmPolicy = value;
  renderChannelInitModal();
};

/** 切換金鑰欄位顯示/隱藏 */
window.toggleChannelInitFieldVisibility = function (fieldId) {
  channelInitState.fieldVisible[fieldId] = !channelInitState.fieldVisible[fieldId];
  renderChannelInitModal();
};

/** 更新金鑰欄位值 */
window.updateChannelInitField = function (fieldId, value) {
  channelInitState.fieldValues[fieldId] = value;
};

/** 切換 Help Accordion */
window.toggleChannelInitHelp = function () {
  const el = document.getElementById("channel-init-help-content");
  if (el) el.classList.toggle("hidden");
  const icon = document.getElementById("channel-init-help-icon");
  if (icon) icon.classList.toggle("rotate-180");
};

/** 儲存 Channel 設定 */
window.saveChannelInit = async function () {
  const reg = CHANNEL_INIT_REGISTRY[channelInitState.channelName];
  if (!reg || channelInitState.saving) return;

  channelInitState.saving = true;
  renderChannelInitModal();

  try {
    const credentials = {};
    for (const field of reg.fields) {
      const val = (channelInitState.fieldValues[field.id] || "").trim();
      credentials[field.id] = val; // 空值表示保留現有
    }

    const config = { dmPolicy: channelInitState.dmPolicy };

    const result = await window.pywebview.api.save_channel_config(
      channelInitState.channelName, credentials, config,
    );

    if (result?.success) {
      showToast(`${reg.label} channel configured successfully`, "success");
      closeChannelInitWizard();
      pluginsPage.reload();
    } else {
      showToast(result?.error?.message || "Failed to save configuration", "error");
    }
  } catch (e) {
    showToast("Failed to save configuration", "error");
  } finally {
    channelInitState.saving = false;
  }
};

/** 渲染 Modal 整體 */
function renderChannelInitModal() {
  if (!channelInitState.active) return;

  const reg = CHANNEL_INIT_REGISTRY[channelInitState.channelName];
  if (!reg) return;

  let modal = document.getElementById("channel-init-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "channel-init-modal";
    document.body.appendChild(modal);
  }

  const totalSteps = reg.steps.length;
  const step = channelInitState.step;

  // Step Indicator
  const stepIndicator = reg.steps.map((label, i) => {
    const n = i + 1;
    const isCompleted = n < step;
    const isCurrent = n === step;
    const circleClass = isCompleted
      ? "bg-status-success text-white"
      : isCurrent
        ? "bg-accent-primary text-white"
        : "bg-bg-secondary text-text-muted border border-border-default";
    const labelClass = isCurrent ? "text-text-primary font-semibold" : "text-text-muted";
    const lineClass = isCompleted ? "bg-status-success" : "bg-border-default";
    const line = n < totalSteps ? `<div class="flex-1 h-0.5 ${lineClass} mx-2"></div>` : "";
    return `<div class="flex items-center ${n < totalSteps ? "flex-1" : ""}">
      <div class="flex flex-col items-center gap-1">
        <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${circleClass}">
          ${isCompleted ? '<i data-lucide="check" class="w-4 h-4"></i>' : n}
        </div>
        <span class="text-xs ${labelClass} whitespace-nowrap">${esc(label)}</span>
      </div>
      ${line}
    </div>`;
  }).join("");

  // Step content
  let stepContent = "";
  if (step === 1) stepContent = renderChannelInitStep1(reg);
  else if (step === 2) stepContent = renderChannelInitStep2(reg);
  else if (step === 3) stepContent = renderChannelInitStep3(reg);

  // Footer buttons
  const backBtn = step > 1
    ? renderButton({ variant: "ghost", icon: "arrow-left", label: "Back", onclick: "channelInitNav(-1)" })
    : "";
  const isLastStep = step === totalSteps;
  const nextBtn = isLastStep
    ? renderButton({
        variant: "primary",
        icon: channelInitState.saving ? "loader" : "check",
        label: channelInitState.saving ? "Saving..." : "Save & Complete",
        onclick: "saveChannelInit()",
        disabled: channelInitState.saving,
      })
    : renderButton({ variant: "primary", icon: "arrow-right", label: "Next", onclick: "channelInitNav(1)" });

  modal.innerHTML = `<div class="fixed inset-0 z-[9998] flex items-center justify-center bg-black/50" onclick="if(event.target===this)closeChannelInitWizard()">
    <div class="bg-bg-primary rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto" onclick="event.stopPropagation()">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 pt-6 pb-2">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white" style="background:${reg.iconColor}">${reg.icon}</div>
          <span class="text-lg font-bold text-text-primary">${esc(reg.label)} Channel Setup</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-sm text-text-muted">Step ${step} of ${totalSteps}</span>
          <button onclick="closeChannelInitWizard()" class="p-1 rounded hover:bg-bg-secondary text-text-muted hover:text-text-primary transition-colors">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>
      </div>

      <!-- Step Indicator -->
      <div class="flex items-start px-6 py-4">${stepIndicator}</div>

      <!-- Content -->
      <div class="px-6 pb-4">${stepContent}</div>

      <!-- Footer -->
      <div class="flex items-center justify-between px-6 py-4 border-t border-border-default">
        <div>${backBtn}</div>
        <div>${nextBtn}</div>
      </div>
    </div>
  </div>`;
  refreshIcons();
}

/** Step 1: Credentials */
function renderChannelInitStep1(reg) {
  const fieldsHtml = reg.fields.map(field => {
    const existing = channelInitState.existingCredentials[field.id];
    const hasExisting = existing && existing.has_value;
    const currentVal = channelInitState.fieldValues[field.id] || "";
    const isVisible = channelInitState.fieldVisible[field.id];
    const inputType = isVisible ? "text" : "password";
    const placeholder = hasExisting
      ? "Leave blank to keep current value"
      : `Enter ${field.label}`;
    const preview = hasExisting && !currentVal
      ? `<div class="text-xs text-text-muted mt-1">Current value: <span class="font-mono">${esc(existing.preview)}</span></div>`
      : "";

    return `<div>
      <label class="block text-sm font-semibold text-text-primary mb-1.5">${esc(field.label)}</label>
      <div class="relative">
        <input type="${inputType}" value="${esc(currentVal)}"
          placeholder="${esc(placeholder)}"
          oninput="updateChannelInitField('${field.id}', this.value)"
          class="w-full h-10 bg-bg-input border border-border-default rounded-lg px-3 pr-10 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary" />
        <button type="button" onclick="toggleChannelInitFieldVisibility('${field.id}')"
          class="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-text-muted hover:text-text-primary">
          <i data-lucide="${isVisible ? "eye-off" : "eye"}" class="w-4 h-4"></i>
        </button>
      </div>
      ${preview}
    </div>`;
  }).join("");

  // Help accordion
  const helpHtml = reg.helpSteps ? `<div class="mt-4">
    <button onclick="toggleChannelInitHelp()" class="flex items-center gap-1 text-sm text-accent-secondary hover:underline">
      <i data-lucide="chevron-down" id="channel-init-help-icon" class="w-4 h-4 transition-transform"></i>
      How to get these credentials?
    </button>
    <div id="channel-init-help-content" class="hidden mt-3 pl-2 border-l-2 border-border-default">
      <ol class="list-decimal list-inside space-y-2 text-sm text-text-secondary">
        ${reg.helpSteps.map(s => `<li>${esc(s)}</li>`).join("")}
      </ol>
    </div>
  </div>` : "";

  return `<div class="space-y-4">
    <div class="flex items-start gap-3 p-4 rounded-md border" style="background:#3b82f610;border-color:#3b82f630">
      <i data-lucide="info" class="w-5 h-5 text-status-info flex-shrink-0 mt-0.5"></i>
      <div>
        <div class="text-sm font-semibold text-status-info">${esc(reg.label)} Messaging API Credentials</div>
        <div class="text-xs text-text-secondary mt-0.5">You'll need credentials from the ${esc(reg.label)} Developers Console.
          ${reg.consoleUrl ? `<a href="#" onclick="event.preventDefault()" class="text-accent-secondary hover:underline ml-1">Open Console</a>` : ""}
        </div>
      </div>
    </div>
    ${fieldsHtml}
    ${helpHtml}
  </div>`;
}

/** Step 2: Webhook Setup */
function renderChannelInitStep2(reg) {
  const wh = channelInitState.webhookData;
  const templateUrl = wh ? wh.template : `https://<your-domain>/${channelInitState.channelName}/webhook`;
  const localUrl = wh ? wh.local_url : "";
  const note = wh ? wh.note : "";

  const instructionsHtml = reg.webhookInstructions
    ? reg.webhookInstructions.map((s, i) => `<li class="py-2 ${i > 0 ? "border-t border-border-default" : ""}">${esc(s)}</li>`).join("")
    : "";

  return `<div class="space-y-4">
    <!-- Webhook URL Card -->
    <div class="p-4 rounded-md border" style="background:#4CAF5015;border-color:#4CAF5040">
      <div class="flex items-center gap-2 mb-3">
        <i data-lucide="link" class="w-5 h-5 text-status-success"></i>
        <span class="text-sm font-semibold text-status-success">Your Webhook URL</span>
      </div>
      <div class="flex items-center gap-2">
        <code class="flex-1 bg-bg-tertiary rounded-lg p-3 text-sm font-mono text-text-primary break-all">${esc(templateUrl)}</code>
        <button onclick="clipboardWrite('${_jsEscapeForOnclick(templateUrl)}'); showToast('Copied!', 'success', 2000)"
          class="flex-shrink-0 p-2 rounded-lg hover:bg-bg-secondary text-text-muted hover:text-text-primary transition-colors" title="Copy">
          <i data-lucide="copy" class="w-4 h-4"></i>
        </button>
      </div>
      <div class="text-xs text-text-muted mt-2">Replace &lt;your-domain&gt; with your public HTTPS domain or ngrok URL</div>
      ${localUrl ? `<div class="text-xs text-text-muted mt-1">Local URL (for testing):
        <code class="font-mono bg-bg-tertiary px-1.5 py-0.5 rounded">${esc(localUrl)}</code>
        <button onclick="clipboardWrite('${_jsEscapeForOnclick(localUrl)}'); showToast('Copied!', 'success', 2000)"
          class="ml-1 text-accent-secondary hover:underline text-xs">copy</button>
      </div>` : ""}
    </div>

    <!-- Setup Instructions -->
    <div class="rounded-lg border border-border-default bg-bg-primary p-4">
      <div class="flex items-center gap-2 mb-3">
        <i data-lucide="clipboard-list" class="w-5 h-5 text-accent-secondary"></i>
        <span class="text-sm font-semibold text-text-primary">Setup Steps in ${esc(reg.label)} Console</span>
      </div>
      <ol class="list-decimal list-inside text-sm text-text-secondary space-y-0">
        ${instructionsHtml}
      </ol>
    </div>
  </div>`;
}

/** Step 3: DM Policy & Summary */
function renderChannelInitStep3(reg) {
  const policyHtml = (reg.dmPolicyOptions || []).map(opt => {
    const isSelected = channelInitState.dmPolicy === opt.value;
    const borderClass = isSelected ? "border-accent-primary border-2" : "border-border-default border";
    const bgClass = isSelected ? "bg-[#ef444408]" : "bg-bg-primary";
    return `<div class="flex items-start gap-3 p-4 rounded-lg cursor-pointer ${borderClass} ${bgClass} transition-colors"
      onclick="setChannelInitDmPolicy('${opt.value}')">
      <input type="radio" name="dm-policy" value="${opt.value}" ${isSelected ? "checked" : ""}
        class="mt-0.5 w-4 h-4 accent-accent-primary cursor-pointer" onchange="setChannelInitDmPolicy('${opt.value}')" />
      <div>
        <div class="text-sm font-semibold text-text-primary">${esc(opt.label)}</div>
        <div class="text-xs text-text-secondary mt-0.5">${esc(opt.desc)}</div>
      </div>
    </div>`;
  }).join("");

  const selectedPolicy = (reg.dmPolicyOptions || []).find(o => o.value === channelInitState.dmPolicy);
  const webhookPath = channelInitState.webhookData?.path || `/${channelInitState.channelName}/webhook`;

  const summaryItems = [
    { label: "Channel", value: reg.label },
    { label: "Credentials", value: `${reg.fields.map(f => f.label).join(" + ")} → .env` },
    { label: "DM Policy", value: selectedPolicy ? selectedPolicy.label : channelInitState.dmPolicy },
    { label: "Webhook", value: `${webhookPath} → configure in ${reg.label} Console` },
  ];

  return `<div class="space-y-4">
    <!-- DM Policy -->
    <div>
      <div class="flex items-center gap-2 mb-2">
        <i data-lucide="shield" class="w-5 h-5 text-accent-secondary"></i>
        <span class="text-sm font-semibold text-text-primary">Direct Message Policy</span>
      </div>
      <div class="text-xs text-text-secondary mb-3">Control who can send direct messages to your ${esc(reg.label)} bot</div>
      <div class="space-y-2">${policyHtml}</div>
    </div>

    <!-- Summary -->
    <div class="bg-bg-secondary rounded-lg p-4">
      <div class="text-sm font-semibold text-text-primary mb-2">Configuration Summary</div>
      <div class="space-y-1.5">
        ${summaryItems.map(item => `<div class="flex items-start gap-2 text-xs text-text-secondary">
          <i data-lucide="check-circle" class="w-3.5 h-3.5 text-status-success flex-shrink-0 mt-0.5"></i>
          <span><span class="font-medium text-text-primary">${esc(item.label)}:</span> ${esc(item.value)}</span>
        </div>`).join("")}
      </div>
    </div>
  </div>`;
}

/** 工具: JS 字串轉義（用於 onclick 屬性內的字串值） */
function _jsEscapeForOnclick(s) {
  return String(s).replace(/\\/g, "\\\\").replace(/'/g, "\\'");
}

/* =================================================================
 * 6b. Fix Plugins 頁面 (WBS 3.12)
 * ================================================================= */

const fixState = {
  report: [],
  diagnosing: false,
  fixing: false,
  progressMap: {},
  lastChecked: null,
};

function formatTimeAgo(date) {
  if (!date) return "";
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 10) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  return `${Math.floor(mins / 60)}h ago`;
}

function renderFixHeader() {
  const el = document.getElementById("fix-plugins-header-actions");
  if (!el) return;
  el.innerHTML = renderButton({
    variant: "secondary",
    icon: "scan",
    label: "Run Diagnostics",
    onclick: "runDiagnostics()",
    disabled: fixState.diagnosing || fixState.fixing,
    loading: fixState.diagnosing,
  });
  refreshIcons();
}

function renderFixBanner() {
  const healthy = fixState.report.filter(r => r.status === "healthy").length;
  const broken = fixState.report.filter(r => r.status === "broken").length;
  const total = fixState.report.length;
  const timeStr = fixState.lastChecked ? formatTimeAgo(fixState.lastChecked) : "";

  if (fixState.diagnosing) {
    return `<div class="flex items-center gap-3 rounded-md px-5 py-3.5" style="background:#3b82f610;border:1px solid #3b82f630">
      <i data-lucide="loader" class="w-5 h-5 text-status-info animate-spin"></i>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-status-info">Running diagnostics...</div>
        <div class="text-xs text-text-secondary mt-0.5">Checking plugin health and configuration</div>
      </div>
    </div>`;
  }
  if (total === 0) {
    return `<div class="flex items-center gap-3 rounded-md px-5 py-3.5" style="background:#3b82f610;border:1px solid #3b82f630">
      <i data-lucide="info" class="w-5 h-5 text-status-info"></i>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-status-info">No installed plugins</div>
        <div class="text-xs text-text-secondary mt-0.5">Install plugins first, then run diagnostics</div>
      </div>
      ${timeStr ? `<span class="text-xs text-text-muted whitespace-nowrap">Last checked: ${esc(timeStr)}</span>` : ""}
    </div>`;
  }
  if (broken === 0) {
    return `<div class="flex items-center gap-3 rounded-md px-5 py-3.5" style="background:#4CAF5015;border:1px solid #4CAF5040">
      <i data-lucide="check-circle" class="w-5 h-5 text-status-success"></i>
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-status-success">All plugins are healthy</div>
        <div class="text-xs text-text-secondary mt-0.5">${total} plugin${total > 1 ? "s" : ""} diagnosed — no issues found</div>
      </div>
      ${timeStr ? `<span class="text-xs text-text-muted whitespace-nowrap">Last checked: ${esc(timeStr)}</span>` : ""}
    </div>`;
  }
  return `<div class="flex items-center gap-3 rounded-md px-5 py-3.5" style="background:#F4433610;border:1px solid #F4433630">
    <i data-lucide="triangle-alert" class="w-5 h-5 text-status-error"></i>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold text-status-error">${broken} plugin${broken > 1 ? "s" : ""} need${broken === 1 ? "s" : ""} attention</div>
      <div class="text-xs text-text-secondary mt-0.5">Issues detected — click Fix All or fix individually</div>
    </div>
    ${timeStr ? `<span class="text-xs text-text-muted whitespace-nowrap">Last checked: ${esc(timeStr)}</span>` : ""}
  </div>`;
}

function renderFixPluginRow(item) {
  const badgeStatus = item.status === "healthy" ? "success" : "error";
  const badgeText = item.status === "healthy" ? "Healthy" : "Broken";

  const issuesHtml = item.issues.length > 0 ? `
    <div class="mt-2.5 flex flex-col gap-2" style="padding-left:36px">
      ${item.issues.map(issue => `
        <div class="flex items-start gap-2">
          <i data-lucide="circle-alert" class="w-3.5 h-3.5 text-status-error flex-shrink-0 mt-0.5"></i>
          <span class="text-xs text-text-secondary">${esc(issue)}</span>
        </div>`).join("")}
      <div class="flex justify-end mt-1">
        ${renderButton({ variant: "primary", icon: "wrench", label: "Fix", size: "sm", onclick: `fixSinglePlugin('${item.name}')`, disabled: fixState.fixing })}
      </div>
    </div>` : "";

  return `<div class="py-4 px-5 border-b border-border-default last:border-b-0 hover:bg-bg-input transition-colors">
    <div class="flex items-center gap-3">
      <div class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold text-white" style="background:${item.icon_color}">${esc(item.icon)}</div>
      <span class="text-sm font-semibold">${esc(item.name)}</span>
      <div class="flex-1"></div>
      ${renderStatusBadge({ status: badgeStatus, text: badgeText })}
    </div>
    ${issuesHtml}
  </div>`;
}

function renderFixProgressOverlay() {
  const names = Object.keys(fixState.progressMap);
  const allDone = names.length > 0 && names.every(n => {
    const s = fixState.progressMap[n].status;
    return s === "done" || s === "failed";
  });

  let itemsHtml = names.map(name => {
    const p = fixState.progressMap[name];
    const item = fixState.report.find(r => r.name === name);
    return renderProgressItem({
      name,
      description: p.message,
      status: p.status,
      icon: item ? item.icon : "?",
    });
  }).join("");

  if (allDone) {
    itemsHtml += `<div class="mt-4">${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Done", onclick: "finishFixAndRediagnose()" })}</div>`;
  }

  const panelEl = document.getElementById("fix-diagnostic-panel");
  if (panelEl) {
    const container = panelEl.querySelector(":scope > div:last-child");
    if (container) { container.innerHTML = itemsHtml; refreshIcons(); }
  }
}

function renderFixPage() {
  const content = document.getElementById("fix-plugins-content");
  if (!content) return;

  const reportRows = fixState.report.map(renderFixPluginRow).join("");
  const panelChildren = fixState.fixing
    ? "" // will be filled by progress overlay
    : (reportRows || '<p class="text-sm text-text-muted py-4 px-5">No diagnostic data available.</p>');

  content.innerHTML = renderFixBanner() + renderSectionPanel({
    icon: "stethoscope",
    iconColor: "text-accent-primary",
    title: "Diagnostic Report",
    description: "Health status of installed plugins",
    children: panelChildren,
    id: "fix-diagnostic-panel",
  });
  refreshIcons();

  if (fixState.fixing) renderFixProgressOverlay();
  renderFixActionBar();
  renderFixHeader();
}

function renderFixActionBar() {
  const bar = document.getElementById("fix-plugins-action-bar");
  if (!bar) return;

  const healthy = fixState.report.filter(r => r.status === "healthy").length;
  const broken = fixState.report.filter(r => r.status === "broken").length;

  if (fixState.report.length === 0 && !fixState.fixing) {
    bar.classList.add("hidden");
    return;
  }
  bar.classList.remove("hidden");
  bar.innerHTML = `<div class="flex items-center justify-between">
    <span class="text-sm text-text-secondary">${healthy} healthy · ${broken} broken</span>
    ${renderButton({
      variant: "primary",
      icon: "wrench",
      label: fixState.fixing ? "Fixing..." : "Fix All",
      onclick: "fixAllPlugins()",
      disabled: broken === 0 || fixState.fixing,
      loading: fixState.fixing,
    })}
  </div>`;
  refreshIcons();
}

async function runDiagnostics() {
  fixState.diagnosing = true;
  fixState.report = [];
  renderFixPage();

  try {
    const result = await window.pywebview.api.diagnose_plugins();
    if (result?.success && result.data) {
      fixState.report = result.data;
    } else {
      fixState.report = [];
      const content = document.getElementById("fix-plugins-content");
      if (content) {
        content.innerHTML = renderErrorBlock({
          message: result?.error?.message || "Failed to run diagnostics",
          retryAction: "runDiagnostics()",
        });
        refreshIcons();
      }
    }
  } catch {
    fixState.report = [];
  }

  fixState.diagnosing = false;
  fixState.lastChecked = new Date();
  renderFixPage();
}

async function fixSinglePlugin(id) {
  fixState.fixing = true;
  fixState.progressMap = { [id]: { status: "pending", message: "Waiting..." } };
  renderFixPage();

  try { await window.pywebview.api.fix_plugins([id]); } catch { /* progress overlay shows status */ }
  fixState.fixing = false;
  renderFixActionBar();
}

async function fixAllPlugins() {
  const broken = fixState.report.filter(r => r.status === "broken");
  if (broken.length === 0) return;

  fixState.fixing = true;
  fixState.progressMap = {};
  broken.forEach(r => { fixState.progressMap[r.name] = { status: "pending", message: "Waiting..." }; });
  renderFixPage();

  try { await window.pywebview.api.fix_all_plugins(); } catch { /* progress overlay shows status */ }
  fixState.fixing = false;
  renderFixActionBar();
}

async function finishFixAndRediagnose() {
  fixState.fixing = false;
  fixState.progressMap = {};
  await runDiagnostics();
}

window.updateFixProgress = function(name, status, message) {
  fixState.progressMap[name] = { status, message };
  renderFixProgressOverlay();
};
window.runDiagnostics = runDiagnostics;
window.fixSinglePlugin = fixSinglePlugin;
window.fixAllPlugins = fixAllPlugins;
window.finishFixAndRediagnose = finishFixAndRediagnose;

registerPage("fix-plugins", {
  onEnter: async () => { await runDiagnostics(); },
  onLeave: () => { fixState.fixing = false; },
});

/* =================================================================
 * 7. 儀表板頁面
 * ================================================================= */

/** 渲染儀表板完整內容 */
function renderDashboardPage(status) {
  const running = status?.running ?? false;
  const services = status?.services ?? [{ name: "gateway", status: "stopped" }];
  const uptime = status?.uptime ?? "\u2014";
  const skillsCount = status?.skills_count ?? 0;
  const pluginsCount = status?.plugins_count ?? 0;
  const runningCount = services.filter(s => s.status === "running").length;

  // 標頭狀態標籤
  const badgeEl = document.getElementById("dashboard-status-badge");
  if (badgeEl) {
    badgeEl.innerHTML = running
      ? renderStatusBadge({ status: "success", text: "Running" })
      : renderStatusBadge({ status: "error", text: "Stopped" });
    refreshIcons();
  }

  // 統計卡片列
  const statsRow = `<div class="flex gap-3">
    ${renderStatCard({ icon: "server", value: `${runningCount}/${services.length}`, label: "Services Running", status: running ? "success" : "error" })}
    ${renderStatCard({ icon: "clock", iconColor: "text-accent-secondary", value: uptime, label: "Uptime", status: "info" })}
    ${renderStatCard({ icon: "zap", iconColor: "text-status-info", value: String(skillsCount), label: "Skills Deployed", status: "info" })}
    ${renderStatCard({ icon: "puzzle", iconColor: "text-accent-secondary", value: String(pluginsCount), label: "Plugins Installed", status: "info" })}
  </div>`;

  // 服務清單
  const serviceListHtml = services.map(svc => {
    const svcStatus = svc.status === "running" ? "success" : "error";
    const svcLabel = svc.status === "running" ? "Running" : "Stopped";
    return `<div class="flex items-center justify-between py-3 border-b border-border-default last:border-b-0">
      <div class="flex items-center gap-3">
        <i data-lucide="radio" class="w-4 h-4 text-accent-primary"></i>
        <span class="text-sm font-medium capitalize">${esc(svc.name)}</span>
      </div>
      ${renderStatusBadge({ status: svcStatus, text: svcLabel })}
    </div>`;
  }).join("");

  // 服務控制按鈕
  let btnHtml;
  if (dashboardState.actionPending) {
    btnHtml = `<div class="flex gap-3 mt-4">
      ${renderButton({ variant: "secondary", icon: "loader", label: "Processing...", disabled: true, loading: true })}
    </div>`;
  } else if (running) {
    btnHtml = `<div class="flex gap-3 mt-4">
      ${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Restart Services", onclick: "handleServiceAction('restart')" })}
      ${renderButton({ variant: "danger", icon: "square", label: "Stop Services", onclick: "handleServiceAction('stop')" })}
    </div>`;
  } else {
    btnHtml = `<div class="flex gap-3 mt-4">
      ${renderButton({ variant: "primary", icon: "play", label: "Start Services", onclick: "handleServiceAction('start')" })}
    </div>`;
  }

  // 服務控制面板
  const serviceControlPanel = renderSectionPanel({
    icon: "activity", iconColor: "text-accent-primary",
    title: "Service Control", description: "Start or stop the OpenClaw service stack",
    children: serviceListHtml + btnHtml, id: "dashboard-svc-panel",
  });

  // 快速操作
  const actionCards = [
    { icon: "monitor", iconColor: "text-status-info", title: "Check Environment", desc: "Verify dependencies", view: "environment" },
    { icon: "zap", iconColor: "text-accent-primary", title: "Deploy Skills", desc: "Manage skill modules", view: "deploy-skills" },
    { icon: "puzzle", iconColor: "text-accent-secondary", title: "Install Plugins", desc: "Manage plugin modules", view: "install-plugins" },
  ];
  const actionCardsHtml = actionCards.map(a =>
    `<div class="bg-bg-input border border-border-default rounded-sm p-4 flex items-center gap-3 cursor-pointer hover:border-accent-primary hover:bg-bg-card transition-colors flex-1 min-w-0"
         onclick="navigateTo('${a.view}')">
      <div class="w-9 h-9 rounded-sm bg-bg-card flex items-center justify-center flex-shrink-0">
        <i data-lucide="${a.icon}" class="w-[18px] h-[18px] ${a.iconColor}"></i>
      </div>
      <div class="min-w-0">
        <div class="text-sm font-semibold">${esc(a.title)}</div>
        <div class="text-xs text-text-muted mt-0.5">${esc(a.desc)}</div>
      </div>
    </div>`
  ).join("");

  const quickActionsPanel = renderSectionPanel({
    icon: "compass", iconColor: "text-accent-secondary",
    title: "Quick Actions", description: "Navigate to common tasks",
    children: `<div class="flex flex-col gap-2">${actionCardsHtml}</div>`,
    id: "dashboard-qa-panel",
  });

  const bottomRow = `<div class="flex gap-4 flex-1 min-h-0">
    <div class="flex-1 min-w-0">${serviceControlPanel}</div>
    <div class="flex-1 min-w-0">${quickActionsPanel}</div>
  </div>`;

  renderInto("dashboard-content", statsRow + bottomRow);
}

/** 處理服務啟停重啟 */
async function handleServiceAction(action) {
  dashboardState.actionPending = true;

  const svcPanel = document.getElementById("dashboard-svc-panel");
  if (svcPanel) {
    const btnContainer = svcPanel.querySelector(".flex.gap-3.mt-4");
    if (btnContainer) {
      btnContainer.innerHTML = renderButton({ variant: "secondary", icon: "loader", label: "Processing...", disabled: true, loading: true });
      refreshIcons();
    }
  }

  try {
    const apiMap = { start: "start_service", stop: "stop_service", restart: "restart_service" };
    await window.pywebview.api[apiMap[action]]();
  } catch { /* 下次輪詢會更新 */ }

  dashboardState.actionPending = false;

  try {
    const resp = await window.pywebview.api.get_service_status();
    if (resp?.success) renderDashboardPage(resp.data);
  } catch { /* 下次輪詢會更新 */ }
}

function startDashboardPolling() {
  stopDashboardPolling();
  dashboardState.pollTimer = setInterval(async () => {
    try {
      const resp = await window.pywebview.api.get_service_status();
      if (resp?.success) renderDashboardPage(resp.data);
    } catch { /* 靜默處理輪詢錯誤 */ }
  }, 10000);
}

function stopDashboardPolling() {
  if (dashboardState.pollTimer) {
    clearInterval(dashboardState.pollTimer);
    dashboardState.pollTimer = null;
  }
}

registerPage("dashboard", {
  onEnter: async () => {
    renderInto("dashboard-content", renderLoading("Loading dashboard..."));
    try {
      const resp = await window.pywebview.api.get_service_status();
      renderDashboardPage(resp?.success ? resp.data : {});
    } catch { renderDashboardPage({}); }
    startDashboardPolling();
  },
  onLeave: () => stopDashboardPolling(),
});

/* =================================================================
 * 8. 環境檢查頁面
 * ================================================================= */

const CHECK_ICONS = {
  "Docker":          { icon: "container", color: "text-status-info" },
  "Docker Compose":  { icon: "layers",    color: "text-status-info" },
  "Docker Desktop":  { icon: "activity",  color: "text-status-success" },
  "Docker Running":  { icon: "activity",  color: "text-status-success" },
  "Node.js":         { icon: "hexagon",   color: "text-status-success" },
  "OpenClaw CLI":    { icon: "terminal",  color: "text-accent-primary" },
  "jq":              { icon: "braces",    color: "text-accent-secondary" },
  "VS Code":         { icon: "code",      color: "text-status-info" },
  "ngrok":           { icon: "globe",     color: "text-text-muted" },
  "systemd Service": { icon: "server",    color: "text-accent-secondary" },
};

/** 渲染環境摘要橫幅 */
function renderSummaryBanner(checks, envFile, lastChecked) {
  const passed = checks.filter(c => c.installed).length;
  const total = checks.length;
  const allPassed = passed === total && envFile.exists;
  const envText = envFile.exists ? ".env file verified" : ".env file missing";

  if (allPassed) {
    return `<div class="flex items-center justify-between rounded-md p-4 border" style="background: #4CAF5015; border-color: #4CAF5040;">
      <div class="flex items-center gap-3">
        <i data-lucide="check-circle" class="w-5 h-5 text-status-success flex-shrink-0"></i>
        <div>
          <div class="text-sm font-semibold text-status-success">All checks passed — environment is ready</div>
          <div class="text-xs text-text-secondary mt-0.5">${passed} of ${total} software checks passed \u00b7 ${esc(envText)}</div>
        </div>
      </div>
      <span class="text-xs text-text-muted">${esc(lastChecked)}</span>
    </div>`;
  }

  const failCount = total - passed + (envFile.exists ? 0 : 1);
  return `<div class="flex items-center justify-between rounded-md p-4 border" style="background: #F4433615; border-color: #F4433640;">
    <div class="flex items-center gap-3">
      <i data-lucide="alert-circle" class="w-5 h-5 text-status-error flex-shrink-0"></i>
      <div>
        <div class="text-sm font-semibold text-status-error">${failCount} check${failCount > 1 ? "s" : ""} failed — action required</div>
        <div class="text-xs text-text-secondary mt-0.5">${passed} of ${total} passed \u00b7 ${esc(envText)}</div>
      </div>
    </div>
    <span class="text-xs text-text-muted">${esc(lastChecked)}</span>
  </div>`;
}

/** 渲染檢查項目網格 */
function renderChecksGrid(checks) {
  const cards = checks.map(c => {
    const meta = CHECK_ICONS[c.name] || { icon: "help-circle", color: "text-text-muted" };
    return renderCheckCard({ icon: meta.icon, iconColor: meta.color, name: c.name, version: c.version, status: c.installed ? "installed" : "not-found" });
  }).join("");
  return `<div class="flex flex-wrap gap-4">${cards}</div>`;
}

/** 渲染 .env 檔案檢查卡片 */
function renderEnvFileCard(envFile) {
  const status = envFile.exists ? "success" : "error";
  const badgeText = envFile.exists ? "Verified" : "Missing";
  return `<div class="bg-bg-card border border-border-default rounded-md p-4 flex items-center gap-3">
    <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="file-text" class="w-[18px] h-[18px] text-accent-secondary"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">.env Configuration File</div>
      <div class="text-xs text-text-muted mt-0.5">${esc(envFile.message)}</div>
    </div>
    ${renderStatusBadge({ status, text: badgeText })}
  </div>`;
}

/** 渲染錯誤指引區塊 */
function renderErrorGuidance(checks) {
  const failed = checks.filter(c => !c.installed);
  if (failed.length === 0) return "";

  const items = failed.map(c =>
    `<li class="text-sm text-text-secondary">
      <span class="font-medium text-text-primary">${esc(c.name)}</span> — ${esc(c.message)}
    </li>`
  ).join("");

  return `<div class="rounded-md p-4 border" style="background: #F4433610; border-color: #F4433630;">
    <div class="flex items-start gap-3">
      <i data-lucide="alert-circle" class="w-5 h-5 text-status-error flex-shrink-0 mt-0.5"></i>
      <div>
        <div class="text-sm font-semibold text-status-error">Action Required</div>
        <ul class="mt-2 space-y-1.5 list-disc list-inside">${items}</ul>
      </div>
    </div>
  </div>`;
}

registerPage("environment", {
  onEnter: async () => {
    renderInto("environment-content", renderLoading("Running environment checks..."));

    // 注入模式標籤
    const badgeEl = document.getElementById("env-mode-badge");
    if (badgeEl && state.currentMode) {
      badgeEl.innerHTML = renderStatusBadge({ status: "info", text: MODE_LABELS[state.currentMode] || state.currentMode });
      refreshIcons();
    }

    try {
      const result = await window.pywebview.api.check_env();
      if (!result?.success) {
        renderInto("environment-content", renderErrorBlock({
          type: result?.error?.type || "INTERNAL",
          message: result?.error?.message || "Unknown error",
          retryAction: "navigateTo('environment')",
        }));
        return;
      }

      const { checks, env_file } = result.data;
      renderInto("environment-content", [
        renderSummaryBanner(checks, env_file, "Last checked: just now"),
        renderChecksGrid(checks),
        renderEnvFileCard(env_file),
        renderErrorGuidance(checks),
      ].join(""));
    } catch (err) {
      renderInto("environment-content", renderErrorBlock({
        message: String(err),
        retryAction: "navigateTo('environment')",
      }));
    }
  },
});

/* =================================================================
 * 9. 設定精靈
 * ================================================================= */

/* ---------- 9.1 模式定義 ---------- */

const DEPLOY_MODES = [
  { id: "docker-windows", icon: "monitor",  iconColor: "text-accent-primary",    borderColor: "#ff5c5c", name: "Docker Windows",         description: "Run OpenClaw in Docker on Windows" },
  { id: "docker-linux",   icon: "terminal", iconColor: "text-accent-secondary",  borderColor: "#14b8a6", name: "Docker Linux / WSL2",     description: "Run OpenClaw in Docker on Linux or WSL2" },
  { id: "native-linux",   icon: "server",   iconColor: "text-text-muted",        borderColor: "#838387", name: "Native Linux (systemd)",  description: "Install directly on Linux with systemd" },
  { id: "remote-ssh",     icon: "cloud",    iconColor: "text-[#8b5cf6]",         borderColor: "#8b5cf6", name: "Remote Server (SSH)",     description: "Connect to a remote server via SSH" },
];

const MODE_BASE = {
  config_dir: "~/.openclaw", workspace_dir: "~/.openclaw/workspace",
  gateway_bind: "lan", gateway_port: "18789",
  bridge_port: "18790", timezone: "Asia/Taipei", docker_image: "openclaw:local",
};

const MODE_DEFAULTS = {
  "docker-windows": { ...MODE_BASE },
  "docker-linux":   { ...MODE_BASE },
  "native-linux":   { ...MODE_BASE, docker_image: "" },
  "remote-ssh":     { ...MODE_BASE },
};

const CONFIG_FIELD_MAP = {
  "input-config-dir": "config_dir", "input-workspace-dir": "workspace_dir",
  "input-gateway-bind": "gateway_bind",
  "input-gateway-port": "gateway_port", "input-bridge-port": "bridge_port",
  "input-timezone": "timezone", "input-docker-image": "docker_image",
};

/* ---------- 9.2 表單狀態管理 ---------- */

/** 快照設定表單值 */
function saveConfigFormState() {
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (el) configState.formValues[key] = el.value;
  }
  const sandbox = document.getElementById("toggle-sandbox");
  if (sandbox) configState.formValues.sandbox = sandbox.checked;
  for (const id of ["input-ssh-host", "input-ssh-port", "input-ssh-username", "input-ssh-key-file", "input-ssh-password"]) {
    const el = document.getElementById(id);
    if (el) configState.formValues[id] = el.value;
  }
}

/** 還原表單值 */
function restoreConfigFormState() {
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (el && configState.formValues[key] !== undefined) el.value = configState.formValues[key];
  }
  const sandbox = document.getElementById("toggle-sandbox");
  if (sandbox && configState.formValues.sandbox !== undefined) sandbox.checked = configState.formValues.sandbox;
  for (const id of ["input-ssh-host", "input-ssh-port", "input-ssh-username", "input-ssh-key-file", "input-ssh-password"]) {
    const el = document.getElementById(id);
    if (el && configState.formValues[id] !== undefined) el.value = configState.formValues[id];
  }
}

/** 套用模式預設值至表單 */
function applyModeDefaults(mode) {
  const defaults = MODE_DEFAULTS[mode];
  if (!defaults) return;
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (!el) continue;
    const current = el.value.trim();
    const isDefault = !current || Object.values(MODE_DEFAULTS).some(d => d[key] === current);
    if (isDefault) el.value = defaults[key];
  }
}

/* ---------- 9.3 第一步 — 渲染 ---------- */

/** 渲染模式選擇卡片 */
function renderRadioCard(mode, selected) {
  const borderStyle = selected ? `border-color: ${mode.borderColor}; border-width: 2px; padding: 15px;` : "";
  const selectedCls = selected ? "radio-card-selected" : "";
  const indicator = selected
    ? `<div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="background: ${mode.borderColor};">
        <i data-lucide="check" class="w-3 h-3 text-white"></i></div>`
    : `<div class="w-5 h-5 rounded-full border-2 border-border-default flex-shrink-0"></div>`;

  return `<div class="radio-card ${selectedCls}" style="${borderStyle}" data-mode="${mode.id}" onclick="selectDeploymentMode('${mode.id}')">
    ${indicator}
    <div class="w-8 h-8 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="${mode.icon}" class="w-4 h-4 ${mode.iconColor}"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">${esc(mode.name)}</div>
      <div class="text-xs text-text-muted mt-0.5">${esc(mode.description)}</div>
    </div>
  </div>`;
}

function renderDeploymentModeSection() {
  const cards = DEPLOY_MODES.map(m => renderRadioCard(m, m.id === configState.selectedMode)).join("");
  return renderSectionPanel({ icon: "monitor", iconColor: "text-accent-primary", title: "Deployment Mode", children: `<div class="grid grid-cols-2 gap-3">${cards}</div>` });
}

function renderSSHSection() {
  const keyRowHidden = configState.sshAuthMethod === "password" ? "hidden" : "";
  const pwdRowHidden = configState.sshAuthMethod === "key" ? "hidden" : "";
  const toggleText = configState.sshAuthMethod === "key" ? "Use password instead" : "Use SSH key instead";

  const formGrid = `
    <div class="grid grid-cols-2 gap-4">
      ${renderInput({ id: "input-ssh-host", label: "Host", icon: "globe", placeholder: "192.168.1.100", required: true })}
      ${renderInput({ id: "input-ssh-port", label: "Port", placeholder: "22", type: "number", value: "22" })}
      ${renderInput({ id: "input-ssh-username", label: "Username", icon: "user", placeholder: "ubuntu", required: true })}
      <div id="ssh-key-row" class="${keyRowHidden}">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-text-secondary">SSH Key File</label>
          <div class="flex gap-2">
            <input id="input-ssh-key-file" type="text" placeholder="~/.ssh/id_rsa" readonly
              class="flex-1 bg-bg-input border border-border-default focus-within:border-accent-primary rounded-sm text-sm text-text-primary placeholder:text-text-muted pl-3 pr-3 py-2.5 outline-none transition-colors" />
            ${renderButton({ variant: "secondary", icon: "folder-open", label: "Browse", size: "sm", onclick: "browseSSHKey()" })}
          </div>
        </div>
      </div>
      <div id="ssh-password-row" class="${pwdRowHidden}">
        ${renderInput({ id: "input-ssh-password", label: "Password", type: "password", placeholder: "Enter password" })}
      </div>
    </div>
    <div class="mt-3 flex items-center justify-between">
      <button type="button" id="btn-toggle-ssh-auth" class="text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0 underline" onclick="toggleSSHAuthMethod()">
        ${toggleText}
      </button>
    </div>
    <div class="mt-4 flex items-center gap-3">
      ${renderButton({ variant: "secondary", icon: "wifi", label: "Test Connection", id: "btn-test-ssh", onclick: "testSSHConnection()" })}
      <span id="ssh-test-badge"></span>
    </div>`;

  return `<div id="ssh-section">${renderSectionPanel({ icon: "terminal", iconColor: "text-[#8b5cf6]", title: "SSH Connection", description: "Connect to your remote server via SSH", children: formGrid })}</div>`;
}

function renderGatewaySection() {
  const d = MODE_DEFAULTS[configState.selectedMode] || MODE_DEFAULTS["docker-windows"];
  const v = (key) => configState.formValues[key] !== undefined ? configState.formValues[key] : d[key];

  const mainGrid = `
    <div class="grid grid-cols-2 gap-4">
      ${renderInput({ id: "input-config-dir", label: "Config Directory", icon: "folder", placeholder: "~/.openclaw", value: v("config_dir") })}
      ${renderInput({ id: "input-workspace-dir", label: "Workspace Directory", icon: "folder", placeholder: "~/.openclaw/workspace", value: v("workspace_dir") })}
      ${renderInput({ id: "input-gateway-bind", label: "Gateway Bind Host", placeholder: "lan", value: v("gateway_bind") })}
      ${renderInput({ id: "input-gateway-port", label: "Gateway Port", type: "number", placeholder: "18789", value: v("gateway_port") })}
    </div>
    <div class="grid grid-cols-2 gap-4 mt-4">
      ${renderInput({ id: "input-bridge-port", label: "Bridge Port", type: "number", placeholder: "18790", value: v("bridge_port") })}
    </div>`;

  const sandboxChecked = configState.formValues.sandbox !== undefined ? configState.formValues.sandbox : true;
  const advancedContent = `
    <div id="advanced-settings" class="collapsible-content mt-4">
      <div class="grid grid-cols-2 gap-4">
        ${renderInput({ id: "input-timezone", label: "Timezone", placeholder: "Asia/Taipei", value: v("timezone") })}
        ${renderInput({ id: "input-docker-image", label: "Docker Image", placeholder: "openclaw:local", value: v("docker_image") })}
      </div>
      <div class="flex items-center gap-2 mt-4">
        <input type="checkbox" id="toggle-sandbox" class="checkbox-custom" ${sandboxChecked ? "checked" : ""} />
        <label for="toggle-sandbox" class="text-sm text-text-secondary cursor-pointer">Enable Sandbox</label>
      </div>
    </div>`;

  const advancedToggle = `
    <button type="button" class="flex items-center gap-1.5 mt-4 text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0" onclick="toggleAdvancedSettings()">
      <i data-lucide="chevron-right" class="w-3.5 h-3.5 collapsible-chevron" id="advanced-chevron"></i>
      <span>Advanced Settings</span>
    </button>`;

  return renderSectionPanel({ icon: "globe", iconColor: "text-accent-secondary", title: "Gateway & Directory", children: mainGrid + advancedToggle + advancedContent });
}

function renderConfigActionBar() {
  const nextDisabled = configState.selectedMode === "remote-ssh" && !configState.sshTestPassed;
  const html = `<div class="flex items-center justify-end gap-3">
    <span class="text-sm text-text-muted font-medium">Step ${configState.step} of 3</span>
    ${renderButton({ variant: "primary", icon: "arrow-right", label: "Next", id: "btn-next-step", disabled: nextDisabled, onclick: "configNextStep()" })}
  </div>`;
  renderInto("config-action-bar", html);
}

function renderConfigStep1() {
  const stepIndicator = renderStepIndicator({ steps: ["Environment", "API Keys", "Initialize"], currentStep: configState.step, completedSteps: [] });
  const sshSection = configState.selectedMode === "remote-ssh" ? renderSSHSection() : `<div id="ssh-section" class="hidden"></div>`;
  renderInto("config-content", [stepIndicator, renderDeploymentModeSection(), sshSection, renderGatewaySection()].join(""));
  renderConfigActionBar();
}

/* ---------- 9.4 第一步 — 事件處理 ---------- */

/** 選擇部署模式 */
function selectDeploymentMode(mode) {
  if (mode === configState.selectedMode) return;
  configState.selectedMode = mode;
  configState.sshTestPassed = false;
  configState.sshTestResult = null;

  window.pywebview.api.save_config({ deployment_mode: mode }).catch(() => {});
  updateSidebarMode(mode);

  // 更新卡片視覺
  document.querySelectorAll(".radio-card").forEach(card => {
    const cardMode = card.dataset.mode;
    const def = DEPLOY_MODES.find(m => m.id === cardMode);
    if (!def) return;

    const isSelected = cardMode === mode;
    card.classList.toggle("radio-card-selected", isSelected);
    card.style.borderColor = isSelected ? def.borderColor : "";
    card.style.borderWidth = isSelected ? "2px" : "";
    card.style.padding = isSelected ? "15px" : "";

    const indicator = card.children[0];
    if (isSelected) {
      indicator.className = "w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0";
      indicator.style.background = def.borderColor;
      indicator.innerHTML = `<i data-lucide="check" class="w-3 h-3 text-white"></i>`;
    } else {
      indicator.className = "w-5 h-5 rounded-full border-2 border-border-default flex-shrink-0";
      indicator.style.background = "";
      indicator.innerHTML = "";
    }
  });
  refreshIcons();

  // 切換 SSH 區段
  let sshEl = document.getElementById("ssh-section");
  if (sshEl) {
    if (mode === "remote-ssh") {
      if (!sshEl.innerHTML.trim()) {
        sshEl.outerHTML = renderSSHSection();
        refreshIcons();
      } else {
        sshEl.classList.remove("hidden");
      }
    } else {
      sshEl.classList.add("hidden");
    }
  }

  applyModeDefaults(mode);
  renderConfigActionBar();
}

/** 瀏覽 SSH 金鑰檔 */
async function browseSSHKey() {
  try {
    const result = await window.pywebview.api.browse_file("Select SSH Key", ["Key Files (*.pem;*.key;*.ppk;*.pub)", "All Files (*.*)"]);
    if (result?.success && result.data?.path) {
      const input = document.getElementById("input-ssh-key-file");
      if (input) input.value = result.data.path;
    }
  } catch { /* 對話框取消 */ }
}

/** 切換 SSH 驗證方式 */
function toggleSSHAuthMethod() {
  configState.sshAuthMethod = configState.sshAuthMethod === "key" ? "password" : "key";
  const keyRow = document.getElementById("ssh-key-row");
  const pwdRow = document.getElementById("ssh-password-row");
  if (keyRow) keyRow.classList.toggle("hidden", configState.sshAuthMethod === "password");
  if (pwdRow) pwdRow.classList.toggle("hidden", configState.sshAuthMethod === "key");
  const toggleBtn = document.getElementById("btn-toggle-ssh-auth");
  if (toggleBtn) toggleBtn.textContent = configState.sshAuthMethod === "key" ? "Use password instead" : "Use SSH key instead";
}

/** 切換進階設定 */
function toggleAdvancedSettings() {
  const content = document.getElementById("advanced-settings");
  const chevron = document.getElementById("advanced-chevron");
  if (content) content.classList.toggle("expanded");
  if (chevron) chevron.classList.toggle("rotated");
}

/** 取得 SSH 連線參數 */
function collectSSHParams() {
  const host = document.getElementById("input-ssh-host")?.value?.trim();
  const port = parseInt(document.getElementById("input-ssh-port")?.value, 10) || 22;
  const username = document.getElementById("input-ssh-username")?.value?.trim();
  const params = { host, port, username };

  if (configState.sshAuthMethod === "key") {
    const keyFile = document.getElementById("input-ssh-key-file")?.value?.trim();
    if (keyFile) params.key_path = keyFile;
  } else {
    const password = document.getElementById("input-ssh-password")?.value;
    if (password) params.password = password;
  }
  return params;
}

/** 測試 SSH 連線 */
async function testSSHConnection() {
  const params = collectSSHParams();
  const badge = document.getElementById("ssh-test-badge");

  if (!params.host || !params.username) {
    if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: "Host and Username are required" });
    refreshIcons();
    return;
  }

  // 顯示連線中狀態
  if (badge) {
    badge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#14b8a618] text-accent-secondary text-xs font-medium">
      <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> Connecting...</span>`;
    refreshIcons();
  }

  const btn = document.getElementById("btn-test-ssh");
  if (btn) { btn.disabled = true; btn.classList.add("opacity-50", "pointer-events-none"); }

  try {
    const result = await window.pywebview.api.test_connection(params);
    if (result?.success) {
      const info = result.data?.server_info || {};
      configState.sshTestPassed = true;
      configState.sshTestResult = info;
      if (badge) badge.innerHTML = renderStatusBadge({ status: "success", text: `Connected — ${info.os || "?"}, ${info.cpu_cores || "?"} cores, ${info.memory_gb || "?"}GB` });
    } else {
      configState.sshTestPassed = false;
      configState.sshTestResult = null;
      if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: result?.error?.message || "Connection failed" });
    }
  } catch (err) {
    configState.sshTestPassed = false;
    configState.sshTestResult = null;
    if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: String(err) });
  } finally {
    if (btn) { btn.disabled = false; btn.classList.remove("opacity-50", "pointer-events-none"); }
    refreshIcons();
    renderConfigActionBar();
  }
}

/** 第一步 → 第二步 */
async function configNextStep() {
  saveConfigFormState();

  // SSH 模式需先驗證
  if (configState.selectedMode === "remote-ssh") {
    if (!configState.sshTestPassed) return;

    const params = collectSSHParams();
    try {
      updateConnectionStatus("connecting");
      const connResult = await window.pywebview.api.connect_remote(params);
      if (!connResult?.success) {
        const badge = document.getElementById("ssh-test-badge");
        if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: connResult?.error?.message || "Connection failed" });
        refreshIcons();
        updateConnectionStatus("error");
        return;
      }
    } catch {
      updateConnectionStatus("error");
      return;
    }
  }

  // 收集設定值並儲存
  const config = { deployment_mode: configState.selectedMode };
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const val = document.getElementById(inputId)?.value?.trim();
    if (val) config[key] = val;
  }
  config.sandbox = document.getElementById("toggle-sandbox")?.checked ?? true;

  try { await window.pywebview.api.save_config(config); } catch { /* 非關鍵 */ }

  configState.step = 2;
  renderConfigStep2();
}

/* ---------- 9.5 第二步 — API Keys ---------- */

/** 儲存第二步表單 */
function saveStep2FormState() {
  step2State.keyValues = {};
  document.querySelectorAll("input[id^='key-']").forEach(input => {
    step2State.keyValues[input.id] = input.value;
  });
}

/** 還原第二步表單 */
function restoreStep2FormState() {
  for (const [id, val] of Object.entries(step2State.keyValues)) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }
  for (const name of step2State.checkedProviders) {
    const fields = document.getElementById(`provider-fields-${name}`);
    if (fields) fields.classList.add("expanded");
    const chk = document.getElementById(`provider-chk-${name}`);
    if (chk) chk.checked = true;
  }
}

/** 渲染 Provider 卡片 */
function renderProviderCard(provider, checked) {
  // 模型區塊
  let modelSection = "";
  const models = step2State.cachedModels?.[provider.name];
  if (provider.dynamic) {
    modelSection = `<div class="mt-3 flex items-center gap-1.5 text-xs text-text-muted italic">
      <i data-lucide="info" class="w-3.5 h-3.5 flex-shrink-0"></i>
      <span>Models are discovered at runtime</span>
    </div>`;
  } else if (models && models.length > 0) {
    const checkedSet = step2State.checkedModels[provider.name] || new Set();
    const pills = models.map(m => {
      const isChecked = checkedSet.has(m.id);
      return `<label class="model-pill inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border-default cursor-pointer select-none ${isChecked ? "model-pill-active" : ""}">
        <input type="checkbox" class="checkbox-custom checkbox-sm" data-provider="${provider.name}" data-model="${m.id}"
          ${isChecked ? "checked" : ""} onchange="toggleModelCheck('${provider.name}', '${m.id}')" />
        <span class="text-sm text-text-secondary">${esc(m.name)}</span>
      </label>`;
    }).join("");
    modelSection = `<div class="mt-3">
      <div class="text-xs font-medium text-text-muted mb-2">Available Models</div>
      <div class="flex flex-wrap gap-1.5">${pills}</div>
    </div>`;
  }

  const keyFields = provider.env_var
    ? `<div id="provider-fields-${provider.name}" class="collapsible-content ${checked ? "expanded" : ""}">
        <div class="mt-3">
          ${renderInput({ id: `key-${provider.env_var}`, label: provider.label + " API Key", icon: "lock", type: "password", placeholder: provider.placeholder || "", value: step2State.keyValues[`key-${provider.env_var}`] || "" })}
        </div>
        ${modelSection}
      </div>`
    : `<div id="provider-fields-${provider.name}" class="collapsible-content ${checked ? "expanded" : ""}">
        <div class="mt-2 text-xs text-text-muted">No API key required — configure URL in settings</div>
        ${modelSection}
      </div>`;

  return `<div class="provider-card-wrap">
    <label class="flex items-center gap-3 cursor-pointer select-none py-2">
      <input type="checkbox" id="provider-chk-${provider.name}" class="checkbox-custom provider-checkbox" data-provider="${provider.name}" ${checked ? "checked" : ""}
        onchange="toggleProviderCheck('${provider.name}')" />
      <span class="text-sm font-medium text-text-primary">${esc(provider.label)}</span>
    </label>
    ${keyFields}
  </div>`;
}

/** 收集所有已勾選供應商中被選取的模型選項 */
function getAllCheckedModelOptions() {
  const options = [];
  for (const name of step2State.checkedProviders) {
    const modelSet = step2State.checkedModels[name];
    if (!modelSet) continue;
    const catalog = step2State.cachedModels?.[name] || [];
    for (const m of catalog) {
      if (modelSet.has(m.id)) {
        options.push({ value: `${name}/${m.id}`, label: `${name}/${m.id}` });
      }
    }
  }
  return options;
}

/** 渲染 Primary Model 下拉選單 */
function renderPrimaryModelDropdown() {
  const options = getAllCheckedModelOptions();
  if (options.length === 0) return "";
  const current = step2State.primaryModel || options[0]?.value || "";
  if (!step2State.primaryModel) step2State.primaryModel = current;
  const optionsHtml = options.map(o =>
    `<option value="${esc(o.value)}" ${o.value === current ? "selected" : ""}>${esc(o.label)}</option>`
  ).join("");
  return `<div id="primary-model-container" class="border-t border-border-default mt-4 pt-4">
    <div class="text-xs font-medium text-text-muted mb-2">Primary Model</div>
    <select id="primary-model-select" class="w-full bg-bg-input border border-border-default rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary cursor-pointer"
      onchange="onPrimaryModelChange(this.value)">
      ${optionsHtml}
    </select>
  </div>`;
}

/** 更新 Primary Model 下拉選單（不 re-render 全頁） */
function updatePrimaryModelDropdown() {
  const options = getAllCheckedModelOptions();
  const container = document.getElementById("primary-model-container");
  const select = document.getElementById("primary-model-select");

  if (options.length === 0) {
    if (container) container.style.display = "none";
    step2State.primaryModel = null;
    return;
  }

  if (container) container.style.display = "";

  if (!options.some(o => o.value === step2State.primaryModel)) {
    step2State.primaryModel = options[0].value;
  }

  if (select) {
    select.innerHTML = options.map(o =>
      `<option value="${esc(o.value)}" ${o.value === step2State.primaryModel ? "selected" : ""}>${esc(o.label)}</option>`
    ).join("");
  }
}

/** 渲染區段（primary / secondary 分組 + More 展開） */
function renderGroupedSection({ icon, iconColor, title, description, items, checkedSet, renderCard, sectionKey, footer }) {
  const primary = items.filter(i => i.primary);
  const secondary = items.filter(i => !i.primary);

  const primaryCards = primary.map(i => renderCard(i, checkedSet.has(i.name))).join("");
  const secondaryCards = secondary.map(i => renderCard(i, checkedSet.has(i.name))).join("");

  const moreSection = secondary.length > 0
    ? `<button type="button" class="flex items-center gap-1.5 mt-3 text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0" onclick="toggleStep2More('${sectionKey}')">
        <i data-lucide="chevron-right" class="w-3.5 h-3.5 collapsible-chevron" id="${sectionKey}-more-chevron"></i>
        <span>More ${sectionKey}...</span>
      </button>
      <div id="${sectionKey}-more" class="collapsible-content">
        <div class="mt-2 grid gap-1">${secondaryCards}</div>
      </div>` : "";

  const footerHtml = footer || "";
  return renderSectionPanel({ icon, iconColor, title, description, children: `<div class="grid gap-1">${primaryCards}</div>${moreSection}${footerHtml}` });
}

function renderConfigStep2ActionBar() {
  const html = `<div class="flex items-center justify-between">
    <div>${renderButton({ variant: "secondary", icon: "arrow-left", label: "Back", onclick: "configPrevStep()" })}</div>
    <div class="flex items-center gap-3">
      <span class="text-sm text-text-muted font-medium">Step ${configState.step} of 3</span>
      ${renderButton({ variant: "primary", icon: "arrow-right", label: "Next", id: "btn-next-step2", onclick: "configNextStep2()" })}
    </div>
  </div>`;
  renderInto("config-action-bar", html);
}

async function renderConfigStep2() {
  // 從 Bridge 取得資料（快取）
  if (!step2State.cachedProviders) {
    try {
      const [pRes, mRes] = await Promise.all([
        window.pywebview.api.get_available_providers(),
        window.pywebview.api.get_provider_models(),
      ]);
      step2State.cachedProviders = pRes?.data || [];
      step2State.cachedModels = mRes?.data || {};
    } catch {
      step2State.cachedProviders = [];
      step2State.cachedModels = {};
    }
  }

  // 首次進入時從 .env 載入既有金鑰
  const isFirstLoad = Object.keys(step2State.keyValues).length === 0
    && step2State.checkedProviders.size === 0;
  if (isFirstLoad) {
    try {
      const envRes = await window.pywebview.api.load_env_keys();
      const envKeys = envRes?.data || {};
      for (const [envVar, val] of Object.entries(envKeys.providers || {})) {
        if (!val) continue;
        step2State.keyValues[`key-${envVar}`] = val;
        const provider = step2State.cachedProviders.find(p => p.env_var === envVar);
        if (provider) step2State.checkedProviders.add(provider.name);
      }
      // 還原模型選擇
      if (envKeys.models) {
        step2State.primaryModel = envKeys.models.primary || null;
        for (const fullId of (envKeys.models.selected || [])) {
          const idx = fullId.indexOf("/");
          if (idx < 0) continue;
          const prov = fullId.slice(0, idx);
          const modelId = fullId.slice(idx + 1);
          if (!step2State.checkedModels[prov]) step2State.checkedModels[prov] = new Set();
          step2State.checkedModels[prov].add(modelId);
        }
      }
    } catch { /* .env 讀取失敗 — 使用空白表單 */ }
  }

  const html = [
    renderStepIndicator({ steps: ["Environment", "API Keys", "Initialize"], currentStep: 2, completedSteps: [1] }),
    renderGroupedSection({
      icon: "cpu", iconColor: "text-accent-primary",
      title: "Model Providers", description: "Select providers and enter API keys \u2014 stored in .env with restricted permissions",
      items: step2State.cachedProviders, checkedSet: step2State.checkedProviders,
      renderCard: renderProviderCard, sectionKey: "providers",
      footer: renderPrimaryModelDropdown(),
    }),
    `<div class="flex items-start gap-3 px-2 py-3">
      <i data-lucide="shield-check" class="w-5 h-5 text-accent-primary flex-shrink-0 mt-0.5"></i>
      <p class="text-xs text-text-secondary leading-relaxed">All keys are stored in .env with restricted file permissions (owner-only access). Each server maintains its own independent .env configuration.</p>
    </div>`,
  ].join("");

  renderInto("config-content", html);
  renderConfigStep2ActionBar();
  restoreStep2FormState();
}

/* ---------- 9.5.1 第二步 — 事件處理 ---------- */

function toggleProviderCheck(name) {
  const chk = document.getElementById(`provider-chk-${name}`);
  if (!chk) return;
  chk.checked ? step2State.checkedProviders.add(name) : step2State.checkedProviders.delete(name);
  const fields = document.getElementById(`provider-fields-${name}`);
  if (fields) fields.classList.toggle("expanded", chk.checked);

  // 模型預設全選 / 取消勾選時清除
  const catalog = step2State.cachedModels?.[name];
  if (chk.checked && catalog?.length > 0 && !step2State.checkedModels[name]) {
    step2State.checkedModels[name] = new Set(catalog.map(m => m.id));
  }
  if (!chk.checked) {
    delete step2State.checkedModels[name];
  }
  updatePrimaryModelDropdown();
}

function toggleModelCheck(providerName, modelId) {
  if (!step2State.checkedModels[providerName]) {
    step2State.checkedModels[providerName] = new Set();
  }
  const set = step2State.checkedModels[providerName];
  const chk = document.querySelector(`input[data-provider="${providerName}"][data-model="${modelId}"]`);
  if (chk?.checked) set.add(modelId); else set.delete(modelId);
  const pill = chk?.closest(".model-pill");
  if (pill) pill.classList.toggle("model-pill-active", !!chk?.checked);
  updatePrimaryModelDropdown();
}

function onPrimaryModelChange(value) {
  step2State.primaryModel = value;
}

function toggleStep2More(section) {
  const content = document.getElementById(`${section}-more`);
  const chevron = document.getElementById(`${section}-more-chevron`);
  if (content) content.classList.toggle("expanded");
  if (chevron) chevron.classList.toggle("rotated");
}

function collectStep2Keys() {
  const keys = { providers: {} };
  for (const name of step2State.checkedProviders) {
    const provider = step2State.cachedProviders?.find(p => p.name === name);
    if (!provider?.env_var) continue;
    const val = document.getElementById(`key-${provider.env_var}`)?.value?.trim();
    if (val) keys.providers[provider.env_var] = val;
  }

  // 模型選擇
  const models = {};
  for (const [provName, modelSet] of Object.entries(step2State.checkedModels)) {
    if (!step2State.checkedProviders.has(provName)) continue;
    for (const modelId of modelSet) {
      models[`${provName}/${modelId}`] = {};
    }
  }
  keys.model_selection = {
    primary: step2State.primaryModel,
    models,
  };

  return keys;
}

function configPrevStep() {
  if (configState.step === 2) {
    saveStep2FormState();
    configState.step = 1;
    renderConfigStep1();
    renderConfigActionBar();
    restoreConfigFormState();
    return;
  }
  if (configState.step === 3) {
    configState.step = 2;
    renderConfigStep2();
  }
}

async function configNextStep2() {
  const btn = document.getElementById("btn-next-step2");
  if (btn) { btn.disabled = true; btn.classList.add("opacity-50", "pointer-events-none"); }

  try {
    saveStep2FormState();
    const keys = collectStep2Keys();
    const hasKeys = Object.values(keys).some(cat => Object.keys(cat).length > 0);
    if (hasKeys) await window.pywebview.api.save_keys(keys);
  } catch { /* 金鑰儲存失敗 — 繼續 */ }
  finally { if (btn) { btn.disabled = false; btn.classList.remove("opacity-50", "pointer-events-none"); } }

  configState.step = 3;
  renderConfigStep3();
}

/* ---------- 9.6 第三步 — 初始化 ---------- */

const INIT_STEPS_DOCKER = [
  { id: 1,  label: "Validate environment",      desc: "Checking Docker and Docker Compose availability" },
  { id: 2,  label: "Validate parameters",        desc: "Checking required configuration values" },
  { id: 3,  label: "Create directory structure", desc: "~/.openclaw/identity/, agents/main/agent/, sessions/" },
  { id: 4,  label: "Generate gateway token",     desc: "Reading from config or generating new token" },
  { id: 5,  label: "Write environment file",     desc: ".env with 16 variables (ports, paths, token, timezone)" },
  { id: 6,  label: "Build/Pull Docker image",    desc: "Building openclaw:local or pulling image" },
  { id: 7,  label: "Fix directory permissions",   desc: "Setting ownership for container user" },
  { id: 8,  label: "Configure gateway",          desc: "Set mode=local, bind, controlUi.allowedOrigins" },
  { id: 9,  label: "Start gateway",              desc: "docker compose up -d openclaw-gateway" },
  { id: 10, label: "Verify health",              desc: "Health check on http://127.0.0.1:{port}/healthz" },
];

const INIT_STEPS_NATIVE = [
  { id: 1, label: "Validate environment",      desc: "Checking Node.js, OpenClaw CLI, systemd availability" },
  { id: 2, label: "Validate parameters",        desc: "Checking required configuration values" },
  { id: 3, label: "Create directory structure", desc: "~/.openclaw/identity/, agents/main/agent/, sessions/" },
  { id: 4, label: "Generate gateway token",     desc: "Reading from config or generating new token" },
  { id: 5, label: "Write environment file",     desc: ".env with environment variables" },
  { id: 6, label: "Configure gateway",          desc: "Set mode=local, bind, controlUi.allowedOrigins" },
  { id: 7, label: "Start gateway",              desc: "systemctl start openclaw-gateway" },
  { id: 8, label: "Verify health",              desc: "Health check on http://127.0.0.1:{port}/healthz" },
];

function getInitSteps() {
  return configState.selectedMode === "native-linux" ? INIT_STEPS_NATIVE : INIT_STEPS_DOCKER;
}

function renderProgressPanel(steps) {
  const items = steps.map(s =>
    `<div data-init-step="${s.id}">${renderProgressItem({ name: s.label, description: s.desc, status: "pending" })}</div>`
  ).join("");
  return renderSectionPanel({
    icon: "loader", iconColor: "text-accent-primary",
    title: "Initialization Progress", description: `Running ${steps.length} steps to set up your environment`,
    children: items, id: "init-progress-panel",
  });
}

function renderDashboardInfoPanel() {
  const port = configState.formValues.gateway_port || "18789";
  const dashUrl = `http://127.0.0.1:${port}/`;

  return renderSectionPanel({
    icon: "layout-dashboard", iconColor: "text-accent-secondary",
    title: "Dashboard Info", description: "Available after Gateway is ready",
    children: `
      <div id="dashboard-info-fields" class="opacity-50 pointer-events-none">
        <div class="grid gap-3">
          ${renderInput({ id: "input-dash-url", label: "Dashboard URL", icon: "globe", value: dashUrl, type: "text" })}
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-text-secondary">Access Token</label>
            <div class="relative">
              <i data-lucide="lock" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"></i>
              <input id="input-dash-token" type="text" value="" readonly placeholder="Generated after init"
                class="w-full bg-bg-input border border-border-default rounded-sm text-sm text-text-primary placeholder:text-text-muted pl-10 pr-16 py-2.5 outline-none font-mono" />
              <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                <button type="button" class="p-1 text-text-muted hover:text-text-secondary transition-colors" onclick="toggleInitToken()" title="Show / Hide">
                  <i id="init-token-eye" data-lucide="eye" class="w-3.5 h-3.5"></i></button>
                <button type="button" class="p-1 text-text-muted hover:text-text-secondary transition-colors" onclick="copyInitToken()" title="Copy">
                  <i data-lucide="copy" class="w-3.5 h-3.5"></i></button>
              </div>
            </div>
          </div>
        </div>
        <div class="mt-4 pt-4 border-t border-border-default">
          <p class="text-xs text-text-secondary mb-3">Open the Dashboard URL in your browser, then approve the pending device request.</p>
          ${renderButton({ variant: "secondary", icon: "smartphone", label: "Approve Pending Device", onclick: "approvePendingDevice()" })}
          <div id="device-pairing-result" class="mt-3"></div>
        </div>
      </div>`,
    id: "dashboard-info-panel",
  });
}

function renderConfigStep3ActionBar() {
  const html = `<div class="flex items-center justify-between">
    <div>${renderButton({ variant: "secondary", icon: "arrow-left", label: "Back", disabled: initState.running, onclick: "configPrevStep()" })}</div>
    <div class="flex items-center gap-3">
      <span class="text-sm text-text-muted font-medium">Step 3 of 3</span>
      ${renderButton({
        variant: "primary",
        icon: initState.running ? "loader" : "play",
        label: initState.running ? "Initializing..." : "Initialize",
        id: "btn-initialize", disabled: initState.running,
        loading: initState.running, onclick: "startInitialization()",
      })}
    </div>
  </div>`;
  renderInto("config-action-bar", html);
}

function renderConfigStep3() {
  const steps = getInitSteps();
  const stepIndicator = renderStepIndicator({ steps: ["Environment", "API Keys", "Initialize"], currentStep: 3, completedSteps: [1, 2] });
  const html = `${stepIndicator}
    <div class="flex gap-5 flex-1 min-h-0">
      <div class="flex-1 min-w-0 overflow-y-auto">${renderProgressPanel(steps)}</div>
      <div class="w-[340px] flex-shrink-0">${renderDashboardInfoPanel()}</div>
    </div>`;
  renderInto("config-content", html);
  renderConfigStep3ActionBar();
  initState.running = false;
}

/** Bridge 進度回呼 — failed 時第 3 參數為步驟名、第 4 參數為錯誤訊息 */
window.updateInitProgress = function (step, status, message, error) {
  const stepId = parseInt(step, 10);
  const container = document.querySelector(`[data-init-step="${stepId}"]`);
  if (!container) return;
  const steps = getInitSteps();
  const meta = steps.find(s => s.id === stepId);
  const mapped = status === "done" ? "done" : status === "failed" ? "failed" : status === "running" ? "running" : "pending";
  container.innerHTML = renderProgressItem({
    name: meta?.label || `Step ${stepId}`,
    description: message || meta?.desc || "",
    status: mapped,
    error: mapped === "failed" ? (error || message) : undefined,
  });
  if (mapped === "failed") {
    initState.failedStep = stepId;
    initState.failedError = error || message;
  }
  refreshIcons();
};

async function startInitialization() {
  if (initState.running) return;
  initState.running = true;
  initState.failedStep = null;
  initState.failedError = null;
  renderConfigStep3ActionBar();

  // 重設所有步驟
  const steps = getInitSteps();
  for (const s of steps) {
    const container = document.querySelector(`[data-init-step="${s.id}"]`);
    if (container) container.innerHTML = renderProgressItem({ name: s.label, description: s.desc, status: "pending" });
  }
  refreshIcons();

  const params = {
    mode: configState.selectedMode,
    config_dir: configState.formValues.config_dir || "~/.openclaw",
    workspace_dir: configState.formValues.workspace_dir || "~/.openclaw/workspace",
    gateway_bind: configState.formValues.gateway_bind || "lan",
    gateway_port: parseInt(configState.formValues.gateway_port, 10) || 18789,
    bridge_port: parseInt(configState.formValues.bridge_port, 10) || 18790,
    timezone: configState.formValues.timezone || "Asia/Taipei",
    docker_image: configState.formValues.docker_image || "openclaw:local",
  };

  try {
    const result = await window.pywebview.api.initialize(params);
    initState.running = false;

    if (result?.success && result.data?.success) {
      const fields = document.getElementById("dashboard-info-fields");
      if (fields) fields.classList.remove("opacity-50", "pointer-events-none");
      initState.gatewayToken = result.data?.gateway_token || "";
      initState.tokenRevealed = false;
      const tokenInput = document.getElementById("input-dash-token");
      if (tokenInput && initState.gatewayToken) tokenInput.value = "\u2022".repeat(initState.gatewayToken.length);
    } else {
      const btn = document.getElementById("btn-initialize");
      if (btn) {
        btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4"></i><span>Retry</span>`;
        btn.disabled = false;
        btn.classList.remove("opacity-50", "pointer-events-none");
        refreshIcons();
      }
    }
    renderConfigStep3ActionBar();
  } catch {
    initState.running = false;
    renderConfigStep3ActionBar();
  }
}

/** 複製錯誤訊息至剪貼簿，icon 切換為 check 回饋 2 秒 */
async function copyProgressError(btn) {
  const block = btn.closest("[data-error-text]");
  const text = block?.dataset?.errorText || "";
  await clipboardWrite(text);
  const icon = btn.querySelector("i");
  if (icon) { icon.setAttribute("data-lucide", "check"); refreshIcons(); }
  setTimeout(() => {
    if (icon) { icon.setAttribute("data-lucide", "copy"); refreshIcons(); }
  }, 2000);
}

/** 從失敗步驟重新執行初始化（步驟為冪等，重跑安全） */
function retryFromFailedStep() {
  startInitialization();
}

/* ---------- 9.6.1 Dashboard Info 輔助 ---------- */

function toggleInitToken() {
  if (!initState.gatewayToken) return;
  initState.tokenRevealed = !initState.tokenRevealed;
  const input = document.getElementById("input-dash-token");
  if (input) input.value = initState.tokenRevealed ? initState.gatewayToken : "\u2022".repeat(initState.gatewayToken.length);
  const icon = document.getElementById("init-token-eye");
  if (icon) { icon.setAttribute("data-lucide", initState.tokenRevealed ? "eye-off" : "eye"); refreshIcons(); }
}

async function copyInitToken() {
  if (!initState.gatewayToken) return;
  await clipboardWrite(initState.gatewayToken);
  const btn = document.querySelector("[onclick='copyInitToken()']");
  if (btn) {
    const icon = btn.querySelector("i");
    if (icon) { icon.setAttribute("data-lucide", "check"); refreshIcons(); }
    setTimeout(() => { if (icon) { icon.setAttribute("data-lucide", "copy"); refreshIcons(); } }, 1500);
  }
}

/* ---------- 9.6.2 裝置配對 ---------- */

function renderDevicePairingResult(resultState, message, devices) {
  const container = document.getElementById("device-pairing-result");
  if (!container) return;

  const templates = {
    loading: () => `<div class="flex items-center gap-2 text-text-muted">
      <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span class="text-xs">${message}</span></div>`,
    empty: () => `<div class="flex items-center gap-2 text-text-muted">
      <i data-lucide="info" class="w-3.5 h-3.5"></i><span class="text-xs">${message}</span></div>`,
    list: () => {
      const rows = (devices || []).map(d => {
        const name = d.displayName || d.deviceId || "Unknown";
        const ip = d.remoteIp || "";
        const rid = d.requestId || "";
        return `<div id="device-row-${rid}" class="flex items-center gap-2 p-2 rounded bg-bg-elevated border border-border-default">
          <i data-lucide="monitor-smartphone" class="w-3.5 h-3.5 text-text-muted flex-shrink-0"></i>
          <div class="flex-1 min-w-0">
            <div class="text-xs font-medium text-text-primary truncate">${name}</div>
            ${ip ? `<div class="text-[11px] text-text-muted">${ip}</div>` : ""}
          </div>
          ${renderButton({ variant: "primary", label: "Approve", size: "sm", onclick: `approveDevice('${rid}')` })}
        </div>`;
      }).join("");
      return `<div class="flex flex-col gap-2"><span class="text-xs text-text-secondary">${message}</span>${rows}</div>`;
    },
    success: () => `<div class="flex items-center gap-2">
      <i data-lucide="circle-check" class="w-3.5 h-3.5 text-green-500"></i><span class="text-xs text-green-500">${message}</span></div>`,
    error: () => `<div class="flex items-center gap-2">
      <i data-lucide="circle-x" class="w-3.5 h-3.5 text-red-400"></i><span class="text-xs text-red-400">${message}</span></div>`,
  };

  container.innerHTML = (templates[resultState] || (() => ""))();
  refreshIcons();
}

async function approvePendingDevice() {
  if (initState.deviceApprovalLoading) return;
  initState.deviceApprovalLoading = true;
  renderDevicePairingResult("loading", "Fetching pending devices...");

  try {
    const result = await window.pywebview.api.list_pending_devices();
    if (!result?.success) {
      renderDevicePairingResult("error", result?.error?.message || "Failed to list devices");
      return;
    }
    const devices = result.data?.devices || [];
    if (devices.length === 0) renderDevicePairingResult("empty", "No pending devices found");
    else renderDevicePairingResult("list", `${devices.length} pending device(s) found`, devices);
  } catch { renderDevicePairingResult("error", "Connection error"); }
  finally { initState.deviceApprovalLoading = false; }
}

async function approveDevice(requestId) {
  const row = document.getElementById(`device-row-${requestId}`);
  if (row) { const btn = row.querySelector("button"); if (btn) { btn.disabled = true; btn.classList.add("opacity-50"); } }
  try {
    const result = await window.pywebview.api.approve_device({ request_id: requestId });
    renderDevicePairingResult(result?.success ? "success" : "error", result?.success ? "Device approved successfully" : (result?.error?.message || "Approval failed"));
  } catch { renderDevicePairingResult("error", "Connection error during approval"); }
}

/* ---------- 9.7 設定頁面生命週期 ---------- */

registerPage("configuration", {
  onEnter: async () => {
    if (configState.rendered) {
      if (configState.step === 1) { renderConfigStep1(); restoreConfigFormState(); }
      else if (configState.step === 2) renderConfigStep2();
      else if (configState.step === 3) renderConfigStep3();
      return;
    }
    try {
      const platform = await window.pywebview.api.detect_platform();
      configState.selectedMode = platform?.data?.current_mode || platform?.data?.suggested_mode || "docker-windows";
    } catch { configState.selectedMode = "docker-windows"; }

    try {
      const saved = await window.pywebview.api.load_config();
      if (saved?.success && saved.data) {
        const s = saved.data;
        for (const key of ["config_dir", "workspace_dir", "gateway_bind", "gateway_port", "bridge_port", "timezone", "docker_image"]) {
          if (s[key] !== undefined) configState.formValues[key] = String(s[key]);
        }
        if (s.sandbox !== undefined) configState.formValues.sandbox = s.sandbox;
        if (s.ssh_host) configState.formValues["input-ssh-host"] = s.ssh_host;
        if (s.ssh_port) configState.formValues["input-ssh-port"] = String(s.ssh_port);
        if (s.ssh_username) configState.formValues["input-ssh-username"] = s.ssh_username;
        if (s.ssh_key_path) configState.formValues["input-ssh-key-file"] = s.ssh_key_path;
      }
    } catch { /* 使用預設值 */ }

    configState.sshTestPassed = false;
    configState.sshTestResult = null;
    configState.step = 1;
    renderConfigStep1();
    configState.rendered = true;
  },
  onLeave: () => {
    if (configState.step === 1) saveConfigFormState();
    else if (configState.step === 2) saveStep2FormState();
  },
});

/* =================================================================
 * 10. Gateway 頁面
 * ================================================================= */

/** 載入所有 Gateway 資料 */
async function loadGatewayData() {
  gatewayState.loading = true;
  gatewayState.pendingBind = null;
  gatewayState.pendingControlUi = null;
  gatewayState.settingsDirty = false;
  renderGatewayPage();

  try {
    const [originsResp, devicesResp, notesResp, infoResp] = await Promise.all([
      window.pywebview.api.get_allowed_origins(),
      window.pywebview.api.list_devices(),
      window.pywebview.api.get_device_notes(),
      window.pywebview.api.get_gateway_info(),
    ]);
    if (originsResp?.success) {
      gatewayState.allowAll = originsResp.data.allow_all;
      gatewayState.origins = (originsResp.data.origins || []).filter(o => o !== "*");
    }
    if (devicesResp?.success) gatewayState.devices = { pending: devicesResp.data.pending || [], paired: devicesResp.data.paired || [] };
    if (notesResp?.success) gatewayState.deviceNotes = notesResp.data.notes || {};
    if (infoResp?.success) gatewayState.info = infoResp.data;
  } catch { /* 使用預設值 */ }

  gatewayState.loading = false;
  renderGatewayPage();
}

function renderGatewayPage() {
  if (gatewayState.loading) { renderInto("gateway-content", renderLoading("Loading gateway data...")); return; }

  renderInto("gateway-content", `
    ${renderGatewayPairingInfoSection()}
    <div class="flex gap-5">
      <div class="flex-1 min-w-0">${renderOriginControlSection()}</div>
      <div class="flex-1 min-w-0">${renderDeviceManagementSection()}</div>
    </div>
  `);
}

function renderGatewayPairingInfoSection() {
  if (!gatewayState.info) {
    return renderSectionPanel({ icon: "link", iconColor: "text-accent-secondary", title: "Connection Info",
      description: "Gateway connection details could not be loaded",
      children: '<p class="text-xs text-text-muted">Unable to read gateway configuration.</p>', id: "gateway-info-panel" });
  }

  const info = gatewayState.info;
  const currentBind = gatewayState.pendingBind ?? info.bind;
  const currentControlUi = gatewayState.pendingControlUi ?? info.control_ui_enabled;
  const bindDescriptions = {
    loopback: "Only accessible from this machine (127.0.0.1)",
    lan: "Accessible from all network interfaces (0.0.0.0)",
  };

  // Gateway URL（唯讀 + Copy）
  const urlSection = `
    <div class="flex flex-col gap-1.5">
      <span class="text-xs font-medium text-text-muted">Gateway URL</span>
      <div class="flex gap-2 items-center">
        <code class="flex-1 text-sm font-mono text-accent-secondary bg-bg-input border border-border-default rounded-sm px-3 py-2 select-all break-all">${esc(info.url)}</code>
        <button type="button" class="flex items-center justify-center w-9 h-9 bg-bg-input border border-border-default rounded-sm text-text-muted hover:text-text-secondary transition-colors cursor-pointer flex-shrink-0" onclick="copyGatewayUrl()" title="Copy URL">
          <i id="gateway-url-copy-icon" data-lucide="copy" class="w-3.5 h-3.5"></i></button>
      </div>
    </div>`;

  // Bind Mode（下拉選單 + 說明）
  const bindSection = `
    <div class="flex flex-col gap-1.5">
      <span class="text-xs font-medium text-text-muted">Bind Mode</span>
      <select id="gateway-bind-select" onchange="onGatewayBindChange(this.value)"
        class="w-full bg-bg-input border border-border-default rounded-sm text-sm text-text-primary px-3 py-2 outline-none focus:border-accent-primary transition-colors cursor-pointer appearance-none"
        style="background-image:url('data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%2212%22 height=%2212%22 viewBox=%220 0 24 24%22 fill=%22none%22 stroke=%22%23838387%22 stroke-width=%222%22><polyline points=%226 9 12 15 18 9%22/></svg>');background-repeat:no-repeat;background-position:right 12px center;">
        <option value="loopback" ${currentBind === "loopback" ? "selected" : ""}>loopback</option>
        <option value="lan" ${currentBind === "lan" ? "selected" : ""}>lan</option>
      </select>
      <span class="text-xs text-text-muted">${esc(bindDescriptions[currentBind] || "")}</span>
    </div>`;

  // Gateway Token（遮罩 + Show/Hide + Copy）
  const token = info.gateway_token || "";
  const maskedToken = token ? token.slice(0, 8) + "\u2026" : "Not configured";
  const tokenSection = `
    <div class="flex flex-col gap-1.5">
      <span class="text-xs font-medium text-text-muted">Gateway Token</span>
      <div class="relative">
        <i data-lucide="lock" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"></i>
        <code id="gateway-token-display" class="block text-sm font-mono bg-bg-input border border-border-default rounded-sm pl-10 ${token ? "pr-16" : "pr-3"} py-2 select-all break-all ${token ? "" : "text-text-muted"}">${esc(maskedToken)}</code>
        ${token ? `
          <div class="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <button type="button" class="p-1 text-text-muted hover:text-text-secondary transition-colors cursor-pointer" onclick="toggleGatewayToken()" title="Show / Hide">
              <i id="gateway-token-eye" data-lucide="eye" class="w-3.5 h-3.5"></i></button>
            <button type="button" class="p-1 text-text-muted hover:text-text-secondary transition-colors cursor-pointer" onclick="copyGatewayToken()" title="Copy">
              <i data-lucide="copy" class="w-3.5 h-3.5"></i></button>
          </div>
        ` : ""}
      </div>
    </div>`;

  // Control UI Enabled（Checkbox）
  const controlUiSection = `
    <div class="flex items-center gap-3">
      <input type="checkbox" id="gateway-control-ui-cb" ${currentControlUi ? "checked" : ""} onchange="onGatewayControlUiChange(this.checked)"
        class="w-4.5 h-4.5 rounded accent-accent-primary cursor-pointer flex-shrink-0">
      <div class="flex flex-col gap-0.5">
        <label for="gateway-control-ui-cb" class="text-sm font-medium text-text-primary cursor-pointer">Control UI Enabled</label>
        <span class="text-xs text-text-muted">Serve the Gateway Control UI web interface</span>
      </div>
    </div>`;

  // Save Settings 按鈕
  const saveSection = `
    <div class="flex justify-end">
      ${renderButton({ variant: "primary", icon: "save", label: "Save Settings", disabled: !gatewayState.settingsDirty, onclick: "saveGatewaySettings()" })}
    </div>`;

  const children = [urlSection, bindSection, tokenSection, controlUiSection, saveSection].join('<div class=""></div>');

  return renderSectionPanel({ icon: "link", iconColor: "text-accent-secondary", title: "Connection Info",
    description: "Gateway endpoint and authentication for device pairing", children, id: "gateway-info-panel" });
}

function renderOriginControlSection() {
  const toggleRow = `
    <div class="flex items-center justify-between py-3">
      <div>
        <div class="text-sm font-medium">Allow All Origins</div>
        <div class="text-xs text-text-muted mt-0.5">Set allowedOrigins to ["*"] — allows any origin</div>
      </div>
      <label class="relative inline-flex items-center cursor-pointer">
        <input type="checkbox" class="sr-only peer" ${gatewayState.allowAll ? "checked" : ""} onchange="toggleAllowAllOrigins(this.checked)">
        <div class="w-9 h-5 bg-bg-input border border-border-default rounded-full peer peer-checked:bg-accent-primary peer-checked:border-accent-primary transition-colors after:content-[''] after:absolute after:top-[3px] after:left-[3px] after:bg-white after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:after:translate-x-4"></div>
      </label>
    </div>`;

  let whitelistHtml = "";
  if (!gatewayState.allowAll) {
    const originRows = gatewayState.origins.map((origin, i) => `
      <div class="flex items-center gap-2 py-2 border-b border-border-default last:border-b-0">
        <i data-lucide="globe" class="w-4 h-4 text-text-muted flex-shrink-0"></i>
        <span class="text-sm flex-1 min-w-0 truncate">${esc(origin)}</span>
        <button class="text-text-muted hover:text-status-error transition-colors cursor-pointer bg-transparent border-0 p-1" onclick="removeOrigin(${i})">
          <i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
      </div>`).join("");

    const emptyMsg = gatewayState.origins.length === 0 ? '<p class="text-xs text-text-muted py-3">No origins configured. Add one below.</p>' : "";
    whitelistHtml = `
      <div class="mt-3 border-t border-border-default pt-3">
        <div class="text-xs font-medium text-text-secondary mb-2">Whitelist</div>
        ${emptyMsg}${originRows}
        <div class="flex gap-2 mt-3">
          <input id="gateway-new-origin" type="text" placeholder="https://example.com"
            class="flex-1 bg-bg-input border border-border-default rounded-sm text-sm text-text-primary placeholder:text-text-muted px-3 py-2 outline-none focus:border-accent-primary transition-colors">
          ${renderButton({ variant: "secondary", icon: "plus", label: "Add", size: "sm", onclick: "addOrigin()" })}
        </div>
      </div>`;
  }

  const saveBtn = `<div class="mt-4">${renderButton({ variant: "primary", icon: "save", label: "Save Origins", onclick: "saveOrigins()" })}</div>`;
  return renderSectionPanel({ icon: "globe", iconColor: "text-status-info", title: "Origin Access Control",
    description: "Manage which origins can access the Gateway Control UI", children: toggleRow + whitelistHtml + saveBtn, id: "gateway-origin-panel" });
}

function renderDeviceManagementSection() {
  const pending = gatewayState.devices.pending || [];
  const paired = gatewayState.devices.paired || [];

  let pendingHtml = "";
  if (pending.length > 0) {
    pendingHtml = `<div class="mb-4">
      <div class="text-xs font-medium text-text-secondary mb-2">Pending Requests (${pending.length})</div>
      ${pending.map(renderPendingDeviceRow).join("")}
    </div>`;
  }

  let pairedHtml = "";
  if (paired.length > 0) {
    pairedHtml = `<div class="${pending.length > 0 ? "border-t border-border-default pt-4" : ""}">
      <div class="text-xs font-medium text-text-secondary mb-2">Paired Devices (${paired.length})</div>
      ${paired.map(renderPairedDeviceRow).join("")}
    </div>`;
  }

  const emptyMsg = pending.length === 0 && paired.length === 0 ? '<p class="text-xs text-text-muted py-3">No devices found.</p>' : "";
  const refreshBtn = `<div class="mt-4">${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Refresh", onclick: "refreshDeviceList()" })}</div>`;

  return renderSectionPanel({ icon: "smartphone", iconColor: "text-accent-primary", title: "Device Management",
    description: "Approve, reject, or remove paired devices", children: pendingHtml + pairedHtml + emptyMsg + refreshBtn, id: "gateway-device-panel" });
}

function renderPendingDeviceRow(device) {
  const name = device.displayName || device.deviceId || "Unknown";
  const ip = device.remoteIp || "";
  const roles = (device.roles || []).join(", ");
  return `<div class="flex items-center gap-3 py-3 border-b border-border-default last:border-b-0">
    <div class="w-8 h-8 rounded-full bg-[#eab30818] flex items-center justify-center flex-shrink-0">
      <i data-lucide="clock" class="w-4 h-4 text-[#eab308]"></i></div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">${esc(name)}</div>
      <div class="text-xs text-text-muted mt-0.5">${esc(ip)}${roles ? " &middot; " + esc(roles) : ""}</div>
    </div>
    <div class="flex gap-1.5 flex-shrink-0">
      ${renderButton({ variant: "primary", icon: "check", label: "Approve", size: "sm", onclick: `approveDeviceFromGateway('${esc(device.requestId)}')` })}
      ${renderButton({ variant: "danger", icon: "x", label: "Reject", size: "sm", onclick: `rejectDevice('${esc(device.requestId)}')` })}
    </div>
  </div>`;
}

function renderPairedDeviceRow(device) {
  const name = device.displayName || device.deviceId || "Unknown";
  const ip = device.remoteIp || "";
  const deviceId = device.deviceId || "";
  const note = gatewayState.deviceNotes[deviceId] || "";
  return `<div class="flex items-center gap-3 py-3 border-b border-border-default last:border-b-0">
    <div class="w-8 h-8 rounded-full bg-[#22c55e18] flex items-center justify-center flex-shrink-0">
      <i data-lucide="smartphone" class="w-4 h-4 text-status-success"></i></div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">${esc(name)}</div>
      <div class="text-xs text-text-muted mt-0.5">${esc(ip)}</div>
    </div>
    <input type="text" value="${esc(note)}" placeholder="Note..."
      class="w-[140px] bg-bg-input border border-border-default rounded-sm text-xs text-text-primary placeholder:text-text-muted px-2 py-1.5 outline-none focus:border-accent-primary transition-colors"
      onblur="saveDeviceNote('${esc(deviceId)}', this.value)">
    <button class="text-text-muted hover:text-status-error transition-colors cursor-pointer bg-transparent border-0 p-1 flex-shrink-0" onclick="removeDevice('${esc(deviceId)}')">
      <i data-lucide="trash-2" class="w-3.5 h-3.5"></i></button>
  </div>`;
}

/* ---------- Gateway 互動函式 ---------- */

function toggleGatewayToken() {
  if (!gatewayState.info?.gateway_token) return;
  gatewayState.tokenRevealed = !gatewayState.tokenRevealed;
  const el = document.getElementById("gateway-token-display");
  const eyeEl = document.getElementById("gateway-token-eye");
  if (el) el.textContent = gatewayState.tokenRevealed ? gatewayState.info.gateway_token : gatewayState.info.gateway_token.slice(0, 8) + "\u2026";
  if (eyeEl) { eyeEl.setAttribute("data-lucide", gatewayState.tokenRevealed ? "eye-off" : "eye"); refreshIcons(); }
}

async function copyGatewayToken() {
  if (!gatewayState.info?.gateway_token) return;
  await clipboardWrite(gatewayState.info.gateway_token);
  const btn = document.querySelector("[onclick='copyGatewayToken()']");
  if (btn) {
    const icon = btn.querySelector("i");
    if (icon) { icon.setAttribute("data-lucide", "check"); refreshIcons(); }
    setTimeout(() => { if (icon) { icon.setAttribute("data-lucide", "copy"); refreshIcons(); } }, 1500);
  }
}

async function copyGatewayUrl() {
  if (!gatewayState.info?.url) return;
  await clipboardWrite(gatewayState.info.url);
  const icon = document.getElementById("gateway-url-copy-icon");
  if (icon) { icon.setAttribute("data-lucide", "check"); refreshIcons(); }
  setTimeout(() => { if (icon) { icon.setAttribute("data-lucide", "copy"); refreshIcons(); } }, 1500);
}

function onGatewayBindChange(value) {
  gatewayState.pendingBind = value;
  gatewayState.settingsDirty = _isGatewaySettingsDirty();
  renderGatewayPage();
}

function onGatewayControlUiChange(checked) {
  gatewayState.pendingControlUi = checked;
  gatewayState.settingsDirty = _isGatewaySettingsDirty();
  renderGatewayPage();
}

function _isGatewaySettingsDirty() {
  if (!gatewayState.info) return false;
  const bindChanged = gatewayState.pendingBind != null && gatewayState.pendingBind !== gatewayState.info.bind;
  const cuiChanged = gatewayState.pendingControlUi != null && gatewayState.pendingControlUi !== gatewayState.info.control_ui_enabled;
  return bindChanged || cuiChanged;
}

async function saveGatewaySettings() {
  if (!gatewayState.settingsDirty) return;
  const params = {};
  if (gatewayState.pendingBind != null) params.bind = gatewayState.pendingBind;
  if (gatewayState.pendingControlUi != null) params.control_ui_enabled = gatewayState.pendingControlUi;

  // 進入 loading 狀態
  const btn = document.querySelector("#gateway-info-panel button[onclick*='saveGateway']");
  if (btn) { btn.disabled = true; btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>Saving &amp; Restarting...</span>`; refreshIcons(); }

  try {
    const resp = await window.pywebview.api.save_gateway_settings(params);
    if (resp?.success) {
      const d = resp.data;
      gatewayState.pendingBind = null;
      gatewayState.pendingControlUi = null;
      gatewayState.settingsDirty = false;
      if (d.restarted) {
        showToast("Settings saved. Gateway restarted.", "success");
      } else {
        showToast("Settings saved but Gateway restart failed. Please restart manually.", "warning", 6000);
      }
      await loadGatewayData();
    } else {
      showToast(resp?.error?.message || "Failed to save gateway settings", "error");
    }
  } catch {
    showToast("Connection error while saving gateway settings", "error");
  }
}

function toggleAllowAllOrigins(checked) {
  gatewayState.allowAll = checked;
  renderGatewayPage();
}

function addOrigin() {
  const input = document.getElementById("gateway-new-origin");
  if (!input) return;
  const val = input.value.trim();
  if (!val || gatewayState.origins.includes(val)) { input.value = ""; return; }
  gatewayState.origins.push(val);
  renderGatewayPage();
}

function removeOrigin(index) {
  gatewayState.origins.splice(index, 1);
  renderGatewayPage();
}

async function saveOrigins() {
  try {
    const resp = await window.pywebview.api.save_allowed_origins({ allow_all: gatewayState.allowAll, origins: gatewayState.origins });
    if (!resp?.success) alert(resp?.error?.message || "Failed to save origins");
  } catch { alert("Connection error while saving origins"); }
}

/** 通用 Gateway 裝置操作 */
async function gatewayDeviceAction(apiMethod, params, errorLabel) {
  try {
    const resp = await apiMethod(params);
    if (resp?.success) await refreshDeviceList();
    else alert(resp?.error?.message || `Failed to ${errorLabel}`);
  } catch { alert(`Connection error during ${errorLabel}`); }
}

function approveDeviceFromGateway(requestId) { gatewayDeviceAction(window.pywebview.api.approve_device, { request_id: requestId }, "approve device"); }
function rejectDevice(requestId) { gatewayDeviceAction(window.pywebview.api.reject_device, { request_id: requestId }, "reject device"); }
function removeDevice(deviceId) { gatewayDeviceAction(window.pywebview.api.remove_device, { device_id: deviceId }, "remove device"); }

async function saveDeviceNote(deviceId, note) {
  try { await window.pywebview.api.save_device_note({ device_id: deviceId, note }); gatewayState.deviceNotes[deviceId] = note; }
  catch { /* 靜默儲存 */ }
}

async function refreshDeviceList() {
  try {
    const [devicesResp, notesResp] = await Promise.all([
      window.pywebview.api.list_devices(),
      window.pywebview.api.get_device_notes(),
    ]);
    if (devicesResp?.success) gatewayState.devices = { pending: devicesResp.data.pending || [], paired: devicesResp.data.paired || [] };
    if (notesResp?.success) gatewayState.deviceNotes = notesResp.data.notes || {};
  } catch { /* 保留現有資料 */ }
  renderGatewayPage();
}

registerPage("gateway", {
  onEnter: () => loadGatewayData(),
  onLeave: () => {},
});

/* =================================================================
 * 11. Bridge 整合與應用程式啟動
 * ================================================================= */

/** Bridge 連線狀態回呼 */
window.updateConnectionStatus = function (status) {
  updateConnectionStatus(status);
};

/** 應用程式初始化 */
async function initApp() {
  const loadingDot = document.getElementById("loading-dot");
  const loadingText = document.getElementById("loading-text");

  try {
    const result = await window.pywebview.api.ping();
    if (result?.success) {
      document.getElementById("app-loading").classList.add("hidden");
      document.getElementById("app-main").classList.remove("hidden");
      refreshIcons();

      try {
        const platform = await window.pywebview.api.detect_platform();
        if (platform?.data) updateSidebarMode(platform.data.current_mode || platform.data.suggested_mode || "docker-windows");
        else if (platform?.current_mode || platform?.suggested_mode) updateSidebarMode(platform.current_mode || platform.suggested_mode || "docker-windows");
      } catch { updateSidebarMode("docker-windows"); }

      navigateTo("dashboard");
    } else {
      throw new Error("Bridge returned unsuccessful response");
    }
  } catch {
    if (loadingDot) loadingDot.className = "w-2.5 h-2.5 rounded-full bg-status-error";
    if (loadingText) loadingText.textContent = "Bridge Unavailable";
  }
}

window.addEventListener("pywebviewready", initApp);
