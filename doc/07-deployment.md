# 7. 部署指南

## 7.1 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| 内存 | 最低 4GB，推荐 8GB+ |
| 磁盘 | 至少 1GB 可用空间 |
| 网络 | 需要访问 LLM API |

## 7.2 本地部署

### 7.2.1 方式一：使用启动脚本（Windows）

```powershell
# 运行启动脚本（同时启动前后端）
.\start.bat
```

### 7.2.2 方式二：手动启动

**启动后端：**
```powershell
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**启动前端：**
```powershell
cd frontend
npm install
npm run dev
```

### 7.2.3 方式三：使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync

# 安装 Node.js（用于前端）
RUN apt-get update && apt-get install -y nodejs npm

# 安装前端依赖
WORKDIR /app/frontend
RUN npm install

WORKDIR /app

# 配置
ENV PYTHONUNBUFFERED=1

# 启动脚本
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

**start.sh:**
```bash
#!/bin/bash
# 启动后端
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
# 启动前端
cd frontend && npm run dev -- --host 0.0.0.0 --port 3000 &
wait
```

```bash
# 构建镜像
docker build -t rhizome .

# 运行容器
docker run -p 3000:3000 -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  rhizome
```

## 7.3 服务器部署

### 7.3.1 使用 systemd 服务

创建后端服务文件 `/etc/systemd/system/rhizome-backend.service`：

```ini
[Unit]
Description=Rhizome Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/rhizome
Environment="PYTHONUNBUFFERED=1"
ExecStart=/path/to/rhizome/.venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

创建前端服务文件 `/etc/systemd/system/rhizome-frontend.service`：

```ini
[Unit]
Description=Rhizome Frontend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/rhizome/frontend
ExecStart=/usr/bin/npm run dev -- --host 0.0.0.0 --port 3000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable rhizome-backend rhizome-frontend
sudo systemctl start rhizome-backend rhizome-frontend
```

### 7.3.2 使用 Gunicorn + Uvicorn（后端）

```bash
# 安装额外依赖
uv add gunicorn

# 运行
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  backend.main:app --bind 0.0.0.0:8000
```

### 7.3.3 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # SSE 流式接口
    location /api/chat/stream {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }
}

## 7.4 云平台部署

### 7.4.1 Azure App Service

**后端部署：**
1. 创建 Web App (Python)
2. 配置启动命令：`uvicorn backend.main:app --host 0.0.0.0 --port 8000`
3. 设置应用设置（环境变量）
4. 部署代码

**前端部署：**
1. 创建 Static Web App
2. 配置构建命令：`npm run build`
3. 配置输出目录：`dist`
4. 配置 API 代理到后端

### 7.4.2 Railway

```toml
# railway.toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT"
```

### 7.4.3 Render

**后端服务：**
1. 创建 Web Service
2. 设置构建命令：`uv sync`
3. 设置启动命令：`uv run uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. 添加环境变量

**前端服务：**
1. 创建 Static Site
2. 设置构建命令：`npm run build`
3. 设置输出目录：`dist`
4. 配置 API 代理

## 7.5 代理配置

### 7.5.1 使用代理访问 LLM

```env
OPENAI_API_BASE=https://your-proxy.com/v1
```

### 7.5.2 系统代理

```bash
# Linux/macOS
export HTTP_PROXY=http://proxy:8080
export HTTPS_PROXY=http://proxy:8080

# Windows
set HTTP_PROXY=http://proxy:8080
set HTTPS_PROXY=http://proxy:8080
```

## 7.6 数据备份

### 7.6.1 备份数据目录

```bash
# 备份
tar -czf rhizome-backup-$(date +%Y%m%d).tar.gz data/

# 恢复
tar -xzf rhizome-backup-20240115.tar.gz
```

### 7.6.2 定时备份（cron）

```bash
# 每天凌晨 3 点备份
0 3 * * * tar -czf /backup/rhizome-$(date +\%Y\%m\%d).tar.gz /path/to/rhizome/data
```

## 7.7 故障排查

### 7.7.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 导入错误 | 运行 `uv sync` 同步依赖 |
| API 连接失败 | 检查网络和 API Key |
| 向量检索无结果 | 确认 Chroma 服务正常运行 |
| 中文编码错误 | 设置 `PYTHONUTF8=1` |

### 7.7.2 日志查看

```bash
# 查看实时日志
tail -f logs/rhizome.log

# 查看错误日志
grep ERROR logs/rhizome.log
```
