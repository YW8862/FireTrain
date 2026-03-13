#!/bin/bash

# FireTrain 测试数据准备脚本
# 用于创建测试账号和准备测试视频

set -e

echo "======================================"
echo "🔧 FireTrain 测试数据准备"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Docker 服务状态
check_docker_status() {
    echo -e "\n📊 检查 Docker 服务状态..."
    if docker compose ps | grep -q "firetrain"; then
        echo -e "${GREEN}✅ Docker 服务正在运行${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Docker 服务未运行，正在启动...${NC}"
        make docker-up
        sleep 10
    fi
}

# 创建测试账号
create_test_users() {
    echo -e "\n👤 创建测试账号..."
    
    # 在 Docker 容器内执行 Python 脚本
    docker compose exec -T backend python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app.db.base import Base
from app.db.session import engine
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.schemas.user import UserRegisterRequest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

async def create_test_user(username, email, password, phone, role="student"):
    """创建测试用户"""
    async with async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        user_repo = UserRepository(session)
        user_service = UserService(user_repo)
        
        # 检查用户是否已存在
        existing_user = await user_repo.get_by_username(username)
        if existing_user:
            print(f"⚠️  用户 {username} 已存在，跳过")
            return
        
        # 创建新用户
        user_data = UserRegisterRequest(
            username=username,
            email=email,
            password=password,
            phone=phone
        )
        
        try:
            user = await user_service.register(user_data)
            print(f"✅ 用户 {username} 创建成功 (ID: {user.id})")
            await session.commit()
        except Exception as e:
            print(f"❌ 创建用户 {username} 失败：{e}")
            await session.rollback()

async def main():
    """主函数"""
    print("\n开始创建测试用户...\n")
    
    # 测试用户列表
    test_users = [
        {
            "username": "student001",
            "email": "student001@firetrain.com",
            "password": "Test123456",
            "phone": "13800138001"
        },
        {
            "username": "admin001",
            "email": "admin001@firetrain.com",
            "password": "Admin123456",
            "phone": "13800138002"
        },
        {
            "username": "testuser",
            "email": "test@firetrain.com",
            "password": "test123456",
            "phone": "13800138000"
        }
    ]
    
    # 创建所有测试用户
    for user_info in test_users:
        await create_test_user(**user_info)
    
    print("\n✅ 所有测试用户创建完成！\n")

if __name__ == "__main__":
    asyncio.run(main())
PYTHON_SCRIPT
}

# 创建测试视频目录
create_test_video_directories() {
    echo -e "\n📁 创建测试视频目录..."
    
    mkdir -p data/videos/test_videos
    mkdir -p backend/data/videos/test_videos
    
    echo -e "${GREEN}✅ 测试视频目录创建成功${NC}"
    echo "   路径：data/videos/test_videos/"
}

# 生成测试视频（使用 FFmpeg）
generate_test_videos() {
    echo -e "\n🎬 生成测试视频..."
    
    # 检查是否安装了 ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${YELLOW}⚠️  FFmpeg 未安装，跳过测试视频生成${NC}"
        echo "   可以手动添加测试视频到 data/videos/test_videos/ 目录"
        return 0
    fi
    
    VIDEO_DIR="data/videos/test_videos"
    
    # 视频 1: 标准操作流程（60 秒黑屏视频）
    echo "   生成 standard_extinguisher_demo.mp4..."
    ffmpeg -f lavfi -i color=c=blue:s=1920x1080:d=60 \
           -f lavfi -i anullsrc=r=44100:cl=stereo \
           -c:v libx264 -c:a aac \
           -pix_fmt yuv420p \
           "$VIDEO_DIR/standard_extinguisher_demo.mp4" \
           -y 2>/dev/null
    
    # 视频 2: 常见错误操作（45 秒黑屏视频）
    echo "   生成 common_errors_demo.mp4..."
    ffmpeg -f lavfi -i color=c=red:s=1920x1080:d=45 \
           -f lavfi -i anullsrc=r=44100:cl=stereo \
           -c:v libx264 -c:a aac \
           -pix_fmt yuv420p \
           "$VIDEO_DIR/common_errors_demo.mp4" \
           -y 2>/dev/null
    
    # 视频 3: 不完整流程（30 秒黑屏视频）
    echo "   生成 incomplete_process_demo.mp4..."
    ffmpeg -f lavfi -i color=c=green:s=1920x1080:d=30 \
           -f lavfi -i anullsrc=r=44100:cl=stereo \
           -c:v libx264 -c:a aac \
           -pix_fmt yuv420p \
           "$VIDEO_DIR/incomplete_process_demo.mp4" \
           -y 2>/dev/null
    
    echo -e "${GREEN}✅ 测试视频生成完成${NC}"
    ls -lh "$VIDEO_DIR"/*.mp4
}

# 验证测试数据
verify_test_data() {
    echo -e "\n✅ 验证测试数据..."
    
    # 检查测试用户
    echo "\n测试账号:"
    echo "  1. student001 / Test123456"
    echo "  2. admin001 / Admin123456"
    echo "  3. testuser / test123456"
    
    # 检查测试视频
    echo -e "\n测试视频:"
    if [ -d "data/videos/test_videos" ]; then
        ls -lh data/videos/test_videos/*.mp4 2>/dev/null || echo "  (暂无测试视频文件)"
    else
        echo "  目录不存在"
    fi
    
    # 测试 API 连接
    echo -e "\n🔗 测试 API 连接..."
    if curl -s http://localhost:8000/docs > /dev/null; then
        echo -e "${GREEN}✅ 后端 API 可访问${NC} (http://localhost:8000)"
    else
        echo -e "${RED}❌ 后端 API 无法访问${NC}"
    fi
    
    if curl -s http://localhost:5173 > /dev/null; then
        echo -e "${GREEN}✅ 前端页面可访问${NC} (http://localhost:5173)"
    else
        echo -e "${YELLOW}⚠️  前端页面无法访问${NC}"
    fi
}

# 打印使用说明
print_usage() {
    echo -e "\n======================================"
    echo "📋 测试数据使用说明"
    echo "======================================"
    
    cat << 'EOF'

🎯 测试账号:

1. 普通学员账号
   用户名：student001
   密码：Test123456
   用途：测试学生角色功能

2. 管理员账号
   用户名：admin001
   密码：Admin123456
   用途：测试管理员权限功能

3. 测试专用账号
   用户名：testuser
   密码：test123456
   用途：快速验证和自动化测试

🎬 测试视频位置:

data/videos/test_videos/
├── standard_extinguisher_demo.mp4    (60 秒，标准操作)
├── common_errors_demo.mp4           (45 秒，错误操作)
└── incomplete_process_demo.mp4      (30 秒，不完整流程)

🔗 API 测试:

# 注册
curl -X POST http://localhost:8000/api/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "student001",
    "email": "student001@firetrain.com",
    "password": "Test123456",
    "phone": "13800138001"
  }'

# 登录
curl -X POST http://localhost:8000/api/user/login \
  -d "username=student001&password=Test123456"

# 获取用户信息
curl -X GET http://localhost:8000/api/user/profile \
  -H "Authorization: Bearer YOUR_TOKEN"

📖 详细文档:

查看 docs/联调记录.md 获取完整的 API 文档和测试用例

======================================
EOF
}

# 主流程
main() {
    check_docker_status
    create_test_users
    create_test_video_directories
    generate_test_videos
    verify_test_data
    print_usage
    
    echo -e "\n${GREEN}======================================"
    echo "✅ 测试数据准备完成！"
    echo -e "======================================${NC}\n"
}

# 执行主流程
main
