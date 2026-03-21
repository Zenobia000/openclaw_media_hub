#!/usr/bin/env bash
# ============================================================
# init-openclaw.sh — 初始化 .openclaw 目錄結構與插件設定
#
# 用法：./scripts/init-openclaw.sh
#
# 流程：
#   1. 建立 .openclaw 目錄結構
#   2. 產生 openclaw.json（Gateway 設定）
#   3. 啟動 Docker Compose
#   4. 設定 API 金鑰（可多組，迴圈詢問）
#   5. 啟用語音轉文字（OpenAI Whisper）
#   6. 裝置配對
#
# 相依工具：bash 4+, docker, curl, jq
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

# 0. 檢查相依工具（jq 缺少時自動安裝）
for cmd in docker curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        if [[ "$cmd" == "jq" ]]; then
            info "找不到 jq，嘗試自動安裝..."
            if command -v apt-get &>/dev/null; then
                sudo apt-get update -qq && sudo apt-get install -y -qq jq
            elif command -v yum &>/dev/null; then
                sudo yum install -y jq
            elif command -v apk &>/dev/null; then
                sudo apk add --no-cache jq
            else
                err "無法自動安裝 jq，請手動安裝：sudo apt-get install jq"
                exit 1
            fi
            if ! command -v jq &>/dev/null; then
                err "jq 安裝失敗，請手動安裝。"
                exit 1
            fi
            ok "jq 已自動安裝"
        else
            err "找不到必要工具：$cmd，請先安裝。"
            exit 1
        fi
    fi
done

info "檢查 Docker 是否正在執行..."
if docker info >/dev/null 2>&1; then
    ok "Docker 已啟動"
else
    err "Docker 未啟動或未安裝。請先開啟 Docker Desktop 再執行此腳本。"
    exit 1
fi

# 1. 建立目錄結構
info "開始初始化 .openclaw 目錄結構..."
info "目標路徑：$OPENCLAW_DIR"

dirs=(
    "$OPENCLAW_DIR"
    "$OPENCLAW_DIR/agents/main/agent"
    "$OPENCLAW_DIR/workspace"
    "$OPENCLAW_DIR/workspace/skills"
)

for dir in "${dirs[@]}"; do
    rel="${dir#"$PROJECT_ROOT"/}"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        ok "建立目錄：$rel"
    else
        info "目錄已存在：$rel（略過）"
    fi
done

# 2. 產生 openclaw.json
if [[ ! -f "$CONFIG_FILE" ]]; then
    cat > "$CONFIG_FILE" <<'JSON'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
JSON
    ok "建立設定檔：.openclaw/openclaw.json（mode=local, bind=0.0.0.0）"
else
    info "設定檔已存在：.openclaw/openclaw.json（略過）"
fi

echo ""
ok "初始化完成！"

# 3. 啟動 Docker Compose
echo ""
info "正在啟動 Docker Compose 服務..."
if docker compose up -d; then
    ok "Docker Compose 服務已啟動"
else
    err "無法啟動 Docker Compose 服務"
    exit 1
fi

echo ""
if ! wait_gateway "等待 Gateway 啟動"; then
    err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
fi

# 4. 設定 API 金鑰（迴圈，可設定多組）
while true; do
    echo ""
    # 顯示目前已設定的 API 金鑰摘要
    if [[ -f "$CONFIG_FILE" ]]; then
        profile_count=$(jq -r '.auth.profiles // {} | keys | length' "$CONFIG_FILE" 2>/dev/null || echo "0")
        if ((profile_count > 0)); then
            ok "目前已設定 $profile_count 組 API 金鑰："
            jq -r '.auth.profiles | to_entries[] | "  • \(.key) （Provider: \(.value.provider), 模式: \(.value.mode)）"' "$CONFIG_FILE" 2>/dev/null | while IFS= read -r line; do
                printf '\033[36m%s\033[0m\n' "$line"
            done
        else
            info "目前尚未設定任何 API 金鑰。"
        fi
    fi

    echo ""
    if ! confirm_yes_no "是否要設定 AI 模型的 API 金鑰？（如 Anthropic Claude、OpenAI 等）"; then
        break
    fi

    echo ""
    info "即將啟動 openclaw 內建設定精靈，請依照提示選擇 Provider 並完成設定。"
    echo ""
    # 使用 -it 以支援互動式精靈
    docker compose exec openclaw-gateway openclaw configure --section model
done

