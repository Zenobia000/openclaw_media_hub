/**
 * OpenClaw GUI — Frontend Application
 *
 * SPA Router, UI Components, Bridge Integration.
 */

/* ============================================================
 * 1. Global State
 * ============================================================ */

/** Current active view ID */
let currentView = null;

/** Page lifecycle hooks: { viewId: { onEnter, onLeave } } */
const pageHooks = {};

/** Current deployment mode (set after detect_platform) */
let currentMode = null;

/** Configuration wizard — Step 1 local state */
let configStep = 1;
let selectedMode = null;
let sshTestPassed = false;
let sshTestResult = null;
let sshAuthMethod = "key"; // "key" | "password"
/** Whether Config Step 1 has been rendered at least once (for page-switch preservation) */
let configRendered = false;
/** Cached form values for Config Step 1 (survives page navigation) */
let configFormValues = {};

/* ============================================================
 * 2. SPA Router
 * ============================================================ */

const VIEW_IDS = [
  "dashboard",
  "configuration",
  "environment",
  "deploy-skills",
  "install-plugins",
  "fix-plugins",
];

/**
 * Navigate to a view by ID.
 * Hides all views, shows target, updates sidebar active state,
 * and fires page lifecycle hooks.
 */
function navigateTo(viewId) {
  if (!VIEW_IDS.includes(viewId)) return;

  // Fire onLeave for current page
  if (currentView && pageHooks[currentView]?.onLeave) {
    pageHooks[currentView].onLeave();
  }

  // Hide all views
  for (const id of VIEW_IDS) {
    const el = document.getElementById(`view-${id}`);
    if (el) el.classList.add("hidden");
  }

  // Show target view
  const target = document.getElementById(`view-${viewId}`);
  if (target) target.classList.remove("hidden");

  // Update sidebar active state
  document.querySelectorAll(".nav-item").forEach((item) => {
    const isActive = item.dataset.view === viewId;
    item.classList.toggle("nav-item-active", isActive);
  });

  currentView = viewId;

  // Fire onEnter for new page
  if (pageHooks[viewId]?.onEnter) {
    pageHooks[viewId].onEnter();
  }
}

/**
 * Register lifecycle hooks for a view.
 */
function registerPage(viewId, hooks) {
  pageHooks[viewId] = hooks;
}

/* ============================================================
 * 3. Sidebar Helpers
 * ============================================================ */

const MODE_LABELS = {
  "docker-windows": "Docker \u00b7 Windows",
  "docker-linux": "Docker \u00b7 Linux/WSL2",
  "native-linux": "Native \u00b7 Linux (systemd)",
  "remote-ssh": "Remote \u00b7 SSH",
};

/**
 * Update sidebar footer mode text.
 */
function updateSidebarMode(mode) {
  currentMode = mode;
  window.__currentMode = mode;
  const el = document.getElementById("sidebar-mode");
  if (el) el.textContent = MODE_LABELS[mode] || mode || "Unknown";

  // Show/hide connection indicator
  const connEl = document.getElementById("sidebar-connection");
  if (connEl) {
    connEl.classList.toggle("hidden", mode !== "remote-ssh");
  }
}

/**
 * Update sidebar connection status indicator.
 */
function updateConnectionStatus(status) {
  const dot = document.getElementById("conn-dot");
  const text = document.getElementById("conn-text");
  if (!dot || !text) return;

  const config = {
    connected:    { color: "bg-status-success", label: "Connected", pulse: false },
    disconnected: { color: "bg-status-error",   label: "Disconnected", pulse: false },
    connecting:   { color: "bg-accent-secondary", label: "Connecting...", pulse: true },
    error:        { color: "bg-status-error",   label: "Connection Error", pulse: true },
  };

  const c = config[status] || config.disconnected;
  dot.className = `w-2 h-2 rounded-full ${c.color}${c.pulse ? " animate-pulse" : ""}`;
  text.textContent = c.label;
}

/**
 * Query bridge for latest connection status.
 */
async function refreshConnectionStatus() {
  try {
    const result = await window.pywebview.api.get_connection_status();
    if (result?.success) {
      updateConnectionStatus(result.data?.status || "disconnected");
    }
  } catch {
    // Bridge not ready or method not available yet
  }
}

/* ============================================================
 * 4. UI Component Render Functions
 * ============================================================ */

/* ---------- 4.1 Button ---------- */

/**
 * Render a button (Primary / Secondary / Danger).
 * @param {Object} opts
 * @param {"primary"|"secondary"|"danger"} opts.variant
 * @param {string} [opts.icon] - Lucide icon name
 * @param {string} opts.label
 * @param {boolean} [opts.disabled]
 * @param {boolean} [opts.loading]
 * @param {string} [opts.id]
 * @param {string} [opts.onclick] - inline onclick handler
 * @param {"sm"|"md"} [opts.size]
 * @returns {string} HTML
 */
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

/* ---------- 4.2 Input ---------- */

