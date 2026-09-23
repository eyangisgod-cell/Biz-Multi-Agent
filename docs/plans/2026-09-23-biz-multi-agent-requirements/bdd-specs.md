# Biz-Multi-Agent 验收场景（BDD Specs）

> 配套文档：本文件为 `_index.md` 的可测试场景集，使用 Gherkin 语法。
> 每个 Feature 对应 `_index.md` §3 的一个功能模块；Scenario 同时覆盖正常路径、边界、异常与降级。

---

## Feature 1: 多模型统一封装层（MultiModelGateway）

### Background
```
Given 系统已配置 Claude / GPT / Gemini / 豆包的 API Key
And 系统已配置按任务类型的路由规则（config/routing.yaml）
And 系统已配置令牌桶限流参数
```

### Scenario: 模型正常调用返回成功结果
```
Given 用户提交 "请用 Sonnet 复述这句话"
When 模型网关收到 chat/completions 请求
Then 网关根据路由规则选择 Sonnet 4.6
And 在 2 秒内返回首个 token（SSE）
And 完整结果在 10 秒内返回
And 调用记录写入成本日志（model, tokens, cost_usd）
```

### Scenario: 模型路由按任务类型生效
```
Given 路由规则配置：
  | task_type       | model                |
  | reasoning       | claude-sonnet-4.6    |
  | generation      | doubao-pro           |
  | classification  | gemini-flash         |
  | embedding       | bge-m3               |
When 任务类型为 "reasoning" 的请求进入网关
Then 网关选择 Sonnet 4.6 而非 GPT-4o
```

### Scenario: 主模型超时自动 Fallback
```
Given 主路由模型 Sonnet 配置 fallback 为 GPT-4o-mini
And 当前 Sonnet 服务端超时（连接 30 秒不返回）
When 网关发起 chat 请求
Then 30 秒后网关判定超时
And 自动重试调用 GPT-4o-mini
And 主次模型结果通过结果归一化层做格式统一后返回
And 调用日志记录 "fallback=true, primary=sleep, secondary=gpt-4o-mini"
```

### Scenario: 限流触发排队而不报错
```
Given 令牌桶配置 RPM=60, TPM=100000
And 当前累计消耗 TPM 已达 95000
When 下一个 8000-token 请求进入
Then 网关把该请求放入等待队列
And 排队 1 秒内完成放行
And 实际响应不返回 429 错误
```

### Scenario: API Key 全部失效进入降级模式
```
Given 配置中有 3 个 Claude Key 与 2 个 GPT Key
And 当前所有 Key 都被服务端拒绝（401/403）
When 新请求进入网关
Then 网关进入 "全模型失效" 状态
And 返回缓存中的兜底话术（业务定义）
And 触发告警通知运维（邮件 + 控制台告警）
And 健康检查 endpoint 标记为 unhealthy
```

### Scenario: 流式输出中断后客户端重连
```
Given SSE 连接已建立并推送了 5 个 chunk
When 客户端 TCP 连接意外中断（5 秒后重连）
Then 服务端能在 5 秒内清理已断开的 writer
And 任务继续在服务端生成，不被错误中断
And 客户端重连后可通过 get_status 拉取完整结果
```

---

## Feature 2: 多 Agent 协作框架（AgentScope）

### Scenario: Orchestrator 拆解选品任务并调度 Agent
```
Given 用户通过 Web 后台提交任务："蓝牙耳机，美客多墨西哥站，Top 20"
When Orchestrator 收到 TaskRequest
Then Orchestrator 输出任务依赖图：
   step1: [DataCollector, RAGAgent]  // 并行
   step2: [Evaluator]                 // 依赖 step1
   step3: [Reporter]                  // 依赖 step2
And 按依赖图依次调度 Agent
And 每个 Agent 的入参/出参记录到 task_steps 表
```

### Scenario: 子任务失败触发 Tenacity 重试
```
Given RAGAgent 第一次调用 LLM 出现 connection error
When Tenacity 装饰器捕获到 retryable exception
Then 进入指数退避（1s, 2s, 4s）
And 重试 3 次
And 若仍失败则把该 step 标记为 failed
And 整个任务标记为 partial_success（其他 Agent 结果保留）
And 错误消息写入死信队列
```

### Scenario: RAG 检索为空回退到纯 LLM 推理
```
Given 查询 query "美客多玩具类目上架限制"
When LlamaIndex 在 Chroma 中检索相似度 > 0.7 的文档
And 没有文档超过阈值
Then RAGAgent 不抛错，返回空结果
And EvaluatorAgent 收到标注 "rag_empty=true"
And ReporterAgent 在报告中标注 "无知识库依据"
```

