#!/bin/bash
# FireTrain 后端快速启动脚本

echo "🚀 正在启动 FireTrain 后端服务..."

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
