/* OpenClaw GUI - Frontend Logic (Structured UI, no terminal) */

// ── Global callbacks (called from Python Bridge) ──

window.onCheckEnvResults = function (results) {
    var container = document.getElementById("check-results");
    var summary = document.getElementById("result-summary");
    var loading = document.getElementById("check-loading");

    loading.style.display = "none";
    container.innerHTML = "";

    var passCount = 0;
    var failCount = 0;

    for (var i = 0; i < results.length; i++) {
        var item = results[i];
        var card = document.createElement("div");
        card.className = "status-card " + (item.installed ? "pass" : "fail");

        var icon = item.installed ? "check-circle" : "x-circle";
        var statusLabel = item.installed ? "PASS" : "FAIL";
        if (!item.required && !item.installed) {
            card.className = "status-card warn";
            icon = "alert-triangle";
            statusLabel = "WARN";
        }

        var versionHtml = item.version
            ? '<span class="card-version">v' + escapeHtml(item.version) + "</span>"
            : "";

        card.innerHTML =
            '<div class="card-left">' +
            '  <i data-lucide="' + icon + '" class="card-icon"></i>' +
            '  <div class="card-info">' +
            '    <div class="card-name">' + escapeHtml(item.name) + versionHtml + "</div>" +
            '    <div class="card-message">' + escapeHtml(item.message) + "</div>" +
            "  </div>" +
            "</div>" +
            '<div class="card-status">' + statusLabel + "</div>";

        container.appendChild(card);

        if (item.installed) {
            passCount++;
        } else if (item.required) {
            failCount++;
        }
    }

    // Re-render lucide icons for new elements
    if (window.lucide) {
        lucide.createIcons();
    }

    // Show summary
    summary.style.display = "block";
    if (failCount === 0) {
        summary.className = "result-summary success";
        summary.innerHTML =
            '<i data-lucide="check-circle" style="width:18px;height:18px"></i> ' +
            "All checks passed (" + passCount + "/" + results.length + ")";
    } else {
        summary.className = "result-summary failure";
        summary.innerHTML =
            '<i data-lucide="alert-circle" style="width:18px;height:18px"></i> ' +
            failCount + " check(s) failed, " + passCount + " passed";
    }

    if (window.lucide) {
        lucide.createIcons();
    }
};

window.onCheckEnvError = function (errorMessage) {
    var container = document.getElementById("check-results");
    var loading = document.getElementById("check-loading");
    var summary = document.getElementById("result-summary");

    loading.style.display = "none";
    container.innerHTML = "";

    summary.style.display = "block";
    summary.className = "result-summary failure";
    summary.innerHTML =
        '<i data-lucide="alert-circle" style="width:18px;height:18px"></i> ' +
        "Error: " + escapeHtml(errorMessage);

    if (window.lucide) {
        lucide.createIcons();
    }
};

// ── Actions ──

function startCheckEnv() {
    var container = document.getElementById("check-results");
    var summary = document.getElementById("result-summary");
    var loading = document.getElementById("check-loading");

    container.innerHTML = "";
    summary.style.display = "none";
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
        document.getElementById("badge-os").textContent = "OS: " + info.os;
        document.getElementById("badge-env").textContent = "Env: " + info.env;
    });

    if (window.lucide) {
        lucide.createIcons();
    }
});