### Scenario: Agent 间消息总线异步通信
```
Given ReporterAgent 正在生成 5MB 的报告 PDF
And ReporterAgent 通过消息总线通知 Orchestrator "step3 finished"
When Orchestrator 收到通知
Then Orchestrator 不阻塞，立即更新 task 状态为 "completed"
And 后续异步触发报告持久化、通知、统计等
```

### Scenario: 共享记忆在并发 Agent 间共享
```
Given DataCollector 和 RAGAgent 并行执行
And 它们都把 "platform=mercadolibre, country=MX" 写入 SharedMemory
When 这两个 Agent 都完成后，EvaluatorAgent 读取 SharedMemory
Then EvaluatorAgent 能读到两个 Agent 的产品数据 + 平台规则
And 没有并发写冲突（最后写者生效，适合"状态覆盖"语义）
```

### Scenario: 链路追踪全链路可视化
```
Given 用户提交一个完整选品任务
When 任务在 Studio 可视化界面查看
Then 能看到 4 个 span：Orchestrator / DataCollector / RAG / Evaluator / Reporter
And 每个 span 显示：开始时间、持续时间、token 用量、模型名
And span 嵌套关系正确（Orchestrator 是 root span）
```

---

## Feature 3: 电商 Agent（电商线）

### Scenario: 完整选品流程 2 分钟内出报告
```
Given 用户在 Web 后台提交："蓝牙耳机，mercadolibre 墨西哥站，Top 20"
When 系统开始执行
Then Orchestrator 在 5 秒内调度 4 个 Agent
And DataCollector 在 30 秒内返回 ≥ 100 条商品数据
And RAGAgent 在 15 秒内返回平台规则文档
And EvaluatorAgent 在 20 秒内完成评分排序
And ReporterAgent 在 15 秒内生成完整报告
And 总耗时 ≤ 120 秒
And 报告含：Top 20 候选、评分明细、市场分析、营销建议
```

### Scenario: 选品报告可导出多种格式
```
Given 选品任务已完成，报告已生成
When 用户点击"导出"
Then 支持三种格式：Markdown、PDF、JSON
And Markdown 文件 < 1 MB
And PDF 含品牌水印（可关闭）
And JSON 字段齐全（候选列表 + 评分明细 + 时间戳）
```

### Scenario: 多语种文案生成通过平台字数校验
```
Given 候选商品需生成美客多墨西哥站文案（语言 es-MX）
When ReporterAgent 调用文案生成
Then 标题 ≤ 60 字符（含西班牙语重音符号）
And 描述 ≤ 5000 字符
And 关键词密度在 3-5% 之间
And 输出满足平台硬约束（不超长、不违规词）
```

### Scenario: 数据采集来源可选
```
Given 用户在新建任务页选择数据源
When 选项为 "CSV 文件"
Then 系统从指定路径读取 CSV（字段：sku, title, price, url）
When 选项为 "官方 API（mercadolibre）"
Then 系统使用已授权的 OAuth token 调用官方 REST API
When 选项为 "Playwright 爬虫（演示模式）"
Then 系统启动 headless Chromium 拉取 mock 站点数据
And 任一选项失败时自动降级到下一选项
```

### Scenario: 图片描述由 VLM 生成
```
Given 候选商品有一张商品图（蓝牙耳机）
When ReporterAgent 调用 VLM（如 GPT-4o-mini 或 Claude vision）
Then VLM 返回 alt text："Wireless Bluetooth Earphone with Charging Case, Matte Black"
And 场景描述："现代办公/通勤场景"
And 卖点提取："主动降噪、续航 30 小时、IPX5 防水"
```

### Scenario: 平台规则查询合规建议
```
Given 用户在 Web 后台提问 "美客多玩具类目上架有什么限制？"
When 查询进入 RAGAgent
Then RAGAgent 在 Chroma 检索相关规则文档
And 返回内容含强制引用来源（如 "[来源: doc_id=ml_toys_rule_2024]"）
And 输出不含凭空捏造的内容
And 输出长度可控（< 500 字）
```

---

## Feature 4: 外贸询盘 Agent（外贸线）

### Scenario: WhatsApp 询盘 15 秒内完成全流程
```
Given 系统已配置 Twilio WhatsApp 集成
And 一个英文询盘到达："Hi, I need 500pcs bluetooth earphone, FOB Shenzhen, target price $8.5, delivery in 30 days"
When Twilio webhook 触发系统接收
Then 3 秒内自动回复（"Thank you for your inquiry..."）
And InfoExtractor 在 5 秒内提取信息：
   | 字段     | 值                              |
   | 产品     | bluetooth earphone              |
   | 数量     | 500 pcs                          |
   | 目标价   | $8.5                            |
   | 交期     | 30 days                         |
   | Incoterm | FOB Shenzhen                    |
And CustomerTier 在 3 秒内给出 "B"
And Quoter 在 10 秒内生成英文 PI 报价单
And 业务员在 Web 后台看到完整结果
```

