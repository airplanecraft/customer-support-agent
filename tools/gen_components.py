import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from drawio_lib import Diagram

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "diagrams")
HL = "#E8590C"      # design-highlight border and badges
P_ENTRY = "#2B8A3E"  # channel → external gateway → orchestrator
P_TOOL = "#C92A2A"   # orchestrator → MCP → internal gateway → systems of record
P_MODEL = "#1971C2"  # orchestrator / RAG → model gateway → models

# ======================= A1 System context =======================
d = Diagram("A1 System Context", 1400, 760)
d.text("A1 · System context — customer support agent (voice + chat) · vertical-agnostic", 40, 10, 1000, 30, 16, True)
phone = d.actor("Customer<br>(phone)", 80, 120)
appu = d.actor("Customer<br>(app / web)", 80, 360)
staff = d.actor("Staff<br>(CS agent / approver)", 80, 530)
tel = d.box("<b>Genesys contact centre</b><br>Cloud CX or Engage (on-prem)<br>IVR · ACD · AudioConnector", 300, 115, 220, 70, "ext")
core = d.box("<b>Customer Support Agent</b><br>generic core + domain pack (regulated)<br><br>LangGraph agents · hybrid RAG · guardrails<br>Qwen: Bailian (cloud) or vLLM (on-prem)",
             520, 300, 380, 280, "core")
idp = d.box("<b>Enterprise IdP (OIDC)</b><br>customer + staff SSO<br>token exchange / CIBA", 1060, 200, 260, 75, "sec")
sysc = d.box("<b>Core systems</b> (domain pack)<br>account system · case management · CRM<br>(via internal API gateway)", 1060, 320, 260, 80, "ext")
noti = d.box("<b>Notification</b><br>SMS gateway · APNs / FCM push", 1060, 440, 260, 65, "ext")
bl = d.box("<b>Alibaba Cloud Model Studio (Bailian)</b><br>cloud profile: Qwen · Paraformer · CosyVoice", 1060, 545, 260, 60, "ext", extra_style="dashed=1;")
d.link(phone, tel, "calls", exit=(1, .5), entry=(0, .5))
d.link(tel, core, "AudioConnector (WSS) · Data Actions", exit=(.5, 1), entry=(.1, 0), points=[(410, 250), (558, 250)])
d.link(appu, core, "HTTPS / WSS + access token<br>(login: OIDC + PKCE at IdP)", exit=(1, .5), entry=(0, .3))
d.link(staff, core, "staff console (staff SSO)", exit=(1, .5), entry=(0, .85))
d.link(core, idp, "token exchange · JWKS", exit=(1, .1), entry=(0, .5))
d.link(core, sysc, "MCP tools → internal API GW<br>TLS / mTLS + user token", exit=(1, .35), entry=(0, .5))
d.link(core, noti, "post-call message", exit=(1, .6), entry=(0, .5))
d.link(core, bl, "cloud profile only", dashed=True, exit=(1, .88), entry=(0, .5))
d.save(os.path.join(OUT, "A1-system-context.drawio"))

# ======================= A2 Components =======================
d = Diagram("A2 Components", 1920, 1600)
d.text("A2 · Components (containers) — one shared core for voice and chat", 40, 10, 900, 30, 16, True)
d.zone("Channels", 20, 50, 1880, 110, "client")
app = d.box("Mobile app<br>(tokens in Keychain / Keystore)", 80, 80, 200, 60, "client")
stf = d.box("Staff console<br>(staff SSO)", 320, 80, 160, 60, "client")
web = d.box("Web browser<br>(HttpOnly cookie only)", 560, 80, 180, 60, "client")
ph = d.box("Phone → Genesys<br>(IVR · ACD · secure DTMF flows)", 1060, 80, 240, 60, "client")
d.note("Config in release bundle:<br>agents.yaml · policy.yaml · session.yaml", 1400, 75, 300, 60)

d.zone("Edge (DMZ)", 20, 180, 1880, 120, "edge")
egw = d.box("<b>External API gateway</b> (client's: Apigee / Kong)<br>JWT verify (JWKS) · WAF · rate limit", 80, 210, 400, 70, "edge")
bff = d.box("<b>Web BFF</b><br>OIDC client · server-side tokens", 560, 210, 200, 70, "edge")
vgw = d.box("<b>Voice gateway</b><br>Genesys AudioConnector (WSS)<br>VAD · barge-in · streaming TTS", 1060, 205, 240, 80, "edge")
scan = d.box("File scan<br>(AV + CDR)", 820, 215, 160, 60, "sec")

