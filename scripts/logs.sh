#!/bin/bash
# FireTrain 项目本地开发日志查看脚本

echo "📋 FireTrain 项目日志查看工具"
echo "================================"
echo ""

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录是 scripts 的上一级目录
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "❌ 日志目录不存在"
    exit 1
fi

echo "日志文件列表："
ls -lh "$LOG_DIR"/*.log 2>/dev/null || echo "暂无日志文件"
echo ""

# 选择要查看的日志
echo "请选择要查看的日志："
echo "1) 后端日志 (backend.log)"
echo "2) 前端日志 (frontend.log)"
echo "3) 同时查看两个日志"
echo "4) 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case "$choice" in
    1)
        echo "📄 查看后端日志..."
        if [ -f "$LOG_DIR/backend.log" ]; then
            tail -f "$LOG_DIR/backend.log"
        else
            echo "❌ 后端日志文件不存在"
        fi
        ;;
    2)
        echo "📄 查看前端日志..."
        if [ -f "$LOG_DIR/frontend.log" ]; then
            tail -f "$LOG_DIR/frontend.log"
        else
            echo "❌ 前端日志文件不存在"
        fi
        ;;
    3)
        echo "📄 同时查看两个日志..."
        if [ -f "$LOG_DIR/backend.log" ] && [ -f "$LOG_DIR/frontend.log" ]; then
            echo "--- 后端日志 ---"
            tail -f "$LOG_DIR/backend.log" &
            BACKEND_PID=$!
            sleep 2
            echo ""
            echo "--- 前端日志 ---"
            tail -f "$LOG_DIR/frontend.log"
            kill $BACKEND_PID 2>/dev/null
        else
            echo "❌ 日志文件不存在"
        fi
        ;;
    4)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
