#!/bin/bash
# 完成训练功能测试脚本

echo "🎯 完成训练功能测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试 API
BASE_URL="https://117.72.44.96:8000"
TOKEN=""

echo -e "${YELLOW}步骤 1: 检查后端服务${NC}"
if curl -k -s --connect-timeout 5 "$BASE_URL/health" | grep -q "ok"; then
    echo -e "${GREEN}✅ 后端服务运行正常${NC}"
else
    echo -e "${RED}❌ 后端服务未运行${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤 2: 模拟登录获取 Token${NC}"
# 这里假设有测试账号，实际使用时需要替换
read -p "请输入测试用户名：" USERNAME
read -sp "请输入测试密码：" PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -k -s -X POST "$BASE_URL/api/user/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

if echo "$LOGIN_RESPONSE" | grep -q "token"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
    echo -e "${GREEN}✅ 登录成功${NC}"
else
    echo -e "${RED}❌ 登录失败：$LOGIN_RESPONSE${NC}"
    echo "提示：如果没有测试账号，请先注册或查看后端日志"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤 3: 开始训练${NC}"
START_RESPONSE=$(curl -k -s -X POST "$BASE_URL/api/training/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"training_type": "fire_extinguisher", "duration_seconds": 120}')

if echo "$START_RESPONSE" | grep -q "training_id"; then
    TRAINING_ID=$(echo "$START_RESPONSE" | jq -r '.training_id')
    echo -e "${GREEN}✅ 训练已开始 (ID: $TRAINING_ID)${NC}"
else
    echo -e "${RED}❌ 开始训练失败：$START_RESPONSE${NC}"
    exit 1
fi
echo ""

echo -e "${YELLOW}步骤 4: 完成训练（不上传视频）${NC}"
echo "注意：此步骤将测试无视频路径情况下的完成训练功能"
echo ""

COMPLETE_RESPONSE=$(curl -k -s -X POST "$BASE_URL/api/training/complete/$TRAINING_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "响应内容:"
echo "$COMPLETE_RESPONSE" | jq .
echo ""

if echo "$COMPLETE_RESPONSE" | grep -q "total_score"; then
    STATUS=$(echo "$COMPLETE_RESPONSE" | jq -r '.status')
    SCORE=$(echo "$COMPLETE_RESPONSE" | jq -r '.total_score')
    FEEDBACK=$(echo "$COMPLETE_RESPONSE" | jq -r '.feedback')
    
    if [ "$STATUS" = "done" ]; then
        echo -e "${GREEN}✅ 完成训练成功！${NC}"
        echo "   总分：$SCORE"
        echo "   反馈：$FEEDBACK"
        echo ""
        echo -e "${GREEN}📝 测试通过：无视频路径也可以正常完成训练并使用模拟评分${NC}"
    else
        echo -e "${YELLOW}⚠️  状态异常：$STATUS${NC}"
    fi
elif echo "$COMPLETE_RESPONSE" | grep -q "视频路径为空"; then
    echo -e "${RED}❌ 测试失败：仍然提示视频路径为空${NC}"
    echo "请检查后端代码是否已正确修改并重启服务"
    exit 1
else
    ERROR_MSG=$(echo "$COMPLETE_RESPONSE" | jq -r '.detail // .message // "未知错误"')
    echo -e "${RED}❌ 完成训练失败：$ERROR_MSG${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo "📋 测试总结"
echo "======================================"
echo ""
echo "✅ 测试项目："
echo "  1. 后端服务正常运行"
echo "  2. 用户登录成功"
echo "  3. 开始训练成功"
echo "  4. 无视频路径完成训练成功"
echo ""
echo "🎉 功能已修复！现在可以无视频完成训练"
echo ""
echo "💡 下一步："
echo "  1. 在前端页面测试完成训练功能"
echo "  2. 访问：https://117.72.44.96:5173/training"
echo "  3. 开始训练 → 等待几秒 → 完成训练"
echo "  4. 确认可以看到评分和反馈"
echo ""
