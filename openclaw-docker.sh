#!/usr/bin/env bash
# ============================================================
# openclaw-docker.sh — OpenClaw 統一入口腳本 (Docker)
#
# 用法：./openclaw-docker.sh <子命令> [參數...]
#
# 子命令：
#   init              初始化 .openclaw 目錄結構與插件設定
#   deploy-skills     部署技能（module_pack → workspace/skills）
#   check-env         檢查環境相依工具
#   fix-plugin        修復插件問題
#   install-plugins   安裝 / 管理插件
# ============================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")/scripts-docker" && pwd)"

usage() {
    cat <<'USAGE'
用法：./openclaw-docker.sh <子命令> [參數...]

子命令：
  init              初始化 .openclaw 目錄結構與插件設定
  deploy-skills     部署技能（module_pack → workspace/skills）
  check-env         檢查環境相依工具
  fix-plugin        修復插件問題
  install-plugins   安裝 / 管理插件
USAGE
    exit 1
}

if [[ $# -lt 1 ]]; then
    usage
fi

cmd="$1"; shift

case "$cmd" in
    init)             exec "$SCRIPTS_DIR/init-openclaw-docker.sh" "$@" ;;
    deploy-skills)    exec "$SCRIPTS_DIR/deploy-skills-docker.sh" "$@" ;;
    check-env)        exec "$SCRIPTS_DIR/check-env-docker.sh" "$@" ;;
    fix-plugin)       exec "$SCRIPTS_DIR/fix-plugin-docker.sh" "$@" ;;
    install-plugins)  exec "$SCRIPTS_DIR/install-plugins-docker.sh" "$@" ;;
    *)
        echo "錯誤：未知的子命令 '$cmd'" >&2
        echo "" >&2
        usage
        ;;
esac
