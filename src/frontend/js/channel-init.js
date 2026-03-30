/**
 * OpenClaw GUI — Channel Init Wizard
 *
 * Channel 初始化 Modal 精靈
 */

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
