import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from drawio_lib import Diagram

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "diagrams")

# ======================= M1 State and memory layers =======================
d = Diagram("M1 State and Memory", 1900, 960)
d.text("M1 · State and memory layers — what lives where, who reads it, who writes it", 40, 10, 1200, 30, 16, True)

d.zone("Short-term (per session · thread_id)", 20, 60, 600, 520, "agent")
st = d.box("<b>LangGraph state</b><br><br>messages (last N turns) · summary<br>channel · language<br>customer_id (after verification)<br>assurance: level · verified_at · expires_at<br>auth_ref (opaque)<br>intents · current worker<br>task_ids · pending draft<br>guard counters · release label<br>retrieved chunk ids (not full text)", 40, 100, 290, 260, "agent")
ck = d.db("<b>Postgres checkpoints</b><br>PostgresSaver · key: thread_id<br>kept 30 days → archive<br>not the audit log", 380, 130, 220, 120)
sm = d.box("<b>trim_messages + summary node</b><br>keep last N turns raw;<br>older turns → summary<br>(versioned prompt, via model gateway)", 40, 400, 290, 110, "core")
d.link(st, ck, "persisted as", dashed=True)
d.link(sm, st, "", dashed=True)

orch = d.box("<b>Orchestrator (LangGraph)</b><br>router + bounded workers<br>stateless pods", 680, 240, 300, 120, "core")
d.link(orch, ck, "every step · durability=async;<br>sync before write tools / interrupt", exit=(0, .3), entry=(1, .5))

d.zone("Long-term and systems of record (per customer)", 1060, 60, 820, 520, "data")
sto = d.db("<b>PostgresStore + pgvector</b><br>('customer', cid, 'summaries')<br>('customer', cid, 'prefs')<br>TTL 90 days · delete on request", 1100, 90, 300, 105)
tsk = d.db("<b>Postgres tasks</b><br>open work · approvals · drafts<br>step-up evidence · no tokens", 1100, 215, 300, 100)
tok = d.db("<b>Redis-sec (dedicated)</b><br>token store: auth_ref → encrypted token<br>TTL ≤ token expiry · deleted at session end", 1100, 335, 300, 100, "sec")
sor = d.box("<b>Systems of record</b><br>accounts · billing · cases<br>via internal API gateway", 1100, 455, 300, 95, "ext")
d.link(orch, sto, "after verification: search(limit=3) + prefs<br>namespace from token sub, never the LLM", exit=(1, .1), entry=(0, .5))
d.link(orch, tsk, "open tasks", exit=(1, .37), entry=(0, .5))
d.link(orch, tok, "resolve auth_ref", exit=(1, .63), entry=(0, .5))
d.link(orch, sor, "facts: always read live", exit=(1, .9), entry=(0, .5))
d.note("<b>Memory = hints. Systems of record = facts.</b><br>Address, balances, contract status are never<br>memory — read live every time.<br>Open work lives in tasks, not memory.", 1440, 90, 420, 105)
d.note("<b>Never in state, checkpoints or memory</b><br>tokens · OTP · raw audio · full ID or card numbers<br>Memory loads only after verification;<br>voice prefetches it while verification runs.", 1440, 215, 420, 105)
d.note("<b>Governance</b><br>customer deletion → drop the namespace<br>TTL sweep for expired entries<br>each memory traceable to session + prompt version", 1440, 340, 420, 95)
d.note("Why not LangMem: no in-conversation memory writes<br>(persistent prompt injection),<br>no free-form fact extraction,<br>LLM calls must go through our gateway.", 740, 430, 250, 120)

d.zone("Long-term write path (background, off the hot path)", 20, 620, 1860, 300, "obs")
kf = d.box("<b>Kafka</b><br>session.ended", 50, 720, 200, 90, "data")
mw = d.box("<b>MemoryWriter worker</b><br>reads the interaction record<br>(intent, outcome, task ids)", 310, 720, 240, 90, "core")
mg = d.box("<b>Model gateway</b><br>summary prompt vN (Git → Langfuse)<br>fixed schema via response_format", 610, 720, 260, 90, "model")
gr = d.box("<b>Output guardrail</b><br>PII redaction · drop identity /<br>authorization claims", 930, 720, 240, 90, "sec")
pt = d.box("<b>Store.put</b><br>namespace from customer_id<br>TTL 90 days", 1230, 720, 220, 90, "data")
au = d.box("<b>Audit</b><br>memory ↔ session ↔<br>prompt version", 1510, 720, 220, 90, "obs")
d.link(orch, kf, "session.ended", exit=(.12, 1), entry=(.5, 0), points=[(716, 670), (150, 670)])
d.link(kf, mw); d.link(mw, mg); d.link(mg, gr); d.link(gr, pt); d.link(pt, au)
d.save(os.path.join(OUT, "M1-state-memory.drawio"))

