#!/bin/bash
# FireTrain 后端快速启动脚本

echo "🚀 正在启动 FireTrain 后端服务..."

# 释放 8000 端口（如果已被占用）
echo "🔍 检查 8000 端口占用情况..."

# 检查是否是 Docker 容器占用了端口
DOCKER_CONTAINER=$(docker ps --filter "publish=8000" --format "{{.ID}} {{.Names}}" 2>/dev/null | head -1)
if [ ! -z "$DOCKER_CONTAINER" ]; then
    CONTAINER_ID=$(echo $DOCKER_CONTAINER | awk '{print $1}')
    CONTAINER_NAME=$(echo $DOCKER_CONTAINER | awk '{print $2}')
    echo "⚠️  发现 Docker 容器 $CONTAINER_NAME ($CONTAINER_ID) 占用 8000 端口"
    echo "🛑 正在停止 Docker 容器..."
    docker stop $CONTAINER_ID 2>/dev/null
    sleep 2
    echo "✅ Docker 容器已停止"
fi

# 方法 1: 使用 lsof (不需要 sudo)
PID=$(lsof -t -i:8000 2>/dev/null)

# 方法 2: 使用 fuser (更可靠)
if [ -z "$PID" ]; then
    PID=$(sudo fuser -k 8000/tcp 2>&1 | grep -oP '\K[0-9]+' | head -1)
fi

if [ ! -z "$PID" ]; then
    echo "⚠️  发现进程 $PID 占用 8000 端口"
    
    # 尝试优雅终止
    echo "📥 发送 TERM 信号..."
    kill $PID 2>/dev/null || sudo kill $PID 2>/dev/null
    sleep 3
    
    # 检查是否仍然占用
    REMAINING=$(lsof -t -i:8000 2>/dev/null)
    if [ ! -z "$REMAINING" ]; then
        echo "⚠️  进程未退出，强制终止..."
        kill -9 $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null
        sleep 1
    fi
    
    # 最终检查
    FINAL_CHECK=$(lsof -t -i:8000 2>/dev/null)
    if [ ! -z "$FINAL_CHECK" ]; then
        echo "❌ 无法释放 8000 端口，请手动处理"
        exit 1
    fi
    
    echo "✅ 8000 端口已释放"
else
    echo "✅ 8000 端口可用"
fi

# 激活虚拟环境
source .venv/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH=/home/yw/FireTrain/backend:$PYTHONPATH

# 初始化数据库（如果不存在）
echo "📦 检查数据库..."
python scripts/init_db.py 2>/dev/null || echo "✅ 数据库已存在"

# 启动服务
echo "🌐 启动后端服务..."
echo "📖 API 文档地址：http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
