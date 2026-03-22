#!/usr/bin/env bash
# ============================================================
# install-plugins-native.sh — 安裝與設定 OpenClaw 插件 (LINE / Discord)（Ubuntu 原生版）
#
# 用法：./scripts/install-plugins-native.sh
#
# 流程：
#   1. 安裝 LINE 插件
#   2. 安裝 Discord 插件
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common-native.sh"

# ── 寫入頻道設定到 openclaw.json（使用 jq）───────────────────

set_channel_config() {
    local channel="$1"
    local settings_json="$2"

    if ! command -v jq &>/dev/null; then
        err "需要 jq 工具來寫入設定。請先安裝：sudo apt install jq"
        return 1
    fi

    local tmp_file
    tmp_file=$(mktemp)
    if jq --arg ch "$channel" --argjson settings "$settings_json" \
        '.channels[$ch] = $settings' "$CONFIG_FILE" > "$tmp_file"; then
        mv "$tmp_file" "$CONFIG_FILE"
        ok "$channel 設定已寫入 .openclaw/openclaw.json"
        return 0
    else
        rm -f "$tmp_file"
        err "無法寫入 ${channel} 設定"
        return 1
    fi
}

# ── 啟動 ngrok tunnel ────────────────────────────────────────

start_ngrok_tunnel() {
    echo ""
    info "LINE Webhook 需要公開 HTTPS URL，正在檢查 ngrok..."

    if ! command -v ngrok &>/dev/null; then
        err "未偵測到 ngrok。請先安裝：https://ngrok.com/download"
        printf '\033[33m  安裝後執行 '\''ngrok config add-authtoken <你的token>'\'' 完成設定\033[0m\n'
        return
    fi

    # 檢查是否已有 tunnel
    local ngrok_url=""
    local api_resp
    if api_resp=$(curl -s --max-time 3 "http://127.0.0.1:4040/api/tunnels" 2>/dev/null); then
        ngrok_url=$(echo "$api_resp" | jq -r \
            '[.tunnels[] | select(.config.addr | test("18789")) | select(.proto == "https")] | .[0].public_url // empty' 2>/dev/null || true)
        if [[ -n "$ngrok_url" ]]; then
            info "偵測到已存在的 tunnel：$ngrok_url"
        fi
    fi

    if [[ -z "$ngrok_url" ]]; then
        info "正在背景啟動 ngrok http 18789..."
        ngrok http 18789 &>/dev/null &
        for (( i=0; i<10; i++ )); do
            sleep 2
            if api_resp=$(curl -s --max-time 3 "http://127.0.0.1:4040/api/tunnels" 2>/dev/null); then
                ngrok_url=$(echo "$api_resp" | jq -r \
                    '[.tunnels[] | select(.proto == "https")] | .[0].public_url // empty' 2>/dev/null || true)
                if [[ -n "$ngrok_url" ]]; then break; fi
            fi
        done
        if [[ -n "$ngrok_url" ]]; then
            ok "ngrok tunnel 已啟動"
        else
            err "ngrok 未在 20 秒內就緒，請手動執行 'ngrok http 18789'"
            return
        fi
    fi

    local webhook_url="$ngrok_url/line/webhook"
    echo ""
    printf '\033[32m============================================================\033[0m\n'
    printf '\033[32m  LINE Webhook URL（請複製）\033[0m\n'
    printf '\033[32m============================================================\033[0m\n'
    echo ""
    printf '\033[33m  %s\033[0m\n' "$webhook_url"
    echo ""
    printf '\033[32m============================================================\033[0m\n'
    echo ""
    info "請至 LINE Developers Console 設定 Webhook URL："
    printf '\033[36m  1. 開啟 https://developers.line.biz/console/\033[0m\n'
    printf '\033[36m  2. 選擇 Provider → Channel → Messaging API settings\033[0m\n'
    printf '\033[36m  3. 貼上 Webhook URL，開啟 Use webhook，點擊 Verify\033[0m\n'
    echo ""
    printf '完成上述設定後，按 Enter 繼續'
    read -r

    # ── Webhook 驗證結果檢查迴圈 ──
    local verified=false
    while [[ "$verified" != "true" ]]; do
        echo ""
        info "正在檢查 Webhook 驗證結果..."

        local latest_status=""
        local inspect_data
        if inspect_data=$(curl -s --max-time 5 "http://127.0.0.1:4040/api/requests/http" 2>/dev/null); then
            latest_status=$(echo "$inspect_data" | jq -r \
                '[.requests[] | select(.request.uri | test("/line/webhook"))] | .[0].response.status // empty' 2>/dev/null || true)
        fi

        if [[ -z "$latest_status" ]]; then
            warn "未偵測到 Webhook 驗證請求。"
            info "如果您已在 LINE Console 完成驗證且顯示成功，可直接繼續。"
            if ! confirm_yes_no "是否重新檢查？"; then verified=true; fi
            continue
        fi

        # 解析 HTTP 狀態碼（支援 "401 Unauthorized" 或純數字）
        local status_code
        if [[ "$latest_status" =~ ([0-9]{3}) ]]; then
            status_code="${BASH_REMATCH[1]}"
        else
            status_code=0
        fi

        if [[ "$status_code" -eq 200 ]]; then
            ok "LINE Webhook 驗證成功！"
            verified=true

        elif [[ "$status_code" -eq 401 ]]; then
            err "LINE Webhook 驗證失敗：$latest_status"
            echo ""
            warn "這通常表示 Channel Access Token 或 Channel Secret 設定不正確。"
            warn "請確認您在 LINE Developers Console 複製的是正確的值。"
            echo ""
            printf '\033[36m  1. 重新輸入 LINE 憑證並重試驗證\033[0m\n'
            printf '\033[36m  2. 略過驗證，繼續後續流程\033[0m\n'
            echo ""
            printf '請選擇 (1/2): '
            read -r choice

            if [[ "$choice" == "1" ]]; then
                printf '請重新輸入 Channel Access Token: '
                read -r new_token
                printf '請重新輸入 Channel Secret: '
                read -r new_secret

                if [[ -z "${new_token// /}" || -z "${new_secret// /}" ]]; then
                    warn "憑證不可為空，請重試。"
                    continue
                fi

                local settings_json
                settings_json=$(jq -n \
                    --arg token "$new_token" \
                    --arg secret "$new_secret" \
                    '{enabled: true, channelAccessToken: $token, channelSecret: $secret, dmPolicy: "open"}')
                set_channel_config "line" "$settings_json"
                if ! restart_and_wait "套用新的 LINE 憑證"; then
                    err "Gateway 未就緒，請手動檢查服務狀態。"
                    verified=true
                    continue
                fi
                echo ""
                info "請再次至 LINE Developers Console 點擊 Verify 按鈕"
                printf '驗證後按 Enter 繼續'
                read -r
            else
                info "略過 Webhook 驗證。"
                verified=true
            fi

        else
            err "LINE Webhook 驗證失敗：HTTP $status_code"
            warn "請檢查 Gateway 服務是否正常運作。"
            if ! confirm_yes_no "是否重試？"; then verified=true; fi
        fi
    done
}

# ── 插件安裝完整流程（安裝 → 設定 → 重啟 → 配對）─────────────
#
# 用法:
#   install_plugin <Name> <Package> <Channel> <credential_keys> <credential_prompts> <build_config_fn>

install_plugin() {
    local name="$1"
    local package="$2"
    local channel="$3"
    local cred_keys_str="$4"
    local cred_prompts_str="$5"
    local build_config_fn="$6"

    echo ""
    if ! confirm_yes_no "是否要安裝 $name 插件？"; then
        info "略過 $name 插件安裝。您可稍後手動執行："
        printf '\033[33m  openclaw plugins install %s\033[0m\n' "$package"
        return
    fi

    # 安裝插件
    info "正在安裝 $name 插件 ($package)..."
    if invoke_gateway plugins install "$package"; then
        ok "$name 插件安裝完成"
    else
        warn "$name 插件安裝失敗。您可稍後手動執行："
        printf '\033[33m  openclaw plugins install %s\033[0m\n' "$package"
    fi

    # 收集憑證
    echo ""
    info "設定 $name 資訊..."

    IFS=',' read -ra cred_keys    <<< "$cred_keys_str"
    IFS=',' read -ra cred_prompts <<< "$cred_prompts_str"

    declare -A creds
    local has_empty=false
    for (( idx=0; idx<${#cred_keys[@]}; idx++ )); do
        local key="${cred_keys[$idx]}"
        local prompt="${cred_prompts[$idx]}"
        printf '%s: ' "$prompt"
        read -r value
        creds["$key"]="$value"
        if [[ -z "${value// /}" ]]; then
            has_empty=true
        fi
    done

    if [[ "$has_empty" == "true" ]]; then
        warn "部分欄位為空，略過設定。您可稍後手動編輯 .openclaw/openclaw.json"
    else
        local settings_json
        settings_json=$("$build_config_fn" "$(declare -p creds)")
        set_channel_config "$channel" "$settings_json"
    fi

    # 重啟以套用插件設定
    restart_and_wait "套用 $name 插件設定" || true

    # ngrok（僅 LINE 需要）
    if [[ "$channel" == "line" ]]; then
        start_ngrok_tunnel
    fi

    # 配對流程
    echo ""
    info "$name 配對流程："
    printf '\033[36m  1. 傳送任意訊息給 %s Bot\033[0m\n' "$name"
    printf '\033[36m  2. Bot 會回傳一組配對碼\033[0m\n'
    echo ""
    local code
    code=$(read_non_empty "取得配對碼後輸入（輸入 n 略過）")

    if [[ "$code" != "n" && "$code" != "N" ]]; then
        info "正在執行 $name 配對審批..."
        if invoke_gateway pairing approve "$channel" "$code"; then
            ok "$name 配對完成！"
        else
            err "$name 配對失敗，請手動執行："
            printf '\033[33m  openclaw pairing approve %s <配對碼>\033[0m\n' "$channel"
        fi
    else
        info "略過 $name 配對。您可稍後手動執行："
        printf '\033[33m  openclaw pairing approve %s <配對碼>\033[0m\n' "$channel"
    fi
}

# ── Build-config 函式：LINE ───────────────────────────────────

build_line_config() {
    eval "$1"  # 還原 associative array
    jq -n \
        --arg token  "${creds[channelAccessToken]}" \
        --arg secret "${creds[channelSecret]}" \
        '{enabled: true, channelAccessToken: $token, channelSecret: $secret, dmPolicy: "open"}'
}

# ── Build-config 函式：Discord ────────────────────────────────

build_discord_config() {
    eval "$1"  # 還原 associative array
    jq -n \
        --arg token "${creds[token]}" \
        '{enabled: true, token: $token, groupPolicy: "allowlist", dmPolicy: "open", streaming: "off"}'
}

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

echo ""
info "開始安裝與設定 OpenClaw 插件..."

# LINE 插件
install_plugin \
    "LINE" \
    "@openclaw/line" \
    "line" \
    "channelAccessToken,channelSecret" \
    "請輸入 Channel Access Token,請輸入 Channel Secret" \
    build_line_config

# Discord 插件
install_plugin \
    "Discord" \
    "@openclaw/discord" \
    "discord" \
    "token" \
    "請輸入 Discord Bot Token" \
    build_discord_config

echo ""
ok "插件安裝與設定流程結束！"