# 5. 語音轉文字功能（偵測到 OpenAI API 金鑰時自動啟用）
echo ""
auth_profiles_file="$OPENCLAW_DIR/agents/main/agent/auth-profiles.json"
openai_profile=""
if [[ -f "$auth_profiles_file" ]]; then
    openai_profile=$(jq -r '.profiles | to_entries[] | select(.value.provider == "openai") | .key' "$auth_profiles_file" 2>/dev/null | head -1)
fi
if [[ -n "$openai_profile" ]]; then
    info "偵測到 OpenAI profile：$openai_profile，自動啟用語音轉文字功能..."
    if jq --arg profile "$openai_profile" '.tools //= {} |
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
        }' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"; then
        ok "語音轉文字功能已啟用（language=zh, model=whisper-1, profile=$openai_profile）"
    else
        err "無法寫入語音設定"
        rm -f "${CONFIG_FILE}.tmp"
    fi
else
    info "未偵測到 OpenAI API 金鑰，略過語音轉文字功能。"
fi

# 重啟以套用設定
if ! restart_and_wait "套用設定"; then
    err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
fi

# 讀取 Dashboard Token
echo ""
info "正在讀取 Dashboard Token..."
dashboard_token=""
if [[ -f "$CONFIG_FILE" ]]; then
    dashboard_token=$(jq -r '.gateway.auth.token // empty' "$CONFIG_FILE" 2>/dev/null || true)
fi
if [[ -n "$dashboard_token" ]]; then
    ok "Dashboard Token 已取得"
else
    err "無法讀取 Token"
    warn "您可手動查看 .openclaw/openclaw.json 中的 gateway.auth.token 欄位。"
fi

# 6. 裝置配對
echo ""
printf '\033[36m============================================================\033[0m\n'
printf '\033[36m  Dashboard 連線資訊\033[0m\n'
printf '\033[36m============================================================\033[0m\n'
if [[ -n "$dashboard_token" ]]; then
    echo ""
    printf '\033[36m  URL  : http://127.0.0.1:18789/\033[0m\n'
    printf '\033[36m  Token: %s\033[0m\n' "$dashboard_token"
    echo ""
else
    warn "  Token 未取得，請手動查看 .openclaw/openclaw.json 中的 gateway.auth.token 欄位。"
    echo ""
fi
printf '\033[36m============================================================\033[0m\n'
echo ""
info "裝置配對流程 — 由於 Gateway 綁定 0.0.0.0，瀏覽器首次連線需配對審批。"
info "請在瀏覽器開啟上方 URL，並使用 Token 登入。"
echo ""

if confirm_yes_no "是否要現在進行裝置配對？"; then
    info "等待瀏覽器連線產生配對請求..."
    request_id=""
    for ((w = 0; w < 60; w += 3)); do
        list_output=$(docker compose exec openclaw-gateway openclaw devices list 2>&1 || true)
        if echo "$list_output" | grep -qP 'Pending \(\d+\)'; then
            pending_count=$(echo "$list_output" | grep -oP 'Pending \(\K\d+' || echo "0")
            if ((pending_count > 0)); then
                request_id=$(echo "$list_output" | grep -oP '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -1)
                [[ -n "$request_id" ]] && break
            fi
        fi
        sleep 3
        if ((w > 0 && w % 15 == 0)); then
            info "仍在等待瀏覽器連線...（已等待 ${w} 秒）"
        fi
    done

    if [[ -n "$request_id" ]]; then
        info "偵測到配對請求：$request_id"
        if invoke_gateway devices approve "$request_id"; then
            ok "裝置配對完成！請重新整理瀏覽器頁面。"
        else
            err "配對審批失敗，請手動執行："
            printf '\033[33m  docker compose exec openclaw-gateway openclaw devices approve %s\033[0m\n' "$request_id"
        fi
    else
        warn "等待逾時，未偵測到配對請求。您可稍後手動執行："
        printf '\033[33m  docker compose exec openclaw-gateway openclaw devices list\033[0m\n'
        printf '\033[33m  docker compose exec openclaw-gateway openclaw devices approve <Request ID>\033[0m\n'
    fi
else
    info "略過裝置配對。您可稍後手動執行："
    printf '\033[33m  docker compose exec openclaw-gateway openclaw devices list\033[0m\n'
    printf '\033[33m  docker compose exec openclaw-gateway openclaw devices approve <Request ID>\033[0m\n'
fi
