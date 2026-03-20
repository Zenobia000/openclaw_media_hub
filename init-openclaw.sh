#!/bin/bash
# ============================================================
# init-openclaw.sh — 初始化 .openclaw 目錄結構與插件設定
#
# 用法：./init-openclaw.sh
#
# 流程：
#   1. 建立 .openclaw 目錄結構
#   2. 部署技能（module_pack → workspace/skills）
#   3. 產生 openclaw.json（Gateway 設定）
#   4. 複製 .env.example → .env
#   5. 啟動 Docker Compose
#   6. 設定 API 金鑰（可多組，迴圈詢問）
#   7. 啟用語音轉文字（OpenAI Whisper）
#   8. 安裝插件（LINE / Discord）
#   9. 裝置配對
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_DIR="${SCRIPT_DIR}/.openclaw"
CONFIG_FILE="${OPENCLAW_DIR}/openclaw.json"
HEALTH_URL="http://127.0.0.1:18789/healthz"
SPIN_CHARS=('|' '/' '-' '\')

# ── ANSI color codes ────────────────────────────────────────
C_RESET='\033[0m'
C_BLUE='\033[0;34m'
C_GREEN='\033[0;32m'
C_YELLOW='\033[0;33m'
C_RED='\033[0;31m'
C_CYAN='\033[0;36m'
C_GRAY='\033[0;90m'

# ── Output helpers ──────────────────────────────────────────
write_info()  { echo -e "${C_BLUE}[INFO]  $1${C_RESET}"; }
write_ok()    { echo -e "${C_GREEN}[OK]    $1${C_RESET}"; }
write_warn()  { echo -e "${C_YELLOW}[WARN]  $1${C_RESET}"; }
write_err()   { echo -e "${C_RED}[ERROR] $1${C_RESET}"; }

# ── Y/n confirmation prompt ────────────────────────────────
confirm_yesno() {
    local prompt="$1"
    local answer
    read -r -p "$prompt (Y/n) " answer
    [[ "$answer" != "n" && "$answer" != "N" ]]
}

# ── Non-empty input prompt (supports 'n' to skip) ──────────
read_nonempty() {
    local prompt="$1"
    local value=""
    while true; do
        read -r -p "$prompt: " value
        if [[ -n "$value" ]]; then
            echo "$value"
            return
        fi
        write_warn "不可空白，請重新輸入或輸入 n 略過。"
    done
}

# ── Execute Gateway CLI command ─────────────────────────────
invoke_gateway() {
    docker compose exec openclaw-gateway openclaw "$@" > /dev/null 2>&1
    return $?
}

# ── Wait for Gateway health (with spinner) ──────────────────
wait_gateway() {
    local label="${1:-等待 Gateway 就緒}"
    local timeout="${2:-30}"

    echo -ne "${C_BLUE}[INFO]  ${label}... ${C_RESET}"
    for (( i=0; i<timeout; i++ )); do
        local spin_idx=$(( i % 4 ))
        echo -ne "\b${C_CYAN}${SPIN_CHARS[$spin_idx]}${C_RESET}"
        local health
        health=$(curl -s -m 2 "$HEALTH_URL" 2>/dev/null) || true
        if echo "$health" | grep -q '"ok":true'; then
            echo -e "\b "
            write_ok "${label} — 完成（${i} 秒）"
            return 0
        fi
        sleep 1
    done
    echo -e "\b "
    write_warn "${label} — 逾時（${timeout} 秒）"
    return 1
}

# ── Restart Docker Compose and wait ─────────────────────────
restart_and_wait() {
    local reason="${1:-套用設定}"
    echo ""
    write_info "正在重新啟動服務以${reason}..."
    if docker compose restart; then
        write_ok "服務已重新啟動"
    else
        write_err "無法重新啟動服務"
        return 1
    fi
    echo ""
    wait_gateway "等待 Gateway 重新就緒"
}

# ── Parse SKILL.md frontmatter ──────────────────────────────
get_skill_meta() {
    local path="$1"

    SKILL_EMOJI="📦"
    SKILL_DESC="(無描述)"

    # Extract YAML frontmatter between --- markers
    local frontmatter=""
    local in_frontmatter=false
    local found_start=false
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if $found_start; then break; else found_start=true; in_frontmatter=true; continue; fi
        fi
        if $in_frontmatter; then frontmatter+="$line"$'\n'; fi
    done < "$path"

    if [[ -z "$frontmatter" ]]; then return; fi

    # Extract emoji (supports nested e.g. metadata.openclaw.emoji)
    local emoji_val
    emoji_val=$(echo "$frontmatter" | sed -n 's/^[[:space:]]*emoji:[[:space:]]*\(.*\)/\1/p' | head -1 | sed "s/[\"']//g" | tr -d '[:space:]')
    if [[ -n "$emoji_val" ]]; then
        SKILL_EMOJI="$emoji_val"
    fi

    # Extract description: first line of content after "description:"
    # Handles: quoted multi-line, block scalar (|/>), single-line quoted/unquoted
    local desc_line
    desc_line=$(echo "$frontmatter" | grep -m1 '^description:' | sed 's/^description:[[:space:]]*//')

    if [[ "$desc_line" == "|" || "$desc_line" == ">" ]]; then
        # Block scalar: take first indented line
        desc_line=$(echo "$frontmatter" | sed -n '/^description:[[:space:]]*[|>]/,/^[^[:space:]]/{
            /^description:/d
            /^[^[:space:]]/d
            p
        }' | head -1 | sed 's/^[[:space:]]*//')
    else
        # Remove surrounding/leading quotes; handle unclosed multiline quotes
        desc_line=$(echo "$desc_line" | sed "s/^[\"']//;s/[\"']$//")
    fi

    if [[ -n "$desc_line" ]]; then
        SKILL_DESC="$desc_line"
    fi
}

# ── Interactive skill selector (TUI with arrow keys) ─────────
show_skill_selector() {
    # Uses parallel arrays: SKILL_NAMES, SKILL_EMOJIS, SKILL_DESCS,
    #   SKILL_SOURCES, SKILL_INSTALLED
    # Returns selected indices in SELECTED_INDICES array

    local count=${#SKILL_NAMES[@]}
    local -a selected=()
    for (( i=0; i<count; i++ )); do
        selected+=("${SKILL_INSTALLED[$i]}")
    done

    SELECTED_INDICES=()
    local cursor=0

    # total lines = 1(title) + 1(│) + count(items) + 1(│) + 1(hint) = count+4
    local total_lines=$(( count + 4 ))

    # Hide cursor, restore on exit/interrupt
    printf '\033[?25l'
    trap 'printf "\033[?25h"' EXIT INT TERM

    # Print initial blank lines to reserve space
    for (( i=0; i<total_lines; i++ )); do printf '\n'; done
    # Move cursor up to start position
    printf "\033[${total_lines}A"

    while true; do
        # Move to start of our drawing area
        printf '\033[0G'

        # Count selected
        local sel_count=0
        for (( i=0; i<count; i++ )); do
            [[ "${selected[$i]}" == "1" ]] && (( sel_count++ )) || true
        done

        # Draw title
        printf '\033[2K'
        printf "${C_CYAN}◆  OpenClaw 初始安裝技能工具${C_RESET}\n"
        printf '\033[2K'
        printf "│\n"

        # Draw skill list
        for (( i=0; i<count; i++ )); do
            printf '\033[2K'
            local check="◻"
            [[ "${selected[$i]}" == "1" ]] && check="◼"
            local tag=""
            [[ "${SKILL_INSTALLED[$i]}" == "1" ]] && tag=" (已安裝)"
            local desc="${SKILL_DESCS[$i]}"
            [[ ${#desc} -gt 50 ]] && desc="${desc:0:47}..."
            local color="${C_RESET}"
            if [[ $i -eq $cursor ]]; then
                color="${C_CYAN}"
            elif [[ "${SKILL_INSTALLED[$i]}" == "1" ]]; then
                color="${C_GRAY}"
            fi
            local pointer=" "
            [[ $i -eq $cursor ]] && pointer=">"
            printf "${color}│  ${pointer} ${check} ${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]} — ${desc}${tag}${C_RESET}\n"
        done

        # Draw footer
        printf '\033[2K'
        printf "│\n"
        printf '\033[2K'
        local status
        [[ $sel_count -gt 0 ]] && status="(已選 ${sel_count} 個)" || status="(未選擇任何技能)"
        printf "${C_GRAY}│  ↑/↓ 移動 • Space: 選取 • a: 全選 • n: 全不選 • Enter: 確認  ${status}${C_RESET}\n"

        # Move cursor back up to top of drawing area for next redraw
        printf "\033[${total_lines}A"

        # Read keypress
        local key
        IFS= read -rsn1 key

        case "$key" in
            $'\x1b')
                # Escape sequence (arrow keys)
                local seq
                IFS= read -rsn2 -t 0.1 seq
                case "$seq" in
                    '[A') # Up
                        (( cursor > 0 )) && (( cursor-- )) || true
                        ;;
                    '[B') # Down
                        (( cursor < count - 1 )) && (( cursor++ )) || true
                        ;;
                esac
                ;;
            ' ') # Space: toggle current
                if [[ "${selected[$cursor]}" == "1" ]]; then
                    selected[$cursor]="0"
                else
                    selected[$cursor]="1"
                fi
                ;;
            'a'|'A') # Select all
                for (( i=0; i<count; i++ )); do selected[$i]="1"; done
                ;;
            'n'|'N') # Deselect all
                for (( i=0; i<count; i++ )); do selected[$i]="0"; done
                ;;
            '') # Enter: confirm
                break
                ;;
        esac
    done

    # Move past drawing area
    printf "\033[${total_lines}B"

    # Show cursor
    printf '\033[?25h'

    # Build result
    for (( i=0; i<count; i++ )); do
        [[ "${selected[$i]}" == "1" ]] && SELECTED_INDICES+=("$i")
    done

    # Show summary
    printf '\033[2K'
    echo -e "${C_CYAN}◇  OpenClaw 初始安裝技能工具${C_RESET}"
    if [[ ${#SELECTED_INDICES[@]} -gt 0 ]]; then
        local names=""
        for idx in "${SELECTED_INDICES[@]}"; do
            [[ -n "$names" ]] && names+=", "
            names+="${SKILL_EMOJIS[$idx]} ${SKILL_NAMES[$idx]}"
        done
        echo -e "│  ${C_GREEN}已選擇: ${names}${C_RESET}"
    else
        echo -e "│  ${C_GRAY}未選擇任何技能${C_RESET}"
    fi
    echo ""
}

# ── Write channel config to openclaw.json ───────────────────
set_channel_config() {
    local channel="$1"
    local config_json="$2"  # JSON string for the channel settings

    if ! jq --arg ch "$channel" --argjson settings "$config_json" \
        '.channels[$ch] = $settings' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"; then
        write_err "無法寫入 ${channel} 設定"
        rm -f "${CONFIG_FILE}.tmp"
        return 1
    fi

    # Ensure .channels exists
    if ! jq 'has("channels")' "$CONFIG_FILE" | grep -q true; then
        jq '.channels = {}' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
        mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
    fi

    jq --arg ch "$channel" --argjson settings "$config_json" \
        '.channels[$ch] = $settings' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
    mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"

    write_ok "${channel} 設定已寫入 .openclaw/openclaw.json"
}

# ── Start ngrok tunnel ──────────────────────────────────────
start_ngrok_tunnel() {
    echo ""
    write_info "LINE Webhook 需要公開 HTTPS URL，正在檢查 ngrok..."

    if ! command -v ngrok &> /dev/null; then
        write_err "未偵測到 ngrok。請先安裝：https://ngrok.com/download"
        echo -e "  ${C_YELLOW}安裝後執行 'ngrok config add-authtoken <你的token>' 完成設定${C_RESET}"
        return
    fi

    # Check existing tunnel
    local ngrok_url=""
    local api_resp
    api_resp=$(curl -s -m 3 "http://127.0.0.1:4040/api/tunnels" 2>/dev/null) || true
    if [[ -n "$api_resp" ]]; then
        ngrok_url=$(echo "$api_resp" | jq -r '.tunnels[] | select(.config.addr | test("18789")) | select(.proto == "https") | .public_url' 2>/dev/null | head -1) || true
        if [[ -n "$ngrok_url" && "$ngrok_url" != "null" ]]; then
            write_info "偵測到已存在的 tunnel：${ngrok_url}"
        else
            ngrok_url=""
        fi
    fi

    if [[ -z "$ngrok_url" ]]; then
        write_info "正在背景啟動 ngrok http 18789..."
        ngrok http 18789 &>/dev/null &
        for (( i=0; i<10; i++ )); do
            sleep 2
            api_resp=$(curl -s -m 3 "http://127.0.0.1:4040/api/tunnels" 2>/dev/null) || true
            if [[ -n "$api_resp" ]]; then
                ngrok_url=$(echo "$api_resp" | jq -r '.tunnels[] | select(.proto == "https") | .public_url' 2>/dev/null | head -1) || true
                if [[ -n "$ngrok_url" && "$ngrok_url" != "null" ]]; then
                    break
                else
                    ngrok_url=""
                fi
            fi
        done
        if [[ -n "$ngrok_url" ]]; then
            write_ok "ngrok tunnel 已啟動"
        else
            write_err "ngrok 未在 20 秒內就緒，請手動執行 'ngrok http 18789'"
            return
        fi
    fi

    local webhook_url="${ngrok_url}/line/webhook"
    echo ""
    echo -e "${C_GREEN}============================================================${C_RESET}"
    echo -e "${C_GREEN}  LINE Webhook URL（請複製）${C_RESET}"
    echo -e "${C_GREEN}============================================================${C_RESET}"
    echo ""
    echo -e "  ${C_YELLOW}${webhook_url}${C_RESET}"
    echo ""
    echo -e "${C_GREEN}============================================================${C_RESET}"
    echo ""
    write_info "請至 LINE Developers Console 設定 Webhook URL："
    echo -e "  ${C_CYAN}1. 開啟 https://developers.line.biz/console/${C_RESET}"
    echo -e "  ${C_CYAN}2. 選擇 Provider → Channel → Messaging API settings${C_RESET}"
    echo -e "  ${C_CYAN}3. 貼上 Webhook URL，開啟 Use webhook，點擊 Verify${C_RESET}"
    echo ""
    read -r -p "完成上述設定後，按 Enter 繼續"

    # ── Webhook verification check loop ──
    local verified=false
    while [[ "$verified" == "false" ]]; do
        echo ""
        write_info "正在檢查 Webhook 驗證結果..."

        local inspect_data latest_status
        inspect_data=$(curl -s -m 5 "http://127.0.0.1:4040/api/requests/http" 2>/dev/null) || true
        latest_status=""

        if [[ -n "$inspect_data" ]]; then
            latest_status=$(echo "$inspect_data" | jq -r '
                [.requests[] | select(.request.uri | test("/line/webhook"))] |
                if length > 0 then .[0].response.status else "" end
            ' 2>/dev/null) || true
        fi

        if [[ -z "$latest_status" || "$latest_status" == "" || "$latest_status" == "null" ]]; then
            write_warn "未偵測到 Webhook 驗證請求。"
            write_info "如果您已在 LINE Console 完成驗證且顯示成功，可直接繼續。"
            if ! confirm_yesno "是否重新檢查？"; then
                verified=true
            fi
            continue
        fi

        # Extract numeric status code
        local status_code
        status_code=$(echo "$latest_status" | grep -oE '[0-9]{3}' | head -1)
        status_code="${status_code:-0}"

        if [[ "$status_code" == "200" ]]; then
            write_ok "LINE Webhook 驗證成功！"
            verified=true

        elif [[ "$status_code" == "401" ]]; then
            write_err "LINE Webhook 驗證失敗：${latest_status}"
            echo ""
            write_warn "這通常表示 Channel Access Token 或 Channel Secret 設定不正確。"
            write_warn "請確認您在 LINE Developers Console 複製的是正確的值。"
            echo ""
            echo -e "  ${C_CYAN}1. 重新輸入 LINE 憑證並重試驗證${C_RESET}"
            echo -e "  ${C_CYAN}2. 略過驗證，繼續後續流程${C_RESET}"
            echo ""
            local choice
            read -r -p "請選擇 (1/2) " choice

            if [[ "$choice" == "1" ]]; then
                local new_token new_secret
                read -r -p "請重新輸入 Channel Access Token: " new_token
                read -r -p "請重新輸入 Channel Secret: " new_secret

                if [[ -z "$new_token" || -z "$new_secret" ]]; then
                    write_warn "憑證不可為空，請重試。"
                    continue
                fi

                local line_config
                line_config=$(jq -n \
                    --arg token "$new_token" \
                    --arg secret "$new_secret" \
                    '{enabled: true, channelAccessToken: $token, channelSecret: $secret, dmPolicy: "open"}')
                set_channel_config "line" "$line_config"
                if ! restart_and_wait "套用新的 LINE 憑證"; then
                    write_err "Gateway 未就緒，請手動檢查容器狀態。"
                    verified=true
                    continue
                fi
                echo ""
                write_info "請再次至 LINE Developers Console 點擊 Verify 按鈕"
                read -r -p "驗證後按 Enter 繼續"
            else
                write_info "略過 Webhook 驗證。"
                verified=true
            fi

        else
            write_err "LINE Webhook 驗證失敗：HTTP ${status_code}"
            write_warn "請檢查 Gateway 服務是否正常運作。"
            if ! confirm_yesno "是否重試？"; then
                verified=true
            fi
        fi
    done
}

# ── Plugin installation flow ────────────────────────────────
# Usage: install_plugin <name> <package> <channel> <config_builder_func> <cred_prompt_key1> <cred_prompt_val1> ...
install_plugin() {
    local name="$1"
    local package="$2"
    local channel="$3"
    local config_builder="$4"
    shift 4

    # Remaining args are key-value pairs for credential prompts
    local -a cred_keys=()
    local -a cred_prompts=()
    while [[ $# -gt 0 ]]; do
        cred_keys+=("$1")
        cred_prompts+=("$2")
        shift 2
    done

    echo ""
    if ! confirm_yesno "是否要安裝 ${name} 插件？"; then
        write_info "略過 ${name} 插件安裝。您可稍後手動執行："
        echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw plugins install ${package}${C_RESET}"
        return
    fi

    # Install plugin
    write_info "正在安裝 ${name} 插件 (${package})..."
    if invoke_gateway plugins install "$package"; then
        write_ok "${name} 插件安裝完成"
    else
        write_warn "${name} 插件安裝失敗。您可稍後手動執行："
        echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw plugins install ${package}${C_RESET}"
    fi

    # Collect credentials
    echo ""
    write_info "設定 ${name} 資訊..."
    local -a cred_values=()
    local has_empty=false
    for (( i=0; i<${#cred_keys[@]}; i++ )); do
        local val
        read -r -p "${cred_prompts[$i]}: " val
        cred_values+=("$val")
        if [[ -z "$val" ]]; then
            has_empty=true
        fi
    done

    if [[ "$has_empty" == "true" ]]; then
        write_warn "部分欄位為空，略過設定。您可稍後手動編輯 .openclaw/openclaw.json"
    else
        # Build config JSON using the config builder function
        local config_json
        config_json=$("$config_builder" "${cred_keys[@]}" "${cred_values[@]}")
        set_channel_config "$channel" "$config_json"
    fi

    # Restart to apply plugin settings
    restart_and_wait "套用 ${name} 插件設定" || true

    # ngrok (LINE only)
    if [[ "$channel" == "line" ]]; then
        start_ngrok_tunnel
    fi

    # Pairing flow
    echo ""
    write_info "${name} 配對流程："
    echo -e "  ${C_CYAN}1. 傳送任意訊息給 ${name} Bot${C_RESET}"
    echo -e "  ${C_CYAN}2. Bot 會回傳一組配對碼${C_RESET}"
    echo ""
    local code
    code=$(read_nonempty "取得配對碼後輸入（輸入 n 略過）")

    if [[ "$code" != "n" && "$code" != "N" ]]; then
        write_info "正在執行 ${name} 配對審批..."
        if invoke_gateway pairing approve "$channel" "$code"; then
            write_ok "${name} 配對完成！"
        else
            write_err "${name} 配對失敗，請手動執行："
            echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw pairing approve ${channel} <配對碼>${C_RESET}"
        fi
    else
        write_info "略過 ${name} 配對。您可稍後手動執行："
        echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw pairing approve ${channel} <配對碼>${C_RESET}"
    fi
}

# ── Config builder functions for plugins ────────────────────
build_line_config() {
    # Args: key1 key2 ... val1 val2 ...
    # For LINE: channelAccessToken channelSecret <token_val> <secret_val>
    local count=$(( $# / 2 ))
    local token="${@:$((count+1)):1}"
    local secret="${@:$((count+2)):1}"
    jq -n \
        --arg token "$token" \
        --arg secret "$secret" \
        '{enabled: true, channelAccessToken: $token, channelSecret: $secret, dmPolicy: "open"}'
}

build_discord_config() {
    local count=$(( $# / 2 ))
    local token="${@:$((count+1)):1}"
    jq -n \
        --arg token "$token" \
        '{enabled: true, token: $token, groupPolicy: "allowlist", dmPolicy: "open", streaming: "off"}'
}

# ════════════════════════════════════════════════════════════════
# Main flow
# ════════════════════════════════════════════════════════════════

# 0. Check Docker
write_info "檢查 Docker 是否正在執行..."
if docker info > /dev/null 2>&1; then
    write_ok "Docker 已啟動"
else
    write_err "Docker 未啟動或未安裝。請先開啟 Docker Desktop 再執行此腳本。"
    exit 1
fi

# 1. Create directory structure
write_info "開始初始化 .openclaw 目錄結構..."
write_info "目標路徑：${OPENCLAW_DIR}"

dirs=(
    "${OPENCLAW_DIR}"
    "${OPENCLAW_DIR}/agents/main/agent"
    "${OPENCLAW_DIR}/workspace"
    "${OPENCLAW_DIR}/workspace/skills"
)

for dir in "${dirs[@]}"; do
    rel="${dir#"${SCRIPT_DIR}/"}"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        write_ok "建立目錄：${rel}"
    else
        write_info "目錄已存在：${rel}（略過）"
    fi
done

# 2. Deploy skills
MODULE_PACK_DIR="${SCRIPT_DIR}/module_pack"
SKILLS_TARGET_DIR="${OPENCLAW_DIR}/workspace/skills"

if [[ -d "$MODULE_PACK_DIR" ]]; then
    write_info "掃描 module_pack 中的技能..."

    # Find all SKILL.md files
    SKILL_NAMES=()
    SKILL_EMOJIS=()
    SKILL_DESCS=()
    SKILL_SOURCES=()
    SKILL_INSTALLED=()

    while IFS= read -r skill_file; do
        skill_dir="$(dirname "$skill_file")"
        skill_name="$(basename "$skill_dir")"

        get_skill_meta "$skill_file"

        SKILL_NAMES+=("$skill_name")
        SKILL_EMOJIS+=("$SKILL_EMOJI")
        SKILL_DESCS+=("$SKILL_DESC")
        SKILL_SOURCES+=("$skill_dir")
        if [[ -d "${SKILLS_TARGET_DIR}/${skill_name}" ]]; then
            SKILL_INSTALLED+=("1")
        else
            SKILL_INSTALLED+=("0")
        fi
    done < <(find "$MODULE_PACK_DIR" -name "SKILL.md" -type f 2>/dev/null | sort)

    if [[ ${#SKILL_NAMES[@]} -eq 0 ]]; then
        write_info "module_pack 中未找到任何技能。"
    else
        show_skill_selector

        installed=0
        removed=0
        skipped=0

        for (( i=0; i<${#SKILL_NAMES[@]}; i++ )); do
            target_dir="${SKILLS_TARGET_DIR}/${SKILL_NAMES[$i]}"
            is_selected=false
            for idx in "${SELECTED_INDICES[@]}"; do
                if [[ "$idx" == "$i" ]]; then
                    is_selected=true
                    break
                fi
            done

            if [[ "$is_selected" == "true" && "${SKILL_INSTALLED[$i]}" == "0" ]]; then
                cp -r "${SKILL_SOURCES[$i]}" "$target_dir"
                write_ok "部署技能：${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]}"
                (( installed++ )) || true
            elif [[ "$is_selected" == "false" && "${SKILL_INSTALLED[$i]}" == "1" ]]; then
                rm -rf "$target_dir"
                write_ok "移除技能：${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]}"
                (( removed++ )) || true
            else
                (( skipped++ )) || true
            fi
        done
        write_info "技能處理完成！新部署 ${installed} 個，移除 ${removed} 個，略過 ${skipped} 個。"
    fi
else
    write_warn "module_pack 目錄不存在，略過技能部署。"
fi

# 3. Generate openclaw.json
if [[ ! -f "$CONFIG_FILE" ]]; then
    cat > "$CONFIG_FILE" << 'JSONEOF'
{
  "gateway": {
    "mode": "local",
    "bind": "custom",
    "customBindHost": "0.0.0.0"
  }
}
JSONEOF
    write_ok "建立設定檔：.openclaw/openclaw.json（mode=local, bind=0.0.0.0）"
else
    write_info "設定檔已存在：.openclaw/openclaw.json（略過）"
fi

echo ""
write_ok "初始化完成！"

# 4. Copy .env.example -> .env
ENV_EXAMPLE="${SCRIPT_DIR}/.env.example"
ENV_FILE="${SCRIPT_DIR}/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$ENV_EXAMPLE" ]]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
        write_ok "已從 .env.example 複製建立 .env"
    else
        write_warn ".env.example 不存在，請手動建立 .env 檔案。"
    fi
else
    write_info ".env 已存在（略過複製）"
fi

# 5. Start Docker Compose
echo ""
write_info "正在啟動 Docker Compose 服務..."
if docker compose up -d; then
    write_ok "Docker Compose 服務已啟動"
else
    write_err "無法啟動 Docker Compose 服務"
    exit 1
fi

# 6. Wait for Gateway
echo ""
if ! wait_gateway "等待 Gateway 啟動"; then
    write_err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
fi

# 7. Configure API keys (loop)
while true; do
    echo ""
    # Show currently configured API keys
    if [[ -f "$CONFIG_FILE" ]]; then
        local_profiles=$(jq -r '.auth.profiles // empty' "$CONFIG_FILE" 2>/dev/null) || true
        if [[ -n "$local_profiles" && "$local_profiles" != "null" && "$local_profiles" != "{}" ]]; then
            local_count=$(echo "$local_profiles" | jq 'length' 2>/dev/null) || local_count=0
            if [[ "$local_count" -gt 0 ]]; then
                write_ok "目前已設定 ${local_count} 組 API 金鑰："
                echo "$local_profiles" | jq -r 'to_entries[] | "  • \(.key) （Provider: \(.value.provider), 模式: \(.value.mode)）"' 2>/dev/null | while IFS= read -r line; do
                    echo -e "  ${C_CYAN}${line}${C_RESET}"
                done
            else
                write_info "目前尚未設定任何 API 金鑰。"
            fi
        else
            write_info "目前尚未設定任何 API 金鑰。"
        fi
    fi

    echo ""
    if ! confirm_yesno "是否要設定 AI 模型的 API 金鑰？（如 Anthropic Claude、OpenAI 等）"; then
        break
    fi

    echo ""
    write_info "即將啟動 openclaw 內建設定精靈，請依照提示選擇 Provider 並完成設定。"
    echo ""
    # Run interactively (no output capture)
    docker compose exec openclaw-gateway openclaw configure --section model || true
done

# 7b. Speech-to-text (OpenAI Whisper)
echo ""
write_info "語音轉文字功能可將語音訊息自動轉為文字（使用 OpenAI Whisper）。"
if confirm_yesno "是否要啟用語音轉文字功能？（需要已設定 OpenAI API 金鑰）"; then
    audio_config='{"enabled":true,"language":"zh","models":[{"provider":"openai","model":"whisper-1","profile":"openai:manual"}],"echoTranscript":true}'
    if jq --argjson audio "$audio_config" \
        '.tools.media.audio = $audio' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" 2>/dev/null; then
        mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        write_ok "語音轉文字功能已啟用（language=zh, model=whisper-1）"
    else
        rm -f "${CONFIG_FILE}.tmp"
        # Ensure tools.media path exists
        jq --argjson audio "$audio_config" \
            'if .tools == null then .tools = {} else . end |
             if .tools.media == null then .tools.media = {} else . end |
             .tools.media.audio = $audio' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp"
        mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
        write_ok "語音轉文字功能已啟用（language=zh, model=whisper-1）"
    fi
else
    write_info "略過語音轉文字功能。您可稍後手動編輯 .openclaw/openclaw.json 的 tools.media.audio 區段。"
fi

# Restart to apply settings
if ! restart_and_wait "套用設定"; then
    write_err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
fi

# Read Dashboard Token
echo ""
write_info "正在讀取 Dashboard Token..."
dashboard_token=""
dashboard_token=$(jq -r '.gateway.auth.token // empty' "$CONFIG_FILE" 2>/dev/null) || true
if [[ -n "$dashboard_token" ]]; then
    write_ok "Dashboard Token 已取得"
else
    write_err "無法讀取 Token"
    write_warn "您可手動查看 .openclaw/openclaw.json 中的 gateway.auth.token 欄位。"
fi

# 8. Install plugins

# LINE plugin
install_plugin "LINE" "@openclaw/line" "line" build_line_config \
    "channelAccessToken" "請輸入 Channel Access Token" \
    "channelSecret" "請輸入 Channel Secret"

# Discord plugin
install_plugin "Discord" "@openclaw/discord" "discord" build_discord_config \
    "token" "請輸入 Discord Bot Token"

# 9. Device pairing
echo ""
echo -e "${C_CYAN}============================================================${C_RESET}"
echo -e "${C_CYAN}  Dashboard 連線資訊${C_RESET}"
echo -e "${C_CYAN}============================================================${C_RESET}"
if [[ -n "$dashboard_token" ]]; then
    echo ""
    echo -e "  ${C_CYAN}URL  : http://127.0.0.1:18789/${C_RESET}"
    echo -e "  ${C_CYAN}Token: ${dashboard_token}${C_RESET}"
    echo ""
else
    write_warn "  Token 未取得，請手動查看 .openclaw/openclaw.json 中的 gateway.auth.token 欄位。"
    echo ""
fi
echo -e "${C_CYAN}============================================================${C_RESET}"
echo ""
write_info "裝置配對流程 — 由於 Gateway 綁定 0.0.0.0，瀏覽器首次連線需配對審批。"
write_info "請在瀏覽器開啟上方 URL，並使用 Token 登入。"
echo ""

if confirm_yesno "是否要現在進行裝置配對？"; then
    write_info "等待瀏覽器連線產生配對請求..."
    request_id=""
    for (( w=0; w<60; w+=3 )); do
        list_output=$(docker compose exec openclaw-gateway openclaw devices list 2>&1) || true
        if echo "$list_output" | grep -qE "Pending \([0-9]+\)"; then
            pending_count=$(echo "$list_output" | grep -oE "Pending \(([0-9]+)\)" | grep -oE "[0-9]+")
            if [[ "$pending_count" -gt 0 ]]; then
                request_id=$(echo "$list_output" | grep -oE "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" | head -1)
                if [[ -n "$request_id" ]]; then
                    break
                fi
            fi
        fi
        sleep 3
        if (( w > 0 && w % 15 == 0 )); then
            write_info "仍在等待瀏覽器連線...（已等待 ${w} 秒）"
        fi
    done

    if [[ -n "$request_id" ]]; then
        write_info "偵測到配對請求：${request_id}"
        if invoke_gateway devices approve "$request_id"; then
            write_ok "裝置配對完成！請重新整理瀏覽器頁面。"
        else
            write_err "配對審批失敗，請手動執行："
            echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw devices approve ${request_id}${C_RESET}"
        fi
    else
        write_warn "等待逾時，未偵測到配對請求。您可稍後手動執行："
        echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw devices list${C_RESET}"
        echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw devices approve <Request ID>${C_RESET}"
    fi
else
    write_info "略過裝置配對。您可稍後手動執行："
    echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw devices list${C_RESET}"
    echo -e "  ${C_YELLOW}docker compose exec openclaw-gateway openclaw devices approve <Request ID>${C_RESET}"
fi
