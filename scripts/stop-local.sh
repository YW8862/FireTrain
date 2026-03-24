#!/bin/bash
# FireTrain 项目本地开发停止脚本

echo "🛑 正在停止 FireTrain 项目..."

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录是 scripts 的上一级目录
BASE_DIR="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$BASE_DIR/logs"

# 停止后端服务
if [ -f "$LOG_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "📥 停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        
        # 等待进程退出
        for i in {1..10}; do
            if ! ps -p $BACKEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # 如果还在运行，强制终止
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "⚠️  后端服务未退出，强制终止..."
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        
        echo "✅ 后端服务已停止"
    else
        echo "ℹ️  后端服务未运行"
    fi
    rm -f "$LOG_DIR/backend.pid"
else
    echo "ℹ️  后端 PID 文件不存在"
fi

# 停止前端服务
if [ -f "$LOG_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "📥 停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        
        # 等待进程退出
        for i in {1..10}; do
            if ! ps -p $FRONTEND_PID > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        # 如果还在运行，强制终止
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "⚠️  前端服务未退出，强制终止..."
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        
        echo "✅ 前端服务已停止"
    else
        echo "ℹ️  前端服务未运行"
    fi
    rm -f "$LOG_DIR/frontend.pid"
else
    echo "ℹ️  前端 PID 文件不存在"
fi

# 清理日志文件（可选）
read -p "是否清空日志文件？(y/N): " choice
case "$choice" in 
    y|Y)
        rm -f "$LOG_DIR"/*.log
        echo "✅ 日志文件已清空"
        ;;
    *)
        echo "ℹ️  保留日志文件"
        ;;
esac

echo ""
echo "🎉 所有服务已停止"