/**
 * Render a form input with label and optional icon.
 * @param {Object} opts
 * @param {string} opts.id
 * @param {string} [opts.label]
 * @param {string} [opts.icon] - Lucide icon name
 * @param {string} [opts.placeholder]
 * @param {"text"|"password"|"number"} [opts.type]
 * @param {string} [opts.value]
 * @param {string} [opts.error]
 * @param {boolean} [opts.required]
 * @returns {string} HTML
 */
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
      <input id="${id}" name="${id}" type="${type}" value="${escapeAttr(value)}" placeholder="${escapeAttr(placeholder)}"
        class="w-full bg-bg-input border ${errorBorder} rounded-sm text-sm text-text-primary placeholder:text-text-muted ${icon ? "pl-10" : "pl-3"} ${type === "password" ? "pr-10" : "pr-3"} py-2.5 outline-none transition-colors" />
      ${passwordToggle}
    </div>
    ${error ? `<span class="text-xs text-status-error">${error}</span>` : ""}
  </div>`;
}

/**
 * Toggle password visibility for an input.
 */
function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const isPassword = input.type === "password";
  input.type = isPassword ? "text" : "password";
  // Update icon in the toggle button
  const btn = input.parentElement.querySelector(".pwd-toggle i");
  if (btn) btn.setAttribute("data-lucide", isPassword ? "eye" : "eye-off");
  lucide.createIcons();
}

/* ---------- 4.3 StatusBadge ---------- */

/**
 * Render a status badge (dot + text).
 * @param {Object} opts
 * @param {"success"|"error"|"warning"|"info"} opts.status
 * @param {string} opts.text
 * @returns {string} HTML
 */
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
    ${escapeHtml(text)}
  </span>`;
}

/* ---------- 4.4 StatCard ---------- */

/**
 * Render a statistics card.
 * @param {Object} opts
 * @param {string} opts.icon - Lucide icon name
 * @param {string} [opts.iconColor] - Tailwind text color class
 * @param {string} opts.value
 * @param {string} opts.label
 * @param {"success"|"error"|"info"} [opts.status]
 * @returns {string} HTML
 */
function renderStatCard({ icon, iconColor = "text-accent-primary", value, label, status }) {
  const badge = status ? renderStatusBadge({ status, text: status }) : "";
  return `<div class="bg-bg-card border border-border-default rounded-md p-5 flex-1 min-w-0">
    <div class="flex items-center justify-between mb-3">
      <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center">
        <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
      </div>
      ${badge}
    </div>
    <div class="text-2xl font-bold">${escapeHtml(value)}</div>
    <div class="text-xs text-text-muted mt-1">${escapeHtml(label)}</div>
  </div>`;
}

/* ---------- 4.5 CheckCard ---------- */

/**
 * Render an environment check card.
 * @param {Object} opts
 * @param {string} opts.icon - Lucide icon name
 * @param {string} [opts.iconColor] - Tailwind text color class
 * @param {string} opts.name
 * @param {string} [opts.version]
 * @param {"installed"|"running"|"not-found"} opts.status
 * @returns {string} HTML
 */
function renderCheckCard({ icon, iconColor = "text-status-info", name, version, status }) {
  const isOk = status === "installed" || status === "running";
  const badgeStatus = isOk ? "success" : "error";
  const badgeText = isOk ? (version || "Installed") : "Not Found";
  return `<div class="bg-bg-card border border-border-default rounded-md p-4 flex items-center gap-3 min-w-[200px] flex-1">
    <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">${escapeHtml(name)}</div>
      ${version ? `<div class="text-xs text-text-muted mt-0.5">${escapeHtml(version)}</div>` : ""}
    </div>
    ${renderStatusBadge({ status: badgeStatus, text: badgeText })}
  </div>`;
}

/* ---------- 4.5.1 Environment Page Helpers ---------- */

const CHECK_ICONS = {
  "Docker":           { icon: "container",  color: "text-status-info" },
  "Docker Compose":   { icon: "layers",     color: "text-status-info" },
  "Docker Desktop":   { icon: "activity",   color: "text-status-success" },
  "Docker Running":   { icon: "activity",   color: "text-status-success" },
  "Node.js":          { icon: "hexagon",    color: "text-status-success" },
  "OpenClaw CLI":     { icon: "terminal",   color: "text-accent-primary" },
  "jq":               { icon: "braces",     color: "text-accent-secondary" },
  "VS Code":          { icon: "code",       color: "text-status-info" },
  "ngrok":            { icon: "globe",      color: "text-text-muted" },
  "systemd Service":  { icon: "server",     color: "text-accent-secondary" },
};

