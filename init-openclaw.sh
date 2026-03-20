#!/usr/bin/env bash
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
#   8. 裝置配對
#
# 相依工具：bash 4+, docker, curl, jq
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_DIR="$SCRIPT_DIR/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"
HEALTH_URL="http://127.0.0.1:18789/healthz"
SPIN_CHARS=('|' '/' '-' '\')

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
    local label="${1:-等待 Gateway 就緒}" timeout="${2:-30}"
    printf '\033[34m[INFO]  %s... \033[0m' "$label"
    for ((i = 0; i < timeout; i++)); do
        printf '\b\033[36m%s\033[0m' "${SPIN_CHARS[$((i % 4))]}"
        if result=$(curl -sf --max-time 2 "$HEALTH_URL" 2>/dev/null); then
            if echo "$result" | grep -q '"ok"\s*:\s*true'; then
                printf '\b \n'
                ok "$label — 完成（${i} 秒）"
                return 0
            fi
        fi
        sleep 1
    done
    printf '\b \n'
    warn "$label — 逾時（${timeout} 秒）"
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
        e=$(echo "$yaml" | grep -oP '(?<=^emoji:\s).+' | head -1 | sed "s/[\"' ]//g")
        [[ -n "$e" ]] && emoji="$e"

        # 嘗試 block scalar（| 或 >），再處理單行
        if echo "$yaml" | grep -qP '^description:\s*[|>]'; then
            local first
            first=$(echo "$yaml" | sed -n '/^description:\s*[|>]/,/^[^ ]/{/^  /p;}' | head -1 | sed 's/^ *//')
            [[ -n "$first" ]] && desc="$first"
        else
            local d
            d=$(echo "$yaml" | grep -oP '(?<=^description:\s).+' | head -1 | sed "s/^[\"']//;s/[\"']$//;s/^ *//;s/ *$//")
            [[ -n "$d" ]] && desc="$d"
        fi
    fi

    SKILL_EMOJI="$emoji"
    SKILL_DESC="$desc"
}

# ── 互動式技能選擇介面 ──────────────────────────────────────

show_skill_selector() {
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
        # 計算需要的行數用於清除：header(1) + bar(1) + search(1) + items(fcount or 1) + bar(1) + footer(1) = fcount+5
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

        printf '\033[36m◆  OpenClaw 初始安裝技能工具\033[0m\n'
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
                    # 清除 UI
                    printf '\033[%dA' "$_last_lines"
                    for ((i = 0; i < _last_lines; i++)); do printf '\033[2K\n'; done
                    printf '\033[%dA' "$_last_lines"
                    printf '\033[90m◇  OpenClaw 初始安裝技能工具\033[0m\n'
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
                printf '\033[90m◇  OpenClaw 初始安裝技能工具\033[0m\n'
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
                # 收集結果
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
                printf '\033[36m◇  OpenClaw 初始安裝技能工具\033[0m\n'
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
    rel="${dir#"$SCRIPT_DIR"/}"
    if [[ ! -d "$dir" ]]; then
        mkdir -p "$dir"
        ok "建立目錄：$rel"
    else
        info "目錄已存在：$rel（略過）"
    fi
done

# 2. 部署技能
MODULE_PACK_DIR="$SCRIPT_DIR/module_pack"
SKILLS_TARGET_DIR="$OPENCLAW_DIR/workspace/skills"

if [[ -d "$MODULE_PACK_DIR" ]]; then
    info "掃描 module_pack 中的技能..."

    # 搜尋所有 SKILL.md
    mapfile -t skill_files < <(find "$MODULE_PACK_DIR" -name "SKILL.md" -type f 2>/dev/null)

    if ((${#skill_files[@]} == 0)); then
        info "module_pack 中未找到任何技能。"
    else
        SKILL_NAMES=()
        SKILL_EMOJIS=()
        SKILL_DESCS=()
        SKILL_SOURCES=()
        SKILL_INSTALLED=()

        for sf in "${skill_files[@]}"; do
            skill_dir="$(dirname "$sf")"
            skill_name="$(basename "$skill_dir")"
            get_skill_meta "$sf"
            SKILL_NAMES+=("$skill_name")
            SKILL_EMOJIS+=("$SKILL_EMOJI")
            SKILL_DESCS+=("$SKILL_DESC")
            SKILL_SOURCES+=("$skill_dir")
            if [[ -d "$SKILLS_TARGET_DIR/$skill_name" ]]; then
                SKILL_INSTALLED+=(1)
            else
                SKILL_INSTALLED+=(0)
            fi
        done

        SELECTOR_RESULT=""
        if show_skill_selector; then
            installed=0 removed=0 skipped=0
            for ((i = 0; i < ${#SKILL_NAMES[@]}; i++)); do
                is_selected=0
                for idx in $SELECTOR_RESULT; do
                    if ((idx == i)); then is_selected=1; break; fi
                done

                target_dir="$SKILLS_TARGET_DIR/${SKILL_NAMES[$i]}"

                if ((is_selected && ! SKILL_INSTALLED[i])); then
                    cp -r "${SKILL_SOURCES[$i]}" "$target_dir"
                    ok "部署技能：${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]}"
                    ((installed++))
                elif (( ! is_selected && SKILL_INSTALLED[i])); then
                    rm -rf "$target_dir"
                    ok "移除技能：${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]}"
                    ((removed++))
                else
                    ((skipped++))
                fi
            done
            info "技能處理完成！新部署 $installed 個，移除 $removed 個，略過 $skipped 個。"
        else
            info "已取消任務，無更動。"
        fi
    fi
else
    warn "module_pack 目錄不存在，略過技能部署。"
fi

# 3. 產生 openclaw.json
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

# 4. 複製 .env.example → .env
env_example="$SCRIPT_DIR/.env.example"
env_file="$SCRIPT_DIR/.env"
if [[ ! -f "$env_file" ]]; then
    if [[ -f "$env_example" ]]; then
        cp "$env_example" "$env_file"
        ok "已從 .env.example 複製建立 .env"
    else
        warn ".env.example 不存在，請手動建立 .env 檔案。"
    fi
else
    info ".env 已存在（略過複製）"
fi

# 5. 啟動 Docker Compose
echo ""
info "正在啟動 Docker Compose 服務..."
if docker compose up -d; then
    ok "Docker Compose 服務已啟動"
else
    err "無法啟動 Docker Compose 服務"
    exit 1
fi

# 6. 等待 Gateway 就緒
echo ""
if ! wait_gateway "等待 Gateway 啟動"; then
    err "Gateway 未就緒，請手動檢查容器狀態。"
    exit 1
fi

# 7. 設定 API 金鑰（迴圈，可設定多組）
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

# 7b. 語音轉文字功能（需要 OpenAI API 金鑰）
echo ""
info "語音轉文字功能可將語音訊息自動轉為文字（使用 OpenAI Whisper）。"
if confirm_yes_no "是否要啟用語音轉文字功能？（需要已設定 OpenAI API 金鑰）"; then
    if jq '.tools //= {} |
        .tools.media = {
            "audio": {
                "enabled": true,
                "language": "zh",
                "models": [
                    {
                        "provider": "openai",
                        "model": "whisper-1",
                        "profile": "openai:manual"
                    }
                ],
                "echoTranscript": true
            }
        }' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"; then
        ok "語音轉文字功能已啟用（language=zh, model=whisper-1）"
    else
        err "無法寫入語音設定"
        rm -f "${CONFIG_FILE}.tmp"
    fi
else
    info "略過語音轉文字功能。您可稍後手動編輯 .openclaw/openclaw.json 的 tools.media.audio 區段。"
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

# 9. 裝置配對
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
