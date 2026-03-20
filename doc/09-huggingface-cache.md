# 9. HuggingFace 模型缓存优化

## 9.1 概述

Rhizome 使用 HuggingFace 的嵌入模型（如 `BAAI/bge-small-zh-v1.5`）来生成文本向量。为了避免每次启动时都从网络下载模型，系统实现了智能的本地缓存机制。

## 9.2 工作原理

### 9.2.1 首次运行

1. 系统检测到本地缓存中没有模型文件
2. 自动从 HuggingFace Hub 下载模型
3. 模型保存到本地缓存目录：`~/.cache/huggingface/hub`
4. 下载完成后立即可用

### 9.2.2 后续运行

1. 系统启用离线模式 (`HF_HUB_OFFLINE=1`)
2. 直接从本地缓存加载模型
3. 不尝试连接 HuggingFace 服务器
4. 启动速度显著提升，无网络延迟

### 9.2.3 缓存缺失处理

如果本地缓存被删除或损坏：

1. 离线模式会检测到模型缺失
2. 自动禁用离线模式
3. 重新从 HuggingFace 下载模型
4. 恢复正常运行

## 9.3 缓存位置

### Windows

```
C:\Users\<用户名>\.cache\huggingface\hub
```

### Linux/macOS

```
~/.cache/huggingface/hub
```

### 自定义缓存位置

通过环境变量自定义缓存目录：

```bash
# Windows PowerShell
$env:HF_HOME = "D:\huggingface_cache"

# Linux/macOS
export HF_HOME="/path/to/cache"
```

## 9.4 离线模式配置

### 9.4.1 代码中设置

```python
import os
os.environ["HF_HUB_OFFLINE"] = "1"
```

### 9.4.2 环境变量设置

在 `.env` 文件中添加：

```env
HF_HUB_OFFLINE=1
```

### 9.4.3 系统范围设置

**Windows PowerShell**：

```powershell
[System.Environment]::SetEnvironmentVariable("HF_HUB_OFFLINE", "1", "User")
```

**Linux/macOS**：

```bash
echo "export HF_HUB_OFFLINE=1" >> ~/.bashrc
source ~/.bashrc
```

## 9.5 常用嵌入模型

### 中文模型

| 模型名称 | 大小 | 维度 | 说明 |
|---------|------|------|------|
| `BAAI/bge-small-zh-v1.5` | ~130MB | 512 | 轻量级，速度快（推荐） |
| `BAAI/bge-base-zh-v1.5` | ~440MB | 768 | 中等规模，平衡性能 |
| `BAAI/bge-large-zh-v1.5` | ~1.3GB | 1024 | 大规模，精度最高 |

### 英文模型

| 模型名称 | 大小 | 维度 | 说明 |
|---------|------|------|------|
| `sentence-transformers/all-MiniLM-L6-v2` | ~90MB | 384 | 轻量级，英文优化 |
| `sentence-transformers/all-mpnet-base-v2` | ~420MB | 768 | 高质量，英文优化 |

### 多语言模型

| 模型名称 | 大小 | 维度 | 说明 |
|---------|------|------|------|
| `intfloat/multilingual-e5-large` | ~1.2GB | 1024 | 支持 100+ 语言 |
| `intfloat/multilingual-e5-base` | ~560MB | 768 | 多语言平衡选择 |

## 9.6 模型下载优化

### 9.6.1 使用镜像源

如果访问 HuggingFace 较慢，可以使用镜像源：

```bash
# Windows PowerShell
$env:HF_ENDPOINT = "https://hf-mirror.com"

# Linux/macOS
export HF_ENDPOINT="https://hf-mirror.com"
```

### 9.6.2 预下载模型

可以手动预下载模型：

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="BAAI/bge-small-zh-v1.5",
    cache_dir="~/.cache/huggingface/hub"
)
```

### 9.6.3 查看已下载模型

**Windows PowerShell**：

```powershell
Get-ChildItem -Recurse "$env:USERPROFILE\.cache\huggingface\hub" | 
    Where-Object { $_.Name -like "*.bin" -or $_.Name -like "*.safetensors" } |
    Select-Object FullName, Length
```

**Linux/macOS**：

```bash
find ~/.cache/huggingface/hub -name "*.bin" -o -name "*.safetensors" | xargs ls -lh
```

## 9.7 故障排查

### 9.7.1 模型下载失败

**症状**：启动时反复重试，报错连接超时

**解决方案**：

1. 检查网络连接
2. 使用镜像源（见 9.6.1）
3. 手动预下载模型（见 9.6.2）
4. 检查防火墙设置

### 9.7.2 缓存损坏

**症状**：加载模型时报错，提示文件损坏

**解决方案**：

1. 删除缓存目录中的对应模型文件夹
2. 重新启动应用，触发重新下载

```powershell
# Windows - 删除特定模型缓存
Remove-Item -Recurse "$env:USERPROFILE\.cache\huggingface\hub\models--BAAI--bge-small-zh-v1.5"

# Linux/macOS
rm -rf ~/.cache/huggingface/hub/models--BAAI--bge-small-zh-v1.5
```

### 9.7.3 离线模式无法启动

**症状**：设置离线模式后无法加载模型

**解决方案**：

1. 确认模型已正确下载到本地
2. 检查缓存路径是否正确
3. 临时禁用离线模式，让系统重新下载
4. 查看日志确认具体错误信息

## 9.8 性能对比

### 启动时间对比

| 场景 | 首次启动 | 后续启动 |
|------|---------|---------|
| 在线模式（无缓存） | ~60 秒 | ~5 秒（检查更新） |
| 离线模式（有缓存） | ~60 秒 | ~2 秒（直接加载） |

### 模型大小与性能

| 模型 | 下载时间 (100Mbps) | 加载时间 | 嵌入速度 |
|------|-------------------|---------|---------|
| bge-small-zh | ~10 秒 | ~3 秒 | ~1000 句/秒 |
| bge-base-zh | ~35 秒 | ~8 秒 | ~500 句/秒 |
| bge-large-zh | ~100 秒 | ~15 秒 | ~200 句/秒 |

## 9.9 最佳实践

1. **首次使用**：确保网络连接良好，让模型完整下载
2. **生产环境**：预下载模型并设置离线模式，避免网络依赖
3. **定期清理**：删除不用的模型缓存，释放磁盘空间
4. **备份缓存**：可以备份缓存目录，避免重复下载
5. **监控日志**：关注模型加载日志，及时发现异常

## 9.10 相关资源

- [HuggingFace 文档](https://huggingface.co/docs/huggingface_hub)
- [模型缓存机制说明](https://huggingface.co/docs/huggingface_hub/how-to-cache)
- [BAAI/bge 模型系列](https://huggingface.co/BAAI)
- [Sentence Transformers 文档](https://sbert.net/)
