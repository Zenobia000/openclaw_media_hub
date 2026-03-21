#!/usr/bin/env bash
# ============================================================
# check-env.sh — 環境檢查腳本
#
# 用法：./scripts/check-env.sh
#
# 此腳本會檢查以下軟體是否已安裝：
#   1. Docker
#   2. VS Code
#   3. ngrok
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
set +e  # 環境檢查時不中斷

all_passed=true

echo ""
printf '\033[36m========================================\033[0m\n'
printf '\033[36m  OpenClaw 環境檢查工具\033[0m\n'
printf '\033[36m========================================\033[0m\n'
echo ""

# ── 1. 檢查 Docker ───────────────────────────────────────────
info "檢查 Docker..."
if docker_version=$(docker --version 2>&1) && [[ $? -eq 0 ]]; then
    ok "Docker 已安裝 — $docker_version"

    # 進一步檢查 Docker 是否正在執行
    if docker info >/dev/null 2>&1; then
        ok "Docker Desktop 正在執行"
    else
        err "Docker 已安裝但未啟動，請開啟 Docker Desktop"
        all_passed=false
    fi
else
    err "Docker 未安裝。請參考 1.軟體安裝指引/1.Docker軟體 進行安裝。"
    all_passed=false
fi

echo ""

# ── 2. 檢查 VS Code ──────────────────────────────────────────
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
    err "VS Code 未安裝。請參考 1.軟體安裝指引/2.VS Code軟體 進行安裝。"
    all_passed=false
fi

echo ""

# ── 3. 檢查 ngrok ────────────────────────────────────────────
info "檢查 ngrok..."
if ngrok_version=$(ngrok version 2>&1) && [[ $? -eq 0 ]]; then
    ok "ngrok 已安裝 — $ngrok_version"
else
    err "ngrok 未安裝。請參考 1.軟體安裝指引/3.ngrok軟體 進行安裝。"
    all_passed=false
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
