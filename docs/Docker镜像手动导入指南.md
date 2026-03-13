# Docker 镜像手动导入指南

## 📋 概述

当网络受限无法直接从 Docker Hub 拉取镜像时，可以通过以下方式手动导入镜像。

## 方法一：从其他机器导出/导入（推荐）

### 1. 在有网络的机器上下载镜像

```bash
# 拉取镜像
docker pull mysql:8.0

# 导出为 tar 文件
docker save mysql:8.0 -o mysql-8.0.tar

# 可选：压缩文件
gzip mysql-8.0.tar
# 生成 mysql-8.0.tar.gz
```

### 2. 传输到目标机器

```bash
# 使用 scp 传输
scp mysql-8.0.tar user@target-machine:/path/to/

# 或使用 U 盘、移动硬盘等物理方式复制
```

### 3. 在目标机器上导入

```bash
# 如果文件被压缩，先解压
gunzip mysql-8.0.tar.gz

# 导入镜像
docker load -i mysql-8.0.tar

# 验证导入
docker images | grep mysql
```

## 方法二：使用国内镜像加速器

### 配置 Docker 镜像加速器

编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com"
  ]
}
```

重启 Docker：

```bash
sudo systemctl daemon-reload
sudo systemctl restart docker
```

然后直接拉取：

```bash
docker pull mysql:8.0
```

## 方法三：从 Docker 镜像仓库下载

### 使用阿里云容器镜像服务

1. 访问 [阿里云镜像仓库](https://cr.console.aliyun.com/)
2. 搜索需要的镜像
3. 按照指引拉取

```bash
# 示例：使用阿里云镜像
docker pull registry.cn-hangzhou.aliyuncs.com/library/mysql:8.0
```

### 使用腾讯云镜像

```bash
docker pull ccr.ccs.tencentyun.com/library/mysql:8.0
```

## 方法四：离线安装包方式

### 1. 下载镜像分层文件

在一些提供 Docker 镜像下载的网站获取：
- [Docker 镜像中文网](https://www.dockerinfo.net/)
- [开源中国镜像站](https://mirrors.oschina.net/)

### 2. 导入分层镜像

```bash
# 通常是一个包含多个文件的目录
docker load -i /path/to/image.tar
```

## 🎯 FireTrain 项目所需镜像

根据你的 `docker-compose.yml`，需要以下镜像：

```yaml
mysql:8.0          # MySQL 数据库
python:3.10-slim   # Python 后端（自动构建）
node:20-slim       # Node.js 前端（自动构建）
```

## 📦 快速操作脚本

创建一键导入脚本：

```bash
#!/bin/bash
# import_images.sh

echo "📦 开始导入 Docker 镜像..."

# 检查文件是否存在
if [ -f "mysql-8.0.tar" ]; then
    echo "正在导入 mysql:8.0..."
    docker load -i mysql-8.0.tar
else
    echo "❌ 未找到 mysql-8.0.tar 文件"
    exit 1
fi

echo ""
echo "✅ 镜像导入完成！"
echo ""
echo "可用镜像列表："
docker images | grep -E "mysql|python|node"
```

使用方法：

```bash
chmod +x import_images.sh
./import_images.sh
```

## 🔍 验证镜像

导入后验证：

```bash
# 查看所有镜像
docker images

# 查看特定镜像详情
docker inspect mysql:8.0

# 测试运行
docker run --rm mysql:8.0 --version
```

## ⚡ 完整流程示例

### 场景：从开发机传输到生产机

```bash
# === 开发机（有网络）===
# 1. 拉取所有需要的镜像
docker pull mysql:8.0
docker pull python:3.10-slim
docker pull node:20-slim

# 2. 导出所有镜像
docker save mysql:8.0 -o firetrain-images.tar
docker save python:3.10-slim >> firetrain-images.tar
docker save node:20-slim >> firetrain-images.tar

# 3. 压缩
tar -czf firetrain-images.tar.gz firetrain-images.tar

# 4. 传输（通过 scp 或其他方式）
scp firetrain-images.tar.gz user@production-server:/opt/

# === 生产机（无网络）===
# 1. 解压
tar -xzf firetrain-images.tar.gz

# 2. 导入
docker load -i firetrain-images.tar

# 3. 验证
docker images

# 4. 启动服务
cd /path/to/FireTrain
make docker-up
```

## 🛠️ 故障排查

### 问题 1：导入失败

```bash
# 错误信息："open /var/lib/docker/tmp...: no space left on device"
# 解决方案：清理磁盘空间
docker system prune -a
df -h
```

### 问题 2：镜像标签不匹配

```bash
# 查看导入的镜像标签
docker images

# 如果需要重新打标签
docker tag old-tag:new-tag mysql:8.0
```

### 问题 3：权限问题

```bash
# 确保有 Docker 权限
sudo usermod -aG docker $USER
newgrp docker
```

## 📚 相关资源

- [Docker save 官方文档](https://docs.docker.com/engine/reference/commandline/save/)
- [Docker load 官方文档](https://docs.docker.com/engine/reference/commandline/load/)
- [国内 Docker 镜像加速](https://gist.github.com/y0ngb1n/7e8f16af3242c7815e7ca2f0a2672190)

## 💡 最佳实践

1. **定期更新**: 定期更新基础镜像以获取安全补丁
2. **版本管理**: 使用明确的版本号（如 `mysql:8.0` 而非 `mysql:latest`）
3. **镜像备份**: 定期备份重要镜像
4. **文档记录**: 记录镜像来源和版本信息
