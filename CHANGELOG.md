# Update history / 更新记录

[README (English)](README.md) | [README（中文）](README.zh-CN.md)

Newest first. Each entry is written in English and Chinese. Diagram IDs refer to `docs/diagrams/`.

最新的在最上面。每条记录都有中英文。图编号对应 `docs/diagrams/`。

---

## v1.10 — 2026-11-25

**English**
- A2 components: nine **design highlights** marked with orange borders and numbered badges (external API gateway, internal API gateway, MCP servers, RAG service, model gateway, token store, approval service, guardrail library, LLMOps plane), with a legend explaining each one.
- Three **key paths** drawn as thick coloured lines: channels → external API gateway → orchestrator (green); orchestrator → MCP → internal API gateway → systems of record (red); orchestrator / RAG → model gateway → Bailian or vLLM (blue).
- A3 network: the same numbering for the gateways, MCP, RAG and model gateway, and the same path colours.
- Section 2 explains how to read A2. Diagram helpers `emph`, `badge` and line width added to `tools/drawio_lib.py`.

**中文**
- A2 组件图：用橙色边框和编号标出九个 **设计亮点**（外部 API 网关、内部 API 网关、MCP server、RAG 服务、模型网关、token store、审批服务、护栏库、LLMOps 区域），并加图例逐条说明。
- 三条 **关键路径** 用加粗彩色线画出：渠道 → 外部 API 网关 → orchestrator（绿）；orchestrator → MCP → 内部 API 网关 → 业务系统（红）；orchestrator / RAG → 模型网关 → 百炼或 vLLM（蓝）。
- A3 网络图：网关、MCP、RAG 和模型网关用同样的编号，路径用同样的颜色。
- 第 2 节说明怎么看 A2。`tools/drawio_lib.py` 新增 `emph`、`badge` 和线宽参数。

---

## v1.9 — 2026-11-25

**English**
- **4.4 Skills rewritten: one folder per agent** (`skills/<agent>/<skill>/SKILL.md`, plus `_shared/`). A worker can load only its own skills and the shared ones listed for it, enforced in code like the tool allowlist.
- Skill catalogue per agent (12 skills), with who loads each one (model or router); compliance-critical skills (`profile_change`, `address_change`, `cancellation`, `refund_request`, `vulnerable_customer`) are loaded by the router.
- `SKILL.md` format: front matter checked at startup (agent, version, owner, compliance review, channels, assurance, tools, eval tags) and a procedure body (when to use, steps, never, hand off, voice).
- Skill lifecycle: owner and compliance review, CI front-matter checks, tagged golden-set cases, versions pinned in the release manifest and recorded in traces.
- 4.2 workers table: new skills `fee_explain`, `billing_explain`, `refund_request`.
- Components table: MCP servers explained (the tool layer; one mTLS client certificate per server so the internal gateway limits each to its own APIs); Order MCP added.
- Diagrams: A2 and A3 add the missing Order MCP (A3 also Identity MCP); A4 adds `order_agent` and the new skills.

**中文**
- **重写 4.4 Skills：每个 agent 一个文件夹**（`skills/<agent>/<skill>/SKILL.md`，另有 `_shared/`）。Worker 只能加载自己的 skill 和为它列出的共享 skill，像工具白名单一样由代码强制执行。
- 按 agent 列出 skill 清单（12 个），并标明由谁加载（模型或路由器）；合规关键的 skill（`profile_change`、`address_change`、`cancellation`、`refund_request`、`vulnerable_customer`）由路由器加载。
- `SKILL.md` 格式：启动时校验的 front matter（agent、版本、负责人、合规审阅、渠道、身份等级、工具、评估标签）和流程正文（适用场景、步骤、禁止事项、转人工、语音）。
- Skill 生命周期：负责人和合规审阅、CI 校验 front matter、带标签的 golden set 用例、版本锁定在发布清单并记录在 trace 中。
- 4.2 worker 表：新增 `fee_explain`、`billing_explain`、`refund_request`。
- 组件表：解释 MCP server（工具层；每个 server 一张 mTLS 客户端证书，内部网关只允许它访问自己的 API）；补上订单 MCP。
- 图：A2 和 A3 补上缺失的订单 MCP（A3 还补上身份 MCP）；A4 加入 `order_agent` 和新 skill。

---

## v1.8 — 2026-11-25

