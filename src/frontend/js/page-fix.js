/**
 * OpenClaw GUI — Fix Plugins Page
 *
 * 外掛修復診斷頁面
 */

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
