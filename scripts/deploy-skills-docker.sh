#!/usr/bin/env bash
# ============================================================
# deploy-skills-docker.sh — 部署技能（module_pack → workspace/skills）(Docker)
#
# 用法：./scripts/deploy-skills-docker.sh
#
# 掃描 module_pack 目錄中的技能（透過 SKILL.md），提供互動式
# 選擇介面讓使用者勾選要部署或移除的技能。
# ============================================================

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

# ════════════════════════════════════════════════════════════════
# 主流程
# ════════════════════════════════════════════════════════════════

MODULE_PACK_DIR="$PROJECT_ROOT/module_pack"
SKILLS_TARGET_DIR="$OPENCLAW_DIR/workspace/skills"

# 確保目標目錄存在
if [[ ! -d "$SKILLS_TARGET_DIR" ]]; then
    mkdir -p "$SKILLS_TARGET_DIR"
    ok "建立目錄：.openclaw/workspace/skills"
fi

if [[ ! -d "$MODULE_PACK_DIR" ]]; then
    warn "module_pack 目錄不存在，略過技能部署。"
    exit 0
fi

info "掃描 module_pack 中的技能..."

# 搜尋所有 SKILL.md
mapfile -t skill_files < <(find "$MODULE_PACK_DIR" -name "SKILL.md" -type f 2>/dev/null)

if ((${#skill_files[@]} == 0)); then
    info "module_pack 中未找到任何技能。"
    exit 0
fi

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
if show_skill_selector "OpenClaw 技能部署工具"; then
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
            installed=$((installed + 1))
        elif (( ! is_selected && SKILL_INSTALLED[i])); then
            rm -rf "$target_dir"
            ok "移除技能：${SKILL_EMOJIS[$i]} ${SKILL_NAMES[$i]}"
            removed=$((removed + 1))
        else
            skipped=$((skipped + 1))
        fi
    done
    info "技能處理完成！新部署 $installed 個，移除 $removed 個，略過 $skipped 個。"
else
    info "已取消任務，無更動。"
fi
