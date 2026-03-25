/**
 * OpenClaw GUI — Frontend Application
 *
 * 監聽 pywebviewready 事件後呼叫 Bridge API 確認連線。
 */

async function checkBridge() {
  const statusDot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");

  try {
    const result = await window.pywebview.api.ping();
    if (result && result.success) {
      statusDot.className = "w-2.5 h-2.5 rounded-full bg-status-success";
      statusText.textContent = "Bridge Connected";
    } else {
      statusDot.className = "w-2.5 h-2.5 rounded-full bg-status-error";
      statusText.textContent = "Bridge Error";
    }
  } catch (err) {
    statusDot.className = "w-2.5 h-2.5 rounded-full bg-status-error";
    statusText.textContent = "Bridge Unavailable";
  }
}

window.addEventListener("pywebviewready", checkBridge);
