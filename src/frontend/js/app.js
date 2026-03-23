/* OpenClaw GUI — 前端互動邏輯（結構化 UI） */

// ── 工具函式 ──

function $(id) { return document.getElementById(id); }

function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function refreshIcons() {
    if (window.lucide) lucide.createIcons();
}

// ── 檢查卡片圖示/色彩對應 ──

var checkMeta = {
    docker:         { icon: "container",  colorClass: "blue" },
    docker_running: { icon: "activity",   colorClass: "green" },
    docker_desktop: { icon: "activity",   colorClass: "green" },
    vscode:         { icon: "code",       colorClass: "blue" },
    ngrok:          { icon: "globe",      colorClass: "blue" },
    nodejs:         { icon: "hexagon",    colorClass: "green" },
    openclaw:       { icon: "terminal",   colorClass: "blue" },
    jq:             { icon: "file-json",  colorClass: "blue" },
    systemd:        { icon: "server",     colorClass: "blue" },
    _default:       { icon: "box",        colorClass: "blue" }
};

function getCheckMeta(key) {
    return checkMeta[key] || checkMeta._default;
}

// ── 環境檢查回呼（由 Python Bridge 呼叫） ──

window.onCheckEnvResults = function (results) {
    var grid = $("check-results");
    var loading = $("check-loading");
    var envFileRow = $("env-file-check");
    var errorGuidance = $("error-guidance");

    loading.style.display = "none";
    grid.innerHTML = "";
    envFileRow.style.display = "none";
    envFileRow.innerHTML = "";
    errorGuidance.style.display = "none";
    errorGuidance.innerHTML = "";

    var passCount = 0;
    var failCount = 0;
    var failedItems = [];

    for (var i = 0; i < results.length; i++) {
        var item = results[i];

        if (item.key === "env_file") {
            renderEnvFileCheck(item);
            if (item.installed) passCount++;
            continue;
        }

        var meta = getCheckMeta(item.key || "");
        var isPassed = item.installed;
        var isWarn = !item.required && !item.installed;

        // 判斷徽章狀態
        var badgeClass, badgeIcon, badgeText;
        if (isPassed) {
            badgeClass = "pass";
            badgeIcon = "check";
            badgeText = (item.key === "docker_running" || item.key === "docker_desktop") ? "Running" : "Installed";
        } else if (isWarn) {
            badgeClass = "warn";
            badgeIcon = "alert-triangle";
            badgeText = "Optional";
        } else {
            badgeClass = "fail";
            badgeIcon = "x";
            badgeText = "Not Found";
            failedItems.push(item);
        }

        var iconColor = isPassed || isWarn ? meta.colorClass : "red";
        var versionText = item.version ? "v" + escapeHtml(item.version) : escapeHtml(item.message || "");

        var card = document.createElement("div");
        card.className = "check-card";
        card.innerHTML =
            '<div class="check-card-top">' +
            '  <div class="check-card-icon-bg ' + iconColor + '">' +
            '    <i data-lucide="' + meta.icon + '" class="card-icon"></i>' +
            '  </div>' +
            '  <div class="check-card-badge ' + badgeClass + '">' +
            '    <i data-lucide="' + badgeIcon + '" class="check-card-badge-icon"></i>' +
            '    <span>' + badgeText + '</span>' +
            '  </div>' +
            '</div>' +
            '<div class="check-card-info">' +
            '  <div class="check-card-name">' + escapeHtml(item.name) + '</div>' +
            '  <div class="check-card-version' + (!isPassed && !isWarn ? " error" : "") + '">' + versionText + '</div>' +
            '</div>';

        grid.appendChild(card);

        if (isPassed) passCount++;
        else if (item.required) failCount++;
    }

    refreshIcons();
    renderSummaryBanner(passCount, failCount, results.length);
    if (failedItems.length > 0) renderErrorGuidance(failedItems);
};

function renderSummaryBanner(passCount, failCount, totalCount) {
    var banner = $("summary-banner");
    var allPassed = failCount === 0;
    var state = allPassed ? "success" : "failure";
    var icon = allPassed ? "check-circle" : "alert-circle";
    var title = allPassed
        ? "All checks passed — environment is ready"
        : failCount + " check(s) failed — action required";

    banner.className = "summary-banner " + state;
    banner.innerHTML =
        '<i data-lucide="' + icon + '" class="summary-icon ' + state + '"></i>' +
        '<div class="summary-text">' +
        '  <div class="summary-title ' + state + '">' + title + '</div>' +
        '  <div class="summary-desc">' + passCount + ' of ' + totalCount + ' checks passed</div>' +
        '</div>' +
        '<span class="summary-time">Last checked: just now</span>';
    banner.style.display = "flex";
    refreshIcons();
}

