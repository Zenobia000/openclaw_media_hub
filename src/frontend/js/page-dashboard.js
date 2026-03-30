/**
 * OpenClaw GUI — Dashboard Page
 *
 * 儀表板頁面：系統狀態、服務控制、快速操作
 */

const dashboardState = { pollTimer: null, actionPending: false };

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
      ? renderStatusBadge({ status: "success", text: t("status.running") })
      : renderStatusBadge({ status: "error", text: t("status.stopped") });
    refreshIcons();
  }

  // 統計卡片列
  const statsRow = `<div class="flex gap-3">
    ${renderStatCard({ icon: "server", value: `${runningCount}/${services.length}`, label: t("dashboard.services_running"), status: running ? "success" : "error" })}
    ${renderStatCard({ icon: "clock", iconColor: "text-accent-secondary", value: uptime, label: t("dashboard.uptime"), status: "info" })}
    ${renderStatCard({ icon: "zap", iconColor: "text-status-info", value: String(skillsCount), label: t("dashboard.skills_deployed"), status: "info" })}
    ${renderStatCard({ icon: "puzzle", iconColor: "text-accent-secondary", value: String(pluginsCount), label: t("dashboard.plugins_installed"), status: "info" })}
  </div>`;

  // 服務清單
  const serviceListHtml = services.map(svc => {
    const svcStatus = svc.status === "running" ? "success" : "error";
    const svcLabel = svc.status === "running" ? t("status.running") : t("status.stopped");
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
      ${renderButton({ variant: "secondary", icon: "loader", label: t("common.processing"), disabled: true, loading: true })}
    </div>`;
  } else if (running) {
    btnHtml = `<div class="flex gap-3 mt-4">
      ${renderButton({ variant: "secondary", icon: "refresh-cw", label: t("dashboard.restart_services"), onclick: "handleServiceAction('restart')" })}
      ${renderButton({ variant: "danger", icon: "square", label: t("dashboard.stop_services"), onclick: "handleServiceAction('stop')" })}
    </div>`;
  } else {
    btnHtml = `<div class="flex gap-3 mt-4">
      ${renderButton({ variant: "primary", icon: "play", label: t("dashboard.start_services"), onclick: "handleServiceAction('start')" })}
    </div>`;
  }

  // 服務控制面板
  const serviceControlPanel = renderSectionPanel({
    icon: "activity", iconColor: "text-accent-primary",
    title: t("dashboard.service_control"), description: t("dashboard.service_control_desc"),
    children: serviceListHtml + btnHtml, id: "dashboard-svc-panel",
  });

  // 快速操作
  const actionCards = [
    { icon: "monitor", iconColor: "text-status-info", title: t("dashboard.action_check_env"), desc: t("dashboard.action_check_env_desc"), view: "environment" },
    { icon: "zap", iconColor: "text-accent-primary", title: t("dashboard.action_deploy_skills"), desc: t("dashboard.action_deploy_skills_desc"), view: "deploy-skills" },
    { icon: "puzzle", iconColor: "text-accent-secondary", title: t("dashboard.action_install_plugins"), desc: t("dashboard.action_install_plugins_desc"), view: "install-plugins" },
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
    title: t("dashboard.quick_actions"), description: t("dashboard.quick_actions_desc"),
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
      btnContainer.innerHTML = renderButton({ variant: "secondary", icon: "loader", label: t("common.processing"), disabled: true, loading: true });
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
    renderInto("dashboard-content", renderLoading(t("loading.dashboard")));
    try {
      const resp = await window.pywebview.api.get_service_status();
      renderDashboardPage(resp?.success ? resp.data : {});
    } catch { renderDashboardPage({}); }
    startDashboardPolling();
  },
  onLeave: () => stopDashboardPolling(),
});