d.zone("Application zone — K8s CPU pool · service-mesh mTLS", 20, 320, 1300, 460, "core")
orch = d.box("<b>Orchestrator</b><br>LangGraph: router + workers<br>checkpoints · token exchange", 400, 360, 280, 100, "core")
tok = d.box("<b>Token store</b><br>auth_ref → token (Redis, TTL)", 740, 370, 240, 60, "sec")
ver = d.box("<b>Verification service</b><br>SMS OTP + DOB (DTMF) → IdP", 1060, 370, 240, 60, "core")
rag = d.box("<b>RAG service</b><br>rewrite · hybrid search ·<br>rerank · citation check", 60, 490, 260, 80, "agent")
mz = d.zone("MCP servers — tools the agents call<br>(own mTLS client cert each)", 700, 470, 320, 272, "agent")
d.box("Account MCP", 720, 517, 280, 36, "agent")
d.box("Case MCP", 720, 561, 280, 36, "agent")
d.box("Order MCP", 720, 605, 280, 36, "agent")
d.box("Change MCP (draft only)", 720, 649, 280, 36, "agent")
d.box("Identity MCP", 720, 693, 280, 36, "agent")
apv = d.box("<b>Approval service</b><br>SoD check → executes stored draft", 1060, 470, 240, 60, "core")
nts = d.box("<b>Notification service</b><br>chat thread / push / SMS", 1060, 570, 240, 60, "core")
mgw = d.box("<b>Model gateway</b><br>routing · quotas · cost per channel", 60, 650, 260, 60, "model")
grd = d.box("<b>Guardrail library</b><br>input / output rules (shared<br>with rule-eval service)", 370, 690, 190, 60, "sec")

d.zone("GPU pool — on-prem profile (cloud profile: Bailian)", 1340, 320, 560, 460, "model")
gpu_main = d.box("Qwen3-32B (AWQ)<br>answers · multi-step agents", 1360, 360, 250, 60, "model")
stt = d.box("Speech (on-prem profile)<br>FunASR / SenseVoice · CosyVoice", 1630, 360, 250, 60, "model")
d.box("Qwen3-8B<br>router · rewrite · verify · judge", 1360, 440, 250, 60, "model")
d.box("Qwen3-Embedding<br>+ Qwen3-Reranker", 1630, 440, 250, 60, "model")
d.box("Qwen3-30B-A3B (optional)<br>low-latency voice", 1360, 520, 250, 60, "model", extra_style="dashed=1;")
d.box("Qwen-VL + PaddleOCR<br>documents", 1630, 520, 250, 60, "model")

d.zone("Data zone (DB protocols · NetworkPolicy · Vault creds)", 20, 800, 1300, 170, "data")
mil = d.db("Milvus<br>dense + BM25", 60, 835, 140, 100)
red = d.db("Redis<br>sessions · OTP", 240, 835, 140, 100)
pg = d.db("Postgres<br>checkpoints · tasks<br>audit index", 470, 835, 150, 100)
obj = d.db("Object storage<br>clauses · uploads", 640, 835, 140, 100)
kf = d.db("Kafka<br>task / session / doc events", 1060, 835, 220, 100)

d.zone("Observability (all services)", 1340, 800, 560, 170, "obs")
d.box("ELK<br>service logs (redacted)", 1360, 835, 250, 55, "obs")
d.box("Prometheus + Grafana<br>metrics · alerts", 1630, 835, 250, 55, "obs")
d.text("LLM traces → Langfuse (LLMOps plane below)", 1360, 905, 520, 30, 11)

d.zone("Client systems (other teams)", 20, 990, 1880, 150, "ext")
idp = d.box("<b>IdP (OIDC)</b><br>customer + staff SSO<br>token exchange / CIBA", 1400, 1020, 240, 80, "sec")
igw = d.box("<b>Internal API gateway</b>", 760, 1030, 200, 60, "edge")
cs = d.box("Account system · Case management · CRM", 1000, 1030, 300, 60, "ext")

