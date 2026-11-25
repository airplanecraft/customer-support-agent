# Update history / 更新记录

[README (English)](README.md) | [README（中文）](README.zh-CN.md)

Newest first. Each entry is written in English and Chinese. Diagram IDs refer to `docs/diagrams/`.

最新的在最上面。每条记录都有中英文。图编号对应 `docs/diagrams/`。

---

## v1.0 — 2026-11-25

Baseline. History starts here; earlier work is folded into this version.

基线版本。更新记录从这里开始，之前的工作都并入这个版本。

**English**
- Vertical-agnostic core plus domain packs, for regulated industries; voice (Genesys) and chat (app, web, WhatsApp) on one shared core.
- Agent design: routing plus bounded workers on LangGraph; config in code; on-demand skills; what one LLM call contains.
- Tool and API contracts (4.6): MCP tools vs internal REST APIs, write tiers T0–T3, quote → confirm → commit, order and refund tools, refund auto-approval switch.
- Hybrid RAG (dense + BM25, RRF, rerank, citation checks); all-Qwen model inventory; cloud (Bailian, Hong Kong) and on-prem (vLLM) profiles.
- Identity: OIDC + PKCE with BFF, voice verification (SMS OTP + DOB via Genesys secure flow), token exchange, TLS vs mTLS, RBAC with seven enforcement points, token ownership in approvals.
- Business flows C1–C7: account lookup (voice, chat), cancellation, account change with approval, orders and history, refund, customer satisfaction.
- Sessions, tasks and recovery; state, memory and caching (11), including the token store and why not LangMem.
- Guardrails, evaluation and testing, LLMOps (Git → pipeline → Langfuse), observability and CSAT, security checklist.
- Known trade-offs, with ⭐ #1: user IDs differ across subsystems.
- Appendix A: limits, timeouts, agent-loop caps and token budgets.
- 28 draw.io diagrams generated from code; Chinese README (`README.zh-CN.md`) sharing the English diagrams.

**中文**
- 与行业无关的通用核心加行业包，面向受监管行业；语音（Genesys）和聊天（App、Web、WhatsApp）共用同一个核心。
- Agent 设计：基于 LangGraph 的路由加受限 worker；配置写在代码里；按需加载 skill；一次 LLM 调用包含什么。
- Tool 与 API 契约（4.6）：MCP 工具与内部 REST API 分层，写操作分 T0–T3 四级，quote → 确认 → commit，订单与退款工具，退款自动批准开关。
- 混合 RAG（向量 + BM25、RRF、重排、引用校验）；全部使用 Qwen 的模型清单；云上（百炼，香港）和本地（vLLM）两种部署形态。
- 身份：OIDC + PKCE 加 BFF，语音核验（Genesys 安全流程中的短信 OTP + 出生日期），token exchange，TLS 与 mTLS，七个执行点的 RBAC，审批中的 token 归属。
- 业务流程 C1–C7：账户查询（语音、聊天）、解约、带审批的账户变更、订单与历史订单、退款、客户满意度。
- 会话、任务与恢复；状态、记忆与缓存（第 11 节），包括 token store 以及为什么不用 LangMem。
- 护栏、评估与测试、LLMOps（Git → 流水线 → Langfuse）、可观测性与满意度、安全检查清单。
- 已知取舍，⭐ 第 1 条：各子系统的用户 ID 不一致。
- 附录 A：限制、超时、agent 循环上限与 token 预算。
- 28 张由代码生成的 draw.io 图；中文 README（`README.zh-CN.md`）与英文版共用图。
