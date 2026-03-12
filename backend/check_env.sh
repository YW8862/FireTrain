#!/bin/bash
# FireTrain 环境检测和优化安装脚本

set -e

echo "========================================"
echo "🔍 FireTrain 环境检测工具"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. 系统信息检测
echo "📊 系统信息检测"
echo "----------------------------------------"
echo "操作系统：$(uname -s)"
echo "架构：$(uname -m)"
echo "Python 版本：$(python3 --version 2>&1)"
echo ""

# 2. CPU 检测
echo "💻 CPU 信息"
echo "----------------------------------------"
lscpu | grep -E "Model name|CPU\(s\)" || echo "无法获取 CPU 信息"
echo ""

# 3. 内存检测
echo "🧠 内存信息"
echo "----------------------------------------"
free -h | grep -E "Mem|Swap"
echo ""

# 4. GPU 检测
echo "🎮 GPU 检测"
echo "----------------------------------------"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}检测到 NVIDIA GPU:${NC}"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    HAS_GPU="true"
else
    echo -e "${YELLOW}未检测到 NVIDIA GPU${NC}"
    echo "将使用 CPU 模式运行 AI 模型"
    HAS_GPU="false"
fi
echo ""

# 5. 磁盘空间检测
echo "💾 磁盘空间"
echo "----------------------------------------"
df -h /home | tail -1
echo ""

# 6. 检查虚拟环境
echo "📦 虚拟环境检测"
echo "----------------------------------------"
if [ -d ".venv" ]; then
    echo -e "${GREEN}虚拟环境已存在${NC}"
    source .venv/bin/activate
    PYTHON_VERSION=$(python --version 2>&1)
    echo "虚拟环境 Python 版本：$PYTHON_VERSION"
else
    echo -e "${YELLOW}虚拟环境不存在${NC}"
    echo "建议先创建虚拟环境：python3 -m venv .venv"
fi
echo ""

# 7. 检查已安装的包
echo "📚 已安装的 AI 相关包"
echo "----------------------------------------"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pip list 2>/dev/null | grep -iE "torch|numpy|opencv|mediapipe|ultralytics" || echo "未安装相关包"
else
    echo "虚拟环境未激活"
fi
echo ""

# 8. 推荐配置
echo "✨ 推荐配置"
echo "----------------------------------------"
if [ "$HAS_GPU" = "true" ]; then
    echo -e "${GREEN}推荐使用 GPU 加速版本:${NC}"
    echo "  torch==2.2.0 (CUDA 版本)"
    echo "  opencv-python-headless (完整版)"
else
    echo -e "${YELLOW}推荐使用 CPU 版本:${NC}"
    echo "  torch==2.2.0+cpu"
    echo "  opencv-python-headless (无头版，节省空间)"
fi
echo ""

# 9. 提供安装选项
echo "========================================"
echo "🚀 安装选项"
echo "========================================"
echo ""
echo "请选择安装方式:"
echo "1) 快速安装 (使用 requirements.txt)"
echo "2) 优化安装 (根据硬件自动选择版本)"
echo "3) 最小化安装 (仅核心依赖)"
echo "4) 退出"
echo ""
read -p "请输入选项 [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "📦 开始快速安装..."
        source .venv/bin/activate
        pip install -r requirements.txt -q
        echo -e "${GREEN}✅ 安装完成!${NC}"
        ;;
    2)
        echo ""
        echo "📦 开始优化安装..."
        source .venv/bin/activate
        
        # 卸载冲突的包
        echo "清理旧版本..."
        pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true
        
        if [ "$HAS_GPU" = "true" ]; then
            echo "安装 GPU 版本的 PyTorch..."
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 -q
        else
            echo "安装 CPU 版本的 PyTorch..."
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu -q
        fi
        
        # 安装其他依赖
        echo "安装其他依赖..."
        pip install fastapi uvicorn sqlalchemy pydantic -q
        pip install python-jose passlib PyJWT -q
        pip install numpy opencv-python-headless mediapipe ultralytics -q
        
        echo -e "${GREEN}✅ 优化安装完成!${NC}"
        ;;
    3)
        echo ""
        echo "📦 开始最小化安装..."
        source .venv/bin/activate
        
        # 只安装核心依赖
        echo "安装核心 Web 框架..."
        pip install fastapi uvicorn sqlalchemy pydantic -q
        
        echo "安装认证相关..."
        pip install python-jose passlib PyJWT -q
        
        echo -e "${GREEN}✅ 最小化安装完成!${NC}"
        echo "提示：后续可以根据需要安装 AI 相关包"
        ;;
    4)
        echo "退出安装"
        exit 0
        ;;
    *)
        echo "无效的选项"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "✅ 环境检测完成"
echo "========================================"
echo ""
echo "下一步操作:"
echo "1. 激活虚拟环境：source .venv/bin/activate"
echo "2. 初始化数据库：cd backend && python scripts/init_db.py"
echo "3. 启动后端服务：./start.sh"
echo "4. 访问 API 文档：http://localhost:8000/docs"
echo ""
