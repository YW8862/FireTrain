# FireTrain MySQL 数据库导入指南

本文档介绍如何将 FireTrain 项目的数据库结构导入到 MySQL 数据库。

---

## 方法一：使用 SQL 文件直接导入（推荐）

### 1. 准备 MySQL 环境

确保你已经安装并启动了 MySQL 服务（版本 5.7+ 或 8.0+）。

```bash
# 检查 MySQL 是否运行
mysql --version

# 启动 MySQL 服务（Ubuntu/Debian）
sudo systemctl start mysql

# 启动 MySQL 服务（macOS）
brew services start mysql
```

### 2. 创建数据库和用户

登录 MySQL：

```bash
mysql -u root -p
```

执行以下 SQL 命令：

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS fire_training
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- 创建专用用户（可选，但推荐）
CREATE USER IF NOT EXISTS 'firetrain'@'localhost' IDENTIFIED BY 'firetrain';

-- 授予权限
GRANT ALL PRIVILEGES ON fire_training.* TO 'firetrain'@'localhost';

-- 刷新权限
FLUSH PRIVILEGES;

-- 退出
EXIT;
```

### 3. 导入表结构

使用提供的 `db/init.sql` 文件导入表结构：

```bash
# 方法 A：直接导入
mysql -u firetrain -pfiretrain fire_training < db/init.sql

# 方法 B：交互式导入
mysql -u firetrain -p fire_training
source /home/yw/FireTrain/db/init.sql
```

### 4. 验证导入结果

```bash
mysql -u firetrain -pfiretrain fire_training -e "SHOW TABLES;"
```

应该看到以下表：
- `users`
- `training_records`
- `action_logs`
- `training_statistics`

---

## 方法二：使用 Python 脚本自动创建（SQLAlchemy）

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并修改数据库配置：

```bash
cd /home/yw/FireTrain
cp .env.example .env
```

编辑 `.env` 文件，修改数据库配置部分：

```ini
# 注释掉 SQLite 配置
# DATABASE_URL=sqlite:///./fire_training.db

# 启用 MySQL 配置
DATABASE_URL=mysql+aiomysql://firetrain:firetrain@localhost:3306/fire_training
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=firetrain
MYSQL_PASSWORD=firetrain
MYSQL_DATABASE=fire_training
```

### 2. 安装 MySQL 驱动

```bash
cd backend
pip install aiomysql
# 或者
pip install -r requirements.txt
```

### 3. 运行初始化脚本

```bash
cd backend
python scripts/init_db.py
```

该脚本会自动创建所有表结构。

---

## 方法三：使用 Docker Compose（最简便）

### 1. 启动 MySQL 容器

项目根目录下执行：

```bash
docker-compose up -d mysql
```

### 2. 等待 MySQL 就绪

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs mysql
```

### 3. 初始化数据库

```bash
# 进入 backend 容器
docker-compose exec backend python scripts/init_db.py
```

或者直接导入 SQL 文件：

```bash
docker-compose exec -T mysql mysql -ufiretrain -pfiretrain fire_training < db/init.sql
```

---

## 完整 SQL 建表语句

如果需要手动执行，以下是完整的建表 SQL（已包含在 `db/init.sql` 中）：

```sql
CREATE DATABASE IF NOT EXISTS fire_training
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE fire_training;

SET time_zone = '+00:00';

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    last_login_at DATETIME(6) NULL,
    can_switch_role TINYINT(1) NULL DEFAULT 0,
    original_role VARCHAR(20) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT uq_users_username UNIQUE (username),
    CONSTRAINT uq_users_email UNIQUE (email)
);

-- 训练记录表
CREATE TABLE IF NOT EXISTS training_records (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    training_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed',
    total_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    step_scores JSON NULL,
    video_path VARCHAR(255) NULL,
    duration_seconds DECIMAL(8, 2) NULL,
    started_at DATETIME(6) NULL,
    completed_at DATETIME(6) NULL,
    feedback TEXT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT fk_training_records_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    INDEX idx_training_records_user_id_created_at (user_id, created_at),
    INDEX idx_training_records_status_created_at (status, created_at)
);

-- 动作日志表
CREATE TABLE IF NOT EXISTS action_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    record_id INT NOT NULL,
    action_name VARCHAR(50) NOT NULL,
    step_index SMALLINT NOT NULL,
    is_correct TINYINT(1) NOT NULL,
    confidence_score DECIMAL(5, 4) NULL,
    action_timestamp DATETIME(6) NOT NULL,
    detail JSON NULL,
    CONSTRAINT fk_action_logs_record_id_training_records
        FOREIGN KEY (record_id) REFERENCES training_records(id)
        ON DELETE CASCADE,
    INDEX idx_action_logs_record_id_step_index (record_id, step_index),
    INDEX idx_action_logs_action_timestamp (action_timestamp)
);

-- 训练统计表
CREATE TABLE IF NOT EXISTS training_statistics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    total_trainings INT NOT NULL DEFAULT 0,
    completed_trainings INT NOT NULL DEFAULT 0,
    total_training_seconds DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    average_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    best_score DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    last_training_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    updated_at DATETIME(6) NOT NULL DEFAULT (UTC_TIMESTAMP(6)),
    CONSTRAINT uq_training_statistics_user_id UNIQUE (user_id),
    CONSTRAINT fk_training_statistics_user_id_users
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

-- 管理员操作日志表
CREATE TABLE IF NOT EXISTS admin_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    admin_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NULL,
    target_id INT NULL,
    details JSON NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_admin_logs_admin_id_users
        FOREIGN KEY (admin_id) REFERENCES users(id),
    INDEX idx_admin_logs_admin_id (admin_id),
    INDEX idx_admin_logs_created_at (created_at)
);

-- 视频检测任务表
CREATE TABLE IF NOT EXISTS video_detection_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    uploader_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NULL,
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    ai_result JSON NULL,
    error_message TEXT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME NULL,
    CONSTRAINT fk_video_detection_tasks_uploader_id_users
        FOREIGN KEY (uploader_id) REFERENCES users(id),
    INDEX idx_video_detection_tasks_uploader_id (uploader_id),
    INDEX idx_video_detection_tasks_status (status),
    INDEX idx_video_detection_tasks_created_at (created_at)
);
```

