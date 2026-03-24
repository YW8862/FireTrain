# FireTrain 本地开发脚本说明

## 📦 脚本列表

### start-local.sh - 启动服务
启动前后端服务（后台运行）

**功能：**
- ✅ 自动释放被占用的端口（8000 和 5173）
- ✅ 自动激活 Python 虚拟环境
- ✅ 自动初始化数据库
- ✅ 支持 HTTPS（如果证书存在）
- ✅ 后台运行，不需要终端保持
- ✅ 自动记录日志到 `logs/` 目录

**使用方法：**
```bash
./scripts/start-local.sh
# 或
make local-up
```

### stop-local.sh - 停止服务
停止所有服务

**功能：**
- ✅ 优雅停止后端和前端服务
- ✅ 强制终止未响应的进程
- ✅ 可选清空日志文件

**使用方法：**
```bash
./scripts/stop-local.sh
# 或
make local-down
```

### logs.sh - 查看日志
交互式查看实时日志

**功能：**
- ✅ 选择查看后端日志
- ✅ 选择查看前端日志
- ✅ 同时查看两个日志

**使用方法：**
```bash
./scripts/logs.sh
# 或
make local-logs
```

## 🚀 快速开始

```bash
# 1. 启动服务
./scripts/start-local.sh

# 2. 访问应用
# 前端：http://localhost:5173
# 后端 API: http://localhost:8000
# API 文档：http://localhost:8000/docs

# 3. 查看日志（可选）
./scripts/logs.sh

# 4. 停止服务（下班时）
./scripts/stop-local.sh
```

## 📂 生成的文件

运行后会在项目根目录生成：

```
FireTrain/
├── logs/                    # 日志目录
│   ├── backend.log         # 后端日志
│   ├── frontend.log        # 前端日志
│   ├── backend.pid         # 后端进程 ID
│   └── frontend.pid        # 前端进程 ID
└── scripts/                 # 脚本目录
    ├── start-local.sh      # 启动脚本
    ├── stop-local.sh       # 停止脚本
    └── logs.sh             # 日志查看脚本
```

## 🔧 Make 命令

也可以使用 Make 命令来管理：

```bash
make local-up      # 启动服务
make local-down    # 停止服务
make local-logs    # 查看日志
make help          # 查看所有可用命令
```

## 💡 常用操作

### 查看服务状态
```bash
# 查看后端进程
ps -p $(cat logs/backend.pid)

# 查看前端进程
ps -p $(cat logs/frontend.pid)

# 查看端口占用
lsof -i:8000  # 后端
lsof -i:5173  # 前端
```

### 查看实时日志
```bash
# 不使用交互式脚本
tail -f logs/backend.log
tail -f logs/frontend.log
```

### 清空日志
```bash
> logs/backend.log
> logs/frontend.log
```

## ⚠️ 注意事项

1. **端口占用**：脚本会自动释放被占用的端口，但如果 Docker 容器正在运行，建议先停止 Docker 服务
2. **虚拟环境**：确保 backend/.venv 已创建并安装了依赖
3. **Node.js**：确保已安装 Node.js 和 npm
4. **SSL 证书**：如果没有 SSL 证书，后端会自动使用 HTTP

## 🆘 故障排查

### 问题：后端启动失败
```bash
# 检查虚拟环境
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# 手动启动测试
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 问题：前端启动失败
```bash
# 检查依赖
cd frontend
npm install

# 手动启动测试
npm run dev
```

### 问题：端口无法释放
```bash
# 手动查找并杀死进程
lsof -i:8000
kill -9 <PID>
```

## 📖 更多文档

详细使用文档请参考：`LOCAL_DEVELOPMENT.md`