/**
 * Render the summary banner (green = all pass, red = failures).
 */
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
          <div class="text-xs text-text-secondary mt-0.5">${passed} of ${total} software checks passed · ${escapeHtml(envText)}</div>
        </div>
      </div>
      <span class="text-xs text-text-muted">${escapeHtml(lastChecked)}</span>
    </div>`;
  }

  const failCount = total - passed + (envFile.exists ? 0 : 1);
  return `<div class="flex items-center justify-between rounded-md p-4 border" style="background: #F4433615; border-color: #F4433640;">
    <div class="flex items-center gap-3">
      <i data-lucide="alert-circle" class="w-5 h-5 text-status-error flex-shrink-0"></i>
      <div>
        <div class="text-sm font-semibold text-status-error">${failCount} check${failCount > 1 ? "s" : ""} failed — action required</div>
        <div class="text-xs text-text-secondary mt-0.5">${passed} of ${total} passed · ${escapeHtml(envText)}</div>
      </div>
    </div>
    <span class="text-xs text-text-muted">${escapeHtml(lastChecked)}</span>
  </div>`;
}

/**
 * Render the checks grid using CHECK_ICONS mapping.
 */
function renderChecksGrid(checks) {
  const cards = checks.map(c => {
    const meta = CHECK_ICONS[c.name] || { icon: "help-circle", color: "text-text-muted" };
    return renderCheckCard({
      icon: meta.icon,
      iconColor: meta.color,
      name: c.name,
      version: c.version,
      status: c.installed ? "installed" : "not-found",
    });
  }).join("");
  return `<div class="flex flex-wrap gap-4">${cards}</div>`;
}

/**
 * Render the .env file check card.
 */
function renderEnvFileCard(envFile) {
  const status = envFile.exists ? "success" : "error";
  const badgeText = envFile.exists ? "Verified" : "Missing";
  return `<div class="bg-bg-card border border-border-default rounded-md p-4 flex items-center gap-3">
    <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="file-text" class="w-[18px] h-[18px] text-accent-secondary"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">.env Configuration File</div>
      <div class="text-xs text-text-muted mt-0.5">${escapeHtml(envFile.message)}</div>
    </div>
    ${renderStatusBadge({ status, text: badgeText })}
  </div>`;
}

/**
 * Render error guidance block (only when failures exist).
 */
function renderErrorGuidance(checks) {
  const failed = checks.filter(c => !c.installed);
  if (failed.length === 0) return "";

  const items = failed.map(c =>
    `<li class="text-sm text-text-secondary">
      <span class="font-medium text-text-primary">${escapeHtml(c.name)}</span> — ${escapeHtml(c.message)}
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

/* ---------- 4.6 SectionPanel ---------- */

/**
 * Render a section panel with icon, title, description, and children.
 * @param {Object} opts
 * @param {string} opts.icon - Lucide icon name
 * @param {string} [opts.iconColor] - Tailwind text color class
 * @param {string} opts.title
 * @param {string} [opts.description]
 * @param {string} [opts.children] - inner HTML
 * @param {string} [opts.id]
 * @returns {string} HTML
 */
function renderSectionPanel({ icon, iconColor = "text-accent-primary", title, description, children = "", id }) {
  const idAttr = id ? `id="${id}"` : "";
  return `<div ${idAttr} class="bg-bg-card border border-border-default rounded-md">
    <div class="px-5 pt-5 pb-4 flex items-start gap-3">
      <div class="w-9 h-9 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0 mt-0.5">
        <i data-lucide="${icon}" class="w-[18px] h-[18px] ${iconColor}"></i>
      </div>
      <div>
        <h3 class="text-base font-semibold">${escapeHtml(title)}</h3>
        ${description ? `<p class="text-[13px] text-text-secondary mt-0.5">${escapeHtml(description)}</p>` : ""}
      </div>
    </div>
    <div class="px-5 pb-5">${children}</div>
  </div>`;
}

/* ---------- 4.7 StepIndicator ---------- */

/**
 * Render a horizontal step indicator.
 * @param {Object} opts
 * @param {string[]} opts.steps - Step labels
 * @param {number} opts.currentStep - 1-based
 * @param {number[]} [opts.completedSteps] - 1-based indices of completed steps
 * @returns {string} HTML
 */
function renderStepIndicator({ steps, currentStep, completedSteps = [] }) {
  const items = steps.map((label, i) => {
    const num = i + 1;
    const isCompleted = completedSteps.includes(num);
    const isActive = num === currentStep;
    const isPending = !isCompleted && !isActive;

    let circle;
    if (isCompleted) {
      circle = `<div class="w-8 h-8 rounded-full bg-status-success flex items-center justify-center flex-shrink-0">
        <i data-lucide="check" class="w-4 h-4 text-white"></i>
      </div>`;
    } else if (isActive) {
      circle = `<div class="w-8 h-8 rounded-full bg-accent-primary flex items-center justify-center flex-shrink-0">
        <span class="text-sm font-bold text-white">${num}</span>
      </div>`;
    } else {
      circle = `<div class="w-8 h-8 rounded-full border-2 border-border-default flex items-center justify-center flex-shrink-0">
        <span class="text-sm font-medium text-text-muted">${num}</span>
      </div>`;
    }

    const labelCls = isActive ? "text-sm font-semibold text-text-primary" : isPending ? "text-sm text-text-muted" : "text-sm text-text-secondary";

    // Connector line (not before the first item)
    const line = i > 0
      ? `<div class="flex-1 h-0.5 ${completedSteps.includes(num) || isActive ? "bg-status-success" : "bg-border-default"}"></div>`
      : "";

    return `${line}<div class="flex items-center gap-2">${circle}<span class="${labelCls}">${escapeHtml(label)}</span></div>`;
  });

  return `<div class="flex items-center gap-3">${items.join("")}</div>`;
}

