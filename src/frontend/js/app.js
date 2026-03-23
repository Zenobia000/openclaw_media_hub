/* OpenClaw GUI - Frontend Logic (Structured UI, no terminal) */

// ── Card icon/color mapping ──

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

// ── Global callbacks (called from Python Bridge) ──

window.onCheckEnvResults = function (results) {
    var grid = document.getElementById("check-results");
    var banner = document.getElementById("summary-banner");
    var loading = document.getElementById("check-loading");
    var envFileRow = document.getElementById("env-file-check");
    var errorGuidance = document.getElementById("error-guidance");

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

        // Handle .env file check separately
        if (item.key === "env_file") {
            renderEnvFileCheck(item);
            if (item.installed) passCount++;
            continue;
        }

        var meta = getCheckMeta(item.key || "");
        var isPassed = item.installed;
        var isWarn = !item.required && !item.installed;

        var card = document.createElement("div");
        card.className = "check-card";

        // Determine badge state
        var badgeClass, badgeIcon, badgeText;
        if (isPassed) {
            badgeClass = "pass";
            badgeIcon = "check";
            badgeText = item.key === "docker_running" || item.key === "docker_desktop"
                ? "Running" : "Installed";
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

        // Icon bg color follows badge state for fail
        var iconColorClass = isPassed ? meta.colorClass : (isWarn ? meta.colorClass : "red");

        var versionText = item.version
            ? "v" + escapeHtml(item.version)
            : escapeHtml(item.message || "");

        card.innerHTML =
            '<div class="check-card-top">' +
            '  <div class="check-card-icon-bg ' + iconColorClass + '">' +
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

        if (isPassed) {
            passCount++;
        } else if (item.required) {
            failCount++;
        }
    }

    // Re-render lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Show summary banner (above cards)
    renderSummaryBanner(passCount, failCount, results.length);

    // Show error guidance for failed items
    if (failedItems.length > 0) {
        renderErrorGuidance(failedItems);
    }
};

