#!/usr/bin/env bash
# ============================================================
# check-env-native.sh — 環境檢查腳本（Ubuntu 原生版）
#
# 用法：./scripts/check-env-native.sh
#
# 此腳本會檢查以下項目：
#   1. Node.js（≥18）
#   2. openclaw CLI
#   3. jq
#   4. VS Code
#   5. ngrok
#   6. systemd service（提示性）
#   7. 複製 .env.example → .env（若 .env 不存在）
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common-native.sh"
set +e  # 環境檢查時不中斷

all_passed=true

echo ""
printf '\033[36m========================================\033[0m\n'
printf '\033[36m  OpenClaw 環境檢查工具（原生版）\033[0m\n'
printf '\033[36m========================================\033[0m\n'
echo ""

# ── 1. 檢查 Node.js ──────────────────────────────────────────
info "檢查 Node.js..."
if node_version=$(node --version 2>&1) && [[ $? -eq 0 ]]; then
    # 解析主版本號
    major_version=$(echo "$node_version" | grep -oP '(?<=v)\d+' | head -1) || true
    if [[ -n "$major_version" ]] && (( major_version >= 18 )); then
        ok "Node.js 已安裝 — $node_version"
    else
        warn "Node.js 版本過舊（$node_version），建議 ≥18"
        all_passed=false
    fi
else
    err "Node.js 未安裝。請先安裝 Node.js（建議 ≥18）："
    printf '\033[33m  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -\033[0m\n'
    printf '\033[33m  sudo apt-get install -y nodejs\033[0m\n'
    all_passed=false
fi

echo ""

# ── 2. 檢查 openclaw CLI ─────────────────────────────────────
info "檢查 openclaw CLI..."
if openclaw_version=$(openclaw --version 2>&1) && [[ $? -eq 0 ]]; then
    ok "openclaw CLI 已安裝 — $openclaw_version"
else
    err "openclaw CLI 未安裝或不在 PATH 中。"
    all_passed=false
fi

echo ""

# ── 3. 檢查 jq ───────────────────────────────────────────────
info "檢查 jq..."
if jq_version=$(jq --version 2>&1) && [[ $? -eq 0 ]]; then
    ok "jq 已安裝 — $jq_version"
else
    err "jq 未安裝。請先安裝：sudo apt-get install -y jq"
    all_passed=false
fi

echo ""

# ── 4. 檢查 VS Code ──────────────────────────────────────────
info "檢查 VS Code..."
if command -v code >/dev/null 2>&1; then
    code_version=$(code --version 2>/dev/null | head -1)
    if [[ "$code_version" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
        ok "VS Code 已安裝 — 版本 $code_version"
    else
        err "VS Code 無法辨識版本資訊"
        all_passed=false
    fi
else
    err "VS Code 未安裝。請參考 https://code.visualstudio.com/ 進行安裝。"
    all_passed=false
fi

echo ""

# ── 5. 檢查 ngrok ────────────────────────────────────────────
info "檢查 ngrok..."
if ngrok_version=$(ngrok version 2>&1) && [[ $? -eq 0 ]]; then
    ok "ngrok 已安裝 — $ngrok_version"
else
    err "ngrok 未安裝。請參考 https://ngrok.com/download 進行安裝。"
    all_passed=false
fi

echo ""

# ── 6. 檢查 systemd service（提示性）─────────────────────────
info "檢查 openclaw-gateway systemd 服務..."
if systemctl list-unit-files "$SERVICE_NAME.service" >/dev/null 2>&1; then
    svc_state=$(systemctl is-active "$SERVICE_NAME" 2>/dev/null) || true
    if [[ "$svc_state" == "active" ]]; then
        ok "openclaw-gateway 服務已設定且正在執行"
    elif [[ "$svc_state" == "inactive" ]]; then
        warn "openclaw-gateway 服務已設定但未啟動"
    else
        warn "openclaw-gateway 服務狀態：$svc_state"
    fi
else
    warn "openclaw-gateway systemd 服務尚未設定（可稍後透過 init 建立）"
fi

# ── 7. 複製 .env.example → .env ──────────────────────────────
echo ""
info "檢查 .env 檔案..."
env_example="$PROJECT_ROOT/.env.example"
env_file="$PROJECT_ROOT/.env"
if [[ ! -f "$env_file" ]]; then
    if [[ -f "$env_example" ]]; then
        cp "$env_example" "$env_file"
        ok "已從 .env.example 複製建立 .env"
    else
        err ".env.example 不存在，請手動建立 .env 檔案。"
        all_passed=false
    fi
else
    ok ".env 已存在"
fi

# ── 結果摘要 ──────────────────────────────────────────────────
echo ""
printf '\033[36m========================================\033[0m\n'
if $all_passed; then
    ok "所有軟體皆已安裝，環境準備就緒！"
else
    err "部分軟體缺少或未啟動，請依照上方提示完成安裝。"
fi
printf '\033[36m========================================\033[0m\n'
echo ""
