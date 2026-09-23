# Biz-Multi-Agent 系统架构与设计

> 配套文档：本文件为 `_index.md` 的架构详述，同目录下另有 `bdd-specs.md`（验收场景）、`feasibility-and-risks.md`（可行性/成本/风险）。

---

## 1. 系统模块全景

### 1.1 分层视图（自顶向下）

```
┌──────────────────────────────────────────────────────────────────┐
│ L0 表现层                                                        │
│  ├─ Web 后台  (FastAPI + Jinja2 + htmx + 极简 JS)                │
│  └─ CLI 工具  (开发者与运维使用)                                  │
├──────────────────────────────────────────────────────────────────┤
│ L1 编排层 (Orchestrator Agent)                                  │
│  └─ 任务拆解  依赖图  并行调度  失败重试 状态机                   │
├──────────────────────────────────────────────────────────────────┤
│ L2 Agent 层                                                      │
│  ├─ 电商线                                                       │
│  │   ├─ DataCollectorAgent     (多平台数据采集)                  │
│  │   ├─ RAGAgent               (平台规则/产品资料检索)            │
│  │   ├─ EvaluatorAgent         (评分/排名/缺口分析)              │
│  │   └─ ReporterAgent          (汇总/报告/多语种文案)            │
│  └─ 外贸线                                                       │
│      ├─ IngestionRouterAgent  (邮件/WhatsApp 入口分发)          │
│      ├─ InfoExtractorAgent    (产品/数量/价格/交期抽取)          │
│      ├─ CustomerTierAgent     (A/B/C 分层)                     │
│      ├─ QuoterAgent           (多语种 PI 报价单生成)            │
│      └─ FollowUpAgent         (24h/72h 邮件提醒)                │
├──────────────────────────────────────────────────────────────────┤
│ L3 服务层                                                        │
│  ├─ 模型网关 (MultiModelGateway)        — 路由/限流/重试/统计    │
│  ├─ RAG 服务 (RAGService)               — LlamaIndex + Chroma   │
│  ├─ 通知服务 (Notifier)                 — 邮件/WhatsApp/SSE      │
│  ├─ 调度服务 (Scheduler)                — APScheduler           │
│  ├─ 浏览器池 (BrowserPool)              — Playwright 无头集群   │
│  ├─ 文件服务 (FileService)              — 上传/解析/导出         │
│  └─ 鉴权服务 (AuthService)              — JWT + RBAC            │
├──────────────────────────────────────────────────────────────────┤
│ L4 数据层                                                        │
│  ├─ SQLite           (业务主数据：任务、询盘、客户、报价单)        │
│  ├─ Chroma           (向量存储：平台规则/产品知识库)              │
│  ├─ 文件存储          (商品图、报告 PDF、临时素材)                │
│  └─ Redis (可选)     (会话缓存、令牌桶状态)                      │
├──────────────────────────────────────────────────────────────────┤
│ 横切关注 (Cross-Cutting)                                          │
│  ├─ 结构化日志  (structlog + Loguru 调试)                        │
│  ├─ 链路追踪   (OpenInference → Phoenix Studio)                 │
│  ├─ 配置中心   (Pydantic Settings + YAML 热重载)                │
│  ├─ 异常处理   (全局中间件 + 分级告警)                            │
│  └─ 鉴权/限流  (FastAPI 中间件)                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 模块自治原则

| 原则 | 落地方式 |
|------|---------|
| 每 Agent 独立 | 独立 Prompt、工具集、模型配置；可单独启停 |
| 服务无状态 | 不在内存保存会话状态（除显式缓存） |
| 数据冷启动 | SQLite 单文件备份，Chroma 文件夹打包 |
| 接口优先 | 层间通过 Protocol/ABC 通信，不依赖具体实现 |

---

## 2. 核心组件契约

### 2.1 Orchestrator Agent（编排器）

**职责**：接收用户/系统提交的任务，拆解子任务、调度 Agent、处理依赖与重试。

**输入**：`TaskRequest { task_type, params, priority, deadline }`

**输出**：`TaskResult { status, report_url, agent_logs }`

**关键接口**：
```python
class Orchestrator(Protocol):
    async def submit(self, request: TaskRequest) -> TaskHandle: ...
    async def get_status(self, handle: TaskHandle) -> TaskResult: ...
    async def cancel(self, handle: TaskHandle) -> bool: ...
