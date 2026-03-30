/**
 * OpenClaw GUI — Gateway Page
 *
 * Gateway 管理頁面：連線資訊、Origin 控制、裝置管理
 */

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