function renderEnvFileCheck(item) {
    var row = $("env-file-check");
    var ok = item.installed;
    var stateClass = ok ? "success" : "fail";
    var badgeClass = ok ? "pass" : "fail";
    var badgeIcon = ok ? "check" : "x";
    var badgeText = ok ? "Verified" : "Missing";
    var desc = ok ? "Copied from .env.example — ready for configuration" : (item.message || ".env file not found");

    row.innerHTML =
        '<div class="env-file-icon-bg ' + stateClass + '">' +
        '  <i data-lucide="file-text" class="env-file-icon"></i>' +
        '</div>' +
        '<div class="env-file-text">' +
        '  <div class="env-file-name">.env Configuration File</div>' +
        '  <div class="env-file-desc">' + escapeHtml(desc) + '</div>' +
        '</div>' +
        '<div class="env-file-badge ' + badgeClass + '">' +
        '  <i data-lucide="' + badgeIcon + '" class="env-file-badge-icon"></i>' +
        '  <span>' + badgeText + '</span>' +
        '</div>';
    row.style.display = "flex";
    refreshIcons();
}

function renderErrorGuidance(failedItems) {
    var container = $("error-guidance");
    var title = "Action Required: Install " + escapeHtml(failedItems[0].name);
    var desc = failedItems.length === 1
        ? escapeHtml(failedItems[0].name) + " is required for " +
          escapeHtml(failedItems[0].message || "this feature") +
          ". Please install it, then re-run the environment check."
        : failedItems.length + " missing dependencies need to be installed. Please install them, then re-run the environment check.";

    container.innerHTML =
        '<i data-lucide="alert-circle" class="error-guidance-icon"></i>' +
        '<div class="error-guidance-text">' +
        '  <div class="error-guidance-title">' + title + '</div>' +
        '  <div class="error-guidance-desc">' + desc + '</div>' +
        '</div>';
    container.style.display = "flex";
    refreshIcons();
}

window.onCheckEnvError = function (errorMessage) {
    $("check-loading").style.display = "none";
    $("check-results").innerHTML = "";

    var banner = $("summary-banner");
    banner.className = "summary-banner failure";
    banner.style.display = "flex";
    banner.innerHTML =
        '<i data-lucide="alert-circle" class="summary-icon failure"></i>' +
        '<div class="summary-text">' +
        '  <div class="summary-title failure">Error: ' + escapeHtml(errorMessage) + '</div>' +
        '</div>';
    refreshIcons();
};

// ── 操作 ──

function startCheckEnv() {
    $("check-results").innerHTML = "";
    $("summary-banner").style.display = "none";
    $("env-file-check").style.display = "none";
    $("error-guidance").style.display = "none";
    $("check-loading").style.display = "flex";

    window.pywebview.api.check_env().then(function (raw) {
        var result = JSON.parse(raw);
        if (!result.ok) window.onCheckEnvError(result.error);
    });
}

// ── 導覽 ──

function navigateTo(viewName) {
    var views = document.querySelectorAll(".view");
    for (var i = 0; i < views.length; i++) views[i].classList.remove("active");
    var target = $("view-" + viewName);
    if (target) target.classList.add("active");

    var navItems = document.querySelectorAll(".nav-item");
    for (var i = 0; i < navItems.length; i++) {
        navItems[i].classList.toggle("active", navItems[i].getAttribute("data-view") === viewName);
    }

    if (viewName === "environment") startCheckEnv();
    if (viewName === "initialize") initWizardLoad();
}

// ── 初始化精靈 ──

var wizardStep = 1;
var wizardData = {
    deployMode: "",
    workingDir: ".openclaw",
    bindHost: "0.0.0.0",
    gatewayMode: "local",
    gatewayPort: 18789
};

var initStepLabels = {
    create_dirs: "建立目錄結構",
    generate_config: "產生設定檔",
    store_keys: "儲存金鑰",
    start_service: "啟動服務",
    wait_gateway: "等待 Gateway 就緒",
    configure_stt: "設定語音轉文字"
};

var STEP_KEYS = ["create_dirs", "generate_config", "store_keys", "start_service", "wait_gateway", "configure_stt"];

var SECRET_KEYS = [
    "line_channel_access_token", "line_channel_secret",
    "discord_bot_token", "openai_api_key",
    "database_url", "redis_url"
];

