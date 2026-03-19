# 7. 部署指南

## 7.1 环境要求

| 组件 | 要求 |
|------|------|
| Python | 3.10+ |
| 内存 | 最低 4GB，推荐 8GB+ |
| 磁盘 | 至少 1GB 可用空间 |
| 网络 | 需要访问 LLM API |

## 7.2 本地部署

### 7.2.1 方式一：使用 uv（推荐）

```powershell
# 1. 克隆项目
cd path/to/project

# 2. 安装依赖
uv sync

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API Key

# 4. 运行
uv run python -m knowledge_agent.ui.gradio_app
```

### 7.2.2 方式二：使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync

# 配置
ENV PYTHONUNBUFFERED=1

# 启动
CMD ["uv", "run", "python", "-m", "knowledge_agent.ui.gradio_app"]
```

```bash
# 构建镜像
docker build -t rhizome .

# 运行容器
docker run -p 7860:7860 \
  -e OPENAI_API_KEY=your-key \
  rhizome
```

## 7.3 服务器部署

### 7.3.1 使用 systemd 服务

创建服务文件 `/etc/systemd/system/rhizome.service`：

```ini
[Unit]
Description=Rhizome Knowledge Agent
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/rhizome
Environment="PYTHONUNBUFFERED=1"
ExecStart=/path/to/rhizome/.venv/bin/python -m knowledge_agent.ui.gradio_app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable rhizome
sudo systemctl start rhizome
```

### 7.3.2 使用 Gunicorn + Uvicorn

```bash
# 安装额外依赖
uv add gunicorn

# 运行
gunicorn -w 4 -k uvicorn.workers.UvicornWorker \
  knowledge_agent.ui.gradio_app:app
```

## 7.4 云平台部署

### 7.4.1 Azure App Service

1. 创建 Web App
2. 配置启动命令：`uv run python -m knowledge_agent.ui.gradio_app`
3. 设置应用设置（环境变量）
4. 部署代码

### 7.4.2 Railway

```toml
# railway.toml
[build]
builder = "nixpacks"
nixpacksPlan = "{ phases = [ \"install\", "build" ], }"

[deploy]
startCommand = "uv run python -m knowledge_agent.ui.gradio_app"
```

### 7.4.3 Render

1. 连接 GitHub 仓库
2. 设置构建命令：`uv sync`
3. 设置启动命令：`uv run python -m knowledge_agent.ui.gradio_app`
4. 添加环境变量

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
