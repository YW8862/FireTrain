# HTTPS 配置指南 - 支持摄像头访问

## 📋 问题说明

Google Chrome 浏览器要求使用 HTTPS 才能调用摄像头（localhost 除外），否则会报错：
```
NotAllowedError: Permission denied
```

## ✅ 解决方案：自签名证书

### 1. 证书已生成

项目已经包含了自签名证书，位于：
- 证书文件：`/home/yw/FireTrain/certs/cert.pem`
- 私钥文件：`/home/yw/FireTrain/certs/key.pem`

### 2. 启动 HTTPS 后端服务

```bash
cd /home/yw/FireTrain/backend
./start_https.sh
```

或使用完整命令：
```bash
cd /home/yw/FireTrain/backend
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ssl-keyfile ../certs/key.pem \
    --ssl-certfile ../certs/cert.pem \
    --reload
```

### 3. 信任证书（重要！）

由于使用的是自签名证书，需要在浏览器中手动信任证书。

#### 方法一：通过浏览器信任（推荐）

1. 打开浏览器访问：`https://117.72.44.96:8000`
2. 浏览器会显示"您的连接不是私密连接"
3. 点击 **"高级"**
4. 点击 **"继续前往 117.72.44.96（不安全）"**
5. 成功后，浏览器会记住这个选择

#### 方法二：系统级别信任（Linux）

```bash
sudo cp /home/yw/FireTrain/certs/cert.pem /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

**注意**：重启浏览器后生效

### 4. 前端配置

前端已经配置为使用 HTTPS：
```bash
VITE_API_BASE_URL=https://117.72.44.96:8000/api
```

如果在前端开发环境（localhost），需要修改 `.env`：
```bash
# 本地开发（localhost 可以使用 HTTP）
VITE_API_BASE_URL=http://localhost:8000/api

# 生产环境（公网 IP 必须使用 HTTPS）
VITE_API_BASE_URL=https://117.72.44.96:8000/api
```

### 5. 测试摄像头

1. 启动后端：`./backend/start_https.sh`
2. 启动前端：`cd frontend && npm run dev`
3. 访问训练页面
4. 点击"开启摄像头"
5. 浏览器会请求摄像头权限，点击"允许"

## 🔧 故障排查

### 问题 1：仍然提示证书错误

**原因**：浏览器没有信任自签名证书

**解决**：
1. 先访问 `https://117.72.44.96:8000/health`
2. 接受浏览器的安全警告
3. 刷新页面，看到 `{"status": "ok"}` 表示成功
4. 然后再访问前端页面

### 问题 2：CORS 错误

**原因**：后端 CORS 配置不正确

**检查**：`backend/app/main.py` 中的 CORS 配置是否包含：
```python
allow_origins=[
    "https://117.72.44.96:5173",  # HTTPS 前端地址
    "http://localhost:5173",       # 本地开发地址
]
```

### 问题 3：混合内容（Mixed Content）错误

**原因**：HTTPS 页面加载了 HTTP 资源

**解决**：确保所有 API 请求都使用 HTTPS，检查 `.env` 中的 `VITE_API_BASE_URL`

## 📝 证书信息

当前证书详情：
- **类型**：自签名证书（X.509）
- **有效期**：365 天
- **颁发给**：localhost
- **组织**：FireTrain
- **位置**：Beijing, CN

### 重新生成证书

如果需要重新生成证书：

```bash
cd /home/yw/FireTrain/certs

# 备份旧证书
mv cert.pem cert.pem.bak
mv key.pem key.pem.bak

# 生成新证书
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=FireTrain/CN=117.72.44.96"
```

## 🌐 其他方案对比

| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **自签名证书** | 免费、快速 | 需要手动信任 | 开发测试 |
| **mkcert** | 浏览器自动信任 | 需要安装工具 | 本地开发 |
| **Let's Encrypt** | 完全信任、正规 | 需要域名 | 生产环境 |
| **商业证书** | 完全信任、有保修 | 昂贵 | 企业生产 |

## 💡 最佳实践建议

### 开发环境
- 使用 `localhost` + HTTP（不需要 HTTPS）
- 或使用 mkcert 创建受信任的本地证书

### 测试/生产环境（公网 IP）
- **短期**：使用自签名证书 + 手动信任
- **长期**：购买域名 + Let's Encrypt 免费证书

### 为什么自签名证书适合你？
- ✅ 不需要域名
- ✅ 完全免费
- ✅ 功能完整
- ⚠️ 只是需要手动信任一次

## 🔗 相关资源

- [Chrome 摄像头权限要求](https://developer.chrome.com/blog/deprecating-webrtc-insecure-origin/)
- [OpenSSL 证书生成教程](https://www.openssl.org/docs/man1.1.1/man1/req.html)
- [mkcert - 简单的本地 HTTPS](https://github.com/FiloSottile/mkcert)