/* ---------- 4.8 ProgressItem ---------- */

/**
 * Render a progress item for initialization / deploy steps.
 * @param {Object} opts
 * @param {string} opts.name
 * @param {string} [opts.description]
 * @param {"done"|"running"|"pending"|"failed"} opts.status
 * @param {string} [opts.icon] - optional emoji or Lucide icon override
 * @returns {string} HTML
 */
function renderProgressItem({ name, description, status, icon }) {
  const statusConfig = {
    done:    { circleClass: "bg-status-success", icon: "check",  iconClass: "text-white", textClass: "text-status-success", label: "Done" },
    running: { circleClass: "bg-accent-primary", icon: "loader", iconClass: "text-white animate-spin", textClass: "text-accent-primary", label: "Running..." },
    pending: { circleClass: "border-2 border-border-default bg-transparent", icon: null, iconClass: "", textClass: "text-text-muted", label: "Pending" },
    failed:  { circleClass: "bg-status-error",   icon: "x",      iconClass: "text-white", textClass: "text-status-error", label: "Failed" },
  };

  const c = statusConfig[status] || statusConfig.pending;

  const circleContent = c.icon
    ? `<i data-lucide="${c.icon}" class="w-3.5 h-3.5 ${c.iconClass}"></i>`
    : "";

  const prefix = icon ? `<span class="text-base mr-2">${icon}</span>` : "";

  return `<div class="flex items-center gap-3 py-3 border-b border-border-default last:border-b-0">
    <div class="w-7 h-7 rounded-full ${c.circleClass} flex items-center justify-center flex-shrink-0">${circleContent}</div>
    ${prefix}
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium">${escapeHtml(name)}</div>
      ${description ? `<div class="text-xs text-text-secondary mt-0.5">${escapeHtml(description)}</div>` : ""}
    </div>
    <span class="text-xs font-medium ${c.textClass}">${c.label}</span>
  </div>`;
}

/* ============================================================
 * 5. Utility Functions
 * ============================================================ */