d.link(app, egw, "HTTPS / WSS + token", exit=(.5, 1), entry=(.25, 0), color=P_ENTRY, width=3)
d.link(stf, egw, "staff token", exit=(.5, 1), entry=(.7, 0), color=P_ENTRY, width=3)
d.link(web, bff, "cookie")
d.link(bff, egw, "token", exit=(0, .5), entry=(1, .5), color=P_ENTRY, width=3)
d.link(ph, vgw, "AudioConnector")
d.link(egw, orch, "chat / API", exit=(.85, 1), entry=(.2, 0), color=P_ENTRY, width=3)
d.link(vgw, ver, "Data Action:<br>OTP + DOB")
d.link(ver, tok, "token", exit=(0, .5), entry=(1, .5))
d.link(orch, tok, "auth_ref", exit=(1, .3), entry=(0, .5))
d.link(vgw, orch, "turns (auth_ref)", exit=(0, .7), entry=(.8, 0), points=[(1030, 261), (1030, 340), (624, 340)])
d.link(orch, rag, "mTLS · rag token", exit=(0, .5), entry=(.5, 0), points=[(190, 410)])
d.link(orch, mz, "mTLS · exchanged tokens", exit=(1, .8), entry=(.5, 0), points=[(860, 440)], color=P_TOOL, width=3)
d.link(orch, mgw, "", exit=(.2, 1), entry=(1, .5), points=[(456, 680)], color=P_MODEL, width=3)
d.link(rag, mgw, "", color=P_MODEL, width=3)
d.link(mgw, gpu_main, "vLLM or Bailian (OpenAI-compatible)", exit=(.5, 1), entry=(0, .5), points=[(190, 760), (1350, 760), (1350, 390)], color=P_MODEL, width=3)
d.link(vgw, stt, "audio", exit=(1, .5), entry=(.5, 0), points=[(1755, 245)])
d.link(rag, mil, "hybrid search", exit=(0, .5), entry=(.3, 0), points=[(40, 530), (40, 820), (102, 820)])
d.link(orch, pg, "checkpoints", exit=(.8, 1), entry=(.85, 0))
d.link(orch, kf, "events", exit=(1, .95), entry=(0, .5), points=[(1040, 455), (1040, 885)])
d.link(kf, nts, "consume", exit=(.5, 0), entry=(.5, 1))
d.link(mz, igw, "mTLS + user token", exit=(.5, 1), entry=(.5, 0), color=P_TOOL, width=3)
d.link(igw, cs, "", color=P_TOOL, width=3)
d.link(ver, idp, "token exchange", dashed=True, exit=(1, .5), entry=(.5, 0), points=[(1320, 400), (1320, 985), (1520, 985)])

llm = d.zone("LLMOps plane — Git is the source of truth; the pipeline is the only writer to Langfuse", 20, 1340, 1880, 220, "obs")
git = d.box("<b>Git</b><br>prompts · models.yaml · evaluators<br>judge prompts · datasets · release.yaml", 60, 1390, 270, 80, "data")
ci = d.box("<b>CI / CD pipeline</b><br>sync → evaluate → gate →<br>label → deploy → canary", 380, 1390, 240, 80, "core")
lf = d.box("<b>Langfuse (self-hosted)</b><br>prompt versions + config · datasets / experiments<br>LLM-as-judge evaluators · traces · annotation queues", 680, 1380, 380, 100, "obs")
rev = d.box("<b>Rule-eval service</b><br>deterministic checks on traces<br>(same code as guardrails)", 1110, 1390, 240, 80, "sec")
reg = d.box("<b>Model registry</b><br>models.yaml (hash, licence, eval, approval)<br>weights in object storage", 1400, 1390, 270, 80, "model")
tst = d.box("<b>Test harness</b><br>user simulator · mock core<br>systems · SIP sim · red team", 1700, 1390, 180, 80, "agent")
d.link(git, ci, "PR merged")
d.link(ci, lf, "push versions · labels")
d.link(lf, rev, "traces", both=True)

# ---- design highlights (A2) ----
for cid, n in [(egw, 1), (igw, 2), (mz, 3), (rag, 4), (mgw, 5), (tok, 6), (apv, 7), (grd, 8), (llm, 9)]:
    d.emph(cid, HL); d.badge(cid, n, HL)
d.box("<b>Design highlights</b><br>"
      "<b>1 External API gateway</b> — the only way in for app, web and staff traffic: WAF, JWT check, rate limits (client's Apigee / Kong)<br>"
      "<b>2 Internal API gateway</b> — the only way to systems of record; each MCP server has its own client cert and reaches only its own APIs<br>"
      "<b>3 MCP servers</b> — our tool layer over the client's APIs: the LLM never sees raw APIs; customer identity comes from the token; changes are drafts only<br>"
      "<b>4 RAG service</b> — hybrid search (vector + BM25), rerank, version-correct clauses, a citation check on every sentence<br>"
      "<b>5 Model gateway</b> — the only way to any model: routes between Bailian and vLLM, quotas, cost per channel, fallback to a smaller model<br>"
      "<b>6 Token store</b> — tokens never enter agent state or prompts; agents carry only an auth_ref<br>"
      "<b>7 Approval service</b> — AI drafts, humans approve; separation of duties before anything takes effect<br>"
      "<b>8 Guardrail library</b> — the same rule code runs live and in offline evaluation<br>"
      "<b>9 LLMOps plane</b> — prompts, models, evaluators and datasets versioned in Git; the pipeline gates every release",
      20, 1155, 1300, 170, "ext", shape="rounded=1", extra_style=f"align=left;spacingLeft=12;fontSize=11;strokeColor={HL};strokeWidth=2;")
d.box("<b>Key paths</b><br>"
      f"<font color=\"{P_ENTRY}\">━━━</font> channels → external API gateway → orchestrator<br>"
      f"<font color=\"{P_TOOL}\">━━━</font> orchestrator → MCP → internal API gateway → systems of record<br>"
      f"<font color=\"{P_MODEL}\">━━━</font> orchestrator / RAG → model gateway → Bailian or vLLM",
      1340, 1155, 560, 170, "ext", shape="rounded=1", extra_style=f"align=left;spacingLeft=12;fontSize=12;strokeColor={HL};strokeWidth=2;")