```

**依赖图（电商选品）**：
```
        Orchestrator
            │
      ┌─────┴─────┐
      │ 阶段1并行 │
   ┌──┴──┐   ┌──┴──┐
   │采集 │   │ RAG │   ← 并发
   └──┬──┘   └──┬──┘
      └───┬─────┘
          ↓
      ┌──────┐
      │评估  │
      └──┬───┘
          ↓
      ┌──────┐
      │汇总报告│
      └──────┘
```

**依赖图（外贸询盘）**：
```
   IngestionRouter
        │
        ↓
   InfoExtractor
        │
        ↓
   CustomerTier  ←  ←  历史交易查询
        │
        ↓
   Quoter
        │
        ↓
   FollowUp (异步，cron 触发)
```

---

## 3. 关键数据模型

### 3.1 任务 / Agent / 报告

```sql
-- 任务主表
CREATE TABLE tasks (
    id              TEXT PRIMARY KEY,           -- UUID
    task_type       TEXT NOT NULL,              -- 'selection' | 'inquiry' | 'analysis'
    status          TEXT NOT NULL,              -- 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
    priority        INTEGER DEFAULT 5,
    input_params    JSON NOT NULL,
    output_payload  JSON,
    error_message   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    agent_trace_id  TEXT,                       -- OpenTelemetry trace_id
    user_id         TEXT NOT NULL,
    tenant_id       TEXT NOT NULL               -- 预留多租户
);

CREATE INDEX idx_tasks_status ON tasks(status, created_at);
CREATE INDEX idx_tasks_user ON tasks(user_id, created_at);

-- 子任务记录（每个 Agent 的执行情况）
CREATE TABLE task_steps (
    id              TEXT PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(id) ON DELETE CASCADE,
    agent_name      TEXT NOT NULL,              -- 'DataCollector' | 'RAG' | ...
    sequence        INTEGER NOT NULL,
    status          TEXT NOT NULL,
    input_payload   JSON,
    output_payload  JSON,
    error_message   TEXT,
    started_at      TIMESTAMP,
    finished_at     TIMESTAMP,
    retry_count     INTEGER DEFAULT 0,
    token_usage     JSON                        -- {input, output, cost_usd}
);

CREATE INDEX idx_steps_task ON task_steps(task_id, sequence);

