#!/bin/bash
# ============================================================
# install_skill_hub.sh — 互動式安裝 skill_hub 擴充技能
#
# 用法：
#   ./install_skill_hub.sh
#
# 此腳本會：
#   1. 掃描 skill_hub/ 中含 SKILL.md 的技能目錄
#   2. 顯示互動式選擇介面供使用者挑選
#   3. 將選擇的技能複製至 .openclaw/workspace/skills/
# ============================================================

set -euo pipefail

# ── Global cleanup on Ctrl+C / exit ──────────────────────────
cleanup() {
    printf '\033[?25h'
    echo ""
    echo -e '\033[0;33m[WARN]  腳本已中斷。\033[0m'
    exit 130
}
trap cleanup INT TERM

# ── 路徑 ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_HUB_DIR="$SCRIPT_DIR/skill_hub"
SKILLS_TARGET_DIR="$SCRIPT_DIR/.openclaw/workspace/skills"

# ── ANSI 顏色 ──────────────────────────────────────────────
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
DARK_GRAY='\033[1;30m'
WHITE='\033[1;37m'
RESET='\033[0m'

write_info()  { printf "${BLUE}[INFO]  %s${RESET}\n" "$1"; }
write_ok()    { printf "${GREEN}[OK]    %s${RESET}\n" "$1"; }
write_warn()  { printf "${YELLOW}[WARN]  %s${RESET}\n" "$1"; }

# ── 檢查 skill_hub 目錄 ──────────────────────────────────────
if [[ ! -d "$SKILL_HUB_DIR" ]]; then
    write_warn "skill_hub 目錄不存在，無可安裝的擴充技能。"
    exit 0
fi

# ── 掃描技能 ──────────────────────────────────────────────────
skill_names=()
skill_emojis=()
skill_descs=()
skill_sources=()
skill_installed=()

while IFS= read -r skill_md; do
    skill_dir="$(dirname "$skill_md")"
    skill_name="$(basename "$skill_dir")"

    # Parse YAML frontmatter
    emoji="📦"
    description="(無描述)"

    # Extract frontmatter block (between first --- and second ---)
    frontmatter=""
    in_frontmatter=false
    found_start=false
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if $found_start; then
                break
            else
                found_start=true
                in_frontmatter=true
                continue
            fi
        fi
        if $in_frontmatter; then
            frontmatter+="$line"$'\n'
        fi
    done < "$skill_md"

    # Parse emoji (supports both top-level and nested e.g. metadata.openclaw.emoji)
    parsed_emoji="$(echo "$frontmatter" | sed -n 's/^[[:space:]]*emoji:[[:space:]]*\(.*\)/\1/p' | head -1 | sed "s/[\"']//g" | tr -d '[:space:]')"
    if [[ -n "$parsed_emoji" ]]; then
        emoji="$parsed_emoji"
    fi

    # Parse description: first line of content after "description:"
    # Handles: quoted multi-line, block scalar (|/>), single-line quoted/unquoted
    local desc_line
    desc_line="$(echo "$frontmatter" | grep -m1 '^description:' | sed 's/^description:[[:space:]]*//')"

    if [[ "$desc_line" == "|" || "$desc_line" == ">" ]]; then
        # Block scalar: take first indented line
        desc_line="$(echo "$frontmatter" | sed -n '/^description:[[:space:]]*[|>]/,/^[^[:space:]]/{
            /^description:/d
            /^[^[:space:]]/d
            p
        }' | head -1 | sed 's/^[[:space:]]*//')"
    else
        # Remove surrounding/leading quotes; handle unclosed multiline quotes
        desc_line="$(echo "$desc_line" | sed "s/^[\"']//;s/[\"']$//")"
    fi

    if [[ -n "$desc_line" ]]; then
        description="$desc_line"
    fi

    # Check if already installed
    installed=false
    if [[ -d "$SKILLS_TARGET_DIR/$skill_name" ]]; then
        installed=true
    fi

    skill_names+=("$skill_name")
    skill_emojis+=("$emoji")
    skill_descs+=("$description")
    skill_sources+=("$skill_dir")
    skill_installed+=("$installed")
done < <(find "$SKILL_HUB_DIR" -name "SKILL.md" -type f | sort)