d.note("Runtime: orchestrator reads prompts by release label (cache + image-baked fallback) · all LLM calls traced to Langfuse · judges call the model gateway (no external APIs)", 60, 1490, 1000, 45)
d.save(os.path.join(OUT, "A2-components.drawio"))

# ======================= A3 Network & deployment =======================
d = Diagram("A3 Network & Deployment", 1800, 1080)
d.text("A3 · Network zones, deployment and transport security (TLS vs mTLS)", 40, 10, 1000, 30, 16, True)
d.zone("Internet", 20, 50, 1760, 110, "client")
cust = d.box("Customer app / browser", 80, 80, 220, 55, "client")
tel = d.box("Genesys Cloud CX (SaaS)<br>or Genesys Engage (on-prem)", 600, 75, 260, 65, "ext")
d.zone("DMZ", 20, 180, 1760, 130, "edge")
waf = d.box("WAF + external API gateway<br>one-way TLS · JWT verify<br>→ orchestrator: TLS / mesh mTLS", 80, 205, 280, 80, "edge")
vg = d.box("Voice gateway<br>AudioConnector WSS endpoint<br>allow-list Genesys · API key + signed handshake", 600, 205, 260, 80, "edge")
d.zone("Application zone — K8s cluster (DC1 primary · DC2 DR)", 20, 330, 1760, 430, "core")
cpu = d.zone("CPU node pool", 40, 370, 880, 320, "core")
orch = d.box("Orchestrator", 80, 410, 180, 55, "core")
rag = d.box("RAG service", 80, 505, 180, 55, "agent")
mg = d.box("Model gateway", 80, 600, 180, 55, "model")
mz = d.zone("MCP servers<br>client cert A–E", 320, 400, 200, 285, "agent")
d.box("Account MCP · cert A", 335, 445, 170, 40, "agent")
d.box("Case MCP · cert B", 335, 491, 170, 40, "agent")
d.box("Order MCP · cert C", 335, 537, 170, 40, "agent")
d.box("Change MCP · cert D", 335, 583, 170, 40, "agent")
d.box("Identity MCP · cert E", 335, 629, 170, 40, "agent")
d.note("<b>Service mesh</b> (Istio)<br>automatic mTLS between pods<br>short-lived workload certs (SPIFFE)<br>authz: only orchestrator → RAG / MCP", 560, 400, 330, 110)
d.note("<b>cert-manager / Vault</b><br>client certs from the client's PKI<br>auto-renewal + expiry alerts", 560, 540, 330, 90)
d.zone("GPU node pool (tainted)", 950, 370, 810, 320, "model")
g1 = d.box("vLLM: Qwen3-32B / 8B", 1000, 410, 240, 55, "model")
d.box("Embedding + reranker", 1000, 505, 240, 55, "model")
g3 = d.box("STT / TTS", 1000, 600, 240, 55, "model")
d.note("NVIDIA GPU Operator<br>KEDA autoscale on vLLM queue depth<br>min replicas (model load is slow)", 1300, 410, 300, 80)
dz = d.zone("Data zone", 20, 780, 720, 150, "data")
d.db("Postgres", 50, 820, 110, 80); d.db("Redis", 180, 820, 100, 80); d.db("Milvus", 300, 820, 100, 80)
d.db("Object storage", 420, 820, 130, 80); d.db("Kafka", 570, 820, 100, 80)
d.zone("Client internal network (other teams)", 760, 780, 1020, 150, "ext")
ig = d.box("Internal API gateway<br>TLS + app token, or mTLS", 800, 820, 260, 70, "edge")
cs = d.box("Accounts · Cases · CRM", 1100, 825, 220, 60, "ext")
d.box("IdP (OIDC)<br>← token exchange (TLS)", 1380, 825, 220, 60, "sec")
d.link(cust, waf, "TLS (one-way) + access token", color=P_ENTRY, width=3)
d.link(tel, vg, "TLS · AudioConnector WSS + Data Actions")
d.link(waf, orch, "", exit=(.32, 1), entry=(.5, 0), color=P_ENTRY, width=3)
d.link(vg, orch, "mTLS", exit=(.5, 1), entry=(.8, 0), points=[(730, 360), (224, 360)])
d.link(vg, g3, "mTLS · audio", exit=(1, .5), entry=(1, .5), points=[(1270, 245), (1270, 627)])
d.link(orch, mz, "mTLS", exit=(1, .5), entry=(0, .15), color=P_TOOL, width=3)
d.link(orch, rag, "mTLS")
d.link(rag, mg, "mTLS", color=P_MODEL, width=3)
d.link(mg, g1, "mTLS", exit=(.5, 1), entry=(0, .5), points=[(170, 715), (970, 715), (970, 437)], color=P_MODEL, width=3)
d.link(cpu, dz, "DB protocols over TLS", exit=(.15, 1), entry=(.2, 0))
d.link(mz, ig, "mTLS (cert per MCP) + user token", exit=(.5, 1), entry=(.5, 0), color=P_TOOL, width=3, points=[(420, 745), (930, 745)])
d.link(ig, cs, "TLS", color=P_TOOL, width=3)
d.note("<b>Legend</b><br>TLS = only the server proves its identity<br>mTLS = both sides present certificates → <b>service-level</b> identity<br>access token = <b>user-level</b> identity and permissions (sent on every user call)", 800, 950, 560, 90)

