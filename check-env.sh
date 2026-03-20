#!/bin/bash
set -euo pipefail

# ANSI color codes
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

write_info() { echo -e "${BLUE}[INFO]  $1${NC}"; }
write_ok()   { echo -e "${GREEN}[OK]    $1${NC}"; }
write_fail() { echo -e "${RED}[FAIL]  $1${NC}"; }

all_passed=true

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  OpenClaw 環境檢查工具${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# 1. Docker
write_info "檢查 Docker..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version 2>&1) && {
        write_ok "Docker 已安裝 — $docker_version"
        if docker info &> /dev/null; then
            write_ok "Docker Desktop 正在執行"
        else
            write_fail "Docker 已安裝但未啟動，請開啟 Docker Desktop"
            all_passed=false
        fi
    } || {
        write_fail "Docker 未安裝。請參考 1.軟體安裝指引/1.Docker軟體 進行安裝。"
        all_passed=false
    }
else
    write_fail "Docker 未安裝。請參考 1.軟體安裝指引/1.Docker軟體 進行安裝。"
    all_passed=false
fi

echo ""

# 2. VS Code
write_info "檢查 VS Code..."
if command -v code &> /dev/null; then
    code_version=$(code --version 2>&1 | head -n 1)
    if [[ "$code_version" =~ [0-9]+\.[0-9]+\.[0-9]+ ]]; then
        echo -e "${GREEN}[OK] VS Code 已安裝 — 版本 $code_version${NC}"
    else
        echo -e "${RED}[FAIL] VS Code 未安裝。請參考 1.軟體安裝指引/2.VS Code軟體 進行安裝。${NC}"
        all_passed=false
    fi
else
    echo -e "${RED}[FAIL] VS Code 未安裝。請參考 1.軟體安裝指引/2.VS Code軟體 進行安裝。${NC}"
    all_passed=false
fi

echo ""

# 3. ngrok
write_info "檢查 ngrok..."
if command -v ngrok &> /dev/null; then
    ngrok_version=$(ngrok version 2>&1) && {
        write_ok "ngrok 已安裝 — $ngrok_version"
    } || {
        write_fail "ngrok 未安裝。請參考 1.軟體安裝指引/3.ngrok軟體 進行安裝。"
        all_passed=false
    }
else
    write_fail "ngrok 未安裝。請參考 1.軟體安裝指引/3.ngrok軟體 進行安裝。"
    all_passed=false
fi

echo ""
echo -e "${CYAN}========================================${NC}"
if [ "$all_passed" = true ]; then
    write_ok "所有軟體皆已安裝，環境準備就緒！"
else
    write_fail "部分軟體缺少或未啟動，請依照上方提示完成安裝。"
fi
echo -e "${CYAN}========================================${NC}"
echo ""
