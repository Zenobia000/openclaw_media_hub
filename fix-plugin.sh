#!/bin/bash
# ============================================================
# fix-plugin.sh — 修復指定插件路徑不存在的問題（通用型）
#
# 用法：
#   ./fix-plugin.sh <plugin_name> [plugin_name2 ...]
#   ./fix-plugin.sh notion
#   ./fix-plugin.sh notion slack google-calendar
#   ./fix-plugin.sh --list                          # 列出已安裝的插件
#   ./fix-plugin.sh --dry-run notion                # 預覽變更但不實際修改
#
# 此腳本會：
#   1. 從 openclaw.json 移除指定插件的設定
#   2. 重啟容器以套用修正
#   3. 執行 openclaw doctor 驗證設定
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/.openclaw/openclaw.json"

# -- ANSI color codes ----------------------------------------
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
DARK_GRAY='\033[1;30m'
WHITE='\033[1;37m'
RESET='\033[0m'

# -- Colored output functions --------------------------------
write_info()  { echo -e "${BLUE}[INFO]  $1${RESET}"; }
write_ok()    { echo -e "${GREEN}[OK]    $1${RESET}"; }
write_warn()  { echo -e "${YELLOW}[WARN]  $1${RESET}"; }
write_err()   { echo -e "${RED}[ERROR] $1${RESET}"; }

# -- Argument parsing ----------------------------------------
LIST=false
DRY_RUN=false
SKIP_RESTART=false
PLUGIN_NAMES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --list)
            LIST=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-restart)
            SKIP_RESTART=true
            shift
            ;;
        -*)
            write_err "未知選項：$1"
            exit 1
            ;;
        *)
            PLUGIN_NAMES+=("$1")
            shift
            ;;
    esac
done

# -- Check config file ---------------------------------------
if [[ ! -f "$CONFIG_FILE" ]]; then
    write_err "找不到設定檔：$CONFIG_FILE"
    exit 1
fi

write_info "讀取設定檔：$CONFIG_FILE"

# -- --list: list installed plugins and exit -----------------
if [[ "$LIST" == true ]]; then
    echo ""
    echo -e "${CYAN}=== 已安裝的插件 ===${RESET}"

    found=false

    # Check plugins.entries
    if jq -e '.plugins.entries // empty' "$CONFIG_FILE" > /dev/null 2>&1; then
        entries_keys=$(jq -r '.plugins.entries | keys[]' "$CONFIG_FILE" 2>/dev/null)
        if [[ -n "$entries_keys" ]]; then
            echo -e "  ${DARK_GRAY}[entries]${RESET}"
            while IFS= read -r key; do
                echo -e "    ${WHITE}- ${key}${RESET}"
                found=true
            done <<< "$entries_keys"
        fi
    fi

    # Check plugins.installs
    if jq -e '.plugins.installs // empty' "$CONFIG_FILE" > /dev/null 2>&1; then
        installs_keys=$(jq -r '.plugins.installs | keys[]' "$CONFIG_FILE" 2>/dev/null)
        if [[ -n "$installs_keys" ]]; then
            echo -e "  ${DARK_GRAY}[installs]${RESET}"
            while IFS= read -r key; do
                echo -e "    ${WHITE}- ${key}${RESET}"
                found=true
            done <<< "$installs_keys"
        fi
    fi

    # Check plugins.load.paths
    if jq -e '.plugins.load.paths // empty' "$CONFIG_FILE" > /dev/null 2>&1; then
        load_paths=$(jq -r '.plugins.load.paths[]' "$CONFIG_FILE" 2>/dev/null)
        if [[ -n "$load_paths" ]]; then
            echo -e "  ${DARK_GRAY}[load.paths]${RESET}"
            while IFS= read -r p; do
                echo -e "    ${WHITE}- ${p}${RESET}"
                found=true
            done <<< "$load_paths"
        fi
    fi

    if [[ "$found" == false ]]; then
        write_info "未發現任何插件設定。"
    fi

    echo ""
    exit 0
fi

