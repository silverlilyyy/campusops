# CampusOps · AI 校园生活规划系统

基于 **需求.docx** 的数据库课程设计代码框架。以「多智能体（Multi-Agent）协作」为核心，实现
「规划 → 执行 → 反馈 → 再规划」的闭环：**Manager / Academic / Schedule / Finance** 四个智能体协同，
由 Manager 汇总用户意图与校园数据生成「行动方案（Plan）」，并在执行后基于反馈迭代优化。

## 技术栈

| 层 | 选型 | 版本 |
| --- | --- | --- |
| 语言 | Python | 3.11 |
| Web 框架 | FastAPI | 0.141+ |
| ASGI | uvicorn | 0.52+ |
| 数据库 | MySQL 8.0 | utf8mb4 |
| 数据访问 | SQLAlchemy 2.0 **Core**（手写表定义，非 ORM） | 2.0.52 |
| 缓存 / Agent 状态 | Redis 7（**非必需**，故障时自动降级） | 8.1.0 |
| 大模型 | DeepSeek（OpenAI 兼容接口） | openai 3.8+ |

## 目录结构

```
campusai/
├── config.py                # 统一配置（从 .env 读取 MySQL / Redis / AI）
├── docker-compose.yml       # 本地开发依赖：MySQL + Redis
├── requirements.txt
├── .env.example             # 环境变量模板（复制为 .env 填写）
├── agents/                  # 多智能体层
│   ├── base.py              # BaseAgent（基类，含 run/session 状态机契约）
│   ├── registry.py          # 智能体注册表（AgentRegistry）
│   ├── manager_agent.py     # Manager：意图理解 / 任务分解 / 结果聚合
│   ├── academic_agent.py    # Academic：学业（考试/作业/课程）
│   ├── schedule_agent.py    # Schedule：日程 / 时间安排
│   ├── finance_agent.py     # Finance：财务 / 预算
│   ├── orchestrator.py      # 编排器：规划闭环主流程 run_planning()
│   ├── replanner.py         # 再规划：基于执行反馈调整
│   ├── llm.py               # DeepSeek 调用封装（含离线降级）
│   ├── prompts.py           # 各智能体的 System Prompt
│   ├── context.py           # 把校园数据组成为 LLM 上下文
│   ├── tools.py             # 给 Agent 用的数据读取工具
├── db/                      # 数据层（SQLAlchemy Core）
│   ├── engine.py            # 引擎 / Session 工厂
│   ├── cache.py             # Redis 封装（全部操作可优雅降级）
│   ├── models/              # 18 张表的元数据（Table 定义）
│   │   ├── base.py          # 公共工具（pk、时间列等）
│   │   ├── user.py          # 用户域
│   │   ├── academic.py      # 学业域
│   │   ├── life.py          # 生活/财务域
│   │   ├── task_plan.py     # 行动方案域
│   │   ├── conversation.py  # 会话域
│   │   └── agent_run.py     # Agent 运行轨迹域
│   └── repos/               # 数据访问仓库（Repository）
│       ├── base.py          # 通用助手 insert_and_fetch() 等
│       ├── user_repo.py / academic_repo.py / life_repo.py
│       ├── task_repo.py / conversation_repo.py / agent_run_repo.py
├── app/                     # API 层（FastAPI）
│   ├── main.py              # 应用工厂 + lifespan（启动时同步 4 个 Agent 到库）
│   ├── api/
│   │   ├── router.py        # 路由汇总（/api/v1）
│   │   ├── deps.py          # 依赖（Session / user_id 校验）
│   │   ├── routes/          # health / users / campus / plans / chat / conversations
│   │   └── schemas/         # Pydantic 响应模型
│   └── services/
│       └── chat_service.py  # 会话与规划业务编排
├── scripts/                 # 运维 / 初始化脚本
│   ├── init_db.py           # 建库建表（metadata.create_all）
│   ├── seed.py              # 写入演示数据
│   └── export_schema.py     # 导出建表 SQL 到 sql/schema.sql
├── sql/
│   ├── schema.sql           # 生成的建表语句
│   └── queries.sql          # 课程设计用查询示例
└── tests/                   # （预留）
```

## 分层架构与规划闭环

```
用户输入
   │
   ▼
┌──────────────────────── 规划闭环（orchestrator.run_planning）──────────────────────┐
│  Manager.understand    → 理解意图、识别目标                                              │
│  Manager.decompose     → 拆解为各专业 Agent 子任务                                        │
│  Academic/Schedule/Finance.analyze → 各自读取校园数据 + LLM 分析，产出建议                 │
│  Manager.aggregate     → 汇总为一份行动方案（Plan + 若干 PlanItem）                        │
│      │                                                                                   │
│      ▼                                                                                   │
│  执行（用户 / 前端按 Plan 执行，产生记录）                                                 │
│      │                                                                                   │
│      ▼                                                                                   │
│  反馈（用户反馈 / 数据变化）                                                              │
│      │                                                                                   │
│      ▼                                                                                   │
│  replanner.replan      → 基于反馈调整原方案（旧方案置为 superseded）                        │
└──────────────────────────────────────────────────────────────────────────┘
```

