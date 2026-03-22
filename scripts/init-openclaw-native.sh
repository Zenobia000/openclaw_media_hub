#!/usr/bin/env bash
# ============================================================
# init-openclaw-native.sh — 初始化 OpenClaw 環境（Ubuntu 原生版）
#
# 用法：./scripts/init-openclaw-native.sh
#
# 流程：
#   1. 檢查 openclaw CLI
#   2. 建立目錄結構與設定檔
#   3. 啟動 openclaw-gateway（systemd）
#   4. 設定 API 金鑰（可多組）
#   5. 語音轉文字（偵測 OpenAI 金鑰自動啟用）
#   6. Dashboard 連線資訊與裝置配對
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common-native.sh"

# ── 輔助函式 ──────────────────────────────────────────────────

# 讀取 openclaw.json
read_config() {
    cat "$CONFIG_FILE"
}

# 寫入 openclaw.json
save_config() {
    local data="$1"
    echo "$data" > "$CONFIG_FILE"
}

# 顯示裝置配對手動指令
show_pairing_hint() {
    local id="${1:-}"
    if [[ -n "$id" ]]; then
        printf '\033[33m  openclaw devices approve %s\033[0m\n' "$id"
    else
        printf '\033[33m  openclaw devices list\033[0m\n'
        printf '\033[33m  openclaw devices approve <ID>\033[0m\n'
    fi
}

# ── 1. 檢查 openclaw CLI ─────────────────────────────────────

info "檢查 openclaw CLI..."
if command -v openclaw >/dev/null 2>&1; then
    ok "openclaw CLI 已安裝"
else
    err "openclaw CLI 未安裝或不在 PATH 中，請先安裝。"
    exit 1
fi

# ── 2. 建立目錄結構與設定檔 ───────────────────────────────────

info "初始化 .openclaw 目錄..."

# 若 .openclaw 存在但不是目錄（例如誤建為檔案），先移除
if [[ -e "$OPENCLAW_DIR" && ! -d "$OPENCLAW_DIR" ]]; then
    warn ".openclaw 存在但不是目錄，將其移除後重新建立。"
    rm -f "$OPENCLAW_DIR"
fi

for dir in \
    "$OPENCLAW_DIR" \
    "$OPENCLAW_DIR/agents" \
    "$OPENCLAW_DIR/agents/main" \
    "$OPENCLAW_DIR/agents/main/agent" \
    "$OPENCLAW_DIR/workspace" \
    "$OPENCLAW_DIR/workspace/skills"; do
    if ! mkdir -p "$dir"; then
        err "無法建立目錄：$dir"
        exit 1
    fi
done
ok "目錄結構就緒"

if [[ ! -f "$CONFIG_FILE" ]]; then
    cat > "$CONFIG_FILE" <<'EOF'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
EOF
    ok "建立 openclaw.json"
fi

echo ""
ok "初始化完成"

# ── 3. 啟動 openclaw-gateway（systemd）────────────────────────

echo ""
info "啟動 openclaw-gateway 服務..."
if systemctl is-active "$SERVICE_NAME" >/dev/null 2>&1; then
    ok "openclaw-gateway 服務已在執行中"
else
    if sudo systemctl start "$SERVICE_NAME" 2>/dev/null; then
        ok "openclaw-gateway 服務已啟動"
    else
        warn "systemd 服務啟動失敗，嘗試直接啟動 Gateway..."
        openclaw gateway &
        ok "openclaw gateway 已背景啟動（PID: $!）"
    fi
fi

echo ""
if ! wait_gateway "等待 Gateway 啟動"; then
    err "Gateway 未就緒，請檢查服務狀態。"
    exit 1
fi

# ── 4. 設定 API 金鑰 ─────────────────────────────────────────