# ======================= M2 Cache map =======================
d = Diagram("M2 Cache Map", 1900, 900)
d.text("M2 · Cache map — where we cache on the request path, the key, the TTL and what invalidates it", 40, 10, 1300, 30, 16, True)
d.text("Request path (simplified)", 30, 55, 400, 25, 12, True)
stages = [
    ("BFF / voice gateway", "client", "<b>Session store</b> (Redis-sec)<br>key: session cookie id<br>TTL: 60 min idle<br>browser holds only the cookie"),
    ("API gateway", "edge", "<b>JWKS</b> by kid<br>refresh on unknown kid<br><b>Rate-limit counters</b><br>(Redis-cache)"),
    ("Orchestrator", "core", "<b>Token store</b> (Redis-sec)<br>auth_ref → encrypted token<br><b>Prompts</b> by release label<br>+ image-baked fallback"),
    ("Model gateway + vLLM", "model", "<b>Prefix cache</b><br>vLLM APC / Bailian<br>context cache<br>static first, dynamic last"),
    ("RAG", "agent", "<b>Embedding</b>: norm(query)<br>+ embedding model version<br><b>Retrieval</b>: query + KB snapshot<br>+ visibility filter"),
    ("Tools / MCP", "core", "<b>Downstream tokens</b><br>key: (auth_ref, aud, scope)<br>TTL: minutes, below expiry"),
    ("Systems of record", "ext", "<b>Account summary</b> (read only)<br>key: customer_id + session<br>TTL 5 min<br>purged by any write tool"),
    ("Answer", "client", "<b>FAQ answers</b><br>exact match only<br>public, non-personal<br>key includes KB snapshot"),
]
prev = None
for i, (name, zone, cache) in enumerate(stages):
    x = 30 + i * 230
    p = d.box(f"<b>{name}</b>", x, 85, 200, 60, zone)
    c = d.box(cache, x, 210, 200, 140, "data", extra_style="fontSize=11;")
    d.link(p, c, "cache", dashed=True)
    if prev:
        d.link(prev, p)
    prev = p

d.zone("Two Redis instances — never mix secrets with caches", 30, 400, 1840, 180, "sec")
d.box("<b>Redis-sec</b>: tokens · OTP · BFF sessions<br>app-level AES-GCM (KMS / Vault keys) · TLS · per-service ACL<br>no RDB/AOF · no backups · KEYS / MONITOR / CONFIG / FLUSHALL disabled<br>eviction → fail closed (re-authenticate)", 70, 445, 860, 110, "sec")
d.box("<b>Redis-cache</b>: embeddings · retrieval · FAQ · account summary · rate limits<br>rebuildable · allkeys-lru · keys always scoped by customer_id<br>where the data is personal", 980, 445, 850, 110, "data")

d.box("<b>Never cached</b><br>write-tool results · entitlements / permissions (or ≤ 60 s) · semantic cache of personalised answers · checkpoints (Postgres is the source of truth)", 30, 620, 1100, 90, "sec")
d.note("<b>Invalidation = version in the key</b><br>KB snapshot, embedding model, release label.<br>A new release changes the key; no manual purges.<br>The only explicit purge: write tools → account summary.", 1180, 610, 690, 110)
d.save(os.path.join(OUT, "M2-cache-map.drawio"))

# ======================= F1 Degradation levels =======================
d = Diagram("F1 Degradation Levels", 1900, 820)
d.text("F1 · Degradation levels and kill switches — fail closed for identity and writes, degrade for reads", 40, 10, 1400, 30, 16, True)
lv = [
    ("<b>Level 0 · Normal</b><br><br>all channels, intents and tools<br>full models (32B / 8B)", "core", "—"),
    ("<b>Level 1 · Reduced</b><br><br>smaller models (8B / 30B-A3B)<br>shorter voice answers<br>some intents go straight to humans", "edge", "GPU short · latency over budget ·<br>Bailian rate-limited · TTS on backup"),
    ("<b>Level 2 · Safe mode</b><br><br><b>RAG answers only</b><br>no tool calls, no writes<br>personal-data intents → handoff", "obs", "IdP / STS down · core systems down ·<br>Redis-sec down · checkpoint writes failing"),
    ("<b>Level 3 · AI off</b><br><br>everything to humans<br>voice → IVR menu / ACD<br>chat → human queue or message", "sec", "severe incident · bad release not<br>rolling back · compliance pause"),
]
prev = None
for i, (label, zone, trig) in enumerate(lv):
    x = 40 + i * 460
    b = d.box(label, x, 80, 400, 190, zone)
    d.box("<b>Enter when</b><br>" + trig, x, 300, 400, 90, "data", extra_style="fontSize=11;")
    if prev:
        d.link(prev, b, "worse")
    prev = b
d.zone("Kill switches (feature flags, no redeploy, effective in seconds)", 40, 430, 1820, 170, "sec")
d.box("<b>Scope</b><br>per channel · per intent ·<br>per tool · per model alias", 80, 475, 380, 100, "sec")
d.box("<b>Who</b><br>on-call SRE or compliance lead<br>every switch audited", 520, 475, 380, 100, "sec")
d.box("<b>Automatic</b><br>IdP / STS down → level 2 for personal intents<br>canary red line → rollback<br>level 3 needs a human decision", 960, 475, 460, 100, "sec")
d.box("<b>Recovery</b><br>step back one level at a time<br>after health checks pass", 1480, 475, 340, 100, "sec")
d.note("Principles: identity and writes fail closed · reads and caches degrade · never fabricate ·<br>tell the customer honestly · events via transactional outbox · unknown write outcome → reconcile, never blind retry", 40, 630, 1100, 70)
d.save(os.path.join(OUT, "F1-degradation-levels.drawio"))