# ---- design highlights (A3, same numbering as A2) ----
for cid, n in [(waf, 1), (ig, 2), (mz, 3), (rag, 4), (mg, 5)]:
    d.emph(cid, HL); d.badge(cid, n, HL)
d.box("<b>Design highlights</b> (numbers as in A2)<br>"
      "1 external API gateway · 2 internal API gateway · 3 MCP servers · 4 RAG · 5 model gateway<br>"
      f"<font color=\"{P_ENTRY}\">━━━</font> channels in · "
      f"<font color=\"{P_TOOL}\">━━━</font> tools → systems of record · "
      f"<font color=\"{P_MODEL}\">━━━</font> model calls",
      20, 950, 740, 90, "ext", shape="rounded=1", extra_style=f"align=left;spacingLeft=12;fontSize=12;strokeColor={HL};strokeWidth=2;")
d.save(os.path.join(OUT, "A3-network-deployment.drawio"))

# ======================= A4 Agent graph =======================
d = Diagram("A4 Agent Graph", 1900, 820)
d.text("A4 · Agent orchestration — routing + bounded workers (deterministic LangGraph state machine)", 40, 10, 1200, 30, 16, True)
st = d.box("START", 40, 370, 90, 40, "data", shape="ellipse")
cl = d.box("<b>classify</b><br>Qwen3-8B · response_format<br>multi-intent (fixed enum)", 170, 350, 210, 80, "model")
nx = d.box("<b>next</b><br>pop intent → worker<br>check role + auth level", 430, 350, 200, 80, "core")
vf = d.box("<b>verify</b> (subgraph)<br>voice: SMS OTP + DOB<br>chat: SSO / step-up", 430, 540, 200, 80, "sec")
d.zone("Workers · create_react_agent · loop ≤ 4 (voice 2) · tools = agent allowlist ∩ role", 700, 130, 560, 560, "agent")
w1 = d.box("<b>clause_agent</b> · Qwen3-32B<br>tools: search_clauses, get_fee_table<br>skills: clause_explain, fee_explain", 730, 160, 500, 70, "agent")
w2 = d.box("<b>account_agent</b> · Qwen3-8B<br>tools: get_accounts, get_account_detail, get_billing_history<br>skills: billing_explain", 730, 240, 500, 70, "agent")
w3 = d.box("<b>case_agent</b> · Qwen3-32B<br>tools: get_case_status, list_required_documents<br>skills: case_guide, document_checklist", 730, 320, 500, 70, "agent")
w5 = d.box("<b>order_agent</b> · Qwen3-32B · writes need confirmation<br>tools: orders · shipment · quote / place / cancel · refunds (T0–T2)<br>skills: order_lookup, returns_guide, refund_request", 730, 400, 500, 75, "agent")
w4 = d.box("<b>service_agent</b> · Qwen3-32B · requires verified (L2)<br>tools: create_change_draft (draft only)<br>skills: profile_change, address_change, cancellation", 730, 485, 500, 75, "agent")
ap = d.box("<b>approve</b> · interrupt() → human approval", 730, 590, 500, 55, "sec")
gd = d.box("<b>guard</b><br>time / question limits<br>sentiment · handoff rules", 1320, 350, 200, 90, "core")
fi = d.box("<b>finish</b><br>summary → CRM · events", 1580, 230, 200, 70, "core")
ho = d.box("<b>handoff</b><br>summary to staff<br>voice: back to Genesys ACD<br>+ participant data (screen pop)", 1580, 470, 200, 95, "edge")
en = d.box("END", 1820, 375, 70, 40, "data", shape="ellipse")
d.link(st, cl); d.link(cl, nx)
d.link(nx, vf, "auth too low", exit=(.3, 1), entry=(.3, 0))
d.link(vf, nx, "verified", exit=(.7, 0), entry=(.7, 1))
d.link(nx, w1, "clause_qa", exit=(1, .1), entry=(0, .5))
d.link(nx, w2, "account_lookup", exit=(1, .3), entry=(0, .5))
d.link(nx, w3, "case_*", exit=(1, .5), entry=(0, .5))
d.link(nx, w5, "order_* · refund", exit=(1, .7), entry=(0, .5))
d.link(nx, w4, "account_change · cancellation", exit=(1, .9), entry=(0, .5))
d.link(w4, ap, "draft created", exit=(.5, 1), entry=(.5, 0))
d.link(w1, gd, "", exit=(1, .5), entry=(0, .15)); d.link(w2, gd, "", exit=(1, .5), entry=(0, .38))
d.link(w3, gd, "", exit=(1, .5), entry=(0, .62)); d.link(w5, gd, "", exit=(1, .5), entry=(0, .85)); d.link(ap, gd, "", exit=(1, .5), entry=(.5, 1))
d.link(gd, nx, "more intents", dashed=True, exit=(.5, 0), entry=(.5, 0), points=[(1420, 100), (530, 100)])
d.link(gd, fi, "queue empty", exit=(1, .3), entry=(0, .5))
d.link(gd, ho, "limit · complaint · low confidence", exit=(1, .7), entry=(0, .5))
d.link(fi, en, "", exit=(1, .5), entry=(.5, 0)); d.link(ho, en, "", exit=(1, .5), entry=(.5, 1))
d.note("Config (versioned): agents.yaml · policy.yaml<br>Identity: config holds auth_ref only (never state / messages)<br>Checkpointer: Postgres · thread_id = call_id / session_id", 40, 680, 560, 70)
d.save(os.path.join(OUT, "A4-agent-graph.drawio"))