function initWizardLoad() {
    wizardStep = 1;
    showWizardStep(1);
    resetProgressList();
    $("init-dashboard-info").style.display = "none";
    $("init-error-banner").style.display = "none";

    window.pywebview.api.get_init_defaults().then(function (raw) {
        var d = JSON.parse(raw);
        Object.assign(wizardData, d);

        $("init-workingDir").value = d.workingDir;
        $("init-bindHost").value = d.bindHost;
        $("init-gatewayMode").value = d.gatewayMode;
        $("init-gatewayPort").value = d.gatewayPort;
        selectDeployMode(d.deployMode);
    });
}

function selectDeployMode(mode) {
    wizardData.deployMode = mode;
    var cards = document.querySelectorAll(".mode-card");
    for (var i = 0; i < cards.length; i++) {
        cards[i].classList.toggle("selected", cards[i].getAttribute("data-mode") === mode);
    }
}

function showWizardStep(step) {
    for (var i = 1; i <= 3; i++) {
        var panel = $("init-step-" + i);
        if (panel) panel.style.display = (i === step) ? "flex" : "none";
    }

    for (var i = 1; i <= 3; i++) {
        var el = $("stepper-" + i);
        el.classList.remove("active", "completed");
        if (i < step) el.classList.add("completed");
        else if (i === step) el.classList.add("active");
    }

    var backBtn = $("init-btn-back");
    var nextBtn = $("init-btn-next");

    backBtn.style.display = (step === 1) ? "none" : "";
    $("init-step-counter").textContent = "Step " + step + " of 3";

    nextBtn.innerHTML = step === 3
        ? '<i data-lucide="rocket" class="btn-icon"></i> Initialize'
        : 'Next <i data-lucide="arrow-right" class="btn-icon"></i>';
    nextBtn.disabled = false;
    refreshIcons();
}

function collectWizardData() {
    wizardData.workingDir = $("init-workingDir").value.trim() || ".openclaw";
    wizardData.bindHost = $("init-bindHost").value.trim() || "0.0.0.0";
    wizardData.gatewayMode = $("init-gatewayMode").value.trim() || "local";
    wizardData.gatewayPort = parseInt($("init-gatewayPort").value, 10) || 18789;
}

function collectSecrets() {
    var secrets = {};
    for (var i = 0; i < SECRET_KEYS.length; i++) {
        var el = $("init-" + SECRET_KEYS[i]);
        secrets[SECRET_KEYS[i]] = el ? el.value.trim() : "";
    }
    return secrets;
}

function countNonEmpty(obj) {
    var count = 0;
    for (var k in obj) { if (obj[k]) count++; }
    return count;
}

function validateWizardStep(step) {
    if (step === 1) {
        if (!wizardData.deployMode) { alert("請選擇部署模式"); return false; }
        var port = parseInt($("init-gatewayPort").value, 10);
        if (isNaN(port) || port < 1 || port > 65535) { alert("Gateway Port 需介於 1-65535"); return false; }
        return true;
    }
    if (step === 2) {
        var token = $("init-line_channel_access_token").value.trim();
        var secret = $("init-line_channel_secret").value.trim();
        if ((token && !secret) || (!token && secret)) { alert("LINE Token 和 Secret 必須成對填寫"); return false; }
        return true;
    }
    return true;
}

function updateChannelStatus() {
    var hasLine = $("init-line_channel_access_token").value.trim() && $("init-line_channel_secret").value.trim();
    var hasDiscord = $("init-discord_bot_token").value.trim();

    setChannelStatus("init-line-status", hasLine);
    setChannelStatus("init-discord-status", hasDiscord);
}

function setChannelStatus(id, configured) {
    var el = $(id);
    el.textContent = configured ? "Configured" : "Not configured";
    el.className = "init-channel-status" + (configured ? " configured" : "");
}

function wizardNext() {
    if (wizardStep < 3) {
        if (!validateWizardStep(wizardStep)) return;
        collectWizardData();
        if (wizardStep === 1) updateChannelStatus();
        wizardStep++;
        if (wizardStep === 3) renderReviewStep();
        showWizardStep(wizardStep);
    } else {
        startInit();
    }
}

function wizardGoTo(step) {
    if (step >= 1 && step < wizardStep) {
        wizardStep = step;
        showWizardStep(wizardStep);
    }
}

