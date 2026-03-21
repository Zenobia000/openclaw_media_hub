#!/usr/bin/env bash
# ============================================================
# openclaw.sh — OpenClaw 統一入口腳本
#
# 用法：./openclaw.sh <子命令> [參數...]
#
# 子命令：
#   init              初始化 .openclaw 目錄結構與插件設定
#   check-env         檢查環境相依工具
#   fix-plugin        修復插件問題
#   install-plugins   安裝 / 管理插件
# ============================================================

set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")/scripts" && pwd)"

usage() {
    cat <<'USAGE'
用法：./openclaw.sh <子命令> [參數...]

子命令：
  init              初始化 .openclaw 目錄結構與插件設定
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
    init)             exec "$SCRIPTS_DIR/init-openclaw.sh" "$@" ;;
    check-env)        exec "$SCRIPTS_DIR/check-env.sh" "$@" ;;
    fix-plugin)       exec "$SCRIPTS_DIR/fix-plugin.sh" "$@" ;;
    install-plugins)  exec "$SCRIPTS_DIR/install-plugins.sh" "$@" ;;
    *)
        echo "錯誤：未知的子命令 '$cmd'" >&2
        echo "" >&2
        usage
        ;;
esac