**English**
- Section 22 tech stack rewritten as a table: category, component, version and what it does in this design (51 rows).
- Versions are the latest releases checked on 2026-11-25 (PyPI, npm, GitHub releases, endoflife.date, Hugging Face); models are listed by Hugging Face ID; managed services (Bailian, Genesys, Apigee) are marked as such.
- Newer model families (Qwen3.5, Qwen3.8, Qwen3-VL-8B, Fun-CosyVoice3) are listed as candidates, adopted only through the golden set and release gates.

**中文**
- 第 22 节技术栈改成表格：类别、组件、版本、在本设计中的用途（51 行）。
- 版本号是 2026-11-25 查到的最新发布版本（PyPI、npm、GitHub releases、endoflife.date、Hugging Face）；模型按 Hugging Face ID 列出；托管服务（百炼、Genesys、Apigee）单独标注。
- 较新的模型系列（Qwen3.5、Qwen3.8、Qwen3-VL-8B、Fun-CosyVoice3）列为候选，只有通过 golden set 和发布闸门才采用。

---

## v1.7 — 2026-11-25

**English**
- **Local development** setup: Ollama on a laptop (Qwen3-8B, quantised) through an OpenAI-compatible API, so application code does not change. Development only; release evaluations still run on the production model on vLLM or Bailian (intro, section 6).
- New **5.4 Vector store options**: Milvus (production), pgvector (phase 1 MVP) and **Zvec** (Alibaba's open-source in-process vector database) for local development, tests and read-only KB snapshots; a `VectorStore` interface keeps them swappable.
- 15.9 test tooling, section 20 (#7 phase 1) and section 22 tech stack list Ollama and Zvec.
- Diagrams: R3 model inventory gets a "Local dev only" row; P1 deployment profiles gets a local-development band.

**中文**
- **本地开发**方案：笔记本上用 Ollama 跑 Qwen3-8B 量化版，接口兼容 OpenAI，应用代码不用改。只用于开发；发布前的评估仍在 vLLM 或百炼上的生产模型上跑（简介、第 6 节）。
- 新增 **5.4 向量库选项**：Milvus（生产）、pgvector（第一阶段 MVP），以及 **Zvec**（阿里开源的进程内向量数据库），用于本地开发、测试和只读知识库快照；用 `VectorStore` 接口保持可替换。
- 15.9 测试工具、第 20 节（第 7 条第一阶段）和第 22 节技术栈加入 Ollama 和 Zvec。
- 图：R3 模型清单新增"仅本地开发"一行；P1 部署形态新增本地开发一栏。

---

## v1.6 — 2026-11-25

**English**
- New **15.9 Test tooling**: open-source tools per layer (unit, LangGraph units, contract, integration, identity, agent evaluation, RAG, red team, voice, web / app / console, performance, fault injection, security, privacy, synthetic data, CI).
- Identity testing: mock-oauth2-server + PyJWT (incl. forged invalid tokens) → Keycloak in CI → the client's real IdP (e.g. an Auth0 test tenant) in staging; code depends only on standard OIDC / OAuth endpoints.
- Voice testing without commercial tools: our own AudioConnector test client, FreeSWITCH or PJSIP as a test caller, SIPp for load; Cyara only if the client already owns it.
- Section 22 tech stack lists the test tooling.

**中文**
- 新增 **15.9 测试工具**：按层列出开源工具（单元、LangGraph 单元、契约、集成、身份、agent 评估、RAG、红队、语音、Web / App / 控制台、性能、故障注入、安全、隐私、合成数据、CI）。
- 身份测试：mock-oauth2-server + PyJWT（含伪造非法 token）→ CI 用 Keycloak → 预发布用客户真实的 IdP（例如 Auth0 测试租户）；代码只依赖标准 OIDC / OAuth 接口。
- 语音测试不依赖商业工具：自研 AudioConnector 测试客户端、FreeSWITCH 或 PJSIP 作为测试来电者、SIPp 压测；Cyara 只在客户已有时使用。
- 第 22 节技术栈加入测试工具。

---

## v1.5 — 2026-11-25

**English**
- Section 15 restructured around how testing is done: 15.1 strategy (test layers + the three suites), 15.2 golden set (now with two case types and a YAML case schema), **15.3 agent simulation harness** (user simulator, voice path, mock backend with fault injection, four kinds of checks incl. end-state checks, k runs with pass^k for safety cases, simulator QA, coverage), **15.4 RAG evaluation** (≈1,000 question–evidence pairs with slices and traps; per-stage metrics and gates from ingestion to citations, abstention and latency; runs on every KB snapshot), 15.5 boundary and red team, 15.6 scoring, **15.7 replay and shadow mode** (2–4 weeks before launch), 15.8 cadence.
- New diagram E3: agent simulation harness.
- Section 5 links to the RAG evaluation; Appendix A and B links updated.

**中文**
- 第 15 节围绕"怎么测"重新组织：15.1 策略（测试分层 + 三套测试集），15.2 golden set（新增两种用例和 YAML 用例格式），**15.3 Agent 模拟测试框架**（用户模拟器、语音链路、可注入故障的模拟后端、四类检查含最终状态检查、跑 k 次且安全类要求 pass^k、模拟器质检、覆盖率），**15.4 RAG 评估**（约 1,000 组问题–证据，含切片和陷阱题；从入库到引用、拒答和延迟的分环节指标与闸门；每个知识库快照都要跑），15.5 边界与红队，15.6 评分，**15.7 回放与影子运行**（上线前 2–4 周），15.8 节奏。
- 新图 E3：Agent 模拟测试框架。
- 第 5 节链接到 RAG 评估；附录 A、B 的链接同步更新。

---

## v1.4 — 2026-11-25

**English**
- New **Appendix B, Failure modes and degradation**: principles (identity and writes fail closed, reads degrade, never fabricate, transactional outbox, reconcile unknown write outcomes); four degradation levels with kill switches; 36 failure modes (`FM-01…36`) across channels, speech, models, retrieval, identity, data, core systems, orchestration, handoff, security and site, each with detection, automatic response and customer experience; recovery objectives (RTO / RPO).
- New diagram F1: degradation levels and kill switches.
- Section 10 recovery table keeps session-level cases and links to Appendix B for component failures; the resilience suite now has one fault-injection case per failure mode.

**中文**
- 新增 **附录 B 故障模式与降级**：原则（身份和写操作 fail closed、只读降级、绝不编造、transactional outbox、写操作结果不确定时对账）；四个降级等级和关闭开关；36 个故障模式（`FM-01…36`），覆盖渠道、语音、模型、检索、身份、数据、核心系统、编排、转人工、安全和站点，每个都有发现方式、自动处理和客户体验；恢复目标（RTO / RPO）。
- 新图 F1：降级等级与关闭开关。
- 第 10 节的恢复表保留会话层面的情况，组件故障链接到附录 B；韧性测试集为每个故障模式准备一个故障注入用例。

---

## v1.3 — 2026-11-25

**English**
- New **section 13, Human handoff and agent console**: four kinds of human-in-the-loop (handoff, approval, agent assist, review); handoff triggers; the handoff packet (facts from system records, only the 3-line summary from the LLM); voice and chat routing via Genesys with `handoff_id` only; verification carries over within the same interaction, the customer's token never goes to the agent; agent console (staff SSO + MFA, assigned interactions only, 8 panels, audited views, wrap-up with feedback on the AI); supervisor can monitor and take over live AI chats; agent assist as phase 2; no hand-back to the AI; metrics.
- New diagrams: A5 agent console layout, C8 handoff sequence.
- Roles: `cs_agent` limited to assigned interactions; new `supervisor` and `qa` rows.
- New boundaries: BND-ACT-08 (assist never sends), BND-DAT-08 (assigned interactions only), BND-TRS-08 (packet facts from system records).
- Sections 13–22 renumbered (14 Guardrails … 22 Tech stack).

**中文**
- 新增 **第 13 节 转人工与坐席控制台**：四种人工介入（转人工、审批、坐席辅助、复核）；转人工的触发条件；交接包（事实来自系统记录，LLM 只写三行摘要）；语音和聊天经 Genesys 路由，只传 `handoff_id`；同一次交互内核验结果沿用，客户 token 永不交给坐席；坐席控制台（员工 SSO + MFA、只看分配的交互、8 个区域、查看留审计、收尾时给 AI 反馈）；主管可监看并接手 AI 聊天；坐席辅助放第二期；不转回 AI；指标。
- 新图：A5 坐席控制台布局、C8 转人工时序图。
- 角色：`cs_agent` 限定为分配的交互；新增 `supervisor` 和 `qa`。
- 新边界：BND-ACT-08（辅助模式不代发）、BND-DAT-08（只看分配的交互）、BND-TRS-08（交接包事实来自系统记录）。
- 第 13–22 节重新编号（14 护栏 …… 22 技术栈）。

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