function renderReviewStep() {
    collectWizardData();
    var modeLabels = { docker_windows: "Windows Docker", docker_linux: "Linux Docker", native_linux: "Native Linux" };
    var items = [
        { label: "Deploy Mode", value: modeLabels[wizardData.deployMode] || wizardData.deployMode },
        { label: "Working Dir", value: wizardData.workingDir },
        { label: "Bind Host", value: wizardData.bindHost },
        { label: "Gateway Mode", value: wizardData.gatewayMode },
        { label: "Gateway Port", value: String(wizardData.gatewayPort) },
        { label: "API Keys", value: countNonEmpty(collectSecrets()) + " configured" }
    ];

    var html = "";
    for (var i = 0; i < items.length; i++) {
        html += '<div class="init-review-item">' +
            '<div class="init-review-label">' + escapeHtml(items[i].label) + '</div>' +
            '<div class="init-review-value">' + escapeHtml(items[i].value) + '</div>' +
            '</div>';
    }
    $("init-review-summary").innerHTML = html;
    resetProgressList();
}

function resetProgressList() {
    for (var i = 0; i < STEP_KEYS.length; i++) {
        var el = $("init-prog-" + STEP_KEYS[i]);
        if (el) {
            el.className = "init-progress-item pending";
            el.innerHTML = '<div class="init-progress-icon"><i data-lucide="circle" class="prog-icon"></i></div>' +
                '<span>' + initStepLabels[STEP_KEYS[i]] + '</span>';
        }
    }
    refreshIcons();
}

function startInit() {
    var nextBtn = $("init-btn-next");
    var backBtn = $("init-btn-back");
    nextBtn.disabled = true;
    backBtn.disabled = true;

    $("init-dashboard-info").style.display = "none";
    $("init-error-banner").style.display = "none";

    collectWizardData();
    var configJson = JSON.stringify(wizardData);
    var secretsJson = JSON.stringify(collectSecrets());

    window.pywebview.api.save_secrets(secretsJson).then(function (raw) {
        var result = JSON.parse(raw);
        if (!result.ok) {
            showInitError("金鑰儲存失敗: " + (result.error || "unknown"));
            nextBtn.disabled = false;
            backBtn.disabled = false;
            return;
        }
        window.pywebview.api.run_init(configJson, secretsJson).then(function (raw2) {
            var result2 = JSON.parse(raw2);
            if (!result2.ok) {
                showInitError(result2.error || "啟動失敗");
                nextBtn.disabled = false;
                backBtn.disabled = false;
            }
        });
    });
}

// ── 初始化回呼（由 Python Bridge 呼叫） ──

var initStepIconMap = { running: "loader", done: "check-circle", error: "x-circle", skipped: "minus-circle" };

window.onInitStepUpdate = function (update) {
    var el = $("init-prog-" + update.key);
    if (!el) return;
    var icon = initStepIconMap[update.status] || "circle";
    var label = initStepLabels[update.key] || update.key;
    var msg = update.message ? " — " + escapeHtml(update.message) : "";

    el.className = "init-progress-item " + update.status;
    el.innerHTML = '<div class="init-progress-icon"><i data-lucide="' + icon + '" class="prog-icon"></i></div>' +
        '<span>' + label + msg + '</span>';
    refreshIcons();
};

window.onInitComplete = function (result) {
    var nextBtn = $("init-btn-next");
    var backBtn = $("init-btn-back");

    if (result.success) {
        $("init-dashboard-url").textContent = result.dashboard_url || "—";
        $("init-dashboard-token").textContent = result.access_token || "—";
        $("init-dashboard-info").style.display = "flex";
        nextBtn.innerHTML = '<i data-lucide="check" class="btn-icon"></i> Done';
        nextBtn.disabled = true;
    } else {
        showInitError(result.error || "未知錯誤");
        nextBtn.innerHTML = '<i data-lucide="rotate-ccw" class="btn-icon"></i> Retry';
        nextBtn.disabled = false;
        nextBtn.onclick = function () { nextBtn.onclick = wizardNext; startInit(); };
    }
    backBtn.disabled = false;
    refreshIcons();
};

window.onInitError = function (msg) {
    showInitError(msg);
    $("init-btn-next").disabled = false;
    $("init-btn-back").disabled = false;
};

function showInitError(msg) {
    $("init-error-msg").textContent = msg;
    $("init-error-banner").style.display = "flex";
    refreshIcons();
}

// ── 應用程式初始化 ──

window.addEventListener("pywebviewready", function () {
    window.pywebview.api.get_platform_info().then(function (raw) {
        var info = JSON.parse(raw);
        var sidebarEnv = $("sidebar-env-info");
        if (sidebarEnv) sidebarEnv.textContent = info.env + " · " + info.os;
        var modeText = $("env-mode-text");
        if (modeText) modeText.textContent = info.env + " Mode";
    });
    refreshIcons();
});