### Scenario: 客户分层准确率 ≥ 80%
```
Given 100 条金样询盘数据（人工已分层）
When 系统对每条询盘分层
Then 准确率 ≥ 80%
And A/B/C 三层分布合理：A<20%, B<50%, C<50%（与人工分布大致一致）
And 系统支持人工覆盖（修改分层后客户表更新）
```

### Scenario: A/C 级客户报价自动发送，B 级需人工确认
```
Given 询盘来自 A 级客户
When QuoterAgent 生成报价单 PI
Then 5 分钟内自动发送报价邮件
And PI 含 Incoterm 2020 标准条款

Given 询盘来自 B 级客户
When QuoterAgent 生成报价单
Then 标记为 "pending_review"
And 业务员在 Web 后台看到 "需确认"
And 业务员点击 "确认发送" 或 "修改" 后才发出

Given 询盘来自 C 级客户
When QuoterAgent 生成报价单
Then 直接发送（不需确认）
```

### Scenario: 24h/72h 跟进邮件自动触发
```
Given 客户已收到报价单但未回复
When 24 小时无回复
Then FollowUpAgent 自动发送第一封跟进邮件
When 72 小时仍无回复
Then 发送第二封跟进邮件（语气更礼貌）
When 7 天仍无回复
Then 任务标记为 "expired"，不再触发跟进
```

### Scenario: 客户信息结构化存储
```
Given 询盘到达，系统抽取到客户信息：
   {name: "John Doe", company: "ABC Trading", phone: "+1234567890", email: "john@abc.com"}
When InfoExtractor 完成
Then customers 表新增一行（phone, email 加密存储）
And inquiries 表新增一行（外键 customer_id）
And Web 后台可按客户名/电话/邮箱查询
```

---

## Feature 5: 业务流程自动化（RPA）

### Scenario: Playwright 演示上架流程
```
Given 演示模式（mock 站点）
When 用户点击 "演示上架流程"
Then 启动 headless Chromium
And 打开 mock 站点登录页
And 自动填入账号密码
And 自动填写商品信息
And 点击 "提交"，截图保留
And 完整流程可在 30 秒内跑完
```

### Scenario: APScheduler 定时执行采集任务
```
Given cron 配置："0 9 * * *" 表示每天 9 点
When 系统时间为第二天 9:00
Then 调度器自动触发选品任务（按昨日任务的延续）
And 任务进入队列，等待 worker 执行
```

### Scenario: 影刀 / ERP 接口预留
```
Given 影刀集成的接口契约：
   POST /api/v1/rpa/execute
   { workflow_id, params }
When 未来影刀账号接入并发起调用
Then 系统返回 202 Accepted + task_id
And 提供查询接口 /api/v1/rpa/tasks/{id}
```

### Scenario: 店小秘 ERP 订单同步（推荐路径）
```
Given 店小秘 OAuth2.0 token 已获取
And 同步频率配置为 5 分钟一次
When 调度器每 5 分钟触发
Then 调用店小秘 /api/order/list 拉取新增订单
And 把订单数据写入本地 orders 表
And Web 后台可查询
```

---

## Feature 6: 工程基础设施

### Scenario: docker-compose up 5 分钟内启动
```
Given 全新环境（Linux VPS 8C16G）
When 用户运行 docker-compose up -d
Then 5 分钟内所有服务就绪（API / Web / Workers / Chroma / Phoenix）
And /docs 路径可访问 Swagger
And /healthz 路径返回 200
```

### Scenario: 结构化日志按 Agent/任务过滤
```
Given 任务已运行，日志已落盘
When 运维执行 `grep task_id=abc123 app.log | jq`
Then 能看到该任务的所有 Agent 日志
And 日志按 trace_id 关联
```

### Scenario: 故障注入测试自动恢复
```
Given 系统正在处理 1 个选品任务
And DataCollector 正在调用 Sonnet
When 运维 kill Sonnet 的进程（模拟主模型故障）
Then 模型网关在 5 秒内检测到故障
And 自动 fallback 到 GPT-4o-mini
And 任务继续完成，报告正常生成
And 告警邮件发给运维
```

### Scenario: 配置热更新不重启服务
```
Given 当前 Prompt 是 "你是助手 A"
When 运维修改 config/prompts.yaml 中 Prompt 为 "你是助手 B"
Then 5 秒内服务自动加载新 Prompt
And 后续任务使用新 Prompt
And 不需要重启 API 或 Workers
```

