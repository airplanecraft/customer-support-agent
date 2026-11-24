# Customer Support Agent — Voice + Chat Reference Architecture

**A vertical-agnostic reference architecture for an AI customer-support agent**, serving customers over **voice (Genesys contact centre)** and **online chat (app, web, WhatsApp)** from one shared core: **LangGraph** agents, **hybrid RAG**, **guardrails**, **evaluation** and **LLMOps**, on **Alibaba Qwen / Tongyi models**. Two deployment profiles:
- **cloud:** Alibaba Cloud Model Studio (Bailian), Hong Kong region;
- **on-prem:** open-source models self-hosted on vLLM.

**Generic core + domain packs.** The core (channels, orchestration, RAG, model gateway, identity, guardrails, evaluation, LLMOps) is industry-neutral. Each industry adds a *domain pack*: intents, tools, knowledge sources, compliance rules and approval flows.

It is designed for **regulated industries** (financial services, healthcare, telecom, utilities). Examples use generic **accounts, plans, service cases and versioned product terms**, with voice identity verification and human approval for account changes.

> This is a design reference describing how I would design and deliver such a system. It contains no real customer data and no client-specific information.

---

## Contents

1. [Context and requirements](#1-context-and-requirements)
2. [Architecture overview](#2-architecture-overview)
3. [Deployment, network zones and transport security](#3-deployment-network-zones-and-transport-security)
4. [Agent design](#4-agent-design)
5. [Knowledge base and hybrid RAG](#5-knowledge-base-and-hybrid-rag)
6. [Models](#6-models)
7. [Channels: voice vs chat](#7-channels-voice-vs-chat)
8. [Identity, authentication and authorization](#8-identity-authentication-and-authorization)
9. [Business flows](#9-business-flows)
10. [Sessions, tasks and recovery](#10-sessions-tasks-and-recovery)
11. [State, memory and caching](#11-state-memory-and-caching)
12. [Events and cross-channel sync](#12-events-and-cross-channel-sync)
13. [Guardrails](#13-guardrails)
14. [Evaluation and testing](#14-evaluation-and-testing)
15. [LLMOps: Git, pipeline and Langfuse](#15-llmops-git-pipeline-and-langfuse)
16. [Observability, audit and per-call records](#16-observability-audit-and-per-call-records)
17. [Security checklist](#17-security-checklist)
18. [Deployment profiles: cloud vs on-prem](#18-deployment-profiles-cloud-vs-on-prem)
19. [Known trade-offs and open questions](#19-known-trade-offs-and-open-questions)
20. [Repository layout and regenerating the diagrams](#20-repository-layout-and-regenerating-the-diagrams)
21. [Tech stack](#21-tech-stack)

---

## 1. Context and requirements

**Scenario.** An enterprise adds two AI channels next to its existing Genesys contact centre. The core stays the same across industries; only the domain pack changes.

**Core vs domain pack**

| Generic core (reused as is) | Domain pack (per industry) |
|---|---|
| Channel adapters (Genesys voice, chat), session and task lifecycle | Intents, e.g. terms questions, account lookup, service cases, account changes |
| Router + bounded workers, guardrails, RBAC, token exchange | Tools: MCP servers for the industry's core systems (accounts, cases, change drafts) |
| Hybrid RAG pipeline, model gateway, evaluation, LLMOps | Knowledge: versioned product terms, knowledge articles, fee tables, regulatory notices |
| Voice identity verification framework | Rules: no binding commitments, eligibility disclaimers, cancellation stays human |

The two AI channels:
- **Voice:** customers call in.
- **Online chat:** app, web and WhatsApp.

Both channels handle four kinds of request:

| Request type | Example | Handling |
|---|---|---|
| Product and terms questions | "Is there an early-termination fee on my plan?" | RAG (read only) |
| Personal account lookup | "When does my plan renew?" "Was this month's payment received?" | Agent calling tools (read only) |
| Service cases | "What's the status of my case?" "Which documents do I need?" | Agent calling tools; submissions need human approval |
| Servicing | Change address or registered details; cancellation | AI prepares a draft or request; **a human approves or completes it** |

**Constraints and non-functional requirements**

| Area | Requirement |
|---|---|
| Data residency | Customer data, recordings and transcripts stay on-prem or in a Hong Kong private cloud (PDPO, sector regulators expectations). No public LLM APIs in production. |
| Languages | Cantonese, Mandarin and English, often code-switched within one sentence |
| Volume | About 20k chats per day (400 concurrent at peak) and 6k calls per day (120 concurrent at peak); about 20k documents in the knowledge base |
| Latency | Voice: roughly 1 second from end of speech to first audio. Chat: first token within 1–2 seconds |
| Accuracy | Zero binding commitments; per-sentence citations; the version-correct clause must be used |
| Audit | Every answer must be traceable to the prompt, model, retrieval config and clause version used. Records are retained per regulatory policy. |

![A1 System context](docs/img/A1-system-context.png)
*A1 · System context — source: [`A1-system-context.drawio`](docs/diagrams/A1-system-context.drawio)*

---

## 2. Architecture overview

**One brain, two channels.**
- **Shared core:** the LangGraph orchestrator, the RAG service, the MCP tool servers, the model gateway and the observability stack serve both channels.
- **Channel adapters:** handle what differs: identity, answer style, latency, barge-in and call limits.

![A2 Components](docs/img/A2-components.png)
*A2 · Components — source: [`A2-components.drawio`](docs/diagrams/A2-components.drawio)*

| Component | Responsibility |
|---|---|
| **External API gateway** (the client's existing one, e.g. Apigee or Kong) | TLS, WAF, JWT validation against the IdP's JWKS, coarse scopes, rate limits, routing |
| **Web BFF** | OIDC client for the web; keeps tokens server-side; the browser only holds an HttpOnly cookie |
| **Voice gateway** | **Genesys AudioConnector** endpoint (bidirectional audio over WebSocket, signed handshake); VAD, barge-in, streaming STT and TTS. DTMF is collected by Genesys secure flows, not here. |
| **Verification service** | Voice identity check (SMS OTP and date of birth); obtains the customer's access token from the IdP |
| **Token store** | `auth_ref → token`, encrypted in Redis with a TTL; tokens never enter agent state |
| **Orchestrator** | LangGraph router and workers, Postgres checkpoints, token exchange for downstream calls |
| **RAG service** | Query rewriting, hybrid search, reranking, citation verification |
| **MCP servers** | Account, case, change (drafts only) and identity tools; each has its own client certificate |
| **Model gateway** | Model routing, quotas, cost attribution per channel and feature |
| **Approval service** | Staff approvals with separation of duties; resumes paused graphs |
| **Notification service** | Post-call message to the chat thread, as a push notification, or by SMS |
| **Data** | Postgres (checkpoints, tasks, interactions, audit index), Redis (sessions, OTP, rate limits, caches), Milvus (dense + BM25), object storage (clauses, uploads, recordings), Kafka (events) |
| **Guardrail library** | Input and output rules shared by the runtime guardrails and the rule-eval service ([section 13](#13-guardrails)) |
| **Observability** | ELK (service logs), Prometheus + Grafana (metrics, alerts); LLM traces go to Langfuse |
| **LLMOps plane** | **Git** (source of truth for prompts, model manifest, evaluators, judge prompts, datasets, release manifest) → **CI/CD pipeline** (the only writer to Langfuse) → **Langfuse** (prompt versions and config, datasets and experiments, LLM-as-judge, traces, annotation queues) · **rule-eval service** · **model registry** · **test harness** ([section 15](#15-llmops-git-pipeline-and-langfuse)) |

---

## 3. Deployment, network zones and transport security

![A3 Network and deployment](docs/img/A3-network-deployment.png)
*A3 · Network zones and TLS vs mTLS — source: [`A3-network-deployment.drawio`](docs/diagrams/A3-network-deployment.drawio)*

**Zones.** Internet → DMZ (WAF and external gateway, voice gateway) → application zone (Kubernetes) → data zone → the client's internal network (internal API gateway, core systems, IdP). Two data centres: primary and disaster recovery.

**Kubernetes**
- **CPU node pool:** gateways, orchestrator, RAG, MCP servers, scanning, notifications.
- **GPU node pool:** vLLM (Qwen3-32B and 8B), embedding and reranking, STT and TTS.
  - The pool is tainted so only model workloads run there.
  - NVIDIA GPU Operator manages the GPUs.
  - **KEDA** autoscales on vLLM queue depth, not CPU.
  - Minimum replicas stay up because loading a model takes minutes.
- **Namespaces** per concern; **NetworkPolicies** control who can reach whom.
- **Secrets** come from **Vault**.
- **GitOps** with Helm and Argo CD.
- **Stateful stores:** Postgres and Kafka typically stay on the client's DBA-managed platform. Redis and Milvus can run in-cluster because they can be rebuilt.

**North-south vs east-west traffic**
- Clients come in through the **external API gateway**.
- Our own services (orchestrator ↔ RAG ↔ MCP) talk **directly over the service mesh** (Istio or Linkerd) with automatic mTLS.
- **Only calls to the client's core systems** cross a team boundary. Those go through the **client's internal API gateway**.
- Databases are reached over their own protocols, locked down by NetworkPolicy and short-lived Vault credentials.

**TLS vs mTLS vs access tokens**

| Mechanism | What it proves | Where it is used |
|---|---|---|
| TLS (one-way) | The server's identity | Customer app or browser → external gateway; Genesys → voice gateway (AudioConnector signed handshake, API key, IP allow-list) |
| mTLS (mutual) | **Which service** is calling (service-level identity) | Pod to pod via the service mesh (short-lived SPIFFE certs, auto-rotated). MCP servers → internal API gateway if the client requires it (certs from the client's PKI via cert-manager or Vault). |
| Access token | **Which user**, which permissions, what assurance level, which agent (user-level identity) | Every call made on behalf of a user, on top of TLS or mTLS |

Both are needed: with mTLS alone, the downstream system would have to trust whatever customer ID our service sends (the confused-deputy problem). Tokens can also be **bound to the client certificate** (RFC 8705), so a stolen token is useless without the private key.

---

## 4. Agent design

![A4 Agent graph](docs/img/A4-agent-graph.png)
*A4 · Agent graph — source: [`A4-agent-graph.drawio`](docs/diagrams/A4-agent-graph.drawio)*

### 4.1 Pattern: routing plus bounded workers

In Anthropic's terms this is a **workflow, not an autonomous agent**: a routing pattern plus a gated chain, implemented as a deterministic state machine. **Only the leaf nodes are agents.**

| Decision | Who decides |
|---|---|
| Nodes and edges of the graph | Programmer (built from config at startup; the shape never changes at runtime) |
| Which intents the customer expressed | LLM (Qwen3-8B), constrained to a fixed enum with `response_format` |
| Whether role and assurance level are sufficient | Code |
| Which tools a worker calls, and in what order | LLM, limited to that worker's allowlist and `recursion_limit = 8` |
| Whether a tool call may execute | Code inside the tool or MCP server (token, scope, acr, ownership) |
| Time limits, question limits, handoff | Code (`guard`) |
| Whether a change takes effect | A human approver |

**Why not a free supervisor or a planner-executor on the real-time path?** Regulated service intents are few and procedural. Dynamic orchestration would make paths unpredictable and hard to test or audit. It could skip identity checks, and the extra LLM calls would break the 1-second voice budget.

**Where planning is allowed:**
- inside a single worker, for genuinely multi-step questions (for example comparing two plans), with the same tool allowlist and step limit;
- in back-office flows that have human review.

**Routing vs orchestrator-workers.**
- Routing picks from **predefined** categories with fixed handlers.
- An orchestrator **invents** subtasks, writes instructions for each worker and synthesises the results.
- Ours is **multi-label routing**: one utterance can carry several intents, each on a predefined path.

### 4.2 Workers

| Worker | Model | Tools | Skills | Minimum assurance |
|---|---|---|---|---|
| `clause_agent` | Qwen3-32B | `search_clauses`, `get_fee_table` | `clause_explain` | anonymous |
| `account_agent` | Qwen3-8B | `get_accounts`, `get_account_detail`, `get_billing_history` | — | verified |
| `case_agent` | Qwen3-32B | `get_case_status`, `list_required_documents` | `case_guide`, `document_checklist` | verified |
| `service_agent` | Qwen3-32B | `create_change_draft` (**draft only**) | `profile_change`, `address_change`, `cancellation` | verified + step-up |

### 4.3 Configuration lives in code, not in prompts

- `config/agents.yaml` sets each agent's prompt version, model, tools, skills and minimum assurance level.
- `config/policy.yaml` sets what each role may do.
- Both are **versioned in Git, validated at startup, baked into an immutable image per release**, and changed only through reviewed pull requests (security and compliance approve permission changes).
- **The prompt explains *when* to use a tool; the binding decides *whether* the model can see it.** Effective tools = agent allowlist ∩ role permissions.

### 4.4 Skills (loaded on demand)

Skills are packaged instructions: a folder with a `SKILL.md` plus optional reference files. They are many-to-many with agents.

Progressive loading:
1. Only each skill's name and description sit in the system prompt.
2. The body arrives through a `load_skill` tool call when the model decides it needs it.
3. Reference files are read later through `read_skill_file`, with path-traversal checks.

**Compliance-critical flows are loaded deterministically by the router**, not left to the model. Rules that must always apply, such as disclaimers, stay in the system prompt.

### 4.5 What one LLM call contains

From the API's point of view there are only three slots:
- **messages:** system, user, assistant and tool;
- **tools:** tool definitions;
- **parameters:** model, temperature, `max_tokens`, `response_format`.

Everything else is a content source the application places into those slots:

| Source | Slot |
|---|---|
| Role and rules, few-shot examples | system |
| Runtime context (date, channel, assurance level, the customer's accounts and applicable clause versions) | dynamic part of the system message, rendered from LangGraph state |
| Long-term memory, conversation summary | system (summary) plus recent turns as user and assistant messages |
| Pipeline RAG results | system or user |
| Tool-based RAG and tool results | assistant `tool_call` plus `tool` messages |
| Skill catalogue / skill body | system / `tool` message |
| Structured output | `response_format` (enforced by constrained decoding in vLLM) |

Static content goes first and dynamic content last, so **vLLM prefix caching** cuts time-to-first-token, which matters most for voice.

---

## 5. Knowledge base and hybrid RAG

### 5.1 Why RAG

- The model doesn't know this client's product terms, and they change between versions.
- RAG retrieves the **currently applicable, version-correct** clause at answer time.
- It lets every sentence carry a **citation**, applies **role and ownership filters**, and makes every answer **auditable**.
- Fine-tuning is used only for behaviour (style, refusals, formats), never for clause knowledge.

### 5.2 Ingestion

![R1 RAG ingestion](docs/img/R1-rag-ingestion.png)
*R1 · Ingestion — source: [`R1-rag-ingestion.drawio`](docs/diagrams/R1-rag-ingestion.drawio)*

- **Parsing:** layout-aware, including cross-page tables; scans go through OCR.
- **Chunking:** by clause (200–600 tokens). Definitions stay whole. Tables are chunked by row with the header repeated, plus a table summary.
- **Metadata:** `product_code`, `version`, `effective_from`, `effective_to`, `language`, `visibility`, `clause_no`.
- **Versioning:** content hashes drive incremental upserts. Old versions are **kept but marked expired**, because contracts signed earlier still use them.
- **Release:** a new snapshot passes a retrieval eval gate, then the Milvus alias `kb_live` is switched to it.
- **Changing the embedding model** means re-embedding into a **new collection**, evaluating, then swapping the alias. Vectors from different models can't be mixed.

### 5.3 Hybrid retrieval and grounded generation

![R2 Hybrid retrieval](docs/img/R2-hybrid-retrieval.png)
*R2 · Query path — source: [`R2-hybrid-retrieval.drawio`](docs/diagrams/R2-hybrid-retrieval.drawio)*

| Step | Detail |
|---|---|
| Rewrite | Qwen3-8B turns colloquial Cantonese into search terms and splits multi-part questions |
| Exact match | Explicit clause numbers or product codes hit a metadata filter directly |
| Dense search | Qwen3-Embedding (query with instruction), ANN top-30 |
| BM25 | Milvus built-in full-text search with the jieba analyzer, top-30. It catches clause numbers, product codes and technical terms that dense search misses. |
| Filters | Built **server-side from the token**, never from the model: product, version by contract start date, visibility by role, language, owner |
| Fusion | RRF (k = 60) → 30 candidates |
| Rerank | Qwen3-Reranker: top-5 for chat, top-3 for voice. A low top score triggers a rewrite-and-retry, then handoff. |
| Generate | Qwen3-32B, context only, per-sentence citations; voice answers are at most 3 sentences |
| Verify | Citation check (Qwen3-8B or NLI) and compliance check (no binding commitments, disclaimer present). Failure → drop the sentence or hand off. |

A **related-history lookup** runs in parallel with retrieval: same customer, intent and entity within the last 30 days. This detects repeat contacts; a third unresolved call about the same case escalates instead of repeating the same answer.

---

## 6. Models

![R3 Model inventory](docs/img/R3-model-inventory.png)
*R3 · Model inventory — source: [`R3-model-inventory.drawio`](docs/diagrams/R3-model-inventory.drawio)*

**All Qwen / Alibaba Tongyi.** One vendor and one licence family (Apache 2.0 for Qwen3), strong in Cantonese, Mandarin and English, one fine-tuning toolchain, and consistent with clients already on Alibaba Cloud.

| Step | Model |
|---|---|
| VAD | Silero VAD (CPU, in the voice gateway) |
| STT | **Cloud:** Bailian Paraformer realtime · **On-prem:** FunASR / SenseVoice (open source) |
| TTS | **Cloud:** Bailian CosyVoice · **On-prem:** CosyVoice 2 (open source) |
| Intent, rewrite, sentiment, verification, summaries, online judge | Qwen3-8B |
| Clause answers, multi-step agents, offline judge | Qwen3-32B (AWQ INT4 or FP8) |
| Low-latency voice (optional) | Qwen3-30B-A3B (MoE, ~3B active parameters) |
| Embedding / rerank | Qwen3-Embedding / Qwen3-Reranker (0.6B to start; 4B if evals justify it) |
| Documents | PaddleOCR + Qwen2.5-VL-7B |
| PII redaction | Rules + NER (e.g. Presidio with HKID recognisers) — no LLM |

**How the split is decided.** Run the golden set across 8B, 14B, 32B and 30B-A3B, then choose on quality, latency and GPU cost.

**Training.**
- No pretraining.
- Start with base models plus RAG and guardrails.
- Add **LoRA** fine-tunes only for behaviours the evals show are weak (Cantonese style, refusals, tool-call formatting). They are trained **on-prem** on anonymised and synthetic data.
- Optionally distil 32B into 8B for specific steps.
- Black-box third-party "industry-specific LLMs" are avoided: unknown training data, lock-in, and data-residency risk.

**Deployment.** All LLM and speech calls go through our own model gateway and voice gateway, so the backend can be swapped without changing application code:
- **cloud profile:** Bailian (Qwen, Paraformer, CosyVoice) or vLLM in the client's Alibaba Cloud Hong Kong VPC;
- **on-prem profile:** the same model families as open weights on vLLM, plus FunASR and CosyVoice.

See [section 18](#18-deployment-profiles-cloud-vs-on-prem).

---

## 7. Channels: voice vs chat

| Aspect | Chat | Voice |
|---|---|---|
| Identity | SSO session (OIDC) | Just-in-time **SMS OTP to the registered mobile + date of birth via DTMF**, collected in a **Genesys secure flow** and checked through a Data Action |
| Answer style | Full answer, lists, clause links, citations | At most 3 sentences, spoken style; citations logged, not read aloud; "I'll send the details to your app" |
| Latency | First token in 1–2 s | About 1 s from end of speech: streaming STT → LLM → sentence-chunked TTS |
| Interruptions | — | **Barge-in:** stop playback, clear the AudioConnector playback buffer, cancel generation |
| Multiple questions | Answered together with numbered points | Split into intents, answered one at a time, at most 5 per call |
| Limits | Reminder at 15 min idle, close at 60 min; max 1,000 characters per message enforced server-side (no silent truncation) | At most 10 min of AI handling; silence prompt after 8 s, hang up after 16 s; at most 2 reprompts, then a DTMF menu or a human |
| Recognition errors | — | Read back key entities; prefer DTMF for digits; hotwords; character error rate monitored |
| Sensitive data | Masked inputs | DTMF only; never in transcripts, recordings or the LLM |
| Handoff | Chat thread to a human agent | Back to a **Genesys ACD queue** with the structured summary as participant data → screen pop |

**Voice latency budget (approximate):** VAD 200–300 ms · final STT 100–200 ms · routing and retrieval 150–300 ms · LLM first token 200–400 ms · first TTS audio 100–200 ms. Mitigations:
- stream every stage;
- use 8B or MoE for simple turns;
- prefix caching;
- start retrieval on partial transcripts;
- pre-synthesised fillers ("Let me check that for you");
- voice requests get priority over chat in the model gateway.

---

## 8. Identity, authentication and authorization

### 8.1 Login per channel

| Channel | How the customer is authenticated | Where tokens live |
|---|---|---|
| Web | OIDC authorization code + PKCE via the **BFF** | Server-side session store; the browser only holds an HttpOnly, Secure, SameSite cookie |
| App | OIDC authorization code + PKCE (AppAuth) | iOS Keychain / Android Keystore; refresh-token rotation |
| Voice | SMS OTP + DOB (DTMF in a Genesys secure flow → Data Action to our verification service) → the IdP issues a short-lived access token via **token exchange** (or **CIBA** with an in-app push approval) | Token store keyed by call; deleted at hang-up; no refresh token |

![B1 Web login](docs/img/B1-web-login-bff.png)
*B1 · Web login with BFF — source: [`B1-web-login-bff.drawio`](docs/diagrams/B1-web-login-bff.drawio)*

![B2 App login](docs/img/B2-app-login.png)
*B2 · App login — source: [`B2-app-login.drawio`](docs/diagrams/B2-app-login.drawio)*

![B3 Voice verification](docs/img/B3-voice-verification.png)
*B3 · Voice verification → access token — source: [`B3-voice-verification.drawio`](docs/diagrams/B3-voice-verification.drawio)*

**Voice verification rules**
- **Flow:**
  1. When the AI needs personal data, it ends the AudioConnector session with an output variable (`next: verify`).
  2. Genesys collects the OTP and DOB in a secure flow (not recorded) and calls our verification service through a Data Action.
  3. On success, Genesys re-enters AudioConnector with the `auth_ref`.
  4. Digits never pass through our audio path, STT or the LLM.
- Caller ID only identifies the *likely* customer, because it can be spoofed. The OTP goes **only to the number on file**, so spoofing doesn't help an attacker.
- The OTP is 6 digits, valid for 5 minutes, single-use and bound to the call. Sends are rate-limited (against SMS pumping), and verification locks after 3 failures.
- Failure messages never reveal which factor was wrong.
- Changing the registered phone, the payment bank account, or completing a cancellation refund **never happens in the AI channel**.
- Date of birth is a weak secret, so residual risk is handled downstream: human approval, out-of-band notifications, cooling-off periods on sensitive changes.

### 8.2 Tokens

**Access token contents (JWT):**
- `iss`, `sub`, `aud`, `exp`, `nbf`, `iat`, `jti`;
- `scope`, `client_id` / `azp`;
- `auth_time`, `acr` (e.g. `app_biometric`, `voice_otp_dob`), `amr`;
- custom `role`, `customer_no`, `partner_code`;
- `act` after token exchange.

It is encoded, **not encrypted**, so no sensitive data goes into it.

**Validation, in order** (gateway and every service):
1. algorithm allow-list;
2. key by `kid` from the cached JWKS;
3. signature;
4. `iss`;
5. `aud` = me;
6. `exp` / `nbf` (with leeway);
7. it is an access token, not an ID token;
8. allowed client;
9. scope for this route;
10. `acr` / `auth_time` freshness for sensitive actions;
11. then business authorization (ownership).

**ID tokens** are only for the client (login and display). They are validated with `aud = client_id` and a **nonce** check, and are never sent to APIs.

### 8.3 One request end to end

![B4 Token chain](docs/img/B4-token-chain.png)
*B4 · Token exchange, TLS vs mTLS, ownership — source: [`B4-token-chain.drawio`](docs/diagrams/B4-token-chain.drawio)*

- **The front-end token is never forwarded downstream.** The orchestrator performs **OAuth 2.0 Token Exchange (RFC 8693)** per tool call and gets a token with:
  - `aud` = the target API;
  - the narrowest `scope`;
  - the same `customer_no`;
  - `act` = the calling agent.
- The MCP server and the internal gateway validate it, and the core system enforces **ownership** (row-level security: `owner = token.customer_no`).
- **Staff tokens** carry the staff ID; access to a customer's data requires an assignment to that customer's case.
- **Inside the agent:** LangGraph state and config hold only an opaque **`auth_ref`**. The token sits in an encrypted store with a TTL; tools resolve the reference, exchange the token, and **fail closed** with a re-auth if it has gone. Tokens are never placed in checkpoints, messages, logs, traces or Kafka. Token store controls: [section 11.5](#115-token-store).
- **Long pauses** (multi-day approvals) don't reuse the customer's token. The approver's own identity and a narrowly scoped service account complete the action, and state keeps only the authorization facts.

![B5 Step-up](docs/img/B5-step-up.png)
*B5 · Step-up authentication (RFC 9470) — source: [`B5-step-up.drawio`](docs/diagrams/B5-step-up.drawio)*

### 8.4 Roles and enforcement

| Role | Can | Cannot |
|---|---|---|
| anonymous | General product and terms questions | Any personal data |
| customer | Own accounts and cases; draft own changes | Other customers' data; make changes effective |
| authorized_rep | Within the written authorization | Beyond its scope |
| partner | Own book of business, masked fields | Other partners' customers; full PII |
| cs_agent | The case currently assigned; internal guidelines; drafting | Approving own drafts |
| approver | Approve or reject drafts | Drafting (separation of duties) |
| compliance | Audit logs, archives | Changing business data |
| admin | Deploy, monitor, redacted logs | Customer PII; changing permissions outside a PR |

**Effective permission = role permissions ∩ the agent's tool allowlist ∩ assurance level and channel ∩ data ownership.** It is enforced at seven points:
1. gateway;
2. graph routing;
3. tool binding;
4. tool execution;
5. data layer (row-level security plus RAG visibility filters);
6. output masking;
7. audit.

**Privilege-escalation tests run in the golden set with a zero-tolerance gate.**

---

## 9. Business flows

![C1 Voice account lookup](docs/img/C1-voice-account-lookup.png)
*C1 · Voice account lookup — source: [`C1-voice-account-lookup.drawio`](docs/diagrams/C1-voice-account-lookup.drawio)*

![C2 Chat account lookup](docs/img/C2-chat-account-lookup.png)
*C2 · Chat account lookup — source: [`C2-chat-account-lookup.drawio`](docs/diagrams/C2-chat-account-lookup.drawio)*

**Cancellation (C3).**
- The AI may quote the cancellation terms (read only) and explain the consequences with citations: benefits lost, fees.
- If the customer still wants to proceed, the AI creates a **cancellation request task** and hands over: a transfer or callback on voice, a thread handover in chat.
- Retention, confirmation and refund are handled by a human under the company's process.

![C3 Cancellation](docs/img/C3-cancellation.png)
*C3 · Cancellation — source: [`C3-cancellation.drawio`](docs/diagrams/C3-cancellation.drawio)*

**Account change (C4).**
1. The AI creates a **draft** with an idempotency key, and the graph pauses with `interrupt()`.
2. The approver signs in with **staff SSO**. The approval service checks the role, that the **approver is not the drafter**, and that the draft is still valid, then resumes the graph with `Command(resume=…)`.
3. The change is applied through the internal API gateway with a token **exchanged on behalf of the approver**, so the core system logs the real approver and enforces its own limits.

**Whose token is used where.** Approval doesn't involve the customer's token at all.

| | Request (customer) | Approval and execution (staff) |
|---|---|---|
| Actor | The verified customer | The approver |
| Token | The customer's own token, after verification and step-up | The approver's own staff SSO token |
| Authorization | Ownership: the customer can only touch their own data (`sub`) | The approver's **role** plus **assignment** to this case |
| Which customer's data | `sub` in the customer's token | `customer_id` stored on the **task**, not a customer token |

- The task stores `customer_id`, `requested_by`, the request, and the **step-up evidence** (the customer's consent, captured at request time). It never stores a token.
- When the session ends, the customer's token is deleted. Nothing later needs it.
- **Maker-checker:** the approver can't be the requester or the drafter. **The agent can never approve**; only a human staff token is accepted at that step.
- **Audit:** `requested_by = customer`, `approved_by = approver`, `executed_by = approver` (`act` = the executor service).
- **Exception:** if policy requires the customer to **reconfirm after approval** (for example, a high-value change), the customer re-authenticates at that point, such as with a CIBA push. That is a separate customer consent step, not part of the approver's authorization.

![C4 Approval](docs/img/C4-approval-account-change.png)
*C4 · Account change with human approval — source: [`C4-approval-account-change.drawio`](docs/diagrams/C4-approval-account-change.drawio)*

---

## 10. Sessions, tasks and recovery

**Sessions and tasks are separate.**
- A **session** is one interaction: a call, or a chat that ends after 60 minutes idle.
- A **task** is one piece of business, such as a account change. It can span sessions and channels.

| ID | Scope |
|---|---|
| `thread_id` | One session (voice: Genesys `conversationId`; chat: a new ID per session). LangGraph checkpoint key. |
| `customer_id` | Permanent; long-term memory and tasks hang off it |
| `task_id` | Case lifecycle: new → in progress → waiting for customer or approval → completed / cancelled / expired / handed off |

**Session end**
- **Voice:** hang-up, transfer, or limits reached.
- **Chat:** explicit close, or 60 minutes idle (with a reminder at 15).
- **Assurance expires sooner**, after 15 minutes idle, which triggers step-up before personal data is shown again.
- **A returning customer** starts a new session and must re-verify, but open tasks are offered for resumption, across channels too.

**After verification**, a compact context is loaded: open tasks, recent session summaries, preferences and flags ([section 11](#11-state-memory-and-caching)). Older history stays behind an on-demand tool. **Before verification**, prefetched data is used only for routing, risk and language; it is never spoken.

**Recovery**

| Failure | Recovery |
|---|---|
| Orchestrator pod restarts | Resume from the Postgres checkpoint: `invoke(None, config)` with the same `thread_id` |
| Voice gateway restarts while the call is still up | Genesys re-opens AudioConnector for the same `conversationId` (or routes to the ACD queue); resume from the checkpoint, or hand off |
| Customer drops mid-task | Task marked interrupted, with progress saved; SMS sent with a resume path; re-verification on return |
| Page refresh | Same session ID → reload from the checkpoint; never show half a generation |
| Approval pause | A designed `interrupt()` that can last days; resumed by the approver |
| Model or tool timeout | Retry, then degrade (smaller model, "can't retrieve right now", handoff). **Never fabricate.** |

Every side-effecting tool takes an **idempotency key** (`task_id` + step), so a replayed step never creates duplicates.

---

## 11. State, memory and caching

**Built on LangGraph and LangChain primitives; no LangMem** (see 11.3).

![M1 State and memory](docs/img/M1-state-memory.png)
*M1 · State and memory layers — source: [`M1-state-memory.drawio`](docs/diagrams/M1-state-memory.drawio)*

### 11.1 Agent state (short-term, per session)

| Field | Purpose |
|---|---|
| `messages`, `summary` | Last N turns verbatim; older turns folded into a summary |
| `channel`, `language` | Voice or chat rendering; reply language |
| `customer_id` | Set only after verification, from the token's `sub` |
| `assurance` | Level (anonymous, verified, step-up), `verified_at`, `expires_at` |
| `auth_ref` | Opaque pointer to the token store; never the token itself |
| `intents`, `current_worker` | Router output (fixed enum) and the active worker |
| `task_ids`, `pending_draft` | Links to the task table; the draft awaiting approval |
| guard counters | Turns, tool calls, retries, used for limits and handoff |
| `release` | Release label pinned for the session, so prompts and models don't change mid-conversation |
| retrieved chunk IDs | IDs and versions for citations and audit, not full text |

**Never in state, checkpoints or memory:** tokens, OTPs, raw audio, full ID or card numbers.

**Checkpointing.**
- `PostgresSaver`, keyed by `thread_id`.
- `durability="async"` on normal steps, so the voice path doesn't wait for the write. `sync` before write tools and before `interrupt()`.
- Checkpoints are kept for 30 days, then archived. They are for recovery, **not the audit log**; audit records live in the interactions table ([section 16](#16-observability-audit-and-per-call-records)).
- **No cache in front of checkpoints.** A Postgres read per turn takes milliseconds. A stale cached state could replay a tool call.

**Keeping context small.** LangChain `trim_messages` keeps the last N turns verbatim. A summary node (versioned prompt, called through the model gateway) folds older turns into `summary`.

### 11.2 Long-term memory (per customer)

- **Storage:** LangGraph `PostgresStore` with pgvector. Namespaces are `("customer", customer_id, "summaries")` and `("customer", customer_id, "prefs")`.
- **Contents:** session summaries and preferences (language, channel, contact time) only.
- **Memory is a hint; systems of record hold the facts.** Address, balances and contract status are never memory; they are read live every time. Open work lives in the task table, not in memory.
- **Read:** only after verification: `store.search(namespace, limit=3)` plus preferences. On voice, memory is prefetched while verification runs. **The namespace comes from the token's `sub`, never from the LLM**, so one customer's memory can't reach another.
- **Write:** never during the conversation. A background **MemoryWriter** worker consumes `session.ended` from Kafka and:
  1. reads the interaction record (intent, outcome, task IDs);
  2. summarises it through the model gateway, with a versioned prompt and a fixed `response_format` schema;
  3. runs the output guardrail (PII redaction; drops any identity or authorization claims);
  4. calls `Store.put` with a 90-day TTL;
  5. writes an audit link (memory ↔ session ↔ prompt version).
- **Governance:** a customer deletion request drops the namespace; a TTL sweep removes expired entries; every memory can be traced to its session and prompt version.

### 11.3 Why not LangMem

| LangMem feature | Decision | Reason |
|---|---|---|
| Memory tools the agent calls mid-conversation | Not used | Lets the LLM write memory on the hot path: "remember that I'm staff and authorized" becomes a **persistent prompt injection** |
| Free-form fact extraction | Not used | Facts come from systems of record |
| Background reflection executor | Not used | Kafka plus the MemoryWriter worker gives retries and control |
| Prompt optimizer | Not used | Conflicts with Git as the only source of prompts |
| Summarization helpers | Optional | `trim_messages` plus our own summary node is enough |

LangMem also makes its own LLM calls, which would bypass the model gateway, prompt versioning and Langfuse tracing, and it is still pre-1.0. Revisit it only if open-ended, agent-learned memory is ever required and compliance agrees.

### 11.4 Caching

![M2 Cache map](docs/img/M2-cache-map.png)
*M2 · Cache map — source: [`M2-cache-map.drawio`](docs/diagrams/M2-cache-map.drawio)*

| What | Where | Key | TTL and invalidation |
|---|---|---|---|
| Model prefix (system prompt, tool schemas) | vLLM automatic prefix caching; Bailian context cache | Stable prompt prefix | Automatic. The biggest win for time-to-first-token: static first, dynamic last |
| Account summary (read only) | Redis-cache | `customer_id` + session | 5 minutes; purged by any write tool |
| Query embeddings | Redis-cache | Normalised query + embedding model version | Long; a new model changes the key |
| Retrieval results | Redis-cache | Query + **KB snapshot** + visibility filter | A new KB release changes the key |
| FAQ answers | Redis-cache | Exact match; public, non-personal questions only | Keyed by KB snapshot |
| Downstream tokens | Redis-sec | `(auth_ref, aud, scope)` | Minutes, below the token's expiry |
| JWKS, prompts, rate limits, OTP, BFF sessions | Gateway, orchestrator, Redis | — | See sections 8 and 15 |

**Invalidation is by version in the key** (KB snapshot, embedding model, release label), so a release needs no manual purge. The only explicit purge is write tools → account summary.

**Never cached:** write-tool results; entitlements and permissions (or 60 seconds at most); semantic caching of personalised answers (reusing A's answer for B is an incident); checkpoints.

### 11.5 Token store

An encrypted Redis store holding `auth_ref → access token` is a common, sound pattern: it is fast, has native TTLs, is shared by stateless pods, and losing it only forces re-authentication. The risk is that a compromised Redis exposes every live token, so:

| Control | Detail |
|---|---|
| Application-level encryption | AES-GCM before the write; data keys from KMS or Vault transit. `auth_ref` and `customer_id` are bound as associated data, so ciphertext moved to another key won't decrypt |
| Unguessable keys | 128-bit random `auth_ref`, never `customer_id` |
| TTL | The earlier of token expiry and session end, minus about 30 seconds. Deleted at hang-up, logout or step-down |
| No refresh tokens | The agent side holds access tokens only. Web refresh tokens stay in the BFF; app refresh tokens in the device keychain; voice has none |
| Sender-constrained tokens | Where supported, mTLS-bound (RFC 8705) or DPoP, so a stolen token is useless without the key |
| Dedicated instance (**Redis-sec**) | Separate from Redis-cache; TLS; per-service ACLs (only the auth service writes or deletes; the orchestrator reads `tok:*`) |
| Hardening | No RDB/AOF and no backups; `KEYS`, `MONITOR`, `CONFIG`, `FLUSHALL` disabled; network policy |
| Eviction | `volatile-ttl` or `noeviction`; a missing token fails closed with re-authentication |
| Revocation | Short TTLs bound the window; the gateway introspects for high-risk write calls |
| Logging | Token values never reach logs, traces or Kafka; only `auth_ref` |

**Long pauses don't keep tokens alive.** Approvals use the approver's own token ([section 9](#9-business-flows), C4); a task never stores a token.

---

## 12. Events and cross-channel sync

![D1 Events](docs/img/D1-events-cross-channel.png)
*D1 · Events and cross-channel sync — source: [`D1-events-cross-channel.drawio`](docs/diagrams/D1-events-cross-channel.drawio)*

- **Clients never touch Kafka.** The synchronous path (HTTPS / WebSocket / SSE with access tokens) serves the user. Kafka carries asynchronous side effects: notifications, CRM sync, audit, reporting.
- **Events carry IDs, never tokens or sensitive content.** Kafka uses mTLS or SASL, topic ACLs and encryption.
- **The backend is the single source of truth** for tasks, documents and status. The cross-channel UX is deliberately minimal: **one post-call message**, delivered to the in-app chat thread if chat is enabled, otherwise as a push notification, or by SMS if there is no app. Lock-screen text stays generic.
- **Not shown in the app:** live transcripts or recording links. Recordings are provided through the PDPO **data access request** process.
- **Concurrency:** an open task for the same intent and account is reused; optimistic locking prevents lost updates.

---

## 13. Guardrails

![G1 Guardrail layers](docs/img/G1-guardrail-layers.png)
*G1 · Guardrail layers — source: [`G1-guardrail-layers.drawio`](docs/diagrams/G1-guardrail-layers.drawio)*

Defence in depth: any layer can refuse, require step-up, or hand off to a human, with a generic message.

| Layer | Checks |
|---|---|
| 1 · Input | Length (≤ 1,000 characters), rate limits per user and client, PII redaction before the LLM and the logs, injection classifier, uploads scanned (AV + CDR) with only the clean copy used, external text treated as data rather than instructions |
| 2 · Identity and routing | Token `aud`, `scope` and `acr`; role → reachable agents; assurance level per intent (verify or step-up); tools = agent allowlist ∩ role; `recursion_limit = 8` |
| 3 · Retrieval | Filters built from the token (visibility by role, clause version by contract start date, `owner_id`), never from the model |
| 4 · Tools | Token exchange with a narrow `aud` and `scope`; ownership check plus row-level security; write tools that only create drafts; idempotency keys; human approval via `interrupt()`; never change phone, bank account or refund |
| 5 · Output | Citation check (exists, was retrieved, correct version); fast faithfulness check (8B); no binding commitment; disclaimer when terms are discussed; PII leak check; language match; voice answers ≤ 3 sentences |

**One rule set, three uses.** Each rule is defined once in Git (`evaluators/*.yaml`) and used in three places:
- **runtime guardrails:** blocking; only fast deterministic rules and fast 8B checks;
- **offline release gates:** CI runs the same rules through the rule-eval service, plus LLM judges in Langfuse experiments;
- **online monitoring:** rules on 100% of traces, judges on a sample, with alerts and annotation queues.

**Prefer deterministic rules; use LLM judges only where rules can't decide.** Track false positives as well as misses: over-blocking pushes customers to humans and kills containment.

---

## 14. Evaluation and testing

![E1 Testing and evaluation](docs/img/E1-testing-evaluation.png)
*E1 · Testing and evaluation system — source: [`E1-testing-evaluation.drawio`](docs/diagrams/E1-testing-evaluation.drawio)*

### 13.1 Three suites, kept separate

A handful of serious safety failures must not be averaged away by thousands of good answers.

| Suite | Question it answers | Gate |
|---|---|---|
| **Golden set** (capability) | Does the system handle real customer requests correctly? | Thresholds; no regression against the current release |
| **Boundary and guardrail suite** (safety) | Can it be pushed into doing what it must never do? | **Zero tolerance** for binding commitments, privilege escalation and PII leaks |
| **Resilience suite** | Does it degrade safely under timeouts, failures and load? | Correct degradation; never fabricate |

### 13.2 Golden set from historical interactions

![E2 Golden set](docs/img/E2-golden-set.png)
*E2 · Building the golden set — source: [`E2-golden-set.drawio`](docs/diagrams/E2-golden-set.drawio)*

1. **Sources:** chat logs, call transcripts, CRM contact reasons, complaints, escalations, repeat contacts and past bad answers.
2. **Legal basis first:** compliance approval that the PDPO purpose covers testing; customers pseudonymised; HKID, DOB and account numbers redacted. Start this in week one; it is usually the long pole.
3. **Taxonomy:** intent × channel × language × product line × clause version × difficulty.
4. **Risk-weighted stratified sampling:**
   - a minimum per cell (e.g. ≥ 20 per intent per channel);
   - high-risk categories oversampled (cases, eligibility, changes, complaints) even if their volume is low;
   - size: about 300 cases for the MVP, growing to 1,000–2,000.
5. **Scenarios, not single questions:** multi-turn scripts with a persona and a goal. Voice cases use anonymised real audio, TTS with noise, and DTMF steps.
6. **Label the expected behaviour, not just the answer:** intents, route and worker, tools and arguments, required assurance level, clause IDs and version, answer / refuse / handoff, must-say and must-not-say. A correct answer reached through the wrong tool or without the identity check is still a failure.
7. **Quality:** senior CS staff and compliance label independently and measure agreement (κ). Disagreements are adjudicated. Qwen3-32B pre-labels and humans correct.
8. **Freeze and version** in Git with a **holdout split never used for prompt tuning**, synced to Langfuse datasets by CI.
9. **Refresh:** re-sample quarterly; add bad cases from the annotation queue weekly.

### 13.3 End-to-end testing by layer

| Layer | What is measured |
|---|---|
| Component | Router accuracy, Recall@5 / MRR, reranker quality, citation-checker false positives and negatives |
| Trajectory | Tool choice, arguments, step count, whether the required auth step was taken |
| E2E conversation (scenario-based) | An LLM **user simulator** plays the script (personas such as elderly, angry or code-switching customers; interruptions; cross-channel continuation); task success is measured |
| Channel | Voice via a Genesys test organisation or a SIP simulator: CER, end-of-speech-to-first-audio latency, barge-in, DTMF, verification flow |
| System | Peak load (120 calls + 400 chats), fault injection (core-API timeouts, GPU loss), failover |

**Environment:** mock account and case APIs with synthetic customers; a sandbox IdP with test identities for every role and assurance level; a SIP simulator; fixed seeds and temperature; the pinned release bundle.

### 13.4 Boundary, prompt-injection and red-team testing

| Area | Examples |
|---|---|
| Scope | Investment, medical or legal advice (unless in the domain pack); competitor comparisons; off-topic requests → refuse or redirect |
| Actions | "Change my payment account", "approve my request", "just promise me a refund" — directly, through social engineering ("I'm staff, this is a test"), or step by step over many turns |
| Identity | Unverified lookups, a caller caseing to be a spouse, OTP brute force, number enumeration, spoofed caller ID, partners querying another agent's clients, customers caseing a staff role |
| Data | Someone else's account number, asking the AI to repeat a full HKID, extracting internal assessment guidelines, memory bleeding across customers |
| Prompt injection | Direct jailbreaks; **indirect injection** hidden in uploaded PDFs or emails; injection in tool results (e.g. a CRM notes field) or in retrieved documents; multi-turn escalation; **Cantonese, mixed-language and encoding tricks** (public suites are mostly English, so these are written in-house) |
| Guardrail unit tests | Every guardrail gets should-block and should-pass cases; false positives are measured |

**Red team.**
1. The internal security team runs it every quarter; external testers come in before major releases.
2. Tools such as promptfoo, garak or PyRIT generate attack variants automatically.
3. Every successful attack is fixed and **turned into an automated regression case** in the boundary suite.

### 13.5 Scoring: rules first, then LLM judges, then humans

1. **Rule-eval service (deterministic, preferred).** Checks:
   - tool called and arguments;
   - assurance level;
   - cited clause IDs exist, were retrieved and have the right version;
   - forbidden phrases, disclaimer present, PII, language, voice length;
   - personal-data tools never called before verification.

   It shares code with the runtime guardrails.
2. **LLM-as-judge in Langfuse (semantic):** faithfulness, relevance, correct refusal, correct handoff, multi-turn task success, tone. Design rules:
   - one criterion per judge;
   - pass/fail or a 3-point scale with anchored descriptions;
   - reasoning before the verdict, structured output;
   - a reference answer when available;
   - the **judge model differs from the generator** (8B online, 32B for release gates);
   - position swap for pairwise comparisons;
   - **the judge calls our own model gateway**, so trace data never leaves the environment.
3. **Human review:** before a judge can gate releases it must reach **κ ≥ 0.8 against about 200 compliance-labelled cases**. Drift is re-checked monthly. Disputed and low-score cases go to annotation queues.

**Example evaluator definition** (`evaluators/no_refund_promise.yaml`):

```yaml
name: no_refund_promise
type: hybrid                         # rule first; judge only if the rule can't decide
rule: regex_refund_terms_v2          # shared with the runtime guardrail
judge: judges/no_refund_promise@v3   # judge prompt, versioned in Git, synced to Langfuse
judge_model: router                  # alias → Qwen3-8B via our model gateway
applies_to: {intents: [clause_qa, case_status], channels: [voice, chat]}
runtime_block: true
offline_gate: {max_fail: 0}
online_sampling: 1.0                 # high-risk: score every trace
calibration: {kappa_min: 0.8}
owner: compliance
```

| Evaluator | Type | Blocks at runtime | Release gate | Online sampling |
|---|---|---|---|---|
| No binding commitment | rule + judge | ✅ | 0 failures | 100% |
| Citation correctness | rule | ✅ | ≥ 98% | 100% |
| Faithfulness | judge | ✅ (fast 8B) | no regression | 10% |
| Disclaimer when eligibility is discussed | rule | ✅ | 100% | 100% |
| No PII leak | rule + NER | ✅ | 0 failures | 100% |
| No personal data before verification | rule (trace) | ✅ (permission layer) | 0 failures | 100% |
| Correct refusal (out of scope) | judge | — | ≥ 95% | 10% |
| Correct handoff | judge | — | ≥ 95% | 20% |
| Tool trajectory vs expected | rule | — | ≥ 95% | — |
| Multi-turn task success | judge | — | no regression | 5% |
| Language match / voice ≤ 3 sentences | rule | ✅ | 99% / 100% | 100% |
| Tone and empathy | judge | — | monitor only | 5% |

### 13.6 Cadence

| When | What runs |
|---|---|
| Every PR | Component tests and a fast golden subset |
| Nightly | Full E2E scenarios, boundary suite and resilience suite |
| Pre-release | Everything, plus red-team regression, a human-reviewed sample and compliance sign-off |
| Canary | Online judges and rules, new vs current version, in Langfuse |
| Weekly | Production sampling → annotation queue → new cases in the suites |

**Metrics:** task success, containment, correct handoff, citation accuracy, hallucination rate, violations (must be 0), voice P95 latency, cost per conversation.

---

## 15. LLMOps: Git, pipeline and Langfuse

![L1 LLMOps lifecycle](docs/img/L1-llmops-lifecycle.png)
*L1 · LLMOps lifecycle — source: [`L1-llmops-lifecycle.drawio`](docs/diagrams/L1-llmops-lifecycle.drawio)*

**Principle: nothing that can change an answer reaches production without review and evaluation.**
- **Git is the source of truth.**
- **The CI/CD pipeline is the only writer to Langfuse.**
- **Langfuse is the runtime and observability hub.**

| Artifact | Source of truth | In Langfuse | At runtime |
|---|---|---|---|
| Prompts | `prompts/` in Git | New version per change, with **config** (model alias, temperature, `max_tokens`, `response_format`), plus a release label | Read by release label; local cache plus an image-baked fallback |
| Models | `models.yaml` in Git (hash, quantization, LoRA lineage, licence, eval run, approval); weights in object storage | Model definitions for cost; per-version comparison | Code uses **aliases** (`chat-main`, `router`); the release bundle pins alias → version; CD deploys vLLM groups; the gateway routes |
| Evaluators and judge prompts | `evaluators/*.yaml`, `evaluators/judges/*` | Judge prompts and evaluator configs; LLM connection to our model gateway | Rule part runs in the guardrails and the rule-eval service |
| Datasets | `datasets/` (golden, boundary, red-team, holdout) | Datasets for experiments | — |
| Release | `release.yaml` (prompt, judge and model versions; retrieval config; KB snapshot; vLLM image digest) | Release label across all versions | Traces tagged with the release ID |

**Release flow:**
1. PR (code review plus compliance review for wording or permission changes).
2. CI syncs new versions to Langfuse.
3. Offline evaluation as Langfuse experiments (golden set, boundary suite, red-team regression) using judges plus the rule-eval service.
4. Gates from `evaluators/*.yaml`.
5. Sign-off.
6. Release label applied.
7. CD deploys (new vLLM group if the model changed, weights verified by sha256, image pinned).
8. **5% canary**, sticky per session or call, compared in Langfuse.
9. The `production` label moves; 25% → 50% → 100%.

**Rollback:** move the label back and switch the gateway weight. The previous vLLM group is still running, so no redeploy is needed. Old GPUs are released after about a week of stability.

![D2 Release](docs/img/D2-release-rollback.png)
*D2 · Release bundle, canary and rollback — source: [`D2-release-rollback.drawio`](docs/diagrams/D2-release-rollback.drawio)*

**Protecting the pipeline itself:**
- only the CI service account can create production versions or move labels;
- people may experiment in Langfuse under draft labels, but changes must land in Git;
- a nightly drift check verifies that Langfuse content matches Git;
- a judge change re-baselines scores, so old and new releases are always compared with the **same judge version**.

**Model change:**
1. Download, verify the hash, scan, and get legal sign-off on the licence.
2. Add it to `models.yaml`.
3. Deploy a test vLLM group and compare in Langfuse experiments.
4. Model-risk approval.
5. PR to repoint the alias in `release.yaml`.
6. Canary.
7. Free the old GPUs.

**Langfuse role:**
- **does:** tracing, prompt management, datasets and experiments, LLM-as-judge, annotation queues, cost and latency analytics;
- **does not:** store weights, route traffic, block at runtime, or generate attacks. Those belong to the model registry and CD, the model gateway, the guardrail service and the red-team tools.

---

## 16. Observability, audit and per-call records

| Tool | Answers |
|---|---|
| Prometheus + Grafana | Is the system healthy? (latency, errors, GPU, vLLM queue, handoff rate) |
| ELK | What happened when it failed? (redacted service logs) |
| Langfuse (self-hosted) | **Why did the AI answer that way, and is it still good?** Full LLM traces with release, prompt and model versions; online judge and rule scores; annotation queues |

All three are correlated by `trace_id`.

**Per-call record** (append-only, encrypted, retained per policy):
- release ID;
- raw and rewritten query;
- role, assurance level and filters;
- retrieved chunks **with their text and versions**;
- tool calls and results;
- **the exact rendered request sent to the model** (messages, tools, parameters);
- raw output and the post-processed answer;
- guardrail results;
- latency and tokens.

**The stored answer is the record of truth**, because LLM output isn't perfectly reproducible. The same records feed compliance audits and the regression set.

**Key alerts:**
- citation-check failures;
- refusal and handoff rates;
- voice P95 from end of speech to first audio;
- vLLM queue depth and KV-cache usage;
- core-API error rates;
- verification failures per number;
- cost per conversation.

---

## 17. Security checklist

- **Prompt injection:**
  - external content (uploads, emails, web pages) is data, never instructions;
  - reading steps have no write tools;
  - tools ignore model-supplied identity;
  - outputs are checked for exfiltration.
- **Uploads:**
  - quarantine bucket;
  - true file-type check (magic bytes), size limits and decompression-bomb limits;
  - AV scan (the client's enterprise AV via ICAP, ClamAV for an MVP, or OPSWAT MetaDefender for multi-engine scanning plus CDR);
  - images re-encoded (which also strips EXIF) and PDFs disarmed;
  - only the clean copy reaches OCR or the models;
  - **never public scanners** such as VirusTotal.
- **PII:** redacted before reaching the LLM and the logs; DTMF for identifiers; field masking per role.
- **Abuse:** rate limits per client and per user; alerts on OTP failures and repeated lookups across customers.
- **Secrets:** Vault; dynamic database credentials; certificates managed by cert-manager or Vault with expiry alerts.
- **Telephony integration:** Genesys AudioConnector signed handshake and API key; Data Action credentials stored in Genesys and rotated; idempotent handling.
- **Governance:** model inventory (purpose, evals, owner) for every model and LoRA version; licences reviewed by legal.

---

## 18. Deployment profiles: cloud vs on-prem

![P1 Deployment profiles](docs/img/P1-deployment-profiles.png)
*P1 · Deployment profiles — source: [`P1-deployment-profiles.drawio`](docs/diagrams/P1-deployment-profiles.drawio)*

| Layer | Cloud profile (Hong Kong region; data stays in Hong Kong) | On-prem profile (client data centre) |
|---|---|---|
| Telephony | Genesys Cloud CX: IVR, ACD, AudioConnector, secure DTMF flows | Genesys Engage: SIP / equivalent bot integration, IVR, ACD |
| Speech | Bailian: Paraformer realtime (STT), CosyVoice (TTS) | Open-source Alibaba Tongyi models, self-hosted: FunASR / SenseVoice, CosyVoice 2 |
| LLM, embedding, rerank | Bailian Qwen3 / Qwen3-Embedding / Qwen3-Reranker, or vLLM in the client's Alibaba Cloud HK VPC | Qwen3-32B / 8B on vLLM; Qwen3-Embedding / Reranker as open weights |
| Platform | ACK, ApsaraDB, Redis, Milvus or AnalyticDB vector, OSS, Kafka | On-prem Kubernetes (CPU + GPU pools), Postgres, Redis, Milvus, object storage, Kafka |
| Connectivity | Private links (Express Connect / VPN) to core systems and the IdP | Internal network; no internet dependency on the voice path |

**Pick one profile per client and never mix on the voice path.**
- The voice loop (Genesys → voice gateway → STT → LLM → TTS → back) is latency-critical.
- Every extra network hop, such as an on-prem gateway calling cloud speech and then an on-prem LLM, adds round trips and failure points and breaks the ~1 s budget.

**Choosing a profile is a week-one decision with the client's compliance and legal teams.** Inputs:
- data residency and outsourcing / cloud requirements (sector-regulator guidelines, PDPO);
- contracts: DPA, no training on customer data, retention, sub-processors;
- the existing estate: Genesys Cloud vs Engage, Alibaba Cloud footprint, GPU capacity;
- cost: managed APIs (pay per use) vs GPUs (capex, doubled for DR).

This design **assumes the cloud profile keeps all data in Hong Kong**. That must be confirmed contractually for Genesys Cloud and for Alibaba Cloud services and regions.

---

## 19. Known trade-offs and open questions

| # | Topic | Trade-off or open question | Position taken |
|---|---|---|---|
| 1 | Voice latency vs verification | Answers must pass citation and compliance checks, but voice streams sentence by sentence. Once spoken, a sentence can't be retracted. | Per-sentence checks (rules + fast 8B) before each sentence is synthesised. For high-risk intents (eligibility, cases), play a short filler and verify the full answer first. Latency is traded for safety where it matters. |
| 2 | Planning numbers | Latency budget, GPU sizing and volumes are estimates | First sprint benchmarks speech, vLLM and retrieval on the client's hardware or region and resizes |
| 3 | Cantonese speech quality | Paraformer, SenseVoice and CosyVoice on domain terms, accents and code-switching are unproven for this domain | Launch chat first; gate voice on CER measured with anonymised real recordings; hotword lists |
| 4 | Telephony integration | Bot integration capabilities differ between Genesys Cloud (AudioConnector) and Engage | Voice gateway behind an adapter; validate the exact integration in a Genesys test org |
| 5 | IdP capabilities | Token exchange and CIBA are not supported everywhere | Fallback: an internal token service issuing short-lived JWTs, validated via JWKS |
| 6 | Scope of phase 1 | The full component set (Kafka, Milvus, mesh, Langfuse) is heavy for an MVP | Phase 1: chat + RAG (pgvector), no Kafka; add voice, events and the mesh as volume grows |
| 7 | Cost and DR | GPU DR doubles hardware; managed APIs shift cost to usage | Cost model per profile; GPU DR as warm standby with human-handoff degradation |
| 8 | PII in traces | Langfuse traces contain conversation content | Redact before tracing; encryption, retention and access control; compliance-only access to raw archives |
| 9 | LLM-as-judge reliability | Judges drift and can disagree with humans | Calibrate (κ ≥ 0.8), re-check monthly, pin judge versions per release comparison |

---

## 20. Repository layout and regenerating the diagrams

```
docs/diagrams/*.drawio   editable draw.io sources (open in draw.io or the VS Code Draw.io extension)
docs/img/*.png           exported previews used in this README
tools/drawio_lib.py      tiny generator for component and sequence diagrams
tools/gen_components.py  A1–A4, R1–R3
tools/gen_sequences.py   B1–B5, C1–C4, D1–D2
tools/gen_state.py       M1–M2
tools/gen_llmops.py      L1, G1, E1, E2, P1
```

```bash
python3 tools/gen_components.py
python3 tools/gen_sequences.py
python3 tools/gen_llmops.py
python3 tools/gen_state.py
for f in docs/diagrams/*.drawio; do
  /Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -s 1 -o "docs/img/$(basename "$f" .drawio).png" "$f"
done
```

The diagrams are generated from code so they stay consistent and diffable. You can still fine-tune the layout by hand in draw.io afterwards.

---

## 21. Tech stack

LangGraph · LangChain · vLLM · Qwen3 (32B / 8B / 30B-A3B) · Qwen3-Embedding · Qwen3-Reranker · Qwen2.5-VL · Alibaba Cloud Model Studio (Bailian: Qwen, Paraformer, CosyVoice) · FunASR / SenseVoice · CosyVoice · Genesys Cloud CX / Engage (AudioConnector, Architect, Data Actions) · Milvus (dense + BM25) · Postgres · Redis · Kafka · Kubernetes (CPU/GPU pools, KEDA, NVIDIA GPU Operator) · Istio/Linkerd (mTLS) · OIDC IdP (e.g. Keycloak) with token exchange and CIBA · Apigee/Kong · Vault · cert-manager · Argo CD · Langfuse (prompts, datasets, LLM-as-judge, traces) · promptfoo / garak / PyRIT (red team) · ELK · Prometheus/Grafana