# ======================= R1 RAG ingestion =======================
d = Diagram("R1 RAG Ingestion", 1560, 640)
d.text("R1 · RAG ingestion — versioned clause knowledge base", 40, 10, 900, 30, 16, True)
s_ = d.box("Sources<br>product terms (PDF) · FAQ<br>guidelines · regulatory notices", 40, 100, 200, 80, "ext")
ob = d.db("Object storage<br>new / revised file event", 280, 95, 170, 90)
pa = d.box("<b>Parse</b><br>layout · cross-page tables<br>OCR for scans (PaddleOCR / Qwen-VL)", 490, 100, 240, 80, "core")
ch = d.box("<b>Chunk</b><br>by clause (200–600 tokens)<br>tables by row + header", 770, 100, 210, 80, "core")
me = d.box("<b>Metadata</b><br>product_code · version · effective dates<br>language · visibility · clause_no", 1020, 100, 250, 80, "core")
hs = d.box("<b>Content hash</b><br>unchanged → skip · changed → upsert<br>old version kept (expired)", 1300, 100, 240, 80, "core")
em = d.box("<b>Qwen3-Embedding</b><br>dense vectors (batched, GPU)", 1300, 290, 240, 70, "model")
bm = d.box("<b>BM25 analyzer</b><br>Milvus built-in · jieba<br>(no model)", 1020, 290, 240, 70, "data")
mv = d.db("<b>Milvus collection</b><br>dense_vec · text → bm25_vec<br>metadata · partitions per product line", 680, 275, 290, 110)
ev = d.box("<b>Eval gate</b><br>golden set Recall@5 / MRR<br>no regression → publish", 380, 290, 240, 80, "sec")
al = d.box("<b>Alias swap</b><br>kb_live → new snapshot<br>(old kept for rollback)", 80, 290, 240, 80, "core")
ca = d.box("Invalidate semantic cache<br>(keys include version)", 80, 430, 240, 60, "data")
d.link(s_, ob); d.link(ob, pa, "event"); d.link(pa, ch); d.link(ch, me); d.link(me, hs)
d.link(hs, em, "changed chunks", exit=(.6, 1), entry=(.6, 0))
d.link(hs, bm, "text", exit=(.15, 1), entry=(.8, 0), points=[(1336, 240), (1212, 240)])
d.link(bm, mv, "", exit=(0, .5), entry=(1, .5))
d.link(em, mv, "", exit=(.5, 1), entry=(.5, 1), points=[(1420, 420), (825, 420)])
d.link(mv, ev, "new snapshot", exit=(0, .5), entry=(1, .5))
d.link(ev, al, "pass", exit=(0, .5), entry=(1, .5))
d.link(al, ca, "")
d.note("Changing the embedding model = re-embed everything into a NEW collection,<br>evaluate, then swap the alias — vectors from different models can't be mixed.", 680, 470, 560, 60)
d.save(os.path.join(OUT, "R1-rag-ingestion.drawio"))

