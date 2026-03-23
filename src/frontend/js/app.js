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
}

// ── Utilities ──

function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
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