while true; do
    echo ""

    # 顯示已設定的金鑰摘要
    key_count=0
    if [[ -f "$CONFIG_FILE" ]]; then
        key_count=$(jq -r '.auth.profiles // {} | keys | length' "$CONFIG_FILE" 2>/dev/null || echo 0)
    fi

    if ((key_count > 0)); then
        ok "已設定 ${key_count} 組 API 金鑰："
        jq -r '.auth.profiles | to_entries[] | "  * \(.key)（\(.value.provider), \(.value.mode)）"' "$CONFIG_FILE" 2>/dev/null | while IFS= read -r line; do
            printf '\033[36m%s\033[0m\n' "$line"
        done
    else
        info "尚未設定 API 金鑰。"
    fi

    echo ""
    if ! confirm_yes_no "是否要設定 API 金鑰？"; then break; fi

    echo ""
    info "啟動設定精靈..."
    echo ""
    openclaw configure --section model
done

# ── 5. 語音轉文字（偵測 OpenAI 金鑰自動啟用）─────────────────

echo ""
auth_file="$OPENCLAW_DIR/agents/main/agent/auth-profiles.json"
openai_profile=""
if [[ -f "$auth_file" ]]; then
    openai_profile=$(jq -r '
        .profiles | to_entries[]
        | select(.value.provider == "openai")
        | .key
    ' "$auth_file" 2>/dev/null | head -1) || true
fi

if [[ -n "$openai_profile" ]]; then
    info "偵測到 OpenAI profile：${openai_profile}，啟用語音轉文字..."
    config=$(read_config)
    updated=$(echo "$config" | jq --arg profile "$openai_profile" '
        .tools //= {} |
        .tools.media = {
            "audio": {
                "enabled": true,
                "language": "zh",
                "models": [
                    {
                        "provider": "openai",
                        "model": "whisper-1",
                        "profile": $profile
                    }
                ],
                "echoTranscript": true
            }
        }
    ') || true
    if [[ -n "$updated" ]]; then
        save_config "$updated"
        ok "語音轉文字已啟用（profile=${openai_profile}）"
    else
        err "語音設定寫入失敗"
    fi
else
    info "未偵測到 OpenAI 金鑰，略過語音轉文字。"
fi

# 重啟套用設定
if ! restart_and_wait "套用設定"; then
    err "Gateway 未就緒，請檢查服務狀態。"
    exit 1
fi

# ── 6. Dashboard 連線資訊與裝置配對 ──────────────────────────

echo ""
token=""
if [[ -f "$CONFIG_FILE" ]]; then
    token=$(jq -r '.gateway.auth.token // empty' "$CONFIG_FILE" 2>/dev/null) || true
fi

printf '\033[36m============================================================\033[0m\n'
printf '\033[36m  Dashboard 連線資訊\033[0m\n'
printf '\033[36m============================================================\033[0m\n'
if [[ -n "$token" ]]; then
    echo ""
    printf '\033[36m  URL  : http://127.0.0.1:18789/\033[0m\n'
    printf '\033[36m  Token: %s\033[0m\n' "$token"
    echo ""
else
    warn "Token 未取得，請查看 openclaw.json 的 gateway.auth.token。"
    echo ""
fi
printf '\033[36m============================================================\033[0m\n'
echo ""
info "Gateway 綁定 0.0.0.0，瀏覽器首次連線需配對審批。"
echo ""

if confirm_yes_no "是否要進行裝置配對？"; then
    info "等待瀏覽器連線..."
    request_id=""
    for ((w = 0; w < 60; w += 3)); do
        output=$(openclaw devices list 2>&1) || true
        if echo "$output" | grep -qP 'Pending \(\d+\)'; then
            pending_count=$(echo "$output" | grep -oP 'Pending \(\K\d+' | head -1) || true
            if [[ -n "$pending_count" ]] && ((pending_count > 0)); then
                request_id=$(echo "$output" | grep -oP '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1) || true
                if [[ -n "$request_id" ]]; then break; fi
            fi
        fi
        sleep 3
        if ((w % 15 == 0 && w > 0)); then info "等待中...（${w} 秒）"; fi
    done

    if [[ -n "$request_id" ]]; then
        info "配對請求：${request_id}"
        if invoke_gateway devices approve "$request_id"; then
            ok "配對完成！請重新整理瀏覽器。"
        else
            err "配對失敗，請手動執行："
            show_pairing_hint "$request_id"
        fi
    else
        warn "等待逾時，請手動執行："
        show_pairing_hint
    fi
else
    info "略過配對。稍後可手動執行："
    show_pairing_hint
fi
