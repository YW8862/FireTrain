#!/bin/bash
# FireTrain SSL 证书安装脚本
# 使用 Let's Encrypt 免费证书

set -e

echo "=========================================="
echo "FireTrain SSL 证书安装脚本"
echo "=========================================="

# 检查 root 权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此脚本: sudo $0"
    exit 1
fi

DOMAIN="firetrain.cn"
EMAIL="admin@firetrain.cn"  # 替换为你的邮箱
WWW_ROOT="/var/www/certbot"
NGINX_CONF="/etc/nginx/sites-available/firetrain.conf"
NGINX_ENABLED="/etc/nginx/sites-enabled/firetrain.conf"

echo "[1/6] 安装 nginx 和 certbot..."
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

echo "[2/6] 创建证书验证目录..."
mkdir -p $WWW_ROOT/.well-known/acme-challenge
chown -R www-data:www-data $WWW_ROOT

echo "[3/6] 停止 nginx..."
systemctl stop nginx

echo "[4/6] 申请 Let's Encrypt 证书..."
certbot certonly --webroot -w $WWW_ROOT \
    -d $DOMAIN \
    -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --non-interactive \
    --keep-until-expiring

echo "[5/6] 部署 nginx 配置..."
cp /home/yw/FireTrain/deploy/nginx.conf $NGINX_CONF
sed -i "s|/etc/letsencrypt/live/firetrain.cn|$CERTBOT_LIVE_PATH|" $NGINX_CONF 2>/dev/null || true
ln -sf $NGINX_CONF $NGINX_ENABLED
rm -f /etc/nginx/sites-enabled/default

echo "[6/6] 启动 nginx 并设置自动续期..."
systemctl start nginx
systemctl enable nginx

# 设置自动续期（Let's Encrypt 证书有效期 90 天）
echo "0 0 * * * certbot renew --quiet" | tee -a /etc/crontab

echo ""
echo "=========================================="
echo "SSL 证书安装完成！"
echo "=========================================="
echo "证书位置: /etc/letsencrypt/live/$DOMAIN/"
echo "Nginx 配置: $NGINX_CONF"
echo "访问地址: https://$DOMAIN"
echo ""
echo "证书将在 90 天后自动续期。"
