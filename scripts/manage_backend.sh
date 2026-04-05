#!/bin/bash
# FireTrain 后端服务快速启动/重启脚本

echo "🔧 FireTrain 后端服务管理工具"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查端口占用
check_port() {
    if lsof -i :8000 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  8000 端口已被占用${NC}"
        lsof -i :8000 | grep uvicorn
        return 0
    else
        echo -e "${GREEN}✅ 8000 端口可用${NC}"
        return 1
    fi
}

# 停止服务
stop_service() {
    echo "🛑 正在停止后端服务..."
    pkill -f "uvicorn app.main:app"
    sleep 2
    
    if ! check_port; then
        echo -e "${GREEN}✅ 服务已停止${NC}"
    fi
}

# 启动服务
start_service() {
    echo "🚀 正在启动后端服务..."
    cd /home/yw/FireTrain/backend
    
    # 检查是否在虚拟环境中
    if [ ! -d ".venv" ]; then
        echo -e "${RED}❌ 虚拟环境不存在，请先安装依赖${NC}"
        echo "提示：运行以下命令："
        echo "  cd /home/yw/FireTrain/backend"
        echo "  python -m venv .venv"
        echo "  source .venv/bin/activate"
        echo "  pip install -r requirements.txt"
        exit 1
    fi
    
    # 使用 start.sh 启动（会自动激活虚拟环境）
    ./start.sh > /home/yw/FireTrain/logs/backend.log 2>&1 &
    
    # 等待启动
    sleep 5
    
    # 检查是否启动成功
    if curl -k -s --connect-timeout 5 https://127.0.0.1:8000/health | grep -q "ok"; then
        echo -e "${GREEN}✅ 后端服务启动成功！${NC}"
        echo ""
        echo "📋 服务信息："
        echo "   - API 文档：https://117.72.44.96:8000/docs"
        echo "   - 健康检查：https://117.72.44.96:8000/health"
        echo "   - 日志查看：tail -f /home/yw/FireTrain/logs/backend.log"
        echo ""
        return 0
    else
        echo -e "${RED}❌ 启动失败，请查看日志${NC}"
        echo ""
        echo "最后 10 行日志："
        tail -10 /home/yw/FireTrain/logs/backend.log
        echo ""
        return 1
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 2
    start_service
}

# 查看状态
status_service() {
    echo "📊 服务状态检查："
    echo ""
    
    # 检查进程
    if ps aux | grep "uvicorn app.main:app" | grep -v grep > /dev/null; then
        echo -e "${GREEN}✅ 后端进程运行中${NC}"
        ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print "   PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}'
    else
        echo -e "${RED}❌ 后端进程未运行${NC}"
    fi
    
    echo ""
    
    # 检查端口
    if check_port; then
        echo -e "${GREEN}✅ 8000 端口监听中${NC}"
        netstat -tlnp 2>/dev/null | grep 8000 | awk '{print "   监听地址:", $4}'
    else
        echo -e "${RED}❌ 8000 端口未监听${NC}"
    fi
    
    echo ""
    
    # 测试连接
    echo "📡 测试服务连接..."
    if curl -k -s --connect-timeout 5 https://127.0.0.1:8000/health | grep -q "ok"; then
        echo -e "${GREEN}✅ 本地访问正常${NC}"
    else
        echo -e "${RED}❌ 本地访问失败${NC}"
    fi
    
    if curl -k -s --connect-timeout 5 https://117.72.44.96:8000/health | grep -q "ok"; then
        echo -e "${GREEN}✅ 公网访问正常${NC}"
    else
        echo -e "${RED}❌ 公网访问失败${NC}"
    fi
    
    echo ""
}

# 主菜单
show_menu() {
    echo "请选择操作："
    echo "  1) 启动服务"
    echo "  2) 停止服务"
    echo "  3) 重启服务"
    echo "  4) 查看状态"
    echo "  5) 退出"
    echo ""
    read -p "请输入选项 (1-5): " choice
    
    case $choice in
        1)
            if check_port; then
                echo -e "${YELLOW}⚠️  服务已在运行，是否强制重启？${NC}"
                read -p "确认重启 (y/n): " confirm
                if [ "$confirm" = "y" ]; then
                    restart_service
                fi
            else
                start_service
            fi
            ;;
        2)
            stop_service
            ;;
        3)
            restart_service
            ;;
        4)
            status_service
            ;;
        5)
            echo "👋 再见！"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 无效选项${NC}"
            ;;
    esac
}

# 如果直接运行脚本，显示菜单
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    show_menu
fi
