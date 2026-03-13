#!/bin/bash
# 后端 HTTPS 启动脚本

echo "正在启动 HTTPS 后端服务..."
cd /home/yw/FireTrain/backend

# 证书路径
CERT_FILE="../certs/cert.pem"
KEY_FILE="../certs/key.pem"

# 检查证书是否存在
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "❌ 错误：SSL 证书不存在！"
    echo "路径：$CERT_FILE"
    echo ""
    echo "请先生成证书："
    echo "cd /home/yw/FireTrain/certs"
    echo "openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes"
    exit 1
fi

echo "✅ 证书文件存在"
echo "📍 证书路径：$CERT_FILE"
echo "🔐 私钥路径：$KEY_FILE"
echo ""
echo "🚀 启动 HTTPS 服务，监听端口 8000..."
echo ""

# 使用 uvicorn 启动 HTTPS 服务
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile="$KEY_FILE" \
    --ssl-certfile="$CERT_FILE" \
    --reload
