#!/bin/bash
# 前端服务启动脚本 - 自动释放端口

echo "🚀 正在启动 FireTrain 前端服务..."

# 检查并释放 5173 端口
PORT=5173
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "⚠️  端口 $PORT 被占用 (PID: $PID)，正在释放..."
    kill -9 $PID 2>/dev/null
    sleep 1
    
    # 确认端口已释放
    REMAINING_PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$REMAINING_PID" ]; then
        echo "❌ 无法释放端口 $PORT，请手动处理"
        exit 1
    else
        echo "✅ 端口 $PORT 已释放"
    fi
else
    echo "✅ 端口 $PORT 可用"
fi

# 启动 Vite 开发服务器
echo "📦 启动 Vite 开发服务器..."
cd /home/yw/FireTrain/frontend
npm run dev