function renderSummaryBanner(passCount, failCount, totalCount) {
    var banner = document.getElementById("summary-banner");
    var now = new Date();
    var timeStr = "Last checked: just now";

    if (failCount === 0) {
        banner.className = "summary-banner success";
        banner.innerHTML =
            '<i data-lucide="check-circle" class="summary-icon success"></i>' +
            '<div class="summary-text">' +
            '  <div class="summary-title success">All checks passed — environment is ready</div>' +
            '  <div class="summary-desc">' + passCount + ' of ' + totalCount + ' checks passed</div>' +
            '</div>' +
            '<span class="summary-time">' + timeStr + '</span>';
    } else {
        banner.className = "summary-banner failure";
        banner.innerHTML =
            '<i data-lucide="alert-circle" class="summary-icon failure"></i>' +
            '<div class="summary-text">' +
            '  <div class="summary-title failure">' + failCount + ' check(s) failed — action required</div>' +
            '  <div class="summary-desc">' + passCount + ' of ' + totalCount + ' checks passed</div>' +
            '</div>' +
            '<span class="summary-time">' + timeStr + '</span>';
    }

    banner.style.display = "flex";

    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderEnvFileCheck(item) {
    var row = document.getElementById("env-file-check");
    var isPassed = item.installed;
    var stateClass = isPassed ? "success" : "fail";
    var badgeClass = isPassed ? "pass" : "fail";
    var badgeIcon = isPassed ? "check" : "x";
    var badgeText = isPassed ? "Verified" : "Missing";
    var desc = isPassed
        ? "Copied from .env.example — ready for configuration"
        : (item.message || ".env file not found");

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

    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderErrorGuidance(failedItems) {
    var container = document.getElementById("error-guidance");
    var lines = [];

    for (var i = 0; i < failedItems.length; i++) {
        var item = failedItems[i];
        lines.push("Action Required: Install " + escapeHtml(item.name));
    }

    var title = lines[0];
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

    if (window.lucide) {
        lucide.createIcons();
    }
}

window.onCheckEnvError = function (errorMessage) {
    var grid = document.getElementById("check-results");
    var loading = document.getElementById("check-loading");
    var banner = document.getElementById("summary-banner");

    loading.style.display = "none";
    grid.innerHTML = "";

    banner.className = "summary-banner failure";
    banner.style.display = "flex";
    banner.innerHTML =
        '<i data-lucide="alert-circle" class="summary-icon failure"></i>' +
        '<div class="summary-text">' +
        '  <div class="summary-title failure">Error: ' + escapeHtml(errorMessage) + '</div>' +
        '</div>';

    if (window.lucide) {
        lucide.createIcons();
    }
};

// ── Actions ──

function startCheckEnv() {
    var grid = document.getElementById("check-results");
    var banner = document.getElementById("summary-banner");
    var loading = document.getElementById("check-loading");
    var envFileRow = document.getElementById("env-file-check");
    var errorGuidance = document.getElementById("error-guidance");

    grid.innerHTML = "";
    banner.style.display = "none";
    envFileRow.style.display = "none";
    errorGuidance.style.display = "none";
    loading.style.display = "flex";

    window.pywebview.api.check_env().then(function (raw) {
        var result = JSON.parse(raw);
        if (!result.ok) {
            window.onCheckEnvError(result.error);
        }
    });
}

// ── Navigation ──

function navigateTo(viewName) {
    var views = document.querySelectorAll(".view");
    for (var i = 0; i < views.length; i++) {
        views[i].classList.remove("active");
    }
    var target = document.getElementById("view-" + viewName);
    if (target) {
        target.classList.add("active");
    }

    var navItems = document.querySelectorAll(".nav-item");
    for (var i = 0; i < navItems.length; i++) {
        navItems[i].classList.remove("active");
        if (navItems[i].getAttribute("data-view") === viewName) {
            navItems[i].classList.add("active");
        }
    }

    // Auto-run environment check when entering the Environment page
    if (viewName === "environment") {
        startCheckEnv();
    }

    // Load wizard defaults when entering Initialize page
    if (viewName === "initialize") {
        initWizardLoad();
    }
}

// ── Utilities ──

function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ── Initialize Wizard ──

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

function initWizardLoad() {
    wizardStep = 1;
    // Reset UI
    showWizardStep(1);
    resetProgressList();
    document.getElementById("init-dashboard-info").style.display = "none";
    document.getElementById("init-error-banner").style.display = "none";

    // Load defaults from backend
    window.pywebview.api.get_init_defaults().then(function (raw) {
        var defaults = JSON.parse(raw);
        wizardData.deployMode = defaults.deployMode;
        wizardData.workingDir = defaults.workingDir;
        wizardData.bindHost = defaults.bindHost;
        wizardData.gatewayMode = defaults.gatewayMode;
        wizardData.gatewayPort = defaults.gatewayPort;

        // Fill form fields
        document.getElementById("init-workingDir").value = defaults.workingDir;
        document.getElementById("init-bindHost").value = defaults.bindHost;
        document.getElementById("init-gatewayMode").value = defaults.gatewayMode;
        document.getElementById("init-gatewayPort").value = defaults.gatewayPort;

        // Pre-select mode card
        selectDeployMode(defaults.deployMode);
    });
}

function selectDeployMode(mode) {
    wizardData.deployMode = mode;
    var cards = document.querySelectorAll(".mode-card");
    for (var i = 0; i < cards.length; i++) {
        cards[i].classList.remove("selected");
        if (cards[i].getAttribute("data-mode") === mode) {
            cards[i].classList.add("selected");
        }
    }
}

function showWizardStep(step) {
    // Show/hide panels
    for (var i = 1; i <= 3; i++) {
        var panel = document.getElementById("init-step-" + i);
        if (panel) panel.style.display = (i === step) ? "flex" : "none";
    }

    // Update stepper
    for (var i = 1; i <= 3; i++) {
        var el = document.getElementById("stepper-" + i);
        el.classList.remove("active", "completed");
        if (i < step) el.classList.add("completed");
        else if (i === step) el.classList.add("active");
    }

    // Update buttons
    var backBtn = document.getElementById("init-btn-back");
    var nextBtn = document.getElementById("init-btn-next");
    var counter = document.getElementById("init-step-counter");

    backBtn.style.display = (step === 1) ? "none" : "";
    counter.textContent = "Step " + step + " of 3";

    if (step === 3) {
        nextBtn.innerHTML = '<i data-lucide="rocket" class="btn-icon"></i> Initialize';
    } else {
        nextBtn.innerHTML = 'Next <i data-lucide="arrow-right" class="btn-icon"></i>';
    }
    nextBtn.disabled = false;

    if (window.lucide) lucide.createIcons();
}

function collectWizardData() {
    wizardData.workingDir = document.getElementById("init-workingDir").value.trim() || ".openclaw";
    wizardData.bindHost = document.getElementById("init-bindHost").value.trim() || "0.0.0.0";
    wizardData.gatewayMode = document.getElementById("init-gatewayMode").value.trim() || "local";
    wizardData.gatewayPort = parseInt(document.getElementById("init-gatewayPort").value, 10) || 18789;
}

function collectSecrets() {
    var keys = [
        "line_channel_access_token", "line_channel_secret",
        "discord_bot_token", "openai_api_key",
        "database_url", "redis_url"
    ];
    var secrets = {};
    for (var i = 0; i < keys.length; i++) {
        var el = document.getElementById("init-" + keys[i]);
        secrets[keys[i]] = el ? el.value.trim() : "";
    }
    return secrets;
}

function validateWizardStep(step) {
    if (step === 1) {
        if (!wizardData.deployMode) {
            alert("請選擇部署模式");
            return false;
        }
        var port = parseInt(document.getElementById("init-gatewayPort").value, 10);
        if (isNaN(port) || port < 1 || port > 65535) {
            alert("Gateway Port 需介於 1-65535");
            return false;
        }
        return true;
    }
    if (step === 2) {
        // LINE token and secret must be paired
        var token = document.getElementById("init-line_channel_access_token").value.trim();
        var secret = document.getElementById("init-line_channel_secret").value.trim();
        if ((token && !secret) || (!token && secret)) {
            alert("LINE Token 和 Secret 必須成對填寫");
            return false;
        }
        return true;
    }
    return true;
}

function updateChannelStatus() {
    var lineToken = document.getElementById("init-line_channel_access_token").value.trim();
    var lineSecret = document.getElementById("init-line_channel_secret").value.trim();
    var discordToken = document.getElementById("init-discord_bot_token").value.trim();

    var lineStatus = document.getElementById("init-line-status");
    var discordStatus = document.getElementById("init-discord-status");

    if (lineToken && lineSecret) {
        lineStatus.textContent = "Configured";
        lineStatus.className = "init-channel-status configured";
    } else {
        lineStatus.textContent = "Not configured";
        lineStatus.className = "init-channel-status";
    }

    if (discordToken) {
        discordStatus.textContent = "Configured";
        discordStatus.className = "init-channel-status configured";
    } else {
        discordStatus.textContent = "Not configured";
        discordStatus.className = "init-channel-status";
    }
}

function wizardNext() {
    if (wizardStep < 3) {
        if (!validateWizardStep(wizardStep)) return;
        collectWizardData();
        if (wizardStep === 1) {
            updateChannelStatus();
        }
        wizardStep++;
        if (wizardStep === 3) {
            renderReviewStep();
        }
        showWizardStep(wizardStep);
    } else {
        startInit();
    }
}

function wizardGoTo(step) {
    if (step < 1 || step > 3) return;
    if (step < wizardStep) {
        wizardStep = step;
        showWizardStep(wizardStep);
    }
}

function renderReviewStep() {
    collectWizardData();
    var secrets = collectSecrets();

    var modeLabels = {
        docker_windows: "Windows Docker",
        docker_linux: "Linux Docker",
        native_linux: "Native Linux"
    };

    var items = [
        { label: "Deploy Mode", value: modeLabels[wizardData.deployMode] || wizardData.deployMode },
        { label: "Working Dir", value: wizardData.workingDir },
        { label: "Bind Host", value: wizardData.bindHost },
        { label: "Gateway Mode", value: wizardData.gatewayMode },
        { label: "Gateway Port", value: String(wizardData.gatewayPort) },
        { label: "API Keys", value: countNonEmpty(secrets) + " configured" }
    ];

    var html = "";
    for (var i = 0; i < items.length; i++) {
        html += '<div class="init-review-item">' +
            '<div class="init-review-label">' + escapeHtml(items[i].label) + '</div>' +
            '<div class="init-review-value">' + escapeHtml(items[i].value) + '</div>' +
            '</div>';
    }

    document.getElementById("init-review-summary").innerHTML = html;
    resetProgressList();
}

function countNonEmpty(obj) {
    var count = 0;
    for (var k in obj) {
        if (obj[k]) count++;
    }
    return count;
}

function resetProgressList() {
    var keys = ["create_dirs", "generate_config", "store_keys", "start_service", "wait_gateway", "configure_stt"];
    for (var i = 0; i < keys.length; i++) {
        var el = document.getElementById("init-prog-" + keys[i]);
        if (el) {
            el.className = "init-progress-item pending";
            el.innerHTML = '<div class="init-progress-icon"><i data-lucide="circle" class="prog-icon"></i></div>' +
                '<span>' + initStepLabels[keys[i]] + '</span>';
        }
    }
    if (window.lucide) lucide.createIcons();
}

function startInit() {
    var nextBtn = document.getElementById("init-btn-next");
    var backBtn = document.getElementById("init-btn-back");
    nextBtn.disabled = true;
    backBtn.disabled = true;

    document.getElementById("init-dashboard-info").style.display = "none";
    document.getElementById("init-error-banner").style.display = "none";

    collectWizardData();
    var secrets = collectSecrets();

    var configJson = JSON.stringify(wizardData);
    var secretsJson = JSON.stringify(secrets);

    // Save secrets first, then run init
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

// Callbacks from Python Bridge

window.onInitStepUpdate = function (update) {
    var el = document.getElementById("init-prog-" + update.key);
    if (!el) return;

    var iconMap = {
        running: "loader",
        done: "check-circle",
        error: "x-circle",
        skipped: "minus-circle"
    };
    var icon = iconMap[update.status] || "circle";
    var label = initStepLabels[update.key] || update.key;
    var msg = update.message ? " — " + escapeHtml(update.message) : "";

    el.className = "init-progress-item " + update.status;
    el.innerHTML = '<div class="init-progress-icon"><i data-lucide="' + icon + '" class="prog-icon"></i></div>' +
        '<span>' + label + msg + '</span>';

    if (window.lucide) lucide.createIcons();
};

window.onInitComplete = function (result) {
    var nextBtn = document.getElementById("init-btn-next");
    var backBtn = document.getElementById("init-btn-back");

    if (result.success) {
        var dashInfo = document.getElementById("init-dashboard-info");
        document.getElementById("init-dashboard-url").textContent = result.dashboard_url || "—";
        document.getElementById("init-dashboard-token").textContent = result.access_token || "—";
        dashInfo.style.display = "flex";

        nextBtn.innerHTML = '<i data-lucide="check" class="btn-icon"></i> Done';
        nextBtn.disabled = true;
    } else {
        showInitError(result.error || "未知錯誤");
        nextBtn.innerHTML = '<i data-lucide="rotate-ccw" class="btn-icon"></i> Retry';
        nextBtn.disabled = false;
        nextBtn.onclick = function () {
            nextBtn.onclick = wizardNext;
            startInit();
        };
    }
    backBtn.disabled = false;

    if (window.lucide) lucide.createIcons();
};

window.onInitError = function (msg) {
    showInitError(msg);
    var nextBtn = document.getElementById("init-btn-next");
    var backBtn = document.getElementById("init-btn-back");
    nextBtn.disabled = false;
    backBtn.disabled = false;
};

function showInitError(msg) {
    var banner = document.getElementById("init-error-banner");
    document.getElementById("init-error-msg").textContent = msg;
    banner.style.display = "flex";
    if (window.lucide) lucide.createIcons();
}

// ── Init ──

window.addEventListener("pywebviewready", function () {
    window.pywebview.api.get_platform_info().then(function (raw) {
        var info = JSON.parse(raw);
        // Update sidebar footer
        var sidebarEnv = document.getElementById("sidebar-env-info");
        if (sidebarEnv) {
            sidebarEnv.textContent = info.env + " · " + info.os;
        }
        // Update header env badge
        var modeText = document.getElementById("env-mode-text");
        if (modeText) {
            modeText.textContent = info.env + " Mode";
        }
    });

    if (window.lucide) {
        lucide.createIcons();
    }
});
