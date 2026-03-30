/**
 * OpenClaw GUI — Configuration Wizard
 *
 * 設定精靈：部署模式選擇、API Keys、初始化
 */

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

/* ---------- 9.1 模式定義 ---------- */

function getDeployModes() {
  return [
    { id: "docker-windows", icon: "monitor",  iconColor: "text-accent-primary",    borderColor: "#ff5c5c", name: t("config.mode_docker_win_name"),   description: t("config.mode_docker_win_desc") },
    { id: "docker-linux",   icon: "terminal", iconColor: "text-accent-secondary",  borderColor: "#14b8a6", name: t("config.mode_docker_linux_name"), description: t("config.mode_docker_linux_desc") },
    { id: "native-linux",   icon: "server",   iconColor: "text-text-muted",        borderColor: "#838387", name: t("config.mode_native_name"),       description: t("config.mode_native_desc") },
    { id: "remote-ssh",     icon: "cloud",    iconColor: "text-[#8b5cf6]",         borderColor: "#8b5cf6", name: t("config.mode_remote_name"),       description: t("config.mode_remote_desc") },
  ];
}

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
  const cards = getDeployModes().map(m => renderRadioCard(m, m.id === configState.selectedMode)).join("");
  return renderSectionPanel({ icon: "monitor", iconColor: "text-accent-primary", title: t("config.deployment_mode"), children: `<div class="grid grid-cols-2 gap-3">${cards}</div>` });
}

function renderSSHSection() {
  const keyRowHidden = configState.sshAuthMethod === "password" ? "hidden" : "";
  const pwdRowHidden = configState.sshAuthMethod === "key" ? "hidden" : "";
  const toggleText = configState.sshAuthMethod === "key" ? t("config.ssh_use_password") : t("config.ssh_use_key");

  const formGrid = `
    <div class="grid grid-cols-2 gap-4">
      ${renderInput({ id: "input-ssh-host", label: t("config.ssh_host"), icon: "globe", placeholder: "192.168.1.100", required: true })}
      ${renderInput({ id: "input-ssh-port", label: t("config.ssh_port"), placeholder: "22", type: "number", value: "22" })}
      ${renderInput({ id: "input-ssh-username", label: t("config.ssh_username"), icon: "user", placeholder: "ubuntu", required: true })}
      <div id="ssh-key-row" class="${keyRowHidden}">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-medium text-text-secondary">${t("config.ssh_key_file")}</label>
          <div class="flex gap-2">
            <input id="input-ssh-key-file" type="text" placeholder="~/.ssh/id_rsa" readonly
              class="flex-1 bg-bg-input border border-border-default focus-within:border-accent-primary rounded-sm text-sm text-text-primary placeholder:text-text-muted pl-3 pr-3 py-2.5 outline-none transition-colors" />
            ${renderButton({ variant: "secondary", icon: "folder-open", label: t("config.ssh_browse"), size: "sm", onclick: "browseSSHKey()" })}
          </div>
        </div>
      </div>
      <div id="ssh-password-row" class="${pwdRowHidden}">
        ${renderInput({ id: "input-ssh-password", label: t("config.ssh_password"), type: "password", placeholder: "Enter password" })}
      </div>
    </div>
    <div class="mt-3 flex items-center justify-between">
      <button type="button" id="btn-toggle-ssh-auth" class="text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0 underline" onclick="toggleSSHAuthMethod()">
        ${toggleText}
      </button>
    </div>
    <div class="mt-4 flex items-center gap-3">
      ${renderButton({ variant: "secondary", icon: "wifi", label: t("config.ssh_test"), id: "btn-test-ssh", onclick: "testSSHConnection()" })}
      <span id="ssh-test-badge"></span>
    </div>`;

  return `<div id="ssh-section">${renderSectionPanel({ icon: "terminal", iconColor: "text-[#8b5cf6]", title: t("config.ssh_title"), description: t("config.ssh_desc"), children: formGrid })}</div>`;
}