- **Agent 会话状态**（status 状态机：created→running→completed/failed）记录在 MySQL，
  Redis 只做**可选缓存**；Redis 不可用时所有读写自动降级、不影响主流程。
- **Action 闭合**：Manager 的 decompose / aggregate 动作与各子 Agent 的 analyze 动作都
  会正确写入 `agent_actions` 并标记 completed。
- **Agent 注册**：应用启动（lifespan）把注册表中的 4 个 Agent 幂等写入 `agents` 表。

## 数据库（18 张表）

按域划分，全部使用 SQLAlchemy Core 手写 `Table`（非 ORM 类）：

- **用户**：`users`、`user_preferences`
- **学业**：`courses`、`exams`、`assignments`、`study_records`
- **生活**：`activities`、`activity_enrollments`
- **财务**：`expenses`、`income`、`budgets`、`budget_categories`
- **行动方案**：`action_plans`、`action_plan_items`
- **会话 / Agent 轨迹**：`conversations`、`conversation_messages`、
  `agents`、`agent_sessions`、`agent_actions`

> 具体列定义见 [db/models/](db/models)，生成的建表 SQL 见 [sql/schema.sql](sql/schema.sql)。

## 快速开始

### 1. 准备环境变量

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

按注释填写 `.env`：MySQL 账号密码、DeepSeek API Key（见 docker-compose 中的默认端口 3307）。

### 2. 启动 MySQL 与 Redis

```bash
docker compose up -d
```

> ⚠️ 若宿主机 6379 端口已被占用（例如本机已运行其它 Redis），可将
> `.env` 中 `REDIS_PORT` 改为其它端口（如 6380）并重启容器；
> 即便 Redis 无法连接，系统也会自动降级运行。

### 3. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

### 4. 初始化库表 + 写入演示数据

```bash
python scripts\init_db.py       # 建表
python scripts\seed.py          # 清空并写入演示数据（含 demo 用户）
```

> 脚本若以 `python scripts\xxx.py` 运行需在项目根目录执行（已配置 PYTHONPATH）。

### 5. 启动 API

```bash
uvicorn app.main:app --reload --port 8010
```

- 健康检查：`GET http://127.0.0.1:8010/health`（返回 MySQL / Redis 连通性与已注册 Agent）
- 接口文档：`http://127.0.0.1:8010/docs`（Swagger UI）

## API 一览（前缀 `/api/v1`）

| 分组 | 路径 | 说明 |
| --- | --- | --- |
| 用户 | `/users/me` | 当前用户 + 偏好 |
| 校园 | `/campus/courses` `/campus/tasks` `/campus/finance/summary` 等 | 课程 / 作业考试 / 财务汇总 |
| 规划 | `/plans/latest` `/plans/{id}` `/plans/{id}/items` | 行动方案查询 |
| 对话 | `/chat` | 发起规划对话（走 orchestrator 闭环） |
| 会话 | `/conversations` | 会话与消息历史 |

所有响应统一为 `{"ok": bool, "data": ..., "message": str}`。

## 关键设计约定

1. **SQLAlchemy Core + Repository**：表结构集中定义在 `db/models`，读写全部经 `db/repos`
   仓库层；不定义 ORM 类，便于课程设计展示原生 SQL 能力。
2. **MySQL 兼容的插入后回读**：MySQL 8 不支持 `INSERT ... RETURNING`（仅 MariaDB 支持），
   统一用 `db/repos/base.py::insert_and_fetch()` —— 先 INSERT 再按主键 SELECT 回读。
3. **时间列**：`messages` / `agent_sessions` / `expenses` / `action_plan_items` 的
   `created_at` 无 `server_default`，仓库层必须显式 `created_at=datetime.now()`。
4. **Redis 优雅降级**：`db/cache.py` 对所有缓存操作做 try/except + 短路开关，
   任何 RedisError 都返回安全默认值而不是抛出，保证核心闭环不依赖 Redis。
5. **事务边界**：`chat_service` 先提交用户消息，再运行 orchestrator，保证数据库与规划解耦。
6. **统一编码**：源码 / 数据均为 UTF-8；Windows 控制台查看中文建议设置
   `PYTHONIOENCODING=utf-8` 或直接读文件（避免 GBK 误码）。

## 智能体

| Agent | 职责 |
| --- | --- |
| ManagerAgent | 意图理解、任务分解、结果聚合（协调者，不实现单步 run） |
| AcademicAgent | 学业分析：课程、考试、作业、学习记录 |
| ScheduleAgent | 日程规划：活动、时间安排、学习时段 |
| FinanceAgent | 财务分析：收支、预算 |

各 Agent 复用同一套 `AgentSession` 状态机与 `agent_actions` 记录，便于审计每轮规划。

## 开发路线（对应需求.docx）

1. 需求分析与 ER 设计（18 表）
2. 基础 CRUD + 数据层
3. 多 Agent 规划闭环（本框架已实现主线）
4. 前端与展示（预留）
