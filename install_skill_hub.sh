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
    parsed_emoji="$(echo "$frontmatter" | sed -n 's/^[[:space:]]*emoji:[[:space:]]*\(.*\)/\1/p' | head -1 | sed "s/^[\"']//;s/[\"']$//" | xargs)"
    if [[ -n "$parsed_emoji" ]]; then
        emoji="$parsed_emoji"
    fi

    # Parse description — block scalar (| or >)
    parsed_desc="$(echo "$frontmatter" | sed -n '/^description:[[:space:]]*[|>]/,/^[^[:space:]]/{
        /^description:/d
        /^[^[:space:]]/d
        p
    }' | head -1 | sed 's/^[[:space:]]*//')"

    if [[ -z "$parsed_desc" ]]; then
        # Parse description — quoted or unquoted single line
        parsed_desc="$(echo "$frontmatter" | sed -n 's/^description:[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)"
    fi
    if [[ -z "$parsed_desc" ]]; then
        parsed_desc="$(echo "$frontmatter" | sed -n "s/^description:[[:space:]]*'\([^']*\)'.*/\1/p" | head -1)"
    fi
    if [[ -z "$parsed_desc" ]]; then
        parsed_desc="$(echo "$frontmatter" | sed -n 's/^description:[[:space:]]*\([^|>].\+\)/\1/p' | head -1 | xargs)"
    fi

    if [[ -n "$parsed_desc" ]]; then
        description="$parsed_desc"
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

# ── 互動式選擇介面 ───────────────────────────────────────────
show_skill_selector() {
    while true; do
        # Count selected
        sel_count=0
        for ((i = 0; i < total; i++)); do
            if [[ "${selected[$i]}" == "true" ]]; then
                ((sel_count++)) || true
            fi
        done

        printf "\n"
        printf "${CYAN}◆  OpenClaw Skill Hub 安裝工具${RESET}\n"
        printf "│\n"

        for ((i = 0; i < total; i++)); do
            # Checkbox marker
            if [[ "${selected[$i]}" == "true" ]]; then
                check="[x]"
            else
                check="[ ]"
            fi

            # Installed tag
            tag=""
            if [[ "${skill_installed[$i]}" == "true" ]]; then
                tag=" (已安裝)"
            fi

            # Truncate description
            desc="${skill_descs[$i]}"
            if [[ ${#desc} -gt 50 ]]; then
                desc="${desc:0:47}..."
            fi

            # Color based on state
            num=$((i + 1))
            line="$check ${skill_emojis[$i]} ${skill_names[$i]} — ${desc}${tag}"

            if [[ "${skill_installed[$i]}" == "true" ]]; then
                printf "│  ${DARK_GRAY}%2d) %s${RESET}\n" "$num" "$line"
            else
                printf "│  ${WHITE}%2d) %s${RESET}\n" "$num" "$line"
            fi
        done

        printf "│\n"
        if [[ $sel_count -gt 0 ]]; then
            printf "${DARK_GRAY}│  輸入編號切換選取 • a: 全選 • n: 全不選 • q: 確認安裝  (已選 %d 個)${RESET}\n" "$sel_count"
        else
            printf "${DARK_GRAY}│  輸入編號切換選取 • a: 全選 • n: 全不選 • q: 確認安裝  (未選擇任何技能)${RESET}\n"
        fi
        printf "\n"

        # Read user input
        read -rp ">>> " input

        case "$input" in
            q|Q)
                return 0
                ;;
            a|A)
                for ((i = 0; i < total; i++)); do
                    selected[$i]="true"
                done
                ;;
            n|N)
                for ((i = 0; i < total; i++)); do
                    selected[$i]="false"
                done
                ;;
            ''|*[!0-9]*)
                # Try to parse space-separated numbers
                valid=false
                for token in $input; do
                    if [[ "$token" =~ ^[0-9]+$ ]]; then
                        idx=$((token - 1))
                        if [[ $idx -ge 0 && $idx -lt $total ]]; then
                            if [[ "${selected[$idx]}" == "true" ]]; then
                                selected[$idx]="false"
                            else
                                selected[$idx]="true"
                            fi
                            valid=true
                        fi
                    fi
                done
                if ! $valid; then
                    write_warn "無效輸入，請輸入技能編號、a、n 或 q。"
                fi
                ;;
            *)
                idx=$((input - 1))
                if [[ $idx -ge 0 && $idx -lt $total ]]; then
                    if [[ "${selected[$idx]}" == "true" ]]; then
                        selected[$idx]="false"
                    else
                        selected[$idx]="true"
                    fi
                else
                    write_warn "編號超出範圍，請輸入 1-$total。"
                fi
                ;;
        esac
    done
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
