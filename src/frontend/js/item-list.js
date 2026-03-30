/**
 * OpenClaw GUI — Item List Page Factory
 *
 * 勾選清單頁面工廠（VS Code Extensions 風格）
 * Skills 與 Plugins 共用
 */

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

/* =================================================================
 * Item List Page Factory
 * ================================================================= */

function createItemListPage(cfg) {
  const ps = { data: [], tab: "", busyId: null, busyAction: null, confirmingId: null, rendered: false };

  const getId = (item) => item[cfg.idField];

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

    const listHtml = renderSectionPanel({
      icon: cfg.icon,
      iconColor: cfg.iconColor,
      title: cfg.panelTitle,
      description: cfg.panelDescription,
      id: cfg.panelId,
      flexFill: true,
      children: renderTabs() + renderList(),
    });

    renderInto(cfg.contentId, `<div class="flex-shrink-0">${bannerHtml}</div>` + listHtml);
  }

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

  function renderList() {
    const tabDef = cfg.tabs.find(t => t.key === ps.tab);
    const filtered = tabDef ? ps.data.filter(tabDef.filterFn) : [];

    if (filtered.length === 0) {
      return `<div class="py-8 text-center text-sm text-text-muted">No items found in this category.</div>`;
    }

    const rowsHtml = filtered.map(item => renderRow(item)).join("");
    return `<div class="flex-1 min-h-0 overflow-y-auto">${rowsHtml}</div>`;
  }

  function renderRow(item) {
    const itemId = getId(item);
    const isInstalled = item[cfg.installedField];
    const isBusy = ps.busyId === itemId;
    const isConfirming = ps.confirmingId === itemId;
    const otherBusy = ps.busyId !== null && ps.busyId !== itemId;

    const iconHtml = cfg.renderRowIcon(item);
    const displayName = cfg.getDisplayName(item);
    const rawDesc = cfg.getDescription(item);
    const desc = rawDesc && rawDesc.length > 80 ? rawDesc.slice(0, 80) + "..." : (rawDesc || "");

    let actionHtml = "";
    if (isBusy) {
      const actionLabel = ps.busyAction === "install" ? cfg.busyInstallLabel : cfg.busyRemoveLabel;
      actionHtml = `<div class="flex items-center gap-2 flex-shrink-0">
        <i data-lucide="loader" class="w-4 h-4 animate-spin text-accent-primary"></i>
        <span class="text-xs text-text-secondary">${actionLabel}</span>
      </div>`;
    } else if (isConfirming) {
      actionHtml = `<div class="flex items-center gap-2 flex-shrink-0">
        <span class="text-xs text-text-secondary">${esc(cfg.confirmRemoveMessage(displayName))}</span>
        ${renderButton({ variant: "danger", label: "Confirm", onclick: `${cfg.removeFn}('${esc(itemId)}')`, size: "sm" })}
        ${renderButton({ variant: "secondary", label: "Cancel", onclick: `${cfg.cancelRemoveFn}()`, size: "sm" })}
      </div>`;
    } else if (isInstalled) {
      const badge = `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-sm text-xs font-medium bg-[#4CAF5015] text-status-success border border-[#4CAF5040]">${cfg.activeLabel}</span>`;
      const extraActions = cfg.renderExtraActions ? cfg.renderExtraActions(item) : "";
      const removeBtn = `<button onclick="event.stopPropagation(); ${cfg.confirmRemoveFn}('${esc(itemId)}')"
        class="inline-flex items-center justify-center w-7 h-7 rounded text-text-muted hover:text-status-error hover:bg-[#ef444418] transition-colors${otherBusy ? " opacity-40 pointer-events-none" : ""}"
        ${otherBusy ? "disabled" : ""}
        title="${esc(cfg.confirmRemoveMessage(displayName))}">
        <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
      </button>`;
      actionHtml = `<div class="flex items-center gap-2 flex-shrink-0">${badge}${extraActions}${removeBtn}</div>`;
    } else {
      actionHtml = `<div class="flex-shrink-0">
        ${renderButton({ variant: "primary", icon: cfg.installIcon, label: cfg.installLabel, onclick: `${cfg.installFn}('${esc(itemId)}')`, size: "sm", disabled: otherBusy })}
      </div>`;
    }

    return `<div class="flex items-center gap-3 px-4 py-3.5 border-b border-border-default last:border-b-0 hover:bg-bg-input transition-colors">
      ${iconHtml}
      <div class="flex-1 min-w-0">
        <div class="text-sm font-semibold text-text-primary">${esc(displayName)}</div>
        <div class="text-xs text-text-secondary mt-0.5 truncate">${esc(desc)}</div>
      </div>
      ${actionHtml}
    </div>`;
  }

  function getListScrollState() {
    const panel = document.getElementById(cfg.panelId);
    if (!panel) return null;
    const scrollable = panel.querySelector(".overflow-y-auto");
    return scrollable ? { el: scrollable, top: scrollable.scrollTop } : null;
  }

  function rerender() {
    const scroll = getListScrollState();
    updatePanelContent(cfg.panelId, renderTabs() + renderList());
    if (scroll) {
      const el = document.getElementById(cfg.panelId)?.querySelector(".overflow-y-auto");
      if (el) el.scrollTop = scroll.top;
    }
    refreshIcons();
  }

  function switchTab(tab) {
    ps.tab = tab;
    ps.confirmingId = null;
    rerender();
  }

  async function handleInstall(id) {
    if (ps.busyId) return;
    ps.busyId = id;
    ps.busyAction = "install";
    ps.confirmingId = null;
    rerender();

    try { await window.pywebview.api[cfg.installApi]([id]); } catch { /* 個別狀態由回呼處理 */ }

    const item = ps.data.find(d => getId(d) === id);
    ps.busyId = null;
    ps.busyAction = null;
    await reload();

    if (cfg.onInstalled) cfg.onInstalled(id, item);
  }

  function confirmUninstall(id) {
    if (ps.busyId) return;
    ps.confirmingId = id;
    rerender();
  }

  function cancelUninstall() {
    ps.confirmingId = null;
    rerender();
  }

  async function handleUninstall(id) {
    if (ps.busyId) return;
    ps.confirmingId = null;
    ps.busyId = id;
    ps.busyAction = "uninstall";
    rerender();

    try { await window.pywebview.api[cfg.uninstallApi]([id]); } catch { /* 個別狀態由回呼處理 */ }

    ps.busyId = null;
    ps.busyAction = null;
    await reload();
  }

  async function reload() {
    const scroll = getListScrollState();
    ps.busyId = null;
    ps.busyAction = null;
    ps.confirmingId = null;
    try {
      const result = await window.pywebview.api[cfg.listApi]();
      if (result?.success && result.data) {
        ps.data = result.data;
      }
    } catch { /* 保留現有資料 */ }
    renderPage();
    if (scroll) {
      const el = document.getElementById(cfg.panelId)?.querySelector(".overflow-y-auto");
      if (el) el.scrollTop = scroll.top;
    }
  }

  window[cfg.progressCallback] = function (id, status, message) {
    if (ps.busyId === id) {
      ps.busyAction = status === "running"
        ? (message?.toLowerCase().includes(cfg.removeKeyword) ? "uninstall" : "install")
        : ps.busyAction;
      rerender();
    }
  };

  registerPage(cfg.pageId, {
    onEnter: async () => {
      if (ps.rendered && !ps.busyId) { await reload(); return; }

      if (!ps.rendered) renderInto(cfg.contentId, renderLoading(`Loading ${cfg.entityNamePlural}...`));

      try {
        const result = await window.pywebview.api[cfg.listApi]();
        if (result?.success && result.data) {
          ps.data = result.data;
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
    onLeave: () => { ps.busyId = null; ps.busyAction = null; ps.confirmingId = null; },
  });

  return { switchTab, handleInstall, confirmUninstall, cancelUninstall, handleUninstall, reload, state: ps };
}

/* ---------- 技能部署頁面實例 ---------- */

const skillsPage = createItemListPage({
  pageId: "deploy-skills", contentId: "deploy-skills-content", badgeId: "deploy-skills-badge",
  panelId: "skills-checklist-panel",
  entityName: "skill", entityNamePlural: "skills", activeCountLabel: "deployed",
  icon: "zap", iconColor: "text-accent-primary",
  panelTitle: "Available Skills",
  panelDescription: "Scanned from module_pack/ (custom modules) and openclaw/skills/ (community skills)",
  listApi: "list_skills", installApi: "deploy_skills", uninstallApi: "remove_skills",
  progressCallback: "updateDeployProgress",
  tabs: [
    { key: "custom", label: "Custom Modules", filterFn: s => s.source === "module_pack" },
    { key: "community", label: "Community Skills", filterFn: s => s.source === "community" },
  ],
  idField: "name", installedField: "installed",
  tabAccentColor: "accent-primary",
  activeSubtitle: "Click Deploy or Remove on each skill to manage",
  emptySubtitle: "Click Deploy on a skill to get started",
  activeLabel: "Deployed",
  installLabel: "Deploy", installIcon: "upload",
  busyInstallLabel: "Deploying...", busyRemoveLabel: "Removing...",
  confirmRemoveMessage: name => `Remove ${name}?`,
  removeKeyword: "remov",
  installFn: "deploySkill", confirmRemoveFn: "confirmRemoveSkill",
  cancelRemoveFn: "cancelRemoveSkill", removeFn: "removeSkill",
  switchTabFn: "switchSkillsTab", reloadFn: "reloadSkillsPage",
  renderRowIcon: s => `<span class="text-base flex-shrink-0">${s.emoji}</span>`,
  getDisplayName: s => s.name,
  getDescription: s => s.description,
  defaultTab: data => data.some(s => s.source === "module_pack") ? "custom" : "community",
});

window.switchSkillsTab = skillsPage.switchTab;
window.deploySkill = skillsPage.handleInstall;
window.confirmRemoveSkill = skillsPage.confirmUninstall;
window.cancelRemoveSkill = skillsPage.cancelUninstall;
window.removeSkill = skillsPage.handleUninstall;
window.reloadSkillsPage = skillsPage.reload;

/* ---------- 外掛安裝頁面實例 ---------- */

const pluginsPage = createItemListPage({
  pageId: "install-plugins", contentId: "install-plugins-content", badgeId: "install-plugins-badge",
  panelId: "plugins-checklist-panel",
  entityName: "plugin", entityNamePlural: "plugins", activeCountLabel: "installed",
  icon: "puzzle", iconColor: "text-accent-secondary",
  panelTitle: "Available Plugins",
  panelDescription: "Extensions from openclaw/extensions/ — install by modifying openclaw.json plugins config",
  listApi: "list_plugins", installApi: "install_plugins", uninstallApi: "uninstall_plugins",
  progressCallback: "updatePluginProgress",
  tabs: PLUGIN_CATEGORIES.map(c => ({
    key: c.key, label: c.label, filterFn: p => p.category === c.key,
  })),
  idField: "id", installedField: "installed",
  tabAccentColor: "accent-secondary",
  activeSubtitle: "Click Install or Uninstall on each plugin to manage",
  emptySubtitle: "Click Install on a plugin to get started",
  activeLabel: "Installed",
  installLabel: "Install", installIcon: "download",
  busyInstallLabel: "Installing...", busyRemoveLabel: "Uninstalling...",
  confirmRemoveMessage: name => `Uninstall ${name}?`,
  removeKeyword: "uninstall",
  installFn: "installPlugin", confirmRemoveFn: "confirmUninstallPlugin",
  cancelRemoveFn: "cancelUninstallPlugin", removeFn: "uninstallPlugin",
  switchTabFn: "switchPluginsTab", reloadFn: "reloadPluginsPage",
  renderRowIcon: p => {
    const color = PLUGIN_COLORS[p.category] || "#6B7280";
    const letter = p.id.charAt(0).toUpperCase();
    return `<div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm font-bold text-white" style="background:${color}">${letter}</div>`;
  },
  getDisplayName: p => (p.category === "channels" && p.channel_label) ? p.channel_label : p.id,
  getDescription: p => (p.category === "channels" && p.channel_blurb) ? p.channel_blurb : p.description,
  defaultTab: data => PLUGIN_CATEGORIES.map(c => c.key).find(k => data.some(p => p.category === k)) || "providers",
  renderExtraActions: p => {
    if (p.category === "channels" && p.installed && CHANNEL_INIT_REGISTRY[p.id]) {
      return `<button onclick="event.stopPropagation(); openChannelInitWizard('${esc(p.id)}')"
        class="inline-flex items-center justify-center w-7 h-7 rounded text-text-muted hover:text-text-primary hover:bg-bg-secondary transition-colors"
        title="Configure ${esc(CHANNEL_INIT_REGISTRY[p.id].label)} channel">
        <i data-lucide="settings" class="w-3.5 h-3.5"></i>
      </button>`;
    }
    return "";
  },
  onInstalled: (id, item) => {
    if (item && item.category === "channels" && CHANNEL_INIT_REGISTRY[id]) {
      openChannelInitWizard(id);
    }
  },
});

window.switchPluginsTab = pluginsPage.switchTab;
window.installPlugin = pluginsPage.handleInstall;
window.confirmUninstallPlugin = pluginsPage.confirmUninstall;
window.cancelUninstallPlugin = pluginsPage.cancelUninstall;
window.uninstallPlugin = pluginsPage.handleUninstall;
window.reloadPluginsPage = pluginsPage.reload;