# -- Check arguments -----------------------------------------
if [[ ${#PLUGIN_NAMES[@]} -eq 0 ]]; then
    write_err "請提供至少一個插件名稱。用法：./fix-plugin.sh <plugin_name> [...]"
    write_info "使用 --list 查看已安裝的插件。"
    exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
    write_warn "=== DryRun 模式：僅預覽變更，不會實際修改檔案 ==="
    echo ""
fi

# -- Remove specified plugins one by one ---------------------
total_modified=false
config=$(cat "$CONFIG_FILE")

for plugin_name in "${PLUGIN_NAMES[@]}"; do
    plugin_modified=false
    echo ""
    echo -e "${CYAN}--- 處理插件：${plugin_name} ---${RESET}"

    target_path="/app/extensions/${plugin_name}"

    # 1. Remove from plugins.load.paths
    if echo "$config" | jq -e '.plugins.load.paths // empty' > /dev/null 2>&1; then
        path_exists=$(echo "$config" | jq --arg p "$target_path" '[.plugins.load.paths[] | select(. == $p)] | length')
        if [[ "$path_exists" -gt 0 ]]; then
            if [[ "$DRY_RUN" == false ]]; then
                config=$(echo "$config" | jq --arg p "$target_path" '.plugins.load.paths = [.plugins.load.paths[] | select(. != $p)]')
            fi
            write_ok "已從 plugins.load.paths 移除 ${target_path}"
            plugin_modified=true
        else
            write_info "plugins.load.paths 中未包含 ${target_path}（略過）"
        fi
    else
        write_info "plugins.load.paths 中未包含 ${target_path}（略過）"
    fi

    # 2. Remove from plugins.entries.<plugin>
    if echo "$config" | jq -e --arg k "$plugin_name" '.plugins.entries[$k] // empty' > /dev/null 2>&1; then
        if [[ "$DRY_RUN" == false ]]; then
            config=$(echo "$config" | jq --arg k "$plugin_name" 'del(.plugins.entries[$k])')
        fi
        write_ok "已移除 plugins.entries.${plugin_name}"
        plugin_modified=true
    else
        write_info "plugins.entries 中無 ${plugin_name} 項目（略過）"
    fi

    # 3. Remove from plugins.installs.<plugin>
    if echo "$config" | jq -e --arg k "$plugin_name" '.plugins.installs[$k] // empty' > /dev/null 2>&1; then
        if [[ "$DRY_RUN" == false ]]; then
            config=$(echo "$config" | jq --arg k "$plugin_name" 'del(.plugins.installs[$k])')
        fi
        write_ok "已移除 plugins.installs.${plugin_name}"
        plugin_modified=true
    else
        write_info "plugins.installs 中無 ${plugin_name} 項目（略過）"
    fi

    if [[ "$plugin_modified" == false ]]; then
        write_info "插件 ${plugin_name} 無需修改。"
    fi

    if [[ "$plugin_modified" == true ]]; then
        total_modified=true
    fi
done

# -- Write back config file ----------------------------------
echo ""
if [[ "$total_modified" == true && "$DRY_RUN" == false ]]; then
    echo "$config" | jq '.' > "$CONFIG_FILE"
    write_ok "設定檔已更新：$CONFIG_FILE"
elif [[ "$DRY_RUN" == true ]]; then
    write_warn "DryRun 模式，設定檔未修改。"
else
    write_info "設定檔無需修改。"
    exit 0
fi

# -- Restart containers --------------------------------------
if [[ "$SKIP_RESTART" == true ]]; then
    write_info "已跳過容器重啟（--skip-restart）。"
elif [[ "$DRY_RUN" == false ]]; then
    echo ""
    write_info "正在重新啟動容器以套用修正..."
    if docker compose restart; then
        write_ok "容器已重新啟動"
    else
        write_err "無法重新啟動容器"
        exit 1
    fi

    # Wait for Gateway to be ready
    spin_chars=('|' '/' '-' '\')
    spin_idx=0
    max_wait=30
    waited=0
    gateway_ready=false

    echo -ne "${BLUE}[INFO]  等待 Gateway 就緒... ${RESET}"
    while [[ $waited -lt $max_wait ]]; do
        echo -ne "\b${CYAN}${spin_chars[$((spin_idx % 4))]}${RESET}"
        spin_idx=$((spin_idx + 1))

        if health=$(curl -sf --max-time 2 "http://127.0.0.1:18789/healthz" 2>/dev/null); then
            ok_value=$(echo "$health" | jq -r '.ok // empty' 2>/dev/null)
            if [[ "$ok_value" == "true" ]]; then
                gateway_ready=true
                break
            fi
        fi

        sleep 1
        waited=$((waited + 1))
    done
    echo -e "\b "

    if [[ "$gateway_ready" == false ]]; then
        write_err "Gateway 未在 ${max_wait} 秒內就緒，請手動檢查容器狀態。"
        exit 1
    fi
    write_ok "Gateway 已就緒（${waited} 秒）"

    # Run openclaw doctor to verify
    echo ""
    write_info "執行 openclaw doctor 驗證設定..."
    if docker compose exec openclaw-gateway openclaw doctor 2>&1; then
        write_ok "openclaw doctor 驗證通過！"
    else
        write_warn "doctor 仍回報問題，嘗試自動修復..."
        if docker compose exec openclaw-gateway openclaw doctor --fix 2>&1; then
            write_ok "openclaw doctor --fix 修復完成！"
        else
            write_err "自動修復失敗，請手動檢查。"
        fi
    fi
fi

echo ""
write_ok "修復流程完成！"
