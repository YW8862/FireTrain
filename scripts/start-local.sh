#!/bin/bash
# FireTrain 项目本地开发启动脚本（后台运行）

echo "🚀 正在启动 FireTrain 项目（后台运行模式）..."

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 项目根目录是 scripts 的上一级目录
BASE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$BASE_DIR/backend"
FRONTEND_DIR="$BASE_DIR/frontend"
LOG_DIR="$BASE_DIR/logs"

# 创建日志目录
mkdir -p "$LOG_DIR"

echo "📂 项目根目录：$BASE_DIR"
echo "📝 日志目录：$LOG_DIR"

# 释放端口函数
release_port() {
    local port=$1
    echo "🔍 检查 $port 端口占用情况..."
    
    # 检查是否是 Docker 容器占用了端口
    DOCKER_CONTAINER=$(docker ps --filter "publish=$port" --format "{{.ID}} {{.Names}}" 2>/dev/null | head -1)
    if [ ! -z "$DOCKER_CONTAINER" ]; then
        CONTAINER_ID=$(echo $DOCKER_CONTAINER | awk '{print $1}')
        CONTAINER_NAME=$(echo $DOCKER_CONTAINER | awk '{print $2}')
        echo "⚠️  发现 Docker 容器 $CONTAINER_NAME ($CONTAINER_ID) 占用 $port 端口"
        echo "🛑 正在停止 Docker 容器..."
        docker stop $CONTAINER_ID 2>/dev/null
        sleep 2
        echo "✅ Docker 容器已停止"
    fi
    
    # 使用 lsof 查找进程
    PID=$(lsof -t -i:$port 2>/dev/null)
    
    if [ ! -z "$PID" ]; then
        echo "⚠️  发现进程 $PID 占用 $port 端口"
        
        # 尝试优雅终止
        echo "📥 发送 TERM 信号..."
        kill $PID 2>/dev/null || sudo kill $PID 2>/dev/null
        sleep 3
        
        # 检查是否仍然占用
        REMAINING=$(lsof -t -i:$port 2>/dev/null)
        if [ ! -z "$REMAINING" ]; then
            echo "⚠️  进程未退出，强制终止..."
            kill -9 $PID 2>/dev/null || sudo kill -9 $PID 2>/dev/null
            sleep 1
        fi
        
        echo "✅ $port 端口已释放"
    else
        echo "✅ $port 端口可用"
    fi
}

# 释放 8000 和 5173 端口
release_port 8000
release_port 5173

# 启动后端服务
start_backend() {
    echo ""
    echo "🌐 启动后端服务..."
    cd "$BACKEND_DIR"
    
    # 激活虚拟环境
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        echo "✅ 虚拟环境已激活"
    else
        echo "❌ 虚拟环境不存在，请先创建"
        return 1
    fi
    
    # 设置 PYTHONPATH
    export PYTHONPATH="$BACKEND_DIR:$PYTHONPATH"
    
    # 初始化数据库（如果不存在）
    echo "📦 检查数据库..."
    python scripts/init_db.py 2>/dev/null || echo "✅ 数据库已存在"
    
    # 检查 SSL 证书是否存在
    CERT_FILE="$BASE_DIR/certs/cert.pem"
    KEY_FILE="$BASE_DIR/certs/key.pem"
    
    # 启动 uvicorn
    if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
        echo "🔒 检测到 SSL 证书，启用 HTTPS..."
        echo "📖 API 文档地址：https://localhost:8000/docs"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ssl-certfile="$CERT_FILE" --ssl-keyfile="$KEY_FILE" >> "$LOG_DIR/backend.log" 2>&1 &
    else
        echo "⚠️  未检测到 SSL 证书，使用 HTTP..."
        echo "📖 API 文档地址：http://localhost:8000/docs"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> "$LOG_DIR/backend.log" 2>&1 &
    fi
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$LOG_DIR/backend.pid"
    echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
}

# 启动前端服务
start_frontend() {
    echo ""
    echo "🎨 启动前端服务..."
    cd "$FRONTEND_DIR"
    
    # 检查 Node.js 版本
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v)
        echo "✅ Node.js 版本：$NODE_VERSION"
    else
        echo "❌ Node.js 未安装，请先安装"
        return 1
    fi
    
    # 检查 node_modules 是否存在
    if [ ! -d "node_modules" ]; then
        echo "⚠️  node_modules 不存在，正在安装依赖..."
        npm install
    fi
    
    # 启动 Vite 开发服务器
    echo "🚀 启动 Vite 开发服务器..."
    npm run dev >> "$LOG_DIR/frontend.log" 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$LOG_DIR/frontend.pid"
    echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
}

# 等待服务启动
wait_for_services() {
    echo ""
    echo "⏳ 等待服务启动..."
    sleep 5
    
    # 检查后端是否启动成功
    if [ -f "$LOG_DIR/backend.pid" ]; then
        BACKEND_PID=$(cat "$LOG_DIR/backend.pid")
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            echo "✅ 后端服务运行正常"
        else
            echo "❌ 后端服务启动失败，请查看日志：$LOG_DIR/backend.log"
        fi
    fi
    
    # 检查前端是否启动成功
    if [ -f "$LOG_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$LOG_DIR/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            echo "✅ 前端服务运行正常"
        else
            echo "❌ 前端服务启动失败，请查看日志：$LOG_DIR/frontend.log"
        fi
    fi
}

# 显示访问信息
show_access_info() {
    echo ""
    echo "=========================================="
    echo "🎉 FireTrain 项目已成功启动！"
    echo "=========================================="
    echo ""
    echo "📊 访问地址："
    echo "   🌐 前端：http://localhost:5173"
    echo "   🔌 后端 API: http://localhost:8000"
    echo "   📖 API 文档：http://localhost:8000/docs"
    echo ""
    echo "📝 日志文件："
    echo "   后端日志：$LOG_DIR/backend.log"
    echo "   前端日志：$LOG_DIR/frontend.log"
    echo ""
    echo "🛑 停止服务："
    echo "   方式 1: 运行 ./stop.sh"
    echo "   方式 2: kill $(cat $LOG_DIR/backend.pid 2>/dev/null) && kill $(cat $LOG_DIR/frontend.pid 2>/dev/null)"
    echo ""
    echo "📋 查看实时日志："
    echo "   tail -f $LOG_DIR/backend.log"
    echo "   tail -f $LOG_DIR/frontend.log"
    echo "=========================================="
}

# 主流程
start_backend
sleep 2
start_frontend
sleep 3
wait_for_services
show_access_info
