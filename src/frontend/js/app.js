/* OpenClaw GUI - Frontend Logic */

// ── Global callbacks (called from Python Bridge) ──

window.onLogLine = function (line, level) {
    var body = document.getElementById("terminal-body");
    if (!body) return;
    var div = document.createElement("div");
    div.className = "log-line " + level;
    div.textContent = line;
    body.appendChild(div);
    body.scrollTop = body.scrollHeight;
};

window.onProcessComplete = function (exitCode) {
    var btnRun = document.getElementById("btn-run-check");
    var btnCancel = document.getElementById("btn-cancel");
    var summary = document.getElementById("result-summary");

    btnRun.disabled = false;
    btnCancel.disabled = true;

    summary.style.display = "block";
    if (exitCode === 0) {
        summary.className = "result-summary success";
        summary.textContent = "All checks passed successfully.";
    } else {
        summary.className = "result-summary failure";
        summary.textContent = "Some checks failed (exit code: " + exitCode + "). Review the output above.";
    }
};

// ── Actions ──

function startCheckEnv() {
    var terminal = document.getElementById("terminal");
    var body = document.getElementById("terminal-body");
    var btnRun = document.getElementById("btn-run-check");
    var btnCancel = document.getElementById("btn-cancel");
    var summary = document.getElementById("result-summary");

    terminal.style.display = "block";
    body.innerHTML = "";
    summary.style.display = "none";
    btnRun.disabled = true;
    btnCancel.disabled = false;

    window.pywebview.api.check_env().then(function (raw) {
        var result = JSON.parse(raw);
        if (!result.ok) {
            window.onLogLine("Error: " + result.error, "error");
            window.onProcessComplete(-1);
        }
    });
}

function cancelProcess() {
    window.pywebview.api.cancel_process().then(function (raw) {
        var result = JSON.parse(raw);
        if (result.ok) {
            window.onLogLine("Process cancelled by user.", "warn");
        }
    });
}

// ── Navigation ──

function navigateTo(viewName) {
    // Hide all views
    var views = document.querySelectorAll(".view");
    for (var i = 0; i < views.length; i++) {
        views[i].classList.remove("active");
    }
    // Show target view
    var target = document.getElementById("view-" + viewName);
    if (target) {
        target.classList.add("active");
    }

    // Update nav items
    var navItems = document.querySelectorAll(".nav-item");
    for (var i = 0; i < navItems.length; i++) {
        navItems[i].classList.remove("active");
        if (navItems[i].getAttribute("data-view") === viewName) {
            navItems[i].classList.add("active");
        }
    }
}

// ── Init ──

window.addEventListener("pywebviewready", function () {
    window.pywebview.api.get_platform_info().then(function (raw) {
        var info = JSON.parse(raw);
        document.getElementById("badge-os").textContent = "OS: " + info.os;
        document.getElementById("badge-env").textContent = "Env: " + info.env;
    });

    // Render lucide icons
    if (window.lucide) {
        lucide.createIcons();
    }
});