### Scenario: LLM 调用成功率 ≥ 99%
```
Given 系统运行 30 天
When 检查 metrics
Then LLM 调用成功率（含重试）≥ 99%
And P99 调用延迟 ≤ 5 秒
And 总成本落在 $300-$500 推荐区间
```

### Scenario: 单元测试覆盖率 ≥ 60%
```
Given 仓库已有单元测试
When 运行 pytest --cov=biz_multi_agent
Then core 业务模块覆盖率 ≥ 60%
And Agent 层 ≥ 50%
And 服务层 ≥ 70%
```

---

## Feature 7: 非功能验收（NFR 性能）

### Scenario: 选品任务并发 5 个不阻塞
```
Given 系统已启动并处于空闲
When 用户同时提交 5 个选品任务
Then 5 个 Worker 容器各处理 1 个
And 5 个任务都在 120 秒内完成
And 无资源竞争错误（CPU < 80%）
```

### Scenario: 询盘突发 100 条/小时不丢失
```
Given 系统处于稳定运行
When 1 小时内涌入 100 条询盘
Then 所有询盘都被记录
And 每条都得到至少 1 次自动响应
And customers / inquiries 表无丢失
And 业务后台可查询
```

---

## Feature 8: 安全验收

### Scenario: API Key 不出现在代码或日志中
```
Given 所有 LLM Key 配置在 .env 文件
When 爬取代码仓库（git grep "sk-" 或 "anthropic"）
Then 命中数 = 0（除 .env.example）
When 爬取运行日志（grep -r "sk-" logs/）
Then 命中数 = 0
```

### Scenario: JWT 鉴权阻止未授权访问
```
Given 用户未登录访问 /api/v1/tasks
When 发出 GET 请求
Then 返回 401 Unauthorized
When 用户携带有效 token 访问
Then 返回 200 OK + 任务列表
```

### Scenario: 客户手机号日志脱敏
```
Given 客户 phone = "13800138000"
When 系统记录客户访问日志
Then 日志中 phone 字段为 "138****8000"
And 数据库中 phone 字段为加密存储
```

### Scenario: SQL 注入防护
```
Given 输入包含恶意字符串："'; DROP TABLE customers; --"
When 用户名输入进入查询
Then 系统使用参数化查询
And 数据库表不被删除
And 查询返回空集
```

---

## Feature 9: 业务验收（用户视角）

### Scenario: 电商运营 30 分钟掌握系统
```
Given 用户首次接触系统
When 按 README 步骤操作：
   | 步骤                      | 期望结果          |
   | docker-compose up         | 5 分钟内启动      |
   | 打开 http://localhost    | Web 后台可访问    |
   | 输入 "蓝牙耳机" 点击运行 | 2 分钟内出报告    |
Then 在 30 分钟内首次完成选品任务
```

### Scenario: 外贸业务员首次报价
```
Given 用户首次接触系统
When 模拟一条 WhatsApp 询盘进入系统
Then 业务员在 Web 后台看到自动回复 + 分层 + 报价草稿
And 点击 "确认发送" 后真实邮件发出
```

---

## Feature 10: 故障恢复

### Scenario: Worker 崩溃任务不丢失
```
Given 1 个 Worker 正在处理任务
And 该 Worker 容器被 kill -9
When Orchestrator 检测到心跳超时
Then 任务被另一 Worker 接管
And 状态基于 Pipeline Checkpoint 恢复
And 任务最终完成，不丢失中间结果
```

### Scenario: 数据库损坏可恢复
```
Given SQLite 数据库损坏（模拟掉电）
When 系统启动检测到 DB 异常
Then 自动从最近备份恢复（≤ 24h 数据）
And 写入异常事件
And 运维收到告警
```

---

## 验收汇总表

| 维度 | 关键场景 | 通过标准 |
|------|---------|---------|
| 模型网关 | Feature 1 全部场景 | 6/6 通过 |
| Agent 框架 | Feature 2 全部场景 | 6/6 通过 |
| 电商线 | Feature 3 全部场景 | 6/6 通过 |
| 外贸线 | Feature 4 全部场景 | 5/5 通过 |
| RPA | Feature 5 全部场景 | 4/4 通过 |
| 工程 | Feature 6 全部场景 | 6/6 通过 |
| 性能 | Feature 7 全部场景 | 2/2 通过 |
| 安全 | Feature 8 全部场景 | 4/4 通过 |
| 业务 | Feature 9 全部场景 | 2/2 通过 |
| 恢复 | Feature 10 全部场景 | 2/2 通过 |

**总计：43 个场景全部通过方可视为 MVP 验收通过。**

---

*配套文件：_index.md | architecture.md | feasibility-and-risks.md*
