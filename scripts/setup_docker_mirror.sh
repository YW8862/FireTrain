#!/bin/bash
# Docker镜像加速器配置脚本

echo "🔧 Docker镜像加速器配置脚本"
echo ""

# 检查是否需要 sudo 权限
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 sudo 运行此脚本"
    echo "   sudo ./setup_docker_mirror.sh"
    exit 1
fi

# 备份现有配置
if [ -f /etc/docker/daemon.json ]; then
    echo "📋 发现现有配置文件，创建备份..."
    cp /etc/docker/daemon.json /etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)
fi

# 创建新的配置文件
cat > /etc/docker/daemon.json << 'EOF'
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1panel.live",
    "https://hub.rat.dev",
    "https://m.daocloud.io",
    "https://mirror.ccs.tencentyun.com"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-level": "warn",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "✅ Docker 配置文件已更新"
echo ""

# 重启 Docker 服务
echo "🔄 正在重启 Docker 服务..."
systemctl daemon-reload
systemctl restart docker

if [ $? -eq 0 ]; then
    echo "✅ Docker 服务重启成功"
else
    echo "❌ Docker 服务重启失败"
    exit 1
fi

echo ""
echo "🎉 Docker镜像加速器配置完成！"
echo ""
echo "测试配置是否生效："
echo "  docker info | grep -A 5 'Registry Mirrors'"
echo ""
echo "尝试拉取镜像："
echo "  docker pull mysql:8.0"
echo ""
