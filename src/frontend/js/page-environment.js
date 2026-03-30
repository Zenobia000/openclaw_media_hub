/**
 * OpenClaw GUI — Environment Check Page
 *
 * 環境檢查頁面：軟體偵測、.env 驗證
 */

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
