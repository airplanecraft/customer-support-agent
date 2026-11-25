# Update history / 更新记录

[README (English)](README.md) | [README（中文）](README.zh-CN.md)

Newest first. Each entry is written in English and Chinese. Diagram IDs refer to `docs/diagrams/`.

最新的在最上面。每条记录都有中英文。图编号对应 `docs/diagrams/`。

---

## v1.2 — 2026-11-25

**English**
- Section 12 expanded and renamed **Cross-channel continuity and sync**: principles (identity never crosses channels, backend as single source of truth, sync state not conversations, eventual consistency), eight scenarios (call → app, app → call, both at once, send to app via plain deep link, "Call us", multi-device, notifications, agent timeline) and rules.
- Deliberately simple: no continuation tokens, no live mirroring, no "on a call" banner, no custom callback.
- BND-TRS-04 now also states that notifications and deep links carry no credentials.

**中文**
- 第 12 节扩写并改名为 **跨渠道衔接与同步**：原则（身份不跨渠道、后端是唯一事实来源、只同步状态不同步对话、最终一致）、八个场景（通话 → App、App → 通话、同时进行、用普通深链接发到 App、"致电客服"、多设备、通知、坐席时间线）以及规则。
- 刻意保持简单：不做续办 token、不做实时镜像、不显示"正在通话"、不做定制回电。
- BND-TRS-04 补充：通知和深链接不带任何凭证。

---

## v1.1 — 2026-11-25

**English**
- Appendix A renamed from "Limits, timeouts and budgets" to **System boundaries**: what the AI may do, see and trust, and how far it may go.
- New boundary lists with IDs, enforcement point, behaviour on crossing and red-team tests: A.1 scope (`BND-SCP`), A.2 actions (`BND-ACT`), A.3 data (`BND-DAT`), A.4 identity and trust (`BND-TRS`).
- Former limit tables moved under A.5 operational boundaries (`BND-OPS-1…7`), unchanged.
- Gates: A.1–A.4 zero tolerance; at least 5 boundary-suite cases per boundary; every test and red-team finding tagged with a boundary ID.
- Section 14.4 now takes its targets from Appendix A; section 4.6 links to A.2.

**中文**
- 附录 A 从"限制超时与预算"改名为 **系统边界**：AI 能做什么、能看到什么、信任谁、最多能做到什么程度。
- 新增带 ID 的边界清单，每条写明执行位置、越界后的处理和红队测试：A.1 业务范围（`BND-SCP`）、A.2 操作（`BND-ACT`）、A.3 数据（`BND-DAT`）、A.4 身份与信任（`BND-TRS`）。
- 原来的限制表移到 A.5 运行边界（`BND-OPS-1…7`），内容不变。
- 闸门：A.1–A.4 零容忍；每条边界在边界测试集里至少 5 个用例；每个测试和红队发现都标注边界 ID。
- 第 14.4 节的测试目标改为来自附录 A；第 4.6 节链接到 A.2。

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