-- 报告
CREATE TABLE reports (
    id              TEXT PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(id) ON DELETE CASCADE,
    format          TEXT,                       -- 'markdown' | 'pdf' | 'json'
    file_path       TEXT,
    template_id     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 电商选品相关

```sql
-- 商品候选
CREATE TABLE products (
    id              TEXT PRIMARY KEY,
    platform        TEXT NOT NULL,              -- 'mercadolibre' | 'shopee' | 'tiktokshop'
    platform_sku    TEXT,
    title           TEXT,
    description     TEXT,
    price           REAL,
    currency        TEXT,
    category        TEXT,
    images          JSON,                       -- URL 列表
    score           REAL,                       -- 评估分数
    score_breakdown JSON,                       -- 多维度评分明细
    raw_data        JSON,                       -- 原始爬取数据
    fetched_at      TIMESTAMP,
    candidate_task  TEXT REFERENCES tasks(id)
);

CREATE INDEX idx_products_platform ON products(platform, score DESC);
CREATE INDEX idx_products_task ON products(candidate_task);

-- 平台规则文档
CREATE TABLE knowledge_docs (
    id              TEXT PRIMARY KEY,
    doc_type        TEXT NOT NULL,              -- 'platform_rule' | 'product_spec' | 'historical_case'
    platform        TEXT,
    title           TEXT,
    content         TEXT,
    metadata        JSON,
    embedding_id    TEXT,                       -- Chroma 中的 ID
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP
);
```

### 3.3 外贸询盘相关

```sql
-- 询盘记录
CREATE TABLE inquiries (
    id              TEXT PRIMARY KEY,
    source          TEXT NOT NULL,              -- 'whatsapp' | 'email'
    raw_text        TEXT NOT NULL,
    received_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_id     TEXT REFERENCES customers(id),
    language        TEXT,                       -- ISO 639-1
    intent          TEXT,                       -- 'quote' | 'sample' | 'partnership' | 'support'
    urgency         TEXT,                       -- 'low' | 'normal' | 'high' | 'urgent'
    status          TEXT,                       -- 'received' | 'processing' | 'replied' | 'closed'
    extracted_info  JSON,                       -- 抽取的询盘信息
    first_response_at TIMESTAMP,
    replied_at      TIMESTAMP,
    task_id         TEXT REFERENCES tasks(id)
);

CREATE INDEX idx_inquiries_customer ON inquiries(customer_id, received_at DESC);
CREATE INDEX idx_inquiries_status ON inquiries(status);

-- 客户
CREATE TABLE customers (
    id              TEXT PRIMARY KEY,
    name            TEXT,
    company         TEXT,
    phone           TEXT,                       -- 加密存储
    email           TEXT,                       -- 加密存储
    country         TEXT,
    tier            TEXT,                       -- 'A' | 'B' | 'C'
    tier_updated_at TIMESTAMP,
    tier_history    JSON,                       -- 分层变更历史
    metadata        JSON,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_tier ON customers(tier, tier_updated_at);

-- 报价单
CREATE TABLE quotes (
    id              TEXT PRIMARY KEY,
    inquiry_id      TEXT REFERENCES inquiries(id),
    customer_id     TEXT REFERENCES customers(id),
    products        JSON,                       -- [{sku, qty, unit_price, total}]
    incoterm        TEXT,                       -- 'FOB' | 'CIF' | 'EXW'
    currency        TEXT,
    total_amount    REAL,
    pi_template     TEXT,                       -- Proforma Invoice 模板
    status          TEXT,                       -- 'draft' | 'sent' | 'accepted' | 'rejected' | 'expired'
    sent_at         TIMESTAMP,
    valid_until     TIMESTAMP,
    created_by      TEXT                        -- 'auto' or user_id
);

-- 跟进任务
CREATE TABLE follow_ups (
    id              TEXT PRIMARY KEY,
    inquiry_id      TEXT REFERENCES inquiries(id),
    customer_id     TEXT REFERENCES customers(id),
    trigger_type    TEXT,                       -- '24h_no_reply' | '72h_follow' | 'manual'
    scheduled_at    TIMESTAMP,
    executed_at     TIMESTAMP,
    status          TEXT,                       -- 'pending' | 'sent' | 'failed' | 'cancelled'
    template_id     TEXT,
    retry_count     INTEGER DEFAULT 0
);

CREATE INDEX idx_followups_scheduled ON follow_ups(status, scheduled_at);
```

---

## 4. Agent 间通信协议

### 4.1 消息格式
```json
{
  "trace_id": "uuid",
  "from_agent": "Orchestrator",
  "to_agent": "DataCollector",
  "message_type": "request" | "response" | "event" | "error",
  "payload": { ... },
  "metadata": {
    "task_id": "uuid",
    "step_id": "uuid",
    "timestamp": "2026-09-23T12:00:00Z",
    "retry_count": 0
  }
}
```

### 4.2 通信方式
| 场景 | 方式 |
|------|------|
| Agent 同步调用 | 函数调用（in-process） |
| Agent 异步事件 | 进程内消息总线（AgentScope MsgHub） |
| 跨进程 | Redis Pub/Sub（多 worker 时） |
| 客户端实时推送 | SSE（每 chunk 推送前端） |

---

## 5. 第三方集成与外部依赖

### 5.1 LLM 厂商适配（统一网关层处理）

| 厂商 | 协议 | 适配策略 |
|------|------|---------|
| 豆包 / DeepSeek / Qwen | OpenAI 兼容 | 统一通过 OpenAI SDK |
| OpenAI / GPT 系列 | OpenAI 兼容 | 原生 SDK |
| Anthropic Claude | 私有 Messages API | 独立 adapter |
| Google Gemini | OpenAI 兼容层（部分） | adapter 兼容 + 私有函数调用 |

> **重要发现**（来自可行性研究）：Claude 必须用独立 SDK，消息格式与 OpenAI 完全不同；LiteLLM 已封装 100+ 模型，**MVP 建议在 L3 服务层用 LiteLLM 而非自研**，把"统一网关层"的复杂度降到最低。

### 5.2 业务数据源

| 数据源 | 接入方式 | 推荐度 |
|--------|---------|--------|
| 店小秘 ERP | OAuth2.0 + REST API | ⭐⭐⭐⭐⭐ 中间层首选 |
| 马帮 ERP | OAuth2.0 + REST API | ⭐⭐⭐⭐ 免费但限频 |
| 美客多官方 API | OAuth2.0 + REST | ⭐⭐⭐ 需卖家资质 + 品牌授权 |
| Shopee Open API | Partner Key + REST | ⭐⭐ 限频严格，反爬强 |
| TikTok Shop Partner API | OAuth2.0 + REST | ⭐⭐ 审批 4-8 周 |
| 第三方数据 (1号榜/蝉妈妈) | 付费 API | ⭐⭐⭐ 替代爬虫方案 |
| Playwright 自研爬虫 | 自维护 | ⭐ 仅演示场景 |

> **可行性研究结论**：直接对接各平台 SaaS (电商) 的浏览器自动化路径**全部为高合规风险**（账号封禁、违规下架）。**推荐折中：以 ERP（店小秘/马帮）为中间层，对接 ERP 即可覆盖 80% 多平台工作；平台侧浏览器自动化仅用于演示，** 不进生产。

### 5.3 通讯 / 邮件

| 服务 | 用途 | 接入方式 |
|------|------|---------|
| Twilio WhatsApp BSP | 询盘入口 | Webhook + REST 发送 |
| SendGrid / Mailgun | 跟进邮件 | SMTP / API |
| SMTP 自建 | 内部测试 | 25 端口 |

### 5.4 浏览器自动化

| 场景 | 工具 | 反检测方案 |
|------|------|----------|
| ERP 后台录入 | Playwright (自维护) | patch `navigator.webdriver` |
| 数据采集 (演示) | Playwright | 限速 + Mock UA |
| 多账号长保活 | 影刀 / AdsPower | 商业指纹浏览器（成本敏感） |

---

## 6. 部署拓扑

### 6.1 开发环境
```
┌─────────────────────────┐
│  本机                    │
│  ├─ docker-compose up   │
│  ├─ 代码热更新（卷挂载） │
│  └─ Mock 数据启用       │
└─────────────────────────┘
资源需求：8C16G（推荐），4C8G（凑合）
```

### 6.2 生产环境（自托管单机）
```
                ┌─────────────────────────────┐
                │ Nginx 反向代理 + HTTPS      │
                │ （Let's Encrypt 自动证书）   │
                └──────────────┬──────────────┘
                               │
       ┌───────────────────────┼────────────────────────┐
       │                       │                        │
       ▼                       ▼                        ▼
┌────────────┐         ┌─────────────┐          ┌─────────────┐
│ Web UI 容器│         │ API 容器     │          │ Workers 容器 │
│ (FastAPI)  │         │ (FastAPI)   │          │ (Agent 任务) │
│ Port 8080  │         │ Port 8000   │          │ × N 横向扩展 │
└────────────┘         └──────┬──────┘          └──────┬──────┘
                              │                       │
       ┌──────────────────────┴───────────────────────┴──────┐
       │                                                      │
       ▼                       ▼                              ▼
┌─────────────┐         ┌──────────────┐           ┌─────────────────┐
│ SQLite      │         │ Chroma       │           │ 共享文件卷       │
│ (业务主数据) │         │ (向量库)     │           │ (报告/上传文件)  │
│ 卷挂载      │         │ 卷挂载       │           │                 │
└─────────────┘         └──────────────┘           └─────────────────┘
       │
       ▼
┌─────────────────┐         ┌─────────────────┐
│ Phoenix Studio  │         │ 结构化日志       │
│ (链路追踪 UI)   │         │ (JSON + 控制台)  │
└─────────────────┘         └─────────────────┘

外联：
- 模型厂商（Anthropic / OpenAI / 火山引擎 / DeepSeek）
- Twilio / SendGrid（通知）
- 店小秘 ERP（OAuth）
```

### 6.3 高可用与扩展
- API 容器 / Workers 容器均可横向扩（K8s / Docker Swarm）
- SQLite 单机够用；超 50 万条询盘需切 PostgreSQL（保留接口）
- Chroma 单实例够；超 1 亿向量需切 Milvus/Qdrant

### 6.4 灰度与回滚
| 维度 | 策略 |
|------|------|
| 配置灰度 | YAML 多版本 + 按用户 ID 路由 |
| 模型灰度 | 路由表按百分比切流量（如 10% 新模型） |
| 代码回滚 | 镜像版本固定，docker-compose pull 上一版本 |
| 数据回滚 | SQLite 每日全量备份，丢失 < 24h |

---

## 7. 国际化与多语种

### 7.1 语种支持矩阵
| 语种 | 代码 | 业务用途 | 翻译方式 |
|------|------|---------|---------|
| 简体中文 | zh-CN | 后台 UI、Prompt 设计 | 原生 |
| 英语 | en | 通用通讯、Shopee SG/TW | LLM 生成 |
| 西班牙语 | es | 美客多 (MLA/MLB/MLM) | LLM 生成 + 平台规则库 |
| 葡萄牙语 | pt | 美客多 MLB | LLM 生成 + 平台规则库 |
| 阿拉伯语 | ar | 未来扩展（待 RAG 准备） | LLM 生成 |
| 印尼语 | id | Shopee ID | LLM 生成 |
| 泰语 | th | Shopee TH | LLM 生成 |

### 7.2 多语种落地的关键约束
- **Embedding 必须用 BGE-M3**（覆盖 100+ 语种）—— Chroma 中文检索召回率比 Milvus 低 5-15%，可在 MVP 容忍
- **平台字数硬约束**（如美客多 title 60 字符）超长必须截断 + 标记提示
- **PI 报价单的法定语言**：默认英文 + 客户语种双语，可在模板中配置

---

## 8. 可观测性体系

### 8.1 三支柱

#### 8.1.1 日志（Logs）
- **库**：structlog（生产 / JSON）+ Loguru（开发 / 彩色）
- **格式**：`{ts, level, trace_id, agent_name, task_id, event, ...fields}`
- **检索**：开发时 tail 控制台；生产时落 JSON 到文件，可用 `jq` / `Loki` 聚合

#### 8.1.2 指标（Metrics）
- 任务计数器 / 失败率（按 Agent、按错误类型）
- LLM 调用次数 / Token 用量 / 成本（按模型、按 Agent）
- 选品任务 P50 / P99 延迟
- 询盘处理 P50 / P99 延迟

#### 8.1.3 链路追踪（Traces）
- **库**：OpenInference（Auto-instrumentation LLM 调用）
- **后端**：Phoenix Studio（自带 UI，零运维）
- **语义约定**：使用 OpenTelemetry `gen_ai.*` 约定
- **采样**：默认 always-on，关键路径 tail-sampling

### 8.2 SLO 定义

| SLO | 目标 | 测量 |
|-----|------|------|
| 选品可用率 | ≥ 99% | 1 - (失败任务数 / 总任务数) |
| 询盘响应延迟 P99 | ≤ 15 秒 | Phoenix trace 查询 |
| 任务完整率 | ≥ 99.5% | 落地数 / 提交数 |
| LLM 调用成功率 | ≥ 99% | 含重试后的成功率 |

---

## 9. 配置管理

### 9.1 配置分层
```
config/
├── base.yaml             # 公共配置
├── development.yaml      # 开发环境
├── staging.yaml          # 测试环境
├── production.yaml       # 生产环境
└── secrets/              # 密钥（不进 git）
    ├── anthropic.yaml
    ├── openai.yaml
    └── twilio.yaml
```

### 9.2 热更新机制
- YAML 文件监听（watchdog）
- 变更时触发 `reload()` 钩子
- 仅特定配置项支持热更新（如 Prompt、路由规则）
- 模型 Key、数据库连接等变更需重启

### 9.3 必须外置的配置
- 所有 API Key（绝对不写代码）
- Prompt 模板（业务可调）
- 路由规则（按任务类型映射模型）
- 限流阈值
- 跟进节奏（24h / 72h）
- 客户分层规则（A/B/C 阈值）

---

## 10. 技术栈汇总

| 类别 | 选型 | 备注 |
|------|------|------|
| 语言 | Python 3.11+ | type hints 全开 |
| Agent 框架 | AgentScope 1.0+ | 阿里通义出品，生产可用 |
| 模型封装 | LiteLLM | 自研复杂度太高 |
| RAG | LlamaIndex 0.10+ | 工作流 API |
| 向量库 | Chroma | 单二进制，MVP 够用 |
| Embedding | BGE-M3 | 中英及多语种 |
| 数据库 | SQLite + SQLAlchemy | 预留 PG 切换 |
| Web 后端 | FastAPI | 自动 OpenAPI |
| Web 前端 | Jinja2 + htmx | 极简，全服务器渲染 |
| 浏览器自动化 | Playwright | 演示为主 |
| 调度 | APScheduler | 同步调度，简单 |
| 重试 | Tenacity + pybreaker | 熔断器 |
| 日志 | structlog + Loguru | 生产 + 开发 |
| 链路追踪 | OpenInference + Phoenix | 零运维 Studio |
| 配置 | Pydantic Settings | YAML + 环境变量 |
| 容器化 | Docker Compose | 单机一键 |
| 邮件 | SendGrid | 多语种模板 |
| WhatsApp | Twilio | BSP，模板预审 |
| 测试 | pytest + pytest-cov | 核心覆盖率 > 60% |

---

*配套文件：bdd-specs.md | feasibility-and-risks.md*
