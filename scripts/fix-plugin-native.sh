#!/usr/bin/env bash
# ============================================================
# fix-plugin-native.sh — 修復指定插件路徑不存在的問題（Ubuntu 原生版）
#
# 用法：
#   ./scripts/fix-plugin-native.sh <plugin_name> [plugin_name2 ...]
#   ./scripts/fix-plugin-native.sh notion
#   ./scripts/fix-plugin-native.sh notion slack google-calendar
#   ./scripts/fix-plugin-native.sh --list                          # 列出已安裝的插件
#   ./scripts/fix-plugin-native.sh --dry-run notion                # 預覽變更但不實際修改
#
# 此腳本會：
#   1. 從 openclaw.json 移除指定插件的設定
#   2. 重啟服務以套用修正
#   3. 執行 openclaw doctor 驗證設定
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common-native.sh"

# -- 檢查 jq 是否可用 ----------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    err "此腳本需要 jq。請先安裝：sudo apt-get install jq"
    exit 1
fi

# -- 解析參數 -------------------------------------------------
LIST=false
DRY_RUN=false
SKIP_RESTART=false
PLUGIN_NAMES=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --list|-l)       LIST=true; shift ;;
        --dry-run|-d)    DRY_RUN=true; shift ;;
        --skip-restart)  SKIP_RESTART=true; shift ;;
        --help|-h)
            echo "用法：$0 [--list] [--dry-run] [--skip-restart] <plugin_name> [...]"
            exit 0
            ;;
        -*)
            err "未知選項：$1"
            exit 1
            ;;
        *)
            PLUGIN_NAMES+=("$1"); shift ;;
    esac
done

# -- 檢查設定檔 -----------------------------------------------
if [[ ! -f "$CONFIG_FILE" ]]; then
    err "找不到設定檔：$CONFIG_FILE"
    exit 1
fi

info "讀取設定檔：$CONFIG_FILE"
config=$(<"$CONFIG_FILE")

# -- --list：列出已安裝的插件後結束 ----------------------------
if $LIST; then
    echo ""
    printf '\033[36m=== 已安裝的插件 ===\033[0m\n'
    found=false

    # plugins.entries
    entries=$(echo "$config" | jq -r '.plugins.entries // empty | keys[]' 2>/dev/null) || true
    if [[ -n "$entries" ]]; then
        printf '\033[90m  [entries]\033[0m\n'
        while IFS= read -r name; do
            printf '    - %s\n' "$name"
            found=true
        done <<< "$entries"
    fi

    # plugins.installs
    installs=$(echo "$config" | jq -r '.plugins.installs // empty | keys[]' 2>/dev/null) || true
    if [[ -n "$installs" ]]; then
        printf '\033[90m  [installs]\033[0m\n'
        while IFS= read -r name; do
            printf '    - %s\n' "$name"
            found=true
        done <<< "$installs"
    fi

    # plugins.load.paths
    paths=$(echo "$config" | jq -r '.plugins.load.paths // empty | .[]' 2>/dev/null) || true
    if [[ -n "$paths" ]]; then
        printf '\033[90m  [load.paths]\033[0m\n'
        while IFS= read -r p; do
            printf '    - %s\n' "$p"
            found=true
        done <<< "$paths"
    fi

    if ! $found; then
        info "未發現任何插件設定。"
    fi

    echo ""
    exit 0
fi

# -- 檢查參數 -------------------------------------------------
if [[ ${#PLUGIN_NAMES[@]} -eq 0 ]]; then
    err "請提供至少一個插件名稱。用法：$0 <plugin_name> [...]"
    info "使用 --list 查看已安裝的插件。"
    exit 1
fi

if $DRY_RUN; then
    warn "=== DryRun 模式：僅預覽變更，不會實際修改檔案 ==="
    echo ""
fi

# -- 自動偵測插件路徑 ------------------------------------------
# 從 plugins.load.paths 中匹配以 /<plugin_name> 結尾的路徑
find_plugin_path() {
    local plugin_name="$1"
    echo "$config" | jq -r --arg name "$plugin_name" \
        '.plugins.load.paths // [] | .[] | select(endswith("/" + $name))' 2>/dev/null | head -1
}

# -- 逐一移除指定插件 ------------------------------------------
total_modified=false

for plugin_name in "${PLUGIN_NAMES[@]}"; do
    plugin_modified=false
    echo ""
    printf '\033[36m--- 處理插件：%s ---\033[0m\n' "$plugin_name"

    # 自動偵測插件路徑
    target_path=$(find_plugin_path "$plugin_name")

    # 1. 移除 plugins.load.paths 中匹配的路徑
    if [[ -n "$target_path" ]]; then
        if ! $DRY_RUN; then
            config=$(echo "$config" | jq --arg path "$target_path" '(.plugins.load.paths) -= [$path]')
        fi
        ok "已從 plugins.load.paths 移除 $target_path"
        plugin_modified=true
    else
        info "plugins.load.paths 中未包含 $plugin_name 相關路徑（略過）"
    fi

    # 2. 移除 plugins.entries.<plugin>
    if echo "$config" | jq -e ".plugins.entries.\"$plugin_name\" // empty" >/dev/null 2>&1; then
        if ! $DRY_RUN; then
            config=$(echo "$config" | jq "del(.plugins.entries.\"$plugin_name\")")
        fi
        ok "已移除 plugins.entries.$plugin_name"
        plugin_modified=true
    else
        info "plugins.entries 中無 $plugin_name 項目（略過）"
    fi

    # 3. 移除 plugins.installs.<plugin>
    if echo "$config" | jq -e ".plugins.installs.\"$plugin_name\" // empty" >/dev/null 2>&1; then
        if ! $DRY_RUN; then
            config=$(echo "$config" | jq "del(.plugins.installs.\"$plugin_name\")")
        fi
        ok "已移除 plugins.installs.$plugin_name"
        plugin_modified=true
    else
        info "plugins.installs 中無 $plugin_name 項目（略過）"
    fi

    if ! $plugin_modified; then
        info "插件 $plugin_name 無需修改。"
    fi

    if $plugin_modified; then
        total_modified=true
    fi
done

# -- 寫回設定檔 ------------------------------------------------
echo ""
if $total_modified && ! $DRY_RUN; then
    echo "$config" | jq '.' > "$CONFIG_FILE"
    ok "設定檔已更新：$CONFIG_FILE"
elif $DRY_RUN; then
    warn "DryRun 模式，設定檔未修改。"
else
    info "設定檔無需修改。"
    exit 0
fi

# -- 重啟服務 --------------------------------------------------
if $SKIP_RESTART; then
    info "已跳過服務重啟（--skip-restart）。"
elif ! $DRY_RUN; then
    echo ""
    info "正在重新啟動服務以套用修正..."
    if sudo systemctl restart "$SERVICE_NAME"; then
        ok "服務已重新啟動"
    else
        err "無法重新啟動服務"
        exit 1
    fi

    # 等待 Gateway 就緒
    if ! wait_gateway "等待 Gateway 就緒" 30; then
        err "Gateway 未在 30 秒內就緒，請手動檢查服務狀態。"
        exit 1
    fi

    # 執行 openclaw doctor 驗證
    echo ""
    info "執行 openclaw doctor 驗證設定..."
    if openclaw doctor 2>&1; then
        ok "openclaw doctor 驗證通過！"
    else
        warn "doctor 仍回報問題，嘗試自動修復..."
        if openclaw doctor --fix 2>&1; then
            ok "openclaw doctor --fix 修復完成！"
        else
            err "自動修復失敗，請手動檢查。"
        fi
    fi
fi

echo ""
ok "修復流程完成！"