total=${#skill_names[@]}

if [[ $total -eq 0 ]]; then
    write_warn "skill_hub 中未找到任何技能（無 SKILL.md）。"
    exit 0
fi

# ── 初始化選擇狀態 ────────────────────────────────────────────
selected=()
for ((i = 0; i < total; i++)); do
    selected+=("${skill_installed[$i]}")
done

# ── 互動式選擇介面 (TUI with arrow keys) ────────────────────
show_skill_selector() {
    local cursor=0
    local total_lines=$(( total + 4 ))  # title + │ + items + │ + hint

    # Hide cursor (global trap handles restore)
    printf '\033[?25l'

    # Reserve space
    for (( i=0; i<total_lines; i++ )); do printf '\n'; done
    printf "\033[${total_lines}A"

    while true; do
        printf '\033[0G'

        # Count selected
        local sel_count=0
        for ((i = 0; i < total; i++)); do
            [[ "${selected[$i]}" == "true" ]] && ((sel_count++)) || true
        done

        # Title
        printf '\033[2K'
        printf "${CYAN}◆  OpenClaw Skill Hub 安裝工具${RESET}\n"
        printf '\033[2K'
        printf "│\n"

        # Skill list
        for ((i = 0; i < total; i++)); do
            printf '\033[2K'
            local check="◻"
            [[ "${selected[$i]}" == "true" ]] && check="◼"
            local tag=""
            [[ "${skill_installed[$i]}" == "true" ]] && tag=" (已安裝)"
            local desc="${skill_descs[$i]}"
            [[ ${#desc} -gt 50 ]] && desc="${desc:0:47}..."
            local color="${RESET}"
            if [[ $i -eq $cursor ]]; then
                color="${CYAN}"
            elif [[ "${skill_installed[$i]}" == "true" ]]; then
                color="${DARK_GRAY}"
            fi
            local pointer=" "
            [[ $i -eq $cursor ]] && pointer=">"
            printf "${color}│  ${pointer} ${check} ${skill_emojis[$i]} ${skill_names[$i]} — ${desc}${tag}${RESET}\n"
        done

        # Footer
        printf '\033[2K'
        printf "│\n"
        printf '\033[2K'
        local status
        [[ $sel_count -gt 0 ]] && status="(已選 ${sel_count} 個)" || status="(未選擇任何技能)"
        printf "${DARK_GRAY}│  ↑/↓ 移動 • Space: 選取 • a: 全選 • n: 全不選 • Enter: 確認  ${status}${RESET}\n"

        # Move back up
        printf "\033[${total_lines}A"

        # Read keypress
        local key
        IFS= read -rsn1 key

        case "$key" in
            $'\x1b')
                local seq
                IFS= read -rsn2 -t 0.1 seq
                case "$seq" in
                    '[A') (( cursor > 0 )) && (( cursor-- )) || true ;;
                    '[B') (( cursor < total - 1 )) && (( cursor++ )) || true ;;
                esac
                ;;
            ' ') # Space: toggle
                if [[ "${selected[$cursor]}" == "true" ]]; then
                    selected[$cursor]="false"
                else
                    selected[$cursor]="true"
                fi
                ;;
            'a'|'A')
                for ((i = 0; i < total; i++)); do selected[$i]="true"; done
                ;;
            'n'|'N')
                for ((i = 0; i < total; i++)); do selected[$i]="false"; done
                ;;
            '') # Enter: confirm
                break
                ;;
        esac
    done

    # Move past drawing area and show cursor
    printf "\033[${total_lines}B"
    printf '\033[?25h'
}

show_skill_selector

# ── 顯示最終選擇摘要 ──────────────────────────────────────────
sel_count=0
sel_names=""
for ((i = 0; i < total; i++)); do
    if [[ "${selected[$i]}" == "true" ]]; then
        ((sel_count++)) || true
        if [[ -n "$sel_names" ]]; then
            sel_names+=", "
        fi
        sel_names+="${skill_emojis[$i]} ${skill_names[$i]}"
    fi
done

printf "\n"
printf "${CYAN}◇  OpenClaw Skill Hub 安裝工具${RESET}\n"
if [[ $sel_count -gt 0 ]]; then
    printf "${GREEN}│  已選擇: %s${RESET}\n" "$sel_names"
else
    printf "${DARK_GRAY}│  未選擇任何技能${RESET}\n"
fi
printf "\n"

# ── 確保目標目錄存在 ──────────────────────────────────────────
if [[ ! -d "$SKILLS_TARGET_DIR" ]]; then
    mkdir -p "$SKILLS_TARGET_DIR"
    write_ok "建立目錄：.openclaw/workspace/skills"
fi

# ── 安裝與移除技能 ──────────────────────────────────────────────────
count_installed=0
count_removed=0
count_skipped=0

for ((i = 0; i < total; i++)); do
    is_selected="${selected[$i]}"
    was_installed="${skill_installed[$i]}"
    target_dir="$SKILLS_TARGET_DIR/${skill_names[$i]}"

    if [[ "$is_selected" == "true" && "$was_installed" == "false" ]]; then
        cp -r "${skill_sources[$i]}" "$target_dir"
        write_ok "安裝技能：${skill_emojis[$i]} ${skill_names[$i]} → .openclaw/workspace/skills/${skill_names[$i]}"
        ((count_installed++)) || true
    elif [[ "$is_selected" == "false" && "$was_installed" == "true" ]]; then
        if [[ -d "$target_dir" ]]; then
            rm -rf "$target_dir"
            write_ok "移除技能：${skill_emojis[$i]} ${skill_names[$i]}"
            ((count_removed++)) || true
        fi
    else
        ((count_skipped++)) || true
    fi
done

# ── 摘要 ──────────────────────────────────────────────────────
printf "\n"
printf "${CYAN}========================================${RESET}\n"
write_ok "處理完成！新安裝 $count_installed 個，移除 $count_removed 個，略過 $count_skipped 個。"
printf "${CYAN}========================================${RESET}\n"
printf "\n"