---

## 注意事项

### 1. 字符集和排序规则

- 使用 `utf8mb4` 字符集支持完整的 Unicode（包括 emoji）
- 使用 `utf8mb4_unicode_ci` 排序规则提供更好的国际化支持

### 2. 时区设置

- 所有时间字段使用 `DATETIME(6)` 类型，支持微秒精度
- 默认值使用 `UTC_TIMESTAMP(6)` 确保时区一致性
- 建议在 MySQL 配置文件中设置：

```ini
[mysqld]
default-time-zone = '+00:00'
```

### 3. JSON 字段

- MySQL 5.7+ 原生支持 JSON 类型
- JSON 字段可以存储嵌套对象和数组
- 可以使用 JSON 函数进行查询和优化

### 4. 外键约束

- 所有外键都设置了 `ON DELETE CASCADE`
- 删除用户时会自动删除相关的训练记录、统计数据等
- 确保数据一致性

### 5. 索引优化

- 常用查询字段已建立索引
- 复合索引优化多条件查询
- 定期使用 `ANALYZE TABLE` 更新统计信息

---

## 常见问题

### Q1: 导入时出现 "Access denied" 错误

**解决方案：**
```bash
# 检查用户权限
mysql -u root -p -e "SELECT User, Host FROM mysql.user;"

# 重新授权
mysql -u root -p -e "GRANT ALL PRIVILEGES ON fire_training.* TO 'firetrain'@'localhost'; FLUSH PRIVILEGES;"
```

### Q2: 出现 "Table already exists" 错误

**解决方案：**
```sql
-- 删除现有表后重新导入
DROP DATABASE fire_training;
CREATE DATABASE fire_training DEFAULT CHARACTER SET utf8mb4;
```

或者修改 SQL 文件中的 `CREATE TABLE IF NOT EXISTS` 为 `DROP TABLE IF EXISTS` + `CREATE TABLE`。

### Q3: SQLAlchemy 连接失败

**解决方案：**
```bash
# 确认安装了正确的驱动
pip install aiomysql

# 测试连接
python -c "from app.db.session import engine; print('Connection OK')"
```

### Q4: 中文数据显示乱码

**解决方案：**
```sql
-- 检查数据库字符集
SHOW VARIABLES LIKE 'character_set%';

-- 确保都是 utf8mb4
ALTER DATABASE fire_training CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 数据库管理工具推荐

### 命令行工具
```bash
# 连接数据库
mysql -u firetrain -pfiretrain fire_training

# 导出数据库
mysqldump -u firetrain -pfiretrain fire_training > backup.sql

# 导入备份
mysql -u firetrain -pfiretrain fire_training < backup.sql
```

### GUI 工具
- **MySQL Workbench** - 官方图形化管理工具
- **DBeaver** - 免费开源的通用数据库工具
- **phpMyAdmin** - Web 界面管理工具
- **Navicat** - 商业数据库管理工具

---

## 性能优化建议

### 1. 索引优化
```sql
-- 查看慢查询
SHOW PROCESSLIST;

-- 分析查询计划
EXPLAIN SELECT * FROM training_records WHERE user_id = 1;
```

### 2. 表维护
```sql
-- 优化表
OPTIMIZE TABLE training_records;

-- 分析表
ANALYZE TABLE users;
```

### 3. 连接池配置

在 `backend/app/db/session.py` 中调整连接池参数：

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=10,          # 连接池大小
    max_overflow=20,       # 最大溢出连接数
    pool_timeout=30,       # 连接超时时间
    pool_recycle=1800,     # 连接回收时间（秒）
)
```

---

## 下一步

数据库导入完成后，你可以：

1. **创建管理员账户**：
   ```bash
   cd backend
   python scripts/create_admin.py
   ```

2. **启动后端服务**：
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

3. **运行测试**：
   ```bash
   cd backend
   pytest tests/
   ```

---

*文档更新时间: 2026-04-10*