/** Escape HTML entities */
function escapeHtml(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Escape for HTML attribute values */
function escapeAttr(str) {
  if (str == null) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Insert HTML into a container and initialize Lucide icons.
 */
function renderInto(containerId, html) {
  const el = document.getElementById(containerId);
  if (el) {
    el.innerHTML = html;
    lucide.createIcons({ nameAttr: "data-lucide" });
  }
}

/* ============================================================
 * 5.1 Environment Page — Lifecycle Hook (US-001, 3.4.5–3.4.8)
 * ============================================================ */

registerPage("environment", {
  onEnter: async () => {
    // Show loading state
    renderInto("environment-content", `
      <div class="flex items-center gap-3 text-text-muted py-8">
        <i data-lucide="loader" class="w-5 h-5 animate-spin"></i>
        <span class="text-sm">Running environment checks...</span>
      </div>
    `);

    // Inject mode badge into header
    const badgeEl = document.getElementById("env-mode-badge");
    if (badgeEl && currentMode) {
      const modeLabel = MODE_LABELS[currentMode] || currentMode;
      badgeEl.innerHTML = renderStatusBadge({ status: "info", text: modeLabel });
      lucide.createIcons({ nameAttr: "data-lucide" });
    }

    try {
      const result = await window.pywebview.api.check_env();
      if (!result || !result.success) {
        const errMsg = result?.error?.message || "Unknown error";
        const errType = result?.error?.type || "INTERNAL";
        renderInto("environment-content", `
          <div class="rounded-md p-4 border border-status-error" style="background: #ef444410;">
            <div class="flex items-center gap-2">
              <i data-lucide="alert-triangle" class="w-5 h-5 text-status-error"></i>
              <span class="text-sm font-semibold text-status-error">${escapeHtml(errType)}</span>
            </div>
            <p class="text-sm text-text-secondary mt-2">${escapeHtml(errMsg)}</p>
            <div class="mt-3">
              ${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Retry", onclick: "navigateTo('environment')" })}
            </div>
          </div>
        `);
        return;
      }

      const { checks, env_file } = result.data;
      const lastChecked = "Last checked: just now";

      const html = [
        renderSummaryBanner(checks, env_file, lastChecked),
        renderChecksGrid(checks),
        renderEnvFileCard(env_file),
        renderErrorGuidance(checks),
      ].join("");

      renderInto("environment-content", html);
    } catch (err) {
      renderInto("environment-content", `
        <div class="rounded-md p-4 border border-status-error" style="background: #ef444410;">
          <div class="text-sm text-status-error font-medium">Failed to run environment check</div>
          <div class="text-xs text-text-muted mt-1">${escapeHtml(String(err))}</div>
          <div class="mt-3">
            ${renderButton({ variant: "secondary", icon: "refresh-cw", label: "Retry", onclick: "navigateTo('environment')" })}
          </div>
        </div>
      `);
    }
  },
});

/* ============================================================
 * 5.2 Configuration Step 1 — Lifecycle & Components (WBS 3.6 + 3.16.3)
 * ============================================================ */

/* ---------- 5.2.1 Mode Definitions ---------- */

const DEPLOY_MODES = [
  { id: "docker-windows", icon: "monitor",  iconColor: "text-accent-primary",  borderColor: "#ff5c5c", name: "Docker Windows",      description: "Run OpenClaw in Docker on Windows" },
  { id: "docker-linux",   icon: "terminal", iconColor: "text-accent-secondary", borderColor: "#14b8a6", name: "Docker Linux / WSL2",  description: "Run OpenClaw in Docker on Linux or WSL2" },
  { id: "native-linux",   icon: "server",   iconColor: "text-text-muted",       borderColor: "#838387", name: "Native Linux (systemd)", description: "Install directly on Linux with systemd" },
  { id: "remote-ssh",     icon: "cloud",    iconColor: "text-[#8b5cf6]",        borderColor: "#8b5cf6", name: "Remote Server (SSH)",  description: "Connect to a remote server via SSH" },
];

/** Default field values per deployment mode */
const MODE_DEFAULTS = {
  "docker-windows": {
    config_dir: "C:\\Users\\%USERNAME%\\.openclaw",
    workspace_dir: "C:\\Users\\%USERNAME%\\.openclaw\\workspace",
    gateway_bind: "lan",
    gateway_mode: "local",
    gateway_port: "18789",
    bridge_port: "18790",
    timezone: "Asia/Taipei",
    docker_image: "openclaw:local",
  },
  "docker-linux": {
    config_dir: "~/.openclaw",
    workspace_dir: "~/.openclaw/workspace",
    gateway_bind: "lan",
    gateway_mode: "local",
    gateway_port: "18789",
    bridge_port: "18790",
    timezone: "Asia/Taipei",
    docker_image: "openclaw:local",
  },
  "native-linux": {
    config_dir: "~/.openclaw",
    workspace_dir: "~/.openclaw/workspace",
    gateway_bind: "lan",
    gateway_mode: "local",
    gateway_port: "18789",
    bridge_port: "18790",
    timezone: "Asia/Taipei",
    docker_image: "",
  },
  "remote-ssh": {
    config_dir: "~/.openclaw",
    workspace_dir: "~/.openclaw/workspace",
    gateway_bind: "lan",
    gateway_mode: "local",
    gateway_port: "18789",
    bridge_port: "18790",
    timezone: "Asia/Taipei",
    docker_image: "openclaw:local",
  },
};

/** Field ID → config key mapping */
const CONFIG_FIELD_MAP = {
  "input-config-dir": "config_dir",
  "input-workspace-dir": "workspace_dir",
  "input-gateway-bind": "gateway_bind",
  "input-gateway-mode": "gateway_mode",
  "input-gateway-port": "gateway_port",
  "input-bridge-port": "bridge_port",
  "input-timezone": "timezone",
  "input-docker-image": "docker_image",
};

/**
 * Snapshot all Config Step 1 form values into configFormValues.
 */
function saveConfigFormState() {
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (el) configFormValues[key] = el.value;
  }
  const sandbox = document.getElementById("toggle-sandbox");
  if (sandbox) configFormValues.sandbox = sandbox.checked;
  // SSH fields
  for (const id of ["input-ssh-host", "input-ssh-port", "input-ssh-username", "input-ssh-key-file", "input-ssh-password"]) {
    const el = document.getElementById(id);
    if (el) configFormValues[id] = el.value;
  }
}

/**
 * Restore saved form values into DOM inputs.
 */
function restoreConfigFormState() {
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (el && configFormValues[key] !== undefined) el.value = configFormValues[key];
  }
  const sandbox = document.getElementById("toggle-sandbox");
  if (sandbox && configFormValues.sandbox !== undefined) sandbox.checked = configFormValues.sandbox;
  for (const id of ["input-ssh-host", "input-ssh-port", "input-ssh-username", "input-ssh-key-file", "input-ssh-password"]) {
    const el = document.getElementById(id);
    if (el && configFormValues[id] !== undefined) el.value = configFormValues[id];
  }
}

/**
 * Apply mode defaults to form fields (only fills empty fields or replaces previous defaults).
 */
function applyModeDefaults(mode) {
  const defaults = MODE_DEFAULTS[mode];
  if (!defaults) return;
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const el = document.getElementById(inputId);
    if (!el) continue;
    // Fill if empty, or if value matches any mode's default (user hasn't customized)
    const current = el.value.trim();
    const isDefault = !current || Object.values(MODE_DEFAULTS).some(d => d[key] === current);
    if (isDefault) el.value = defaults[key];
  }
}

/* ---------- 5.2.2 Render: Radio Card ---------- */

/**
 * Render a deployment mode radio card.
 * @param {Object} mode - Mode definition from DEPLOY_MODES
 * @param {boolean} selected - Whether this card is currently selected
 * @returns {string} HTML
 */
