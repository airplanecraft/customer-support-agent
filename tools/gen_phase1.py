import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from drawio_lib import Diagram

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "diagrams")

# ======================= P2 Phase 1 deployment =======================
d = Diagram("P2 Phase 1 Deployment", 1900, 1000)
d.text("P2 · Phase 1 (lean) deployment — 4 deployable units, 5–6 infrastructure components, cloud hosting first", 40, 10, 1500, 30, 16, True)

d.zone("Channels", 20, 60, 300, 640, "client")
app = d.box("<b>App / web chat</b><br>phase 1", 50, 110, 240, 70, "client")
hum = d.box("<b>Human chat</b><br>client's existing live chat<br>or Genesys messaging", 50, 230, 240, 90, "client")
gx = d.box("<b>Genesys voice</b><br><i>phase 1b</i><br>≤ 30 concurrent AI calls", 50, 370, 240, 90, "ext", extra_style="dashed=1;")
stf = d.box("<b>Staff</b><br>approvers · agents", 50, 520, 240, 70, "client")

d.zone("Application (Kubernetes / ACK) — no service mesh", 360, 60, 760, 640, "core")
bff = d.box("<b>Web BFF</b><br>OIDC client · sessions<br>handoff-packet page (read only)<br>approver page (refunds over threshold)", 390, 100, 330, 120, "edge")
agent = d.box("<b>Agent app</b> (modular monolith, Python)<br><br>LangGraph orchestrator · router + workers<br>RAG (pgvector + Postgres full-text)<br>tools in-process (no MCP servers)<br>guardrails · confirmation module<br>approval module · handoff module<br>model routing library · auth_ref + token exchange", 390, 250, 700, 200, "core")
wk = d.box("<b>Worker</b> (same codebase)<br>outbox delivery · notifications<br>memory writer · CSAT survey", 390, 480, 330, 110, "core")
vg = d.box("<b>Voice gateway</b><br><i>phase 1b</i><br>AudioConnector · VAD · STT / TTS", 760, 480, 330, 110, "edge", extra_style="dashed=1;")
d.link(app, bff, "chat"); d.link(bff, agent, "", exit=(.5, 1), entry=(.25, 0))
d.link(gx, vg, "audio", dashed=True, exit=(1, .5), entry=(0, .5), points=[(335, 415), (335, 650), (740, 650), (740, 535)])
d.link(stf, bff, "", exit=(1, .5), entry=(0, .8), points=[(350, 555), (350, 196)])

d.zone("Data", 1160, 60, 340, 640, "data")
pg = d.db("<b>Postgres</b> + sync replica<br>pgvector + full-text (BM25)<br>checkpoints · tasks · outbox<br>confirmations · audit · memory", 1185, 100, 290, 150)
rs = d.db("<b>Redis-sec</b><br>token store only", 1185, 280, 290, 90, "sec")
ob = d.db("<b>Object storage</b><br>documents · uploads", 1185, 400, 290, 90)
lf = d.box("<b>Langfuse</b> (self-hosted)<br>prompts · datasets · judges · traces", 1185, 520, 290, 90, "obs")
d.link(agent, pg, "", exit=(1, .2), entry=(0, .5)); d.link(agent, rs, "", exit=(1, .5), entry=(0, .5))
d.link(agent, lf, "traces", exit=(1, .9), entry=(0, .5), dashed=True)

d.zone("Models", 1540, 60, 340, 300, "model")
d.box("<b>Cloud (first choice)</b><br>Bailian: Qwen · speech<br><b>no GPUs</b>", 1565, 100, 290, 100, "model")
d.box("<b>On-prem</b><br>vLLM: chat 3–4 GPUs<br>+ 2–4 for speech in 1b<br>DR not doubled", 1565, 220, 290, 120, "model", extra_style="dashed=1;")

d.zone("Client systems", 1540, 400, 340, 300, "ext")
idp = d.box("<b>IdP</b><br>OIDC · token exchange", 1565, 440, 290, 70, "sec")
gw = d.box("<b>Internal API gateway</b><br>→ systems of record (mTLS)", 1565, 540, 290, 80, "ext")
d.link(agent, gw, "tools · token exchange", exit=(1, .65), entry=(0, .5), points=[(1520, 380), (1520, 580)])

d.zone("Deferred until a trigger is met (see the upgrade table)", 20, 740, 1860, 120, "edge")
d.box("Kafka → <b>outbox</b> · Milvus → <b>pgvector</b> · service mesh → <b>ingress + NetworkPolicy</b> · MCP servers → <b>in-process tools</b> · model gateway service → <b>library</b> · Redis-cache → <b>in-process cache</b> · ELK → <b>client's logging</b> · full agent console → <b>phase 2</b>", 50, 785, 1800, 55, "edge", extra_style="fontSize=12;")
d.save(os.path.join(OUT, "P2-phase1-deployment.drawio"))
print("phase1 done")
