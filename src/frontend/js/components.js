/**
 * OpenClaw GUI — UI Components
 *
 * 共用 UI 元件：按鈕、輸入框、狀態標籤、卡片、面板、步驟指示器、進度項目
 */

/* ---------- 按鈕 ---------- */

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

/* ---------- 輸入框 ---------- */

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

/* ---------- 狀態標籤 ---------- */

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

/* ---------- 統計卡片 ---------- */

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

/* ---------- 環境檢查卡片 ---------- */

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

/* ---------- 區段面板 ---------- */

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

/* ---------- 步驟指示器 ---------- */

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

/* ---------- 進度項目 ---------- */

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
