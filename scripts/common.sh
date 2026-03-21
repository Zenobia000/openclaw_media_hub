#!/usr/bin/env bash
# ============================================================
# common.sh — OpenClaw 腳本共用函式庫
#
# 用法：在腳本開頭加入
#   source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
#
# 提供：
#   變數：PROJECT_ROOT, OPENCLAW_DIR, CONFIG_FILE, HEALTH_URL, SPIN_CHARS
#   函式：info, ok, warn, err,
#         confirm_yes_no, read_non_empty,
#         invoke_gateway, wait_gateway, restart_and_wait,
#         get_skill_meta, show_skill_selector
# ============================================================

set -euo pipefail

# ── 路徑常數 ─────────────────────────────────────────────────

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPTS_DIR")"
OPENCLAW_DIR="$PROJECT_ROOT/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
HEALTH_URL="http://127.0.0.1:18789/healthz"
SPIN_CHARS=('|' '/' '-' '\')

# 確保 docker compose 等指令使用專案根目錄
cd "$PROJECT_ROOT"

# ── 輸出工具 ─────────────────────────────────────────────────

info()  { printf '\033[34m[INFO]  %s\033[0m\n' "$1"; }
ok()    { printf '\033[32m[OK]    %s\033[0m\n' "$1"; }
warn()  { printf '\033[33m[WARN]  %s\033[0m\n' "$1"; }
err()   { printf '\033[31m[ERROR] %s\033[0m\n' "$1"; }

# ── Y/n 確認提示 ─────────────────────────────────────────────

confirm_yes_no() {
    local prompt="$1" answer
    read -rp "$prompt (Y/n) " answer
    [[ "$answer" != "n" && "$answer" != "N" ]]
}

# ── 非空輸入提示（支援 n 略過）────────────────────────────────

read_non_empty() {
    local prompt="$1" value=""
    while true; do
        read -rp "$prompt" value
        if [[ -n "${value// /}" ]]; then
            echo "$value"
            return
        fi
        warn "不可空白，請重新輸入或輸入 n 略過。"
    done
}

# ── 執行 Gateway CLI 指令 ────────────────────────────────────

invoke_gateway() {
    docker compose exec openclaw-gateway openclaw "$@" >/dev/null 2>&1
}

# ── 等待 Gateway 就緒（含 spinner）───────────────────────────

wait_gateway() {
    local label="${1:-等待 Gateway 就緒}" timeout="${2:-60}"
    local i result
    printf '\033[34m[INFO]  %s... \033[0m' "$label"
    for ((i = 0; i < timeout; i++)); do
        printf '\b\033[36m%s\033[0m' "${SPIN_CHARS[$((i % 4))]}"
        if result=$(curl -sf --max-time 2 "$HEALTH_URL" 2>/dev/null); then
            if [[ "$result" == *'"ok":true'* ]]; then
                printf '\b \n'
                ok "$label — 完成（${i} 秒）"
                return 0
            fi
        fi
        sleep 1
    done
    printf '\b \n'
    warn "$label — 逾時（${timeout} 秒）"
    # 顯示容器狀態以協助除錯
    local cstate
    cstate=$(docker inspect --format='{{.State.Status}}:{{.State.Health.Status}}' openclaw-gateway 2>/dev/null) || true
    if [[ -n "$cstate" ]]; then
        warn "容器狀態：$cstate"
    fi
    return 1
}

# ── 重啟 Docker Compose 並等待就緒 ───────────────────────────

restart_and_wait() {
    local reason="${1:-套用設定}"
    echo ""
    info "正在重新啟動服務以${reason}..."
    if docker compose restart; then
        ok "服務已重新啟動"
    else
        err "無法重新啟動服務"
        return 1
    fi
    echo ""
    wait_gateway "等待 Gateway 重新就緒"
}

# ── 解析 SKILL.md frontmatter ────────────────────────────────

get_skill_meta() {
    local path="$1"
    local content emoji="📦" desc="(無描述)"
    content=$(<"$path")

    # 提取 frontmatter
    local yaml=""
    if [[ "$content" =~ ^---$'\n'(.*)$'\n'--- ]]; then
        yaml="${BASH_REMATCH[1]}"
    elif [[ "$content" =~ ^---[[:space:]](.*)--- ]]; then
        # fallback: more relaxed matching
        yaml=$(echo "$content" | sed -n '/^---$/,/^---$/{ /^---$/d; p; }')
    fi

    if [[ -n "$yaml" ]]; then
        local e
        e=$(echo "$yaml" | grep -oP '^\s*emoji:\s*\K.+' | head -1 | sed "s/[\"' ]//g") || true
        [[ -n "$e" ]] && emoji="$e"

        # 嘗試 block scalar（| 或 >），再處理單行
        if echo "$yaml" | grep -qP '^description:\s*[|>]'; then
            local first
            first=$(echo "$yaml" | sed -n '/^description:\s*[|>]/,/^[^ ]/{/^  /p;}' | head -1 | sed 's/^ *//') || true
            [[ -n "$first" ]] && desc="$first"
        else
            local d
            d=$(echo "$yaml" | grep -oP '^\s*description:\s*\K.+' | head -1 | sed "s/^[\"']//;s/[\"']$//;s/^ *//;s/ *$//") || true
            [[ -n "$d" ]] && desc="$d"
        fi
    fi

    SKILL_EMOJI="$emoji"
    SKILL_DESC="$desc"
}

# ── 互動式技能選擇介面 ──────────────────────────────────────

show_skill_selector() {
    local title="${1:-OpenClaw 技能選擇工具}"
    # 引數：全域陣列 SKILL_NAMES, SKILL_EMOJIS, SKILL_DESCS, SKILL_SOURCES, SKILL_INSTALLED
    local count=${#SKILL_NAMES[@]}
    if ((count == 0)); then return 1; fi

    # 初始化選取狀態（已安裝的預設勾選）
    local -a selected=()
    for ((i = 0; i < count; i++)); do
        selected+=("${SKILL_INSTALLED[$i]}")
    done

    local cursor=0 search="" key

    # 隱藏游標
    printf '\033[?25l'

    # 確保退出時恢復游標
    trap 'printf "\033[?25h"' RETURN

    while true; do
        # 篩選符合搜尋的技能索引
        local -a filtered=()
        for ((i = 0; i < count; i++)); do
            if [[ -z "$search" ]] ||
               [[ "${SKILL_NAMES[$i],,}" == *"${search,,}"* ]] ||
               [[ "${SKILL_DESCS[$i],,}" == *"${search,,}"* ]]; then
                filtered+=("$i")
            fi
        done

        local fcount=${#filtered[@]}
        if ((fcount == 0)); then cursor=0;
        elif ((cursor >= fcount)); then cursor=$((fcount - 1)); fi

        local sel_count=0
        for ((i = 0; i < count; i++)); do
            ((selected[i])) && ((sel_count++))
        done

        # ── 繪製 UI ──
        local total_lines=$(( (fcount > 0 ? fcount : 1) + 5 ))

        # 移到起始位置並清除（第一次除外）
        if [[ -n "${_selector_drawn:-}" ]]; then
            printf '\033[%dA' "$_last_lines"
            for ((i = 0; i < _last_lines; i++)); do
                printf '\033[2K\n'
            done
            printf '\033[%dA' "$_last_lines"
        fi
        _selector_drawn=1
        _last_lines=$total_lines

        printf '\033[36m◆  %s\033[0m\n' "$title"
        printf '│\n'
        printf '│  搜尋: \033[33m%s\033[0m_\n' "$search"

        for ((fi = 0; fi < fcount; fi++)); do
            local idx=${filtered[$fi]}
            local name="${SKILL_NAMES[$idx]}"
            local emoji="${SKILL_EMOJIS[$idx]}"
            local desc="${SKILL_DESCS[$idx]}"
            local check="◻" tag="" color

            ((selected[idx])) && check="◼"
            ((SKILL_INSTALLED[idx])) && tag=" (已安裝)"

            # 截斷描述
            if ((${#desc} > 50)); then desc="${desc:0:47}..."; fi

            if ((fi == cursor)); then color='\033[36m'        # cyan
            elif ((SKILL_INSTALLED[idx])); then color='\033[90m' # dark gray
            else color='\033[37m'; fi                           # white

            printf "${color}│  %s %s %s — %s%s\033[0m\n" "$check" "$emoji" "$name" "$desc" "$tag"
        done

        if ((fcount == 0)); then
            printf '\033[90m│  （無符合的技能）\033[0m\n'
        fi

        printf '│\n'

        local status
        if ((sel_count > 0)); then status="(已選 $sel_count 個)";
        else status="(未選擇任何技能)"; fi
        printf '\033[90m│  ↑/↓ 移動 • Space/Tab: 選取 • Enter: 確認 • a: 全選 • q/Esc: 取消  %s\033[0m\n' "$status"

        # ── 按鍵處理 ──
        printf '\033[?25h'  # 顯示游標
        IFS= read -rsn1 key
        printf '\033[?25l'  # 隱藏游標

        case "$key" in
            $'\x1b')  # Escape 序列或 Esc 鍵
                read -rsn1 -t 0.1 key2 || key2=""
                if [[ "$key2" == "[" ]]; then
                    read -rsn1 -t 0.1 key3 || key3=""
                    case "$key3" in
                        A) ((cursor > 0)) && ((cursor--)) ;;  # Up
                        B) ((fcount > 0 && cursor < fcount - 1)) && ((cursor++)) ;; # Down
                    esac
                else
                    # 純 Esc 鍵 — 取消
                    printf '\033[%dA' "$_last_lines"
                    for ((i = 0; i < _last_lines; i++)); do printf '\033[2K\n'; done
                    printf '\033[%dA' "$_last_lines"
                    printf '\033[90m◇  %s\033[0m\n' "$title"
                    printf '\033[90m│  已取消\033[0m\n'
                    echo ""
                    SELECTOR_RESULT=""
                    return 1
                fi
                ;;
            q)  # 取消（q 鍵方便終端操作）
                printf '\033[%dA' "$_last_lines"
                for ((i = 0; i < _last_lines; i++)); do printf '\033[2K\n'; done
                printf '\033[%dA' "$_last_lines"
                printf '\033[90m◇  %s\033[0m\n' "$title"
                printf '\033[90m│  已取消\033[0m\n'
                echo ""
                SELECTOR_RESULT=""
                return 1
                ;;
            " "|$'\t')  # Space 或 Tab — 切換選取
                if ((fcount > 0)); then
                    local tidx=${filtered[$cursor]}
                    selected[$tidx]=$(( 1 - selected[tidx] ))
                fi
                ;;
            "")  # Enter — 確認
                SELECTOR_RESULT=""
                for ((i = 0; i < count; i++)); do
                    if ((selected[i])); then
                        SELECTOR_RESULT+="$i "
                    fi
                done
                SELECTOR_RESULT="${SELECTOR_RESULT% }"

                # 清除 UI 並顯示結果
                printf '\033[%dA' "$_last_lines"
                for ((i = 0; i < _last_lines; i++)); do printf '\033[2K\n'; done
                printf '\033[%dA' "$_last_lines"
                printf '\033[36m◇  %s\033[0m\n' "$title"
                if [[ -n "$SELECTOR_RESULT" ]]; then
                    local names=""
                    for idx in $SELECTOR_RESULT; do
                        names+="${SKILL_EMOJIS[$idx]} ${SKILL_NAMES[$idx]}, "
                    done
                    printf '\033[32m│  已選擇: %s\033[0m\n' "${names%, }"
                else
                    printf '\033[90m│  未選擇任何技能\033[0m\n'
                fi
                echo ""
                return 0
                ;;
            a)  # 全選/取消全選
                local all_selected=1
                for fi_idx in "${filtered[@]}"; do
                    if (( ! selected[fi_idx] )); then all_selected=0; break; fi
                done
                for fi_idx in "${filtered[@]}"; do
                    selected[$fi_idx]=$(( 1 - all_selected ))
                done
                ;;
            $'\x7f'|$'\b')  # Backspace
                if ((${#search} > 0)); then
                    search="${search:0:${#search}-1}"
                fi
                ;;
            *)  # 一般字元 — 加入搜尋
                if [[ "$key" =~ ^[[:print:]]$ ]]; then
                    search+="$key"
                fi
                ;;
        esac
    done
}