function renderGatewaySection() {
  const d = MODE_DEFAULTS[configState.selectedMode] || MODE_DEFAULTS["docker-windows"];
  const v = (key) => configState.formValues[key] !== undefined ? configState.formValues[key] : d[key];

  const mainGrid = `
    <div class="grid grid-cols-2 gap-4">
      ${renderInput({ id: "input-config-dir", label: t("config.config_dir"), icon: "folder", placeholder: "~/.openclaw", value: v("config_dir") })}
      ${renderInput({ id: "input-workspace-dir", label: t("config.workspace_dir"), icon: "folder", placeholder: "~/.openclaw/workspace", value: v("workspace_dir") })}
      ${renderInput({ id: "input-gateway-bind", label: t("config.gateway_bind"), placeholder: "lan", value: v("gateway_bind") })}
      ${renderInput({ id: "input-gateway-port", label: t("config.gateway_port"), type: "number", placeholder: "18789", value: v("gateway_port") })}
    </div>
    <div class="grid grid-cols-2 gap-4 mt-4">
      ${renderInput({ id: "input-bridge-port", label: t("config.bridge_port"), type: "number", placeholder: "18790", value: v("bridge_port") })}
    </div>`;

  const sandboxChecked = configState.formValues.sandbox !== undefined ? configState.formValues.sandbox : true;
  const advancedContent = `
    <div id="advanced-settings" class="collapsible-content mt-4">
      <div class="grid grid-cols-2 gap-4">
        ${renderInput({ id: "input-timezone", label: t("config.timezone"), placeholder: "Asia/Taipei", value: v("timezone") })}
        ${renderInput({ id: "input-docker-image", label: t("config.docker_image"), placeholder: "openclaw:local", value: v("docker_image") })}
      </div>
      <div class="flex items-center gap-2 mt-4">
        <input type="checkbox" id="toggle-sandbox" class="checkbox-custom" ${sandboxChecked ? "checked" : ""} />
        <label for="toggle-sandbox" class="text-sm text-text-secondary cursor-pointer">${t("config.enable_sandbox")}</label>
      </div>
    </div>`;

  const advancedToggle = `
    <button type="button" class="flex items-center gap-1.5 mt-4 text-xs text-text-muted hover:text-text-secondary cursor-pointer bg-transparent border-0 p-0" onclick="toggleAdvancedSettings()">
      <i data-lucide="chevron-right" class="w-3.5 h-3.5 collapsible-chevron" id="advanced-chevron"></i>
      <span>${t("config.advanced")}</span>
    </button>`;

  return renderSectionPanel({ icon: "globe", iconColor: "text-accent-secondary", title: t("config.gateway_dir_title"), children: mainGrid + advancedToggle + advancedContent });
}

function renderConfigActionBar() {
  const nextDisabled = configState.selectedMode === "remote-ssh" && !configState.sshTestPassed;
  const html = `<div class="flex items-center justify-end gap-3">
    <span class="text-sm text-text-muted font-medium">${t("common.step_x_of_y", { step: configState.step, total: 3 })}</span>
    ${renderButton({ variant: "primary", icon: "arrow-right", label: t("common.next"), id: "btn-next-step", disabled: nextDisabled, onclick: "configNextStep()" })}
  </div>`;
  renderInto("config-action-bar", html);
}