# ======================= R2 Hybrid retrieval =======================
d = Diagram("R2 Hybrid Retrieval", 1900, 760)
d.text("R2 · Hybrid retrieval and grounded generation (query path)", 40, 10, 900, 30, 16, True)
q = d.box("Customer question<br>(chat text / STT transcript)", 40, 300, 190, 70, "client")
rw = d.box("<b>Rewrite</b> · Qwen3-8B<br>Cantonese colloquial → search terms<br>split multi-part questions", 270, 290, 240, 90, "model")
ex = d.box("<b>Exact match</b><br>clause_no / product_code<br>→ metadata filter hit", 580, 130, 240, 75, "data")
dn = d.box("<b>Dense search</b><br>Qwen3-Embedding (query + instruction)<br>ANN top-30", 580, 295, 240, 80, "model")
bs = d.box("<b>BM25 full-text</b><br>Milvus built-in · jieba<br>top-30", 580, 460, 240, 75, "data")
fl = d.note("<b>Filters (server-side, derived from the token)</b><br>product_code · version by contract start date<br>visibility by role · language · owner_id<br>applied to dense + BM25", 560, 580, 300, 90)
rrf = d.box("<b>RRF fusion</b><br>k = 60 → 30 candidates", 880, 295, 190, 80, "core")
rr = d.box("<b>Qwen3-Reranker</b><br>chat top-5 · voice top-3<br>low score → retry / handoff", 1110, 290, 230, 90, "model")
tx = d.db("Object storage<br>clause text", 1150, 450, 150, 80)
gen = d.box("<b>Generate</b> · Qwen3-32B<br>answer only from context<br>per-sentence citations<br>voice: ≤ 3 sentences", 1380, 280, 230, 110, "model")
vc = d.box("<b>Citation check</b><br>Qwen3-8B / NLI", 1660, 150, 200, 60, "sec")
cc = d.box("<b>Compliance check</b><br>no binding commitment · disclaimer", 1660, 260, 200, 65, "sec")
out = d.box("Answer (streamed)<br>+ trace to Langfuse", 1660, 370, 200, 60, "client")
hd = d.box("Handoff to human", 1660, 520, 200, 55, "edge")
d.link(q, rw)
d.link(rw, ex, "", exit=(1, .2), entry=(0, .5)); d.link(rw, dn, "", exit=(1, .5), entry=(0, .5)); d.link(rw, bs, "", exit=(1, .8), entry=(0, .5))
d.link(ex, rrf, "", exit=(1, .5), entry=(.5, 0)); d.link(dn, rrf, "", exit=(1, .5), entry=(0, .5)); d.link(bs, rrf, "", exit=(1, .5), entry=(.5, 1))
d.link(fl, bs, "", dashed=True, exit=(.5, 0), entry=(.5, 1))
d.link(rrf, rr)
d.link(rr, tx, "fetch text", exit=(.5, 1), entry=(.5, 0))
d.link(rr, gen, "top-k", exit=(1, .5), entry=(0, .5))
d.link(tx, gen, "", exit=(1, .5), entry=(.5, 1))
d.link(gen, vc, "", exit=(1, .2), entry=(0, .5))
d.link(vc, cc, "pass", exit=(.5, 1), entry=(.5, 0))
d.link(cc, out, "pass", exit=(.5, 1), entry=(.5, 0))
d.link(vc, hd, "fail", exit=(1, .5), entry=(1, .3), points=[(1880, 180), (1880, 536)])
d.link(cc, hd, "fail", exit=(1, .7), entry=(1, .7), points=[(1870, 305), (1870, 558)])
d.note("Why hybrid: dense handles paraphrase (张单点解贵咗 ≈ why is my bill higher);<br>BM25 nails clause numbers, product codes and technical terms.<br>In parallel: related-history lookup (same intent + entity, last 30 days).", 40, 600, 480, 80)
d.save(os.path.join(OUT, "R2-hybrid-retrieval.drawio"))

# ======================= R3 Model inventory (no edges) =======================
d = Diagram("R3 Model Inventory", 1500, 1000)
d.text("R3 · Model inventory — all Alibaba Qwen / Tongyi: Bailian in the cloud profile, open source on-prem", 40, 10, 1200, 30, 16, True)
rows = [
    ("Voice in", [("Silero VAD", "end-of-speech · CPU"), ("Paraformer realtime (Bailian)", "STT · cloud profile"), ("FunASR / SenseVoice", "STT · on-prem profile (open source)")]),
    ("Understand", [("Qwen3-8B", "intent (multi) · rewrite · sentiment"), ("Qwen3-8B", "account_agent (single read)")]),
    ("Retrieve", [("Qwen3-Embedding", "dense vectors · semantic cache"), ("Milvus BM25 (jieba)", "keyword search · not a model"), ("Qwen3-Reranker", "cross-encoder rerank")]),
    ("Answer / act", [("Qwen3-32B", "clause answers · multi-step agents"), ("Qwen3-30B-A3B (optional)", "low-latency voice (MoE)")]),
    ("Guard", [("Qwen3-8B / NLI", "citation verification"), ("Rules + Qwen3-8B", "compliance check"), ("Rules + NER (Presidio)", "PII redaction")]),
    ("Documents", [("PaddleOCR", "text extraction"), ("Qwen2.5-VL-7B", "receipt / report fields")]),
    ("Voice out", [("CosyVoice (Bailian)", "TTS · cloud profile"), ("CosyVoice 2 (open source)", "TTS · on-prem profile")]),
    ("Evaluate", [("Qwen3-8B judge", "online sampling (calibrated)"), ("Qwen3-32B + human", "offline release gate")]),
    ("Local dev only", [("Ollama · Qwen3-8B (quantised)", "laptop · OpenAI-compatible API"), ("Zvec (embedded)", "dense + full-text (jieba) · dev / tests"), ("Release evals", "always on the production model")]),
]
y = 60
for stage, models in rows:
    d.box(f"<b>{stage}</b>", 40, y, 150, 70, "edge")
    for i, (m, desc) in enumerate(models):
        zone = "data" if any(k in m for k in ("Milvus", "Rules", "PaddleOCR", "VAD", "Zvec", "Release")) else "model"
        d.box(f"<b>{m}</b><br>{desc}", 220 + i * 330, y, 300, 70, zone)
    y += 95
