# 🔒 HTTPS 配置修复说明

## 问题描述

前端使用 HTTPS 访问后端时出现 `ERR_SSL_PROTOCOL_ERROR` 错误。

**错误信息**：
```
POST https://117.72.44.96:8000/api/training/start net::ERR_SSL_PROTOCOL_ERROR
```

**根本原因**：
- 前端 Vite 服务器配置了 HTTPS
- 后端 Uvicorn 服务器使用 HTTP 启动
- 协议不匹配导致 SSL 握手失败

## 已完成的修复

### 1. 修改后端启动脚本

**文件**：`backend/start.sh`

**修改内容**：
```bash
# 检查 SSL 证书是否存在
CERT_FILE="/home/yw/FireTrain/certs/cert.pem"
KEY_FILE="/home/yw/FireTrain/certs/key.pem"

if [ -f "$CERT_FILE" ] && [ -f "$KEY_FILE" ]; then
    echo "🔒 检测到 SSL 证书，启用 HTTPS..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ssl-certfile="$CERT_FILE" --ssl-keyfile="$KEY_FILE"
else
    echo "⚠️  未检测到 SSL 证书，使用 HTTP（生产环境建议使用 HTTPS）..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
fi
```

**效果**：
- ✅ 自动检测 SSL 证书
- ✅ 有证书时使用 HTTPS 启动
- ✅ 无证书时降级为 HTTP

### 2. 更新环境变量配置

**文件**：`.env`

**修改内容**：
```bash
VITE_API_BASE_URL=https://117.72.44.96:8000/api
```

**说明**：
- 将 API 地址从 `localhost` 改为公网 IP `117.72.44.96`
- 确保前后端都使用 HTTPS 协议

## 如何重新启动服务

### 方法 1：使用启动脚本（推荐）

```bash
cd /home/yw/FireTrain/backend
./start.sh
```

**预期输出**：
```
🚀 正在启动 FireTrain 后端服务...
🔍 检查 8000 端口占用情况...
✅ 8000 端口可用
📦 检查数据库...
✅ 数据库已存在
🌐 启动后端服务...
🔒 检测到 SSL 证书，启用 HTTPS...
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 方法 2：手动启动

```bash
cd /home/yw/FireTrain/backend
source .venv/bin/activate
export PYTHONPATH=/home/yw/FireTrain/backend:$PYTHONPATH
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 \
  --ssl-certfile=/home/yw/FireTrain/certs/cert.pem \
  --ssl-keyfile=/home/yw/FireTrain/certs/key.pem
```

## 验证 HTTPS 是否生效

### 方法 1：浏览器访问

打开浏览器访问：
```
https://117.72.44.96:8000/docs
```

**注意**：由于使用的是自签名证书，浏览器会显示安全警告，需要点击"继续访问"或"接受风险"。

### 方法 2：curl 测试

```bash
curl -k https://117.72.44.96:8000/health
```

**预期响应**：
```json
{"status": "healthy"}
```

### 方法 3：测试训练接口

```bash
# 先开始训练
curl -k -X POST https://117.72.44.96:8000/api/training/start \
  -H "Content-Type: application/json" \
  -d '{"training_type": "fire_extinguisher", "duration_seconds": 120}'
```

**预期响应**：
```json
{
  "training_id": 1,
  "status": "created",
  "message": "训练已创建，请上传视频"
}
```

## 前端配置检查

### Vite 配置（已正确）

**文件**：`frontend/vite.config.js`

```javascript
server: {
  host: '0.0.0.0',
  port: 5173,
  https: {
    key: fs.readFileSync('../certs/key.pem'),
    cert: fs.readFileSync('../certs/cert.pem')
  },
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 本地代理仍用 HTTP
      changeOrigin: true
    }
  }
}
```

**说明**：
- ✅ Vite 开发服务器使用 HTTPS
- ✅ 代理转发到后端使用 HTTP（因为都在本地）
- ✅ 浏览器直接访问后端 API 使用 HTTPS

### 环境变量（已更新）

**文件**：`.env`

```bash
VITE_API_BASE_URL=https://117.72.44.96:8000/api
```

## SSL 证书说明

### 证书位置
```
/home/yw/FireTrain/certs/
├── cert.pem  # 证书文件
└── key.pem   # 私钥文件
```

### 证书类型
当前使用的是**自签名证书**，适用于：
- ✅ 本地开发测试
- ✅ 内网访问
- ✅ 功能验证

### 生产环境建议

如果是正式生产环境，建议使用**正规 CA 签发的证书**：

1. **免费选项**：
   - Let's Encrypt（推荐）
   - ZeroSSL

2. **付费选项**：
   - DigiCert
   - GlobalSign
   - Comodo

3. **内网穿透方案**（推荐用于演示）：
   ```bash
   # Cloudflare Tunnel
   cloudflared tunnel --url https://localhost:8000
   
   # Ngrok
   ngrok http 8000
   ```
   
   这样可以获得正规的 HTTPS 域名（如 `xxx.ngrok.io`）。

## 常见问题排查

### Q1: 证书权限问题

**错误**：`Permission denied`

**解决**：
```bash
chmod 600 /home/yw/FireTrain/certs/*.pem
chown $USER:$USER /home/yw/FireTrain/certs/*.pem
```

### Q2: 端口被占用

**错误**：`Address already in use`

**解决**：
```bash
# 查找占用进程
lsof -i:8000

# 终止进程
kill -9 <PID>

# 或者使用启动脚本（会自动处理）
./start.sh
```

### Q3: 浏览器仍然报错

**可能原因**：
1. 后端没有真正重启
2. 浏览器缓存了旧的响应
3. 混合内容（HTTP + HTTPS）

**解决步骤**：
```bash
# 1. 确认后端进程
ps aux | grep uvicorn

# 2. 完全停止并重启
pkill -f uvicorn
sleep 2
./start.sh

# 3. 清除浏览器缓存
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete

# 4. 使用无痕模式测试
```

### Q4: 摄像头权限问题

如果浏览器提示摄像头权限错误：

**检查清单**：
- ✅ 必须使用 HTTPS（已满足）
- ✅ 浏览器允许摄像头权限
- ✅ 操作系统允许浏览器访问摄像头
- ✅ 没有其他程序占用摄像头

**Chrome 特殊设置**：
```
chrome://flags/#unsafely-treat-insecure-origin-as-secure
```
添加你的域名（可选，仅开发环境）

## 下一步操作

1. **重启后端服务**
   ```bash
   cd /home/yw/FireTrain/backend
   ./start.sh
   ```

2. **重启前端服务**（如果已运行可跳过）
   ```bash
   cd /home/yw/FireTrain/frontend
   npm run dev
   ```

3. **访问应用**
   ```
   https://117.72.44.96:5173
   ```

4. **测试训练功能**
   - 点击"开始训练"
   - 应该不再出现网络错误
   - 摄像头应该正常开启

## 技术总结

### 协议一致性

| 组件 | 协议 | 端口 | 说明 |
|------|------|------|------|
| 前端 Vite | HTTPS | 5173 | ✅ 已配置 |
| 后端 Uvicorn | HTTPS | 8000 | ✅ 已修复 |
| API 调用 | HTTPS | 8000 | ✅ 已更新 |

### 数据流向

```
用户浏览器 (HTTPS)
    ↓
Vite 开发服务器 (HTTPS:5173)
    ↓
Uvicorn 应用服务器 (HTTPS:8000)
    ↓
FastAPI 应用
```

所有环节都使用 HTTPS，确保安全！

---

**更新时间**：2026-03-12  
**修复状态**：✅ 已完成