function renderConfigStep1() {
  const stepIndicator = renderStepIndicator({ steps: [t("config.step_environment"), t("config.step_api_keys"), t("config.step_initialize")], currentStep: configState.step, completedSteps: [] });
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
    const def = getDeployModes().find(m => m.id === cardMode);
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
  if (toggleBtn) toggleBtn.textContent = configState.sshAuthMethod === "key" ? t("config.ssh_use_password") : t("config.ssh_use_key");
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
    if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: t("config.ssh_host_required") });
    refreshIcons();
    return;
  }

  // 顯示連線中狀態
  if (badge) {
    badge.innerHTML = `<span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#14b8a618] text-accent-secondary text-xs font-medium">
      <i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i> ${t("status.connecting")}</span>`;
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
      if (badge) badge.innerHTML = renderStatusBadge({ status: "success", text: t("config.ssh_connected", { os: info.os || "?", cpu_cores: info.cpu_cores || "?", memory_gb: info.memory_gb || "?" }) });
    } else {
      configState.sshTestPassed = false;
      configState.sshTestResult = null;
      if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: result?.error?.message || t("config.ssh_failed") });
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
        if (badge) badge.innerHTML = renderStatusBadge({ status: "error", text: connResult?.error?.message || t("config.ssh_failed") });
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
      <span>${t("config.models_runtime")}</span>
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
      <div class="text-xs font-medium text-text-muted mb-2">${t("config.available_models")}</div>
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
        <div class="mt-2 text-xs text-text-muted">${t("config.no_key_required")}</div>
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
    <div class="text-xs font-medium text-text-muted mb-2">${t("config.primary_model")}</div>
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
        <span>${t("config.more_section", { section: sectionKey })}</span>
      </button>
      <div id="${sectionKey}-more" class="collapsible-content">
        <div class="mt-2 grid gap-1">${secondaryCards}</div>
      </div>` : "";

  const footerHtml = footer || "";
  return renderSectionPanel({ icon, iconColor, title, description, children: `<div class="grid gap-1">${primaryCards}</div>${moreSection}${footerHtml}` });
}

function renderConfigStep2ActionBar() {
  const html = `<div class="flex items-center justify-between">
    <div>${renderButton({ variant: "secondary", icon: "arrow-left", label: t("common.back"), onclick: "configPrevStep()" })}</div>
    <div class="flex items-center gap-3">
      <span class="text-sm text-text-muted font-medium">${t("common.step_x_of_y", { step: configState.step, total: 3 })}</span>
      ${renderButton({ variant: "primary", icon: "arrow-right", label: t("common.next"), id: "btn-next-step2", onclick: "configNextStep2()" })}
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
    renderStepIndicator({ steps: [t("config.step_environment"), t("config.step_api_keys"), t("config.step_initialize")], currentStep: 2, completedSteps: [1] }),
    renderGroupedSection({
      icon: "cpu", iconColor: "text-accent-primary",
      title: t("config.model_providers"), description: t("config.model_providers_desc"),
      items: step2State.cachedProviders, checkedSet: step2State.checkedProviders,
      renderCard: renderProviderCard, sectionKey: "providers",
      footer: renderPrimaryModelDropdown(),
    }),
    `<div class="flex items-start gap-3 px-2 py-3">
      <i data-lucide="shield-check" class="w-5 h-5 text-accent-primary flex-shrink-0 mt-0.5"></i>
      <p class="text-xs text-text-secondary leading-relaxed">${t("config.security_note")}</p>
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

function getInitStepsDocker() {
  return [
    { id: 1,  label: t("config.init_docker_1"),  desc: t("config.init_docker_1_desc") },
    { id: 2,  label: t("config.init_docker_2"),  desc: t("config.init_docker_2_desc") },
    { id: 3,  label: t("config.init_docker_3"),  desc: t("config.init_docker_3_desc") },
    { id: 4,  label: t("config.init_docker_4"),  desc: t("config.init_docker_4_desc") },
    { id: 5,  label: t("config.init_docker_5"),  desc: t("config.init_docker_5_desc") },
    { id: 6,  label: t("config.init_docker_6"),  desc: t("config.init_docker_6_desc") },
    { id: 7,  label: t("config.init_docker_7"),  desc: t("config.init_docker_7_desc") },
    { id: 8,  label: t("config.init_docker_8"),  desc: t("config.init_docker_8_desc") },
    { id: 9,  label: t("config.init_docker_9"),  desc: t("config.init_docker_9_desc") },
    { id: 10, label: t("config.init_docker_10"), desc: t("config.init_docker_10_desc") },
  ];
}

function getInitStepsNative() {
  return [
    { id: 1, label: t("config.init_native_1"), desc: t("config.init_native_1_desc") },
    { id: 2, label: t("config.init_native_2"), desc: t("config.init_native_2_desc") },
    { id: 3, label: t("config.init_native_3"), desc: t("config.init_native_3_desc") },
    { id: 4, label: t("config.init_native_4"), desc: t("config.init_native_4_desc") },
    { id: 5, label: t("config.init_native_5"), desc: t("config.init_native_5_desc") },
    { id: 6, label: t("config.init_native_6"), desc: t("config.init_native_6_desc") },
    { id: 7, label: t("config.init_native_7"), desc: t("config.init_native_7_desc") },
    { id: 8, label: t("config.init_native_8"), desc: t("config.init_native_8_desc") },
  ];
}

function getInitSteps() {
  return configState.selectedMode === "native-linux" ? getInitStepsNative() : getInitStepsDocker();
}

function renderProgressPanel(steps) {
  const items = steps.map(s =>
    `<div data-init-step="${s.id}">${renderProgressItem({ name: s.label, description: s.desc, status: "pending" })}</div>`
  ).join("");
  return renderSectionPanel({
    icon: "loader", iconColor: "text-accent-primary",
    title: t("config.init_progress"), description: t("config.init_progress_desc", { count: steps.length }),
    children: items, id: "init-progress-panel",
  });
}

function renderDashboardInfoPanel() {
  const port = configState.formValues.gateway_port || "18789";
  const dashUrl = `http://127.0.0.1:${port}/`;

  return renderSectionPanel({
    icon: "layout-dashboard", iconColor: "text-accent-secondary",
    title: t("config.dashboard_info"), description: t("config.dashboard_info_desc"),
    children: `
      <div id="dashboard-info-fields" class="opacity-50 pointer-events-none">
        <div class="grid gap-3">
          ${renderInput({ id: "input-dash-url", label: t("config.dashboard_url"), icon: "globe", value: dashUrl, type: "text" })}
          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-medium text-text-secondary">${t("config.access_token")}</label>
            <div class="relative">
              <i data-lucide="lock" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted"></i>
              <input id="input-dash-token" type="text" value="" readonly placeholder="${t("config.generated_after_init")}"
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
          <p class="text-xs text-text-secondary mb-3">${t("config.approve_instructions")}</p>
          ${renderButton({ variant: "secondary", icon: "smartphone", label: t("config.approve_pending"), onclick: "approvePendingDevice()" })}
          <div id="device-pairing-result" class="mt-3"></div>
        </div>
      </div>`,
    id: "dashboard-info-panel",
  });
}

