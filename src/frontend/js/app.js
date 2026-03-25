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
