# AI校园生活规划agent

基于 Python + MySQL + Redis 的 AI 校园生活规划 Agent，AI 模型通过 DeepSeek（OpenAI 兼容接口）接入。

## 技术栈

| 组件 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.14 | 运行时 |
| MySQL | 8.0 | Docker 引入 |
| Redis | 7 | Docker 引入 |
| DeepSeek | deepseek-chat | OpenAI 兼容接口，已预留配置 |

## 目录结构

```
campusops/
├── docker-compose.yml   # MySQL + Redis 容器编排
├── config.py            # 统一配置入口（读取 .env）
├── requirements.txt     # Python 依赖
├── .env.example         # 环境变量模板
├── .env                 # 实际环境变量（已 git 忽略）
└── .gitignore
```

## 快速开始

### 1. 准备环境变量

```powershell
Copy-Item .env.example .env
```

编辑 `.env`，填入数据库密码和 [DeepSeek API Key](https://platform.deepseek.com)。

### 2. 启动 MySQL 和 Redis

```powershell
docker compose up -d
```

查看状态与日志：

```powershell
docker compose ps
docker compose logs -f mysql redis
```

停止（保留数据）/ 停止并清空数据：

```powershell
docker compose down
docker compose down -v
```

### 3. 创建 Python 虚拟环境并安装依赖

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. 验证连接

```powershell
python -c "from config import settings; print(settings.mysql.host, settings.redis.port, settings.ai.model)"
```

## 配置项说明

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `MYSQL_HOST` / `MYSQL_PORT` | 127.0.0.1 / 3307 | MySQL 连接地址（Docker 映射到宿主机 3307，容器内仍为 3306） |
| `MYSQL_DATABASE` / `MYSQL_USER` / `MYSQL_PASSWORD` | campusops / campusops | 应用库与账号 |
| `MYSQL_ROOT_PASSWORD` | - | MySQL root 密码（Docker 初始化用） |
| `REDIS_HOST` / `REDIS_PORT` | 127.0.0.1 / 6379 | Redis 连接地址 |
| `REDIS_PASSWORD` / `REDIS_DB` | - / 0 | Redis 密码与库号 |
| `DEEPSEEK_API_KEY` | - | DeepSeek 密钥 |
| `DEEPSEEK_BASE_URL` | https://api.deepseek.com | API 地址 |
| `DEEPSEEK_MODEL` | deepseek-chat | 模型名（可选 deepseek-reasoner） |
| `AI_TEMPERATURE` / `AI_MAX_TOKENS` | 0.7 / 4096 | 采样温度 / 最大输出 token |

代码中通过 [config.py](config.py) 的 `settings` 统一读取，例如：

```python
from config import settings

settings.mysql.host      # MySQL 地址
settings.redis.password  # Redis 密码
settings.ai.model        # AI 模型名
```