function renderConfigStep3ActionBar() {
  const html = `<div class="flex items-center justify-between">
    <div>${renderButton({ variant: "secondary", icon: "arrow-left", label: t("common.back"), disabled: initState.running, onclick: "configPrevStep()" })}</div>
    <div class="flex items-center gap-3">
      <span class="text-sm text-text-muted font-medium">${t("common.step_x_of_y", { step: 3, total: 3 })}</span>
      ${renderButton({
        variant: "primary",
        icon: initState.running ? "loader" : "play",
        label: initState.running ? t("config.initializing") : t("config.initialize"),
        id: "btn-initialize", disabled: initState.running,
        loading: initState.running, onclick: "startInitialization()",
      })}
    </div>
  </div>`;
  renderInto("config-action-bar", html);
}

function renderConfigStep3() {
  const steps = getInitSteps();
  const stepIndicator = renderStepIndicator({ steps: [t("config.step_environment"), t("config.step_api_keys"), t("config.step_initialize")], currentStep: 3, completedSteps: [1, 2] });
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
        btn.innerHTML = `<i data-lucide="refresh-cw" class="w-4 h-4"></i><span>${t("common.retry")}</span>`;
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
          ${renderButton({ variant: "primary", label: t("gateway.approve"), size: "sm", onclick: `approveDevice('${rid}')` })}
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
  renderDevicePairingResult("loading", t("config.fetching_devices"));

  try {
    const result = await window.pywebview.api.list_pending_devices();
    if (!result?.success) {
      renderDevicePairingResult("error", result?.error?.message || "Failed to list devices");
      return;
    }
    const devices = result.data?.devices || [];
    if (devices.length === 0) renderDevicePairingResult("empty", t("config.no_pending_devices"));
    else renderDevicePairingResult("list", t("config.pending_devices_found", { count: devices.length }), devices);
  } catch { renderDevicePairingResult("error", t("config.connection_error")); }
  finally { initState.deviceApprovalLoading = false; }
}

async function approveDevice(requestId) {
  const row = document.getElementById(`device-row-${requestId}`);
  if (row) { const btn = row.querySelector("button"); if (btn) { btn.disabled = true; btn.classList.add("opacity-50"); } }
  try {
    const result = await window.pywebview.api.approve_device({ request_id: requestId });
    renderDevicePairingResult(result?.success ? "success" : "error", result?.success ? t("config.device_approved") : (result?.error?.message || "Approval failed"));
  } catch { renderDevicePairingResult("error", t("config.connection_error_approval")); }
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