d.note("Small models for simple, latency-sensitive steps; 32B where citations and tool accuracy matter;<br>"
       "rules or specialised models where possible. The split is decided by golden-set runs (8B / 14B / 32B / 30B-A3B).<br>"
       "Fine-tune behaviour only (LoRA, on-prem, anonymised + synthetic data) — never clause knowledge.", 220, y + 10, 980, 70)
d.save(os.path.join(OUT, "R3-model-inventory.drawio"))

# ======================= A5 Agent console =======================
d = Diagram("A5 Agent Console", 1900, 1000)
d.text("A5 · Agent console — what a human agent sees after handoff (embedded in the Genesys agent desktop)", 40, 10, 1400, 30, 16, True)
d.zone("Agent console · staff SSO + MFA · roles: cs_agent / supervisor / approver / qa / compliance · data only for interactions assigned to this agent", 20, 50, 1460, 900, "client")
d.box("<b>Header</b> · customer (masked) · <b>verified by AI 10:02 (voice_otp_dob)</b> · handoff reason · sentiment · language · channel · wait time", 40, 90, 1420, 50, "edge")
d.box("<b>1 · Handoff summary</b> <i>(AI-generated, marked)</i><br>3 lines, fixed schema<br>intent(s) · why handed off · what the customer wants next", 40, 160, 460, 130, "agent")
d.box("<b>2 · Full bot transcript</b><br>chat text · voice STT transcript with confidence<br>redacted · DTMF never shown", 40, 310, 460, 300, "core")
d.box("<b>3 · AI answers and citations</b><br>each answer with clause ID + version<br>click → clause text of that version", 520, 160, 460, 220, "core")
d.box("<b>4 · Tool-call timeline</b><br>tool · arguments (masked) · result · time<br>guardrail events (refusals, step-ups)", 520, 400, 460, 210, "core")
d.box("<b>5 · Open tasks and drafts</b><br>from the task table (system facts)<br>status · pending approvals", 1000, 160, 460, 150, "data")
d.box("<b>6 · Customer overview</b><br>from CRM · masked per role<br>accounts · recent orders · flags", 1000, 330, 460, 140, "ext")
d.box("<b>7 · Knowledge search</b><br>same hybrid RAG<br>+ internal-visibility articles", 1000, 490, 460, 120, "agent")
d.box("<b>8 · Actions and wrap-up</b> (per role)<br>create / update tasks · approvals go to the approver queue (never own drafts)<br>wrap-up notes drafted by AI → agent edits → CRM · disposition code<br><b>feedback on the AI</b>: right / wrong + reason code → annotation queue → golden set", 40, 630, 1420, 120, "sec")
d.note("<b>Facts vs summary</b>: verification, tasks, tool calls and citations come from system records;<br>only the 3-line summary is written by the LLM, and it is labelled as AI-generated.", 40, 770, 700, 70)
d.note("<b>Console hardening</b>: every view audited (who, what, when) · no PII in URLs ·<br>export / copy limited · CSP · idle timeout · access revoked 30 min after wrap-up", 760, 770, 700, 70)
d.box("<b>Supervisor view</b><br>live queues and wait times<br><b>monitor live AI chats</b><br>take over a chat at any time<br>handoff reasons by intent", 1520, 90, 350, 220, "obs")
d.box("<b>Phase 2 · Agent assist</b><br>suggested replies · next best action<br>auto wrap-up notes<br><b>the agent decides; the AI never<br>sends on the agent's behalf</b>", 1520, 340, 350, 200, "model")
d.box("<b>No hand-back</b><br>once a human takes over,<br>the conversation stays human<br>until it ends", 1520, 570, 350, 140, "edge")
d.save(os.path.join(OUT, "A5-agent-console.drawio"))
print("components done")
