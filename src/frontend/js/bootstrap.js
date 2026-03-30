/**
 * OpenClaw GUI — Bootstrap
 *
 * Bridge 整合與應用程式啟動
 */

/** Bridge 連線狀態回呼 */
window.updateConnectionStatus = function (status) {
  updateConnectionStatus(status);
};

/** 應用程式初始化 */
async function initApp() {
  const loadingDot = document.getElementById("loading-dot");
  const loadingText = document.getElementById("loading-text");

  try {
    const result = await window.pywebview.api.ping();
    if (result?.success) {
      // ── i18n: 載入語系偏好 ──
      let locale = "zh-TW";
      try {
        const lr = await window.pywebview.api.get_locale();
        if (lr?.success && lr.data?.locale) locale = lr.data.locale;
        else if (navigator.language?.startsWith("en")) locale = "en";
      } catch { if (navigator.language?.startsWith("en")) locale = "en"; }
      __i18n = (locale === "en" ? window.__locale_en : window.__locale_zhTW) || {};
      __i18nLocale = locale;
      document.documentElement.lang = locale;
      _i18nScanDOM();

      document.getElementById("app-loading").classList.add("hidden");
      document.getElementById("app-main").classList.remove("hidden");
      refreshIcons();

      try {
        const platform = await window.pywebview.api.detect_platform();
        if (platform?.data) updateSidebarMode(platform.data.current_mode || platform.data.suggested_mode || "docker-windows");
        else if (platform?.current_mode || platform?.suggested_mode) updateSidebarMode(platform.current_mode || platform.suggested_mode || "docker-windows");
      } catch { updateSidebarMode("docker-windows"); }

      navigateTo("dashboard");
    } else {
      throw new Error("Bridge returned unsuccessful response");
    }
  } catch {
    if (loadingDot) loadingDot.className = "w-2.5 h-2.5 rounded-full bg-status-error";
    if (loadingText) loadingText.textContent = t("loading.bridge_unavailable");
  }
}

window.addEventListener("pywebviewready", initApp);
