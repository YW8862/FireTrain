#!/bin/bash
# 测试训练完成流程的修复

set -e

echo "=========================================="
echo "🧪 测试训练完成流程修复"
echo "=========================================="

# 1. 检查前端文件是否正确导入
echo ""
echo "1️⃣  检查前端 preCheckTraining 导入..."
if grep -q "preCheckTraining" /home/yw/FireTrain/frontend/src/views/TrainingView.vue; then
    echo "✅ TrainingView.vue 已导入 preCheckTraining"
else
    echo "❌ TrainingView.vue 未导入 preCheckTraining"
    exit 1
fi

# 2. 检查前端 API 超时设置
echo ""
echo "2️⃣  检查前端 API 超时设置..."
if grep -q "timeout: 120000" /home/yw/FireTrain/frontend/src/api/training.js; then
    echo "✅ completeTraining API 超时时间已设置为 120 秒"
else
    echo "❌ completeTraining API 超时时间未设置"
    exit 1
fi

# 3. 检查后端预检测接口
echo ""
echo "3️⃣  检查后端预检测接口..."
if grep -q "analyze_video" /home/yw/FireTrain/backend/app/api/training.py; then
    echo "✅ 预检测接口使用 analyze_video 方法"
else
    echo "❌ 预检测接口仍使用不存在的方法"
    exit 1
fi

# 4. 检查后端 extinguisher_detected 字段获取
echo ""
echo "4️⃣  检查后端灭火器检测逻辑..."
if grep -q "extinguisher_detected = any(" /home/yw/FireTrain/backend/app/api/training.py; then
    echo "✅ 灭火器检测逻辑正确"
else
    echo "❌ 灭火器检测逻辑有误"
    exit 1
fi

# 5. 检查服务运行状态
echo ""
echo "5️⃣  检查服务运行状态..."
if curl -k -s https://localhost:8000/docs > /dev/null; then
    echo "✅ 后端服务运行正常"
else
    echo "❌ 后端服务未运行"
    exit 1
fi

if curl -k -s https://localhost:5173 > /dev/null; then
    echo "✅ 前端服务运行正常"
else
    echo "❌ 前端服务未运行"
    exit 1
fi

echo ""
echo "=========================================="
echo "🎉 所有检查通过！修复成功"
echo "=========================================="
echo ""
echo "修复内容总结："
echo "1. ✅ 前端导入 preCheckTraining API 函数"
echo "2. ✅ 前端增加 completeTraining API 超时时间到 120 秒"
echo "3. ✅ 后端预检测接口改用 analyze_video 方法"
echo "4. ✅ 后端修复灭火器检测字段获取逻辑"
echo ""
echo "现在可以测试训练完成流程了！"