function renderRadioCard(mode, selected) {
  const borderStyle = selected
    ? `border-color: ${mode.borderColor}; border-width: 2px; padding: 15px;`
    : "";
  const selectedCls = selected ? "radio-card-selected" : "";
  const indicator = selected
    ? `<div class="w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0" style="background: ${mode.borderColor};">
        <i data-lucide="check" class="w-3 h-3 text-white"></i>
      </div>`
    : `<div class="w-5 h-5 rounded-full border-2 border-border-default flex-shrink-0"></div>`;

  return `<div class="radio-card ${selectedCls}" style="${borderStyle}" data-mode="${mode.id}" onclick="selectDeploymentMode('${mode.id}')">
    ${indicator}
    <div class="w-8 h-8 rounded-sm bg-bg-input flex items-center justify-center flex-shrink-0">
      <i data-lucide="${mode.icon}" class="w-4 h-4 ${mode.iconColor}"></i>
    </div>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-semibold">${escapeHtml(mode.name)}</div>
      <div class="text-xs text-text-muted mt-0.5">${escapeHtml(mode.description)}</div>
    </div>
  </div>`;
}

/* ---------- 5.2.3 Render: Deployment Mode Section ---------- */

function renderDeploymentModeSection() {
  const cards = DEPLOY_MODES.map(m => renderRadioCard(m, m.id === selectedMode)).join("");
  return renderSectionPanel({
    icon: "monitor",
    iconColor: "text-accent-primary",
    title: "Deployment Mode",
    children: `<div class="grid grid-cols-2 gap-3">${cards}</div>`,
  });
}

/* ---------- 5.2.4 Render: SSH Connection Section ---------- */

function renderSSHSection() {
  const keyRowHidden = sshAuthMethod === "password" ? "hidden" : "";
  const pwdRowHidden = sshAuthMethod === "key" ? "hidden" : "";
  const toggleText = sshAuthMethod === "key" ? "Use password instead" : "Use SSH key instead";

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

  return `<div id="ssh-section">${renderSectionPanel({
    icon: "terminal",
    iconColor: "text-[#8b5cf6]",
    title: "SSH Connection",
    description: "Connect to your remote server via SSH",
    children: formGrid,
  })}</div>`;
}

/* ---------- 5.2.5 Render: Gateway & Directory Section ---------- */

function renderGatewaySection() {
  const d = MODE_DEFAULTS[selectedMode] || MODE_DEFAULTS["docker-windows"];
  const mainGrid = `
    <div class="grid grid-cols-2 gap-4">
      ${renderInput({ id: "input-config-dir", label: "Config Directory", icon: "folder", placeholder: "~/.openclaw", value: d.config_dir })}
      ${renderInput({ id: "input-workspace-dir", label: "Workspace Directory", icon: "folder", placeholder: "~/.openclaw/workspace", value: d.workspace_dir })}
      ${renderInput({ id: "input-gateway-bind", label: "Gateway Bind Host", placeholder: "lan", value: d.gateway_bind })}
      ${renderInput({ id: "input-gateway-mode", label: "Gateway Mode", placeholder: "local", value: d.gateway_mode })}
      ${renderInput({ id: "input-gateway-port", label: "Gateway Port", type: "number", placeholder: "18789", value: d.gateway_port })}
      ${renderInput({ id: "input-bridge-port", label: "Bridge Port", type: "number", placeholder: "18790", value: d.bridge_port })}
    </div>`;

  const advancedContent = `
    <div id="advanced-settings" class="collapsible-content mt-4">
      <div class="grid grid-cols-2 gap-4">
        ${renderInput({ id: "input-timezone", label: "Timezone", placeholder: "Asia/Taipei", value: d.timezone })}
        ${renderInput({ id: "input-docker-image", label: "Docker Image", placeholder: "openclaw:local", value: d.docker_image })}
      </div>
      <div class="flex items-center gap-2 mt-4">
        <input type="checkbox" id="toggle-sandbox" class="checkbox-custom" checked />
        <label for="toggle-sandbox" class="text-sm text-text-secondary cursor-pointer">Enable Sandbox</label>
      </div>
    </div>`;

  const advancedToggle = `
    <button type="button" class="flex items-center gap-1.5 mt-4 text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0" onclick="toggleAdvancedSettings()">
      <i data-lucide="chevron-right" class="w-3.5 h-3.5 collapsible-chevron" id="advanced-chevron"></i>
      <span>Advanced Settings</span>
    </button>`;

  return renderSectionPanel({
    icon: "globe",
    iconColor: "text-accent-secondary",
    title: "Gateway & Directory",
    children: mainGrid + advancedToggle + advancedContent,
  });
}

/* ---------- 5.2.6 Render: Action Bar ---------- */

function renderConfigActionBar() {
  const nextDisabled = selectedMode === "remote-ssh" && !sshTestPassed;
  const html = `<div class="flex items-center justify-end gap-3">
    <span class="text-sm text-text-muted font-medium">Step ${configStep} of 3</span>
    ${renderButton({ variant: "primary", icon: "arrow-right", label: "Next", id: "btn-next-step", disabled: nextDisabled, onclick: "configNextStep()" })}
  </div>`;
  renderInto("config-action-bar", html);
}

/* ---------- 5.2.7 Render: Step 1 Composition ---------- */

