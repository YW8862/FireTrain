#!/bin/bash
# FireTrain SSL 证书自动生成/更新脚本

# 获取项目根目录（scripts 的父目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"
CERT_DIR="$BASE_DIR/certs"
CERT_FILE="$CERT_DIR/cert.pem"
KEY_FILE="$CERT_DIR/key.pem"
DAYS_VALID=365

echo "🔒 FireTrain SSL 证书管理工具"
echo "================================"
echo ""

# 检查证书是否存在
if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "ℹ️  检测到现有证书："
    openssl x509 -in "$CERT_FILE" -noout -dates 2>/dev/null || echo "无法读取证书信息"
    echo ""
    
    read -p "是否重新生成证书？(y/N): " choice
    case "$choice" in
        y|Y)
            echo "🔄 正在重新生成证书..."
            ;;
        *)
            echo "✅ 保留现有证书"
            exit 0
            ;;
    esac
fi

# 创建证书目录
mkdir -p "$CERT_DIR"

echo "📝 生成新的 SSL 证书..."
echo ""

# 生成自签名证书
openssl req -x509 -newkey rsa:4096 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days $DAYS_VALID \
    -nodes \
    -subj "/C=CN/ST=State/L=City/O=FireTrain/OU=Development/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 证书生成成功！"
    echo ""
    echo "📋 证书信息："
    echo "   证书文件：$CERT_FILE"
    echo "   私钥文件：$KEY_FILE"
    echo "   有效期：$DAYS_VALID 天"
    echo ""
    echo "📖 证书详情："
    openssl x509 -in "$CERT_FILE" -noout -subject -dates -ext subjectAltName 2>/dev/null
    echo ""
    echo "⚠️  重要提示："
    echo "   1. 这是自签名证书，浏览器会显示警告"
    echo "   2. 开发环境可以手动信任此证书"
    echo "   3. 生产环境请使用正式的 CA 证书"
    echo ""
    echo "🔧 使用方法："
    echo "   - Docker 启动：make docker-up"
    echo "   - 本地启动：./scripts/start-local.sh"
    echo ""
else
    echo "❌ 证书生成失败！"
    exit 1
fi
