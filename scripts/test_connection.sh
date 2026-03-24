#!/bin/bash
# FireTrain 服务连接测试脚本

echo "🔍 FireTrain 服务连接测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果计数
PASS=0
FAIL=0

# 测试函数
test_connection() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "测试：$name ... "
    
    if curl -k -s --connect-timeout 5 "$url" | grep -q "$expected"; then
        echo -e "${GREEN}✅ 通过${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ 失败${NC}"
        ((FAIL++))
        return 1
    fi
}

test_port() {
    local name=$1
    local port=$2
    
    echo -n "检查端口 $port ($name) ... "
    
    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 监听中${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}❌ 未监听${NC}"
        ((FAIL++))
        return 1
    fi
}

# 1. 检查端口
echo "📊 步骤 1: 检查服务端口"
echo "--------------------------------------"
test_port "后端服务" 8000
test_port "前端服务" 5173
echo ""

# 2. 测试后端 API
echo "📊 步骤 2: 测试后端 API"
echo "--------------------------------------"
test_connection "后端健康检查 (localhost)" "https://localhost:8000/health" '"status":"ok"'
test_connection "后端健康检查 (公网 IP)" "https://117.72.44.96:8000/health" '"status":"ok"'
test_connection "后端根路径" "https://117.72.44.96:8000/" "FireTrain"
echo ""

# 3. 测试前端（如果运行）
echo "📊 步骤 3: 测试前端服务"
echo "--------------------------------------"
if lsof -i :5173 > /dev/null 2>&1; then
    test_connection "前端首页 (localhost)" "https://localhost:5173" "FireTrain"
    test_connection "前端首页 (公网 IP)" "https://117.72.44.96:5173" "FireTrain"
else
    echo -e "${YELLOW}⚠️  前端服务未运行，跳过测试${NC}"
fi
echo ""

# 4. 显示进程信息
echo "📊 步骤 4: 当前运行的服务"
echo "--------------------------------------"
echo "后端服务:"
ps aux | grep uvicorn | grep -v grep | awk '{print "  PID:", $2, "状态:", $8}'
echo ""
echo "前端服务:"
ps aux | grep vite | grep -v grep | awk '{print "  PID:", $2, "状态:", $8}'
echo ""

# 5. 总结
echo "======================================"
echo "📋 测试总结"
echo "======================================"
echo -e "通过：${GREEN}$PASS${NC}"
echo -e "失败：${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    echo ""
    echo "📋 正确的访问方式："
    echo "   • 本地开发（前端）：https://localhost:5173"
    echo "   • 本地开发（后端）：https://localhost:8000/docs"
    echo "   • 远程访问（后端）：https://117.72.44.96:8000/docs"
    echo "   • 生产环境部署：请使用 Docker 或 Nginx"
else
    echo -e "${RED}❌ 部分测试失败，请检查相关服务${NC}"
fi

echo ""
exit $FAIL