function renderConfigStep1() {
  const stepIndicator = renderStepIndicator({
    steps: ["Environment", "API Keys", "Initialize"],
    currentStep: configStep,
    completedSteps: [],
  });

  const sshSection = selectedMode === "remote-ssh" ? renderSSHSection() : `<div id="ssh-section" class="hidden"></div>`;

  const html = [
    stepIndicator,
    renderDeploymentModeSection(),
    sshSection,
    renderGatewaySection(),
  ].join("");

  renderInto("config-content", html);
  renderConfigActionBar();
}

/* ---------- 5.2.8 Event Handlers ---------- */

/**
 * Handle deployment mode radio card selection.
 * Uses DOM-only updates to preserve form values.
 */
function selectDeploymentMode(mode) {
  if (mode === selectedMode) return;
  selectedMode = mode;
  sshTestPassed = false;
  sshTestResult = null;

  // Persist mode (fire-and-forget)
  window.pywebview.api.save_config({ deployment_mode: mode }).catch(() => {});

  // Update sidebar
  updateSidebarMode(mode);

  // Update radio card visuals
  document.querySelectorAll(".radio-card").forEach((card) => {
    const cardMode = card.dataset.mode;
    const def = DEPLOY_MODES.find((m) => m.id === cardMode);
    if (!def) return;

    const isSelected = cardMode === mode;
    card.classList.toggle("radio-card-selected", isSelected);
    card.style.borderColor = isSelected ? def.borderColor : "";
    card.style.borderWidth = isSelected ? "2px" : "";
    card.style.padding = isSelected ? "15px" : "";

    // Update indicator
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
  lucide.createIcons({ nameAttr: "data-lucide" });

  // Toggle SSH section
  let sshEl = document.getElementById("ssh-section");
  if (sshEl) {
    if (mode === "remote-ssh") {
      if (!sshEl.innerHTML.trim()) {
        // Replace empty placeholder with full SSH section
        sshEl.outerHTML = renderSSHSection();
        lucide.createIcons({ nameAttr: "data-lucide" });
      } else {
        sshEl.classList.remove("hidden");
      }
    } else {
      sshEl.classList.add("hidden");
    }
  }

  // Apply mode-specific defaults to gateway/directory fields
  applyModeDefaults(mode);

  // Update action bar
  renderConfigActionBar();
}

/**
 * Open native file picker for SSH key.
 */
async function browseSSHKey() {
  try {
    const result = await window.pywebview.api.browse_file(
      "Select SSH Key",
      ["Key Files (*.pem;*.key;*.ppk;*.pub)", "All Files (*.*)"]
    );
    if (result?.success && result.data?.path) {
      const input = document.getElementById("input-ssh-key-file");
      if (input) input.value = result.data.path;
    }
  } catch {
    // Dialog cancelled or error — no action needed
  }
}

/**
 * Toggle between SSH key and password authentication.
 */
function toggleSSHAuthMethod() {
  sshAuthMethod = sshAuthMethod === "key" ? "password" : "key";
  const keyRow = document.getElementById("ssh-key-row");
  const pwdRow = document.getElementById("ssh-password-row");
  if (keyRow) keyRow.classList.toggle("hidden", sshAuthMethod === "password");
  if (pwdRow) pwdRow.classList.toggle("hidden", sshAuthMethod === "key");

  // Update toggle link text
  const toggleBtn = document.getElementById("btn-toggle-ssh-auth");
  if (toggleBtn) {
    toggleBtn.textContent = sshAuthMethod === "key" ? "Use password instead" : "Use SSH key instead";
  }
}

/**
 * Toggle advanced settings collapsible.
 */
function toggleAdvancedSettings() {
  const content = document.getElementById("advanced-settings");
  const chevron = document.getElementById("advanced-chevron");
  if (content) content.classList.toggle("expanded");
  if (chevron) chevron.classList.toggle("rotated");
}

/**
 * Test SSH connection — calls Bridge API and updates inline badge.
 */
async function testSSHConnection() {
  const host = document.getElementById("input-ssh-host")?.value?.trim();
  const port = parseInt(document.getElementById("input-ssh-port")?.value, 10) || 22;
  const username = document.getElementById("input-ssh-username")?.value?.trim();

  // Validate required fields
  if (!host || !username) {
    const badge = document.getElementById("ssh-test-badge");
    if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: "Host and Username are required" });
    lucide.createIcons({ nameAttr: "data-lucide" });
    return;
  }

  // Build params based on auth method
  const params = { host, port, username };
  if (sshAuthMethod === "key") {
    const keyFile = document.getElementById("input-ssh-key-file")?.value?.trim();
    if (keyFile) params.key_path = keyFile;
  } else {
    const password = document.getElementById("input-ssh-password")?.value;
    if (password) params.password = password;
  }

  // Show connecting badge
  const badge = document.getElementById("ssh-test-badge");
  if (badge) {
    badge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#14b8a618] text-accent-secondary text-xs font-medium">
      <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i>
      Connecting...
    </span>`;
    lucide.createIcons({ nameAttr: "data-lucide" });
  }

  // Disable test button during request
  const btn = document.getElementById("btn-test-ssh");
  if (btn) { btn.disabled = true; btn.classList.add("opacity-50", "pointer-events-none"); }

  try {
    const result = await window.pywebview.api.test_connection(params);
    if (result?.success) {
      const info = result.data?.server_info || {};
      const infoText = `Connected — ${info.os || "?"}, ${info.cpu_cores || "?"} cores, ${info.memory_gb || "?"}GB`;
      sshTestPassed = true;
      sshTestResult = info;
      if (badge) badge.innerHTML = renderStatusBadge({ status: "success", text: infoText });
    } else {
      sshTestPassed = false;
      sshTestResult = null;
      const errMsg = result?.error?.message || "Connection failed";
      if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: errMsg });
    }
  } catch (err) {
    sshTestPassed = false;
    sshTestResult = null;
    if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: String(err) });
  } finally {
    if (btn) { btn.disabled = false; btn.classList.remove("opacity-50", "pointer-events-none"); }
    lucide.createIcons({ nameAttr: "data-lucide" });
    renderConfigActionBar();
  }
}

/**
 * Handle Next button — validate, persist, navigate to Step 2.
 */
async function configNextStep() {
  // Validate SSH mode requirements
  if (selectedMode === "remote-ssh") {
    if (!sshTestPassed) return;

    const host = document.getElementById("input-ssh-host")?.value?.trim();
    const port = parseInt(document.getElementById("input-ssh-port")?.value, 10) || 22;
    const username = document.getElementById("input-ssh-username")?.value?.trim();
    const params = { host, port, username };

    if (sshAuthMethod === "key") {
      const keyFile = document.getElementById("input-ssh-key-file")?.value?.trim();
      if (keyFile) params.key_path = keyFile;
    } else {
      const password = document.getElementById("input-ssh-password")?.value;
      if (password) params.password = password;
    }

    // Establish persistent connection
    try {
      updateConnectionStatus("connecting");
      const connResult = await window.pywebview.api.connect_remote(params);
      if (!connResult?.success) {
        const badge = document.getElementById("ssh-test-badge");
        if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: connResult?.error?.message || "Connection failed" });
        lucide.createIcons({ nameAttr: "data-lucide" });
        updateConnectionStatus("error");
        return;
      }
    } catch (err) {
      updateConnectionStatus("error");
      return;
    }
  }

  // Collect gateway/directory config
  const config = { deployment_mode: selectedMode };
  for (const [inputId, key] of Object.entries(CONFIG_FIELD_MAP)) {
    const val = document.getElementById(inputId)?.value?.trim();
    if (val) config[key] = val;
  }
  config.sandbox = document.getElementById("toggle-sandbox")?.checked ?? true;

  // Persist config
  try {
    await window.pywebview.api.save_config(config);
  } catch {
    // Config save failed — continue anyway, not critical
  }

  // Navigate to Step 2 (placeholder — WBS 3.7 will implement Step 2 page)
  configStep = 2;
  // TODO: renderConfigStep2() — to be implemented in WBS 3.7
}

/* ---------- 5.2.9 Page Lifecycle Registration ---------- */

registerPage("configuration", {
  onEnter: async () => {
    if (configRendered) {
      // Page revisited — restore cached form values without re-rendering
      restoreConfigFormState();
      return;
    }
    // First visit — load persisted settings and render
    try {
      const platform = await window.pywebview.api.detect_platform();
      selectedMode = platform?.data?.current_mode || platform?.data?.suggested_mode || "docker-windows";
    } catch {
      selectedMode = "docker-windows";
    }
    sshTestPassed = false;
    sshTestResult = null;
    configStep = 1;
    renderConfigStep1();
    configRendered = true;
  },
  onLeave: () => {
    saveConfigFormState();
  },
});

/* ============================================================
 * 6. Bridge Integration & App Bootstrap
 * ============================================================ */

/**
 * Bridge callback: update connection status from Python side.
 */
window.updateConnectionStatus = function (status) {
  updateConnectionStatus(status);
};

/**
 * Check bridge connectivity, then show main app.
 */
async function initApp() {
  const loadingDot = document.getElementById("loading-dot");
  const loadingText = document.getElementById("loading-text");

  try {
    const result = await window.pywebview.api.ping();

    if (result && result.success) {
      // Bridge connected — show main app
      document.getElementById("app-loading").classList.add("hidden");
      document.getElementById("app-main").classList.remove("hidden");

      // Initialize Lucide icons in the sidebar
      lucide.createIcons({ nameAttr: "data-lucide" });

      // Detect platform and update sidebar
      try {
        const platform = await window.pywebview.api.detect_platform();
        if (platform?.data) {
          updateSidebarMode(platform.data.current_mode || platform.data.suggested_mode || "docker-windows");
        } else if (platform?.current_mode || platform?.suggested_mode) {
          updateSidebarMode(platform.current_mode || platform.suggested_mode || "docker-windows");
        }
      } catch {
        updateSidebarMode("docker-windows");
      }

      // Navigate to default page
      navigateTo("dashboard");
    } else {
      throw new Error("Bridge returned unsuccessful response");
    }
  } catch {
    if (loadingDot) loadingDot.className = "w-2.5 h-2.5 rounded-full bg-status-error";
    if (loadingText) loadingText.textContent = "Bridge Unavailable";
  }
}

// Wait for PyWebView ready event
window.addEventListener("pywebviewready", initApp);
