import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from drawio_lib import Sequence

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "diagrams")

def save(s, fname):
    s.finish(); s.save(os.path.join(OUT, fname))

# ---------------- B1 Web login (OIDC + PKCE + BFF) ----------------
s = Sequence("B1 Web login (BFF)", [("u", "Customer", "client"), ("br", "Browser", "client"), ("bff", "Web BFF", "edge"),
                                     ("idp", "IdP (OIDC)", "sec"), ("ts", "Session store<br>(Redis, encrypted)", "data")])
s.text("B1 · Web login — OIDC authorization code + PKCE, tokens kept server-side (BFF)", 40, 10, 900, 30, 16, True)
s.msg("u", "br", "open the support page")
s.msg("br", "bff", "GET /login")
s.msg("bff", "bff", "create state, nonce, PKCE code_verifier → challenge")
s.msg("bff", "br", "302 → IdP /authorize?client_id, redirect_uri, scope, state, nonce, code_challenge", ret=True)
s.msg("br", "idp", "GET /authorize")
s.msg("u", "idp", "authenticate (password + OTP / passkey)")
s.msg("idp", "br", "302 → /callback?code, state", ret=True)
s.msg("br", "bff", "GET /callback?code, state")
s.msg("bff", "bff", "check state == stored state (CSRF)")
s.msg("bff", "idp", "POST /token (code + code_verifier + client auth)")
s.msg("idp", "bff", "id_token + access_token + refresh_token", ret=True)
s.msg("bff", "bff", "verify ID token: JWKS signature, iss, aud = client_id, exp, nonce")
s.msg("bff", "ts", "store tokens under session id")
s.msg("bff", "br", "Set-Cookie: sid (HttpOnly, Secure, SameSite) — no tokens in browser", ret=True)
s.note_over("br", "ts", "Later calls: browser sends cookie → BFF loads access token → Authorization: Bearer … to API gateway")
save(s, "B1-web-login-bff.drawio")

# ---------------- B2 App login ----------------
s = Sequence("B2 App login", [("u", "Customer", "client"), ("app", "Mobile app", "client"), ("sb", "System browser", "client"),
                               ("idp", "IdP (OIDC)", "sec"), ("gw", "External API gateway", "edge")])
s.text("B2 · Mobile app login — authorization code + PKCE (AppAuth), tokens in Keychain / Keystore", 40, 10, 1000, 30, 16, True)
s.msg("u", "app", "tap Log in")
s.msg("app", "app", "state, nonce, PKCE verifier")
s.msg("app", "sb", "open /authorize (code_challenge)")
s.msg("sb", "idp", "authorize")
s.msg("u", "idp", "authenticate (biometric / passkey)")
s.msg("idp", "app", "redirect app-scheme://callback?code, state", ret=True)
s.msg("app", "idp", "POST /token (code + code_verifier)")
s.msg("idp", "app", "id_token + access_token (5–15 min) + refresh_token", ret=True)
s.msg("app", "app", "validate ID token (iss, aud, nonce); store tokens in Keychain / Keystore")
s.msg("app", "gw", "API call · Authorization: Bearer access_token")
s.msg("gw", "app", "200", ret=True)
s.msg("app", "idp", "before expiry: POST /token (refresh_token)")
s.msg("idp", "app", "new access_token (refresh token rotated)", ret=True)
save(s, "B2-app-login.drawio")

# ---------------- B3 Voice verification -> token ----------------
s = Sequence("B3 Voice verification", [("c", "Caller", "client"), ("gx", "Genesys<br>(Architect · IVR)", "ext"), ("vg", "Voice gateway<br>(AudioConnector)", "edge"),
                                        ("vs", "Verification svc", "core"), ("crm", "CRM", "ext"), ("sms", "SMS gateway", "ext"),
                                        ("idp", "IdP", "sec"), ("ts", "Token store", "data")])
s.text("B3 · Voice 'login' — Genesys collects OTP + date of birth in a secure flow → IdP issues a short-lived access token", 40, 10, 1200, 30, 16, True)
s.msg("c", "gx", "inbound call (recording notice played by Genesys)")
s.msg("gx", "vg", "AudioConnector session open (inputVariables: conversationId, ANI) · signed handshake")
s.msg("vg", "vg", "prefetch by ANI: risk + language only (never spoken)")
s.note_over("c", "vg", "Caller asks about own account → personal data needed → AI ends the session with outputVariables {next: verify}")
s.msg("vg", "gx", "close session · outputVariables {next: verify}", ret=True)
s.msg("gx", "vs", "Data Action: start verification (ANI)")
s.msg("vs", "crm", "lookup customer by registered mobile")
s.msg("crm", "vs", "customer C-88231 (candidate)", ret=True)
s.msg("vs", "sms", "OTP to the REGISTERED mobile only (rate-limited)")
s.msg("c", "gx", "DTMF (secure flow): OTP# + DOB#")
s.msg("gx", "vs", "Data Action: verify (OTP, DOB) — not recorded, never to STT / LLM")
s.msg("vs", "vs", "OTP 5 min, single use, bound to conversationId; DOB; max 3 attempts")
s.msg("vs", "idp", "token exchange (verification-svc client creds + verified assertion)")
s.msg("idp", "vs", "access_token: customer_no, acr=voice_otp_dob, 15 min, no refresh", ret=True)
s.msg("vs", "ts", "store token, TTL = expiry")
s.msg("vs", "gx", "auth_ref (opaque) — or generic failure → ACD queue", ret=True)
s.msg("gx", "vg", "re-open AudioConnector (inputVariables: auth_ref)")
s.note_over("vg", "ts", "End of call → delete token. Failure messages never reveal which factor failed.")
save(s, "B3-voice-verification.drawio")

# ---------------- B4 API request token chain ----------------
s = Sequence("B4 Token chain", [("cl", "Client<br>(app / BFF / voice gw)", "client"), ("eg", "External API GW", "edge"),
                                 ("or", "Orchestrator", "core"), ("idp", "IdP", "sec"), ("mcp", "Account MCP server", "agent"),
                                 ("ig", "Internal API GW", "edge"), ("ps", "Account system", "ext")])
s.text("B4 · One request end to end — access token, token exchange, TLS vs mTLS, ownership check", 40, 10, 1100, 30, 16, True)
s.msg("cl", "eg", "TLS · Authorization: Bearer user token (aud=orchestrator)")
s.msg("eg", "eg", "JWKS signature (kid) · alg · iss · aud · exp · scope · rate limit · strip X-Customer-Id")
s.msg("eg", "or", "forward (mesh mTLS)")
s.msg("or", "or", "re-validate token (zero trust); token → token store; config holds auth_ref only")
s.msg("or", "or", "LLM: account_agent decides get_account_detail(A123)")
s.msg("or", "idp", "token exchange: subject_token=user token, audience=account-api, scope=account:read")
s.msg("idp", "or", "downstream token: aud=account-api, customer_no, act={account_agent}, 5 min", ret=True)
s.msg("or", "mcp", "mTLS (mesh) + downstream token")
s.msg("mcp", "mcp", "validate token: aud, scope, acr")
s.msg("mcp", "ig", "mTLS with client cert (or TLS + app token) + downstream token")
s.msg("ig", "ig", "verify cert (service identity) + JWT (user identity) + quotas")
s.msg("ig", "ps", "GET /accounts/A123")
s.msg("ps", "ps", "ownership: A123.owner == token.customer_no (row-level security)")
s.msg("ps", "ig", "account data (masked fields per role)", ret=True)
s.msg("ig", "mcp", "200", ret=True)
s.msg("mcp", "or", "result (audit: sub + act)", ret=True)
s.msg("or", "cl", "streamed answer", ret=True)
s.note_over("mcp", "ps", "mTLS = WHICH SERVICE is calling (service level) · access token = WHICH USER and WHAT is allowed (user level)", zone="sec")
save(s, "B4-token-chain.drawio")

# ---------------- B5 Step-up ----------------
s = Sequence("B5 Step-up", [("u", "Customer", "client"), ("app", "App / voice gateway", "client"), ("eg", "API GW / Orchestrator", "edge"),
                             ("ch", "Change MCP", "agent"), ("idp", "IdP", "sec")])
s.text("B5 · Step-up authentication before a sensitive action (RFC 9470)", 40, 10, 900, 30, 16, True)
s.msg("u", "app", "\"Change my registered details\"")
s.msg("app", "eg", "request with current token (auth_time 40 min ago)")
s.msg("eg", "ch", "create_change_draft")
s.msg("ch", "eg", "401 insufficient_user_authentication (acr_values, max_age=300)", ret=True)
s.msg("eg", "app", "step-up required", ret=True)
s.frame("alt  app", "u", "idp", s.y + 20, s.y + 185)
s.y += 25
s.msg("app", "idp", "app: /authorize?acr_values=app_biometric&max_age=300")
s.msg("u", "idp", "fingerprint / face")
s.msg("idp", "app", "new token (fresh auth_time)", ret=True)
s.y += 30
s.frame("alt  voice", "u", "idp", s.y + 20, s.y + 150)
s.y += 25
s.msg("app", "u", "voice: new SMS OTP → DTMF")
s.msg("app", "idp", "token exchange → fresh token (acr=voice_otp_dob)")
s.y += 30
s.msg("app", "eg", "retry with new token")
s.msg("eg", "ch", "create_change_draft → draft D-901 (human approval next)")
save(s, "B5-step-up.drawio")

# ---------------- C1 Voice account lookup ----------------
s = Sequence("C1 Voice account lookup", [("c", "Caller", "client"), ("gx", "Genesys", "ext"), ("vg", "Voice gateway<br>(VAD · barge-in)", "edge"),
                                         ("sp", "Speech (STT / TTS)<br>Bailian or open source", "model"),
                                         ("or", "Orchestrator<br>(LangGraph)", "core"), ("llm", "Qwen3<br>(Bailian or vLLM)", "model"),
                                         ("mcp", "Account MCP", "agent"), ("core", "Account system<br>(via internal GW)", "ext"), ("kf", "Kafka → notify", "data")],
             gap=175)
s.text("C1 · Voice: \"When does my plan renew?\" (Genesys AudioConnector; cloud or on-prem speech)", 40, 10, 1100, 30, 16, True)
s.msg("c", "gx", "speech")
s.msg("gx", "vg", "AudioConnector audio frames (WSS)")
s.msg("vg", "sp", "streaming STT")
s.msg("sp", "vg", "transcript (end of speech by VAD)", ret=True)
s.msg("vg", "or", "invoke(thread_id=conversationId, auth_ref=None)")
s.msg("or", "llm", "classify (8B, response_format)")
s.msg("llm", "or", "intents=[account_lookup]", ret=True)
s.msg("or", "or", "next: account_agent needs verified; auth level 0 → verify")
s.note_over("c", "or", "Verification in Genesys secure flow (see B3) → session re-opened with auth_ref", zone="sec")
s.msg("or", "llm", "ReAct step: call get_accounts")
s.msg("or", "mcp", "get_accounts (exchanged token)")
s.msg("mcp", "core", "GET /customers/{token.customer_no}/accounts")
s.msg("core", "mcp", "2 plans", ret=True)
s.msg("mcp", "or", "Plan A (…4567), Plan B (…8901)", ret=True)
s.msg("or", "vg", "ask which plan (say or press 1 / 2)", ret=True)
s.msg("c", "gx", "\"the first one\"")
s.msg("gx", "vg", "audio → STT → selection")
s.msg("vg", "or", "selection")
s.msg("or", "mcp", "get_account_detail(…4567)")
s.msg("mcp", "or", "renews 2027-03-15", ret=True)
s.msg("or", "llm", "voice style: ≤ 3 sentences, per-sentence checks")
s.msg("or", "vg", "sentences (streamed)", ret=True)
s.msg("vg", "sp", "streaming TTS")
s.msg("sp", "vg", "audio chunks", ret=True)
s.msg("vg", "gx", "audio back over AudioConnector; barge-in stops playback", ret=True)
s.msg("gx", "c", "playback", ret=True)
s.msg("c", "gx", "hang up")
s.msg("gx", "vg", "session closed")
s.msg("vg", "or", "session end: summary, clear auth_ref, close trace")
s.msg("or", "kf", "session.ended → one post-call message (chat thread / push / SMS)")
save(s, "C1-voice-account-lookup.drawio")

# ---------------- C2 Chat account lookup ----------------
s = Sequence("C2 Chat account lookup", [("u", "Customer", "client"), ("app", "App (logged in)", "client"), ("eg", "External API GW", "edge"),
                                        ("or", "Orchestrator", "core"), ("llm", "Qwen3 (vLLM)", "model"), ("mcp", "Account MCP", "agent"),
                                        ("core", "Account system", "ext")])
s.text("C2 · App / web chat: same brain, different channel adapter", 40, 10, 900, 30, 16, True)
s.msg("u", "app", "type: 我个计划几时续期？")
s.msg("app", "eg", "WSS connect: first message = access token (or SSE + Authorization header)")
s.msg("eg", "eg", "validate JWT (JWKS) · max 1,000 chars · rate limit")
s.msg("eg", "or", "invoke(thread_id=session_id, auth_ref)")
s.msg("or", "llm", "classify → account_lookup")
s.msg("or", "or", "role=customer, auth via SSO (acr=app_biometric) → account_agent")
s.msg("or", "mcp", "get_accounts / get_account_detail (exchanged token)")
s.msg("mcp", "core", "via internal API GW (mTLS + token)")
s.msg("core", "mcp", "Plan B renews 2027-06-30", ret=True)
s.msg("mcp", "or", "result", ret=True)
s.msg("or", "llm", "chat style: full answer + clause links")
s.msg("or", "app", "stream answer over WSS / SSE", ret=True)
s.note_over("u", "or", "Idle 15 min → reminder · 60 min → session closed · auth idle 15 min → step-up before personal data")
save(s, "C2-chat-account-lookup.drawio")

# ---------------- C3 Cancellation ----------------
s = Sequence("C3 Cancellation", [("c", "Customer<br>(voice or chat)", "client"), ("or", "Orchestrator", "core"), ("llm", "Qwen3-32B", "model"),
                               ("mcp", "Account MCP", "agent"), ("rag", "RAG", "agent"), ("task", "Task service", "core"),
                               ("cs", "Human agent<br>(staff SSO)", "client"), ("core", "Account system", "ext")])
s.text("C3 · Cancellation — AI explains and quotes (read-only); request goes to a human; refund never via AI", 40, 10, 1200, 30, 16, True)
s.msg("c", "or", "\"I want to cancel my plan\"")
s.msg("or", "or", "intent=cancellation → needs verified (OTP + DOB / SSO)")
s.msg("or", "mcp", "get_cancellation_quote(plan) — read only")
s.msg("mcp", "core", "quote")
s.msg("core", "mcp", "refund amount, early-termination fee", ret=True)
s.msg("or", "rag", "clauses: cancellation terms, benefits lost, fees")
s.msg("or", "llm", "explain consequences + quote (with citations, no advice to cancel)")
s.msg("or", "c", "refund $…, benefits end, a fee applies — still want to proceed?", ret=True)
s.msg("c", "or", "yes")
s.msg("or", "task", "create cancellation request task T-7120 (idempotency key)")
s.msg("or", "c", "voice: transfer to Genesys ACD queue + participant data; chat: hand over thread", ret=True)
s.msg("task", "cs", "task + summary + verified identity level (screen pop)")
s.msg("cs", "c", "retention conversation, confirm identity per company process")
s.msg("cs", "core", "submit cancellation (staff token, approval rules)")
s.msg("core", "c", "refund to registered account + notification", ret=True)
s.note_over("or", "cs", "AI boundary: quote + explain + create request. Confirmation, refund and changing bank account stay human.", zone="sec")
save(s, "C3-cancellation.drawio")

# ---------------- C4 Approval (account change) ----------------
s = Sequence("C4 Approval", [("c", "Customer", "client"), ("or", "Orchestrator<br>(LangGraph)", "core"), ("ch", "Change MCP", "agent"),
                              ("pg", "Postgres<br>checkpoint", "data"), ("ap", "Approver<br>(staff SSO)", "client"), ("as", "Approval service", "core"),
                              ("idp", "IdP", "sec"), ("core", "Account system<br>(internal GW)", "ext"), ("kf", "Kafka → notify", "data")])
s.text("C4 · Account change — draft, human approval, apply on behalf of the approver", 40, 10, 1100, 30, 16, True)
s.msg("c", "or", "change registered details (verified + step-up done)")
s.msg("or", "ch", "create_change_draft(idempotency_key=T-5521:draft)")
s.msg("ch", "or", "draft D-901 (status: pending)", ret=True)
s.msg("or", "pg", "interrupt() → state saved (no tokens, only authorization facts)")
s.msg("or", "c", "\"Submitted — processed within 2 working days\"", ret=True)
s.note_over("c", "pg", "Task T-5521 stores customer_id, requested_by, request + step-up evidence. No token of any kind.", zone="sec")
s.msg("c", "or", "session ends (hang-up / chat idle)")
s.msg("or", "or", "delete customer token (auth_ref) — not needed again")
s.note_over("c", "kf", "… hours / days later …")
s.msg("ap", "as", "approve D-901 (approver's own token, role=approver)")
s.msg("as", "as", "check role · approver ≠ drafter (SoD) · draft still valid")
s.msg("as", "idp", "token exchange on behalf of approver: aud=account-change-api, scope=account:change")
s.msg("idp", "as", "token (sub=U123, act=executor)", ret=True)
s.msg("as", "core", "execute stored draft D-901 (complete, versioned API request; mTLS + approver token) — customer_id from the task; core checks assignment + limits")
s.msg("core", "as", "applied", ret=True)
s.msg("as", "pg", "audit: requested_by=customer · approved_by=U123 · executed_by=U123 (act=executor)")
s.msg("as", "kf", "task.updated (completed)")
s.note_over("or", "as", "No old graph is needed to execute: a release deployed during the pause can't break it. Command(resume) only if the session is still open, to tell the customer.", zone="core")
s.msg("kf", "c", "SMS / push: change completed", ret=True)
save(s, "C4-approval-account-change.drawio")

# ---------------- C5 Orders: history lookup + place order ----------------
s = Sequence("C5 Orders", [("c", "Customer<br>(chat / voice)", "client"), ("or", "Orchestrator<br>(LangGraph)", "core"), ("om", "Order MCP", "agent"),
                            ("rc", "Redis-cache", "data"), ("os", "Order service<br>(internal GW)", "ext"), ("ar", "Order archive<br>(> 90 days)", "data")])
s.text("C5 · Orders — history lookup, then place order with quote → confirm → commit", 40, 10, 1100, 30, 16, True)
s.note_over("c", "ar", "Customer verified · customer_id comes from the token's sub, never a tool argument", zone="sec")
s.msg("c", "or", "\"The headphones I bought last March?\"")
s.msg("or", "om", "search_order_history(keyword=headphones, date_range=2025-03, limit≤5)")
s.msg("om", "os", "GET /customers/me/orders:search?q=headphones&from=…&to=…")
s.msg("os", "ar", "older than 90 days → archive query")
s.msg("ar", "os", "matches", ret=True)
s.msg("os", "om", "2 orders (summaries only)", ret=True)
s.msg("om", "rc", "cache: customer + session + query hash, 5 min")
s.msg("om", "or", "ORD-1182 · ORD-1190 (id, date, amount, status, first item)", ret=True)
f0 = s.y + 20; s.y += 25
s.msg("or", "c", "chat: UI renders order cards from tool data (not LLM text)", ret=True)
s.msg("or", "c", "voice: \"Two orders in March — the 12th or the 28th?\"", ret=True)
s.frame("alt  channel", "c", "or", f0, s.y + 20); s.y += 30
s.msg("c", "or", "\"Order the same again\"")
s.msg("or", "om", "quote_order(items of ORD-1190, address_ref=default)")
s.msg("om", "os", "POST /orders:quote")
s.msg("os", "om", "Q-77: $899, delivery Fri, confirmation_token (5 min, bound to customer + payload hash)", ret=True)
s.msg("or", "c", "\"$899, delivered Friday to your default address — confirm?\" (button / say yes / press 1)", ret=True)
s.msg("c", "or", "explicit \"Yes\"")
s.msg("or", "om", "place_order(confirmation_token)  — no other parameters")
s.msg("om", "os", "POST /orders  Idempotency-Key: T-6001:place")
s.msg("os", "os", "verify token signature · payload hash · expiry · ownership")
s.msg("os", "om", "ORD-1203 created", ret=True)
s.msg("om", "rc", "purge this customer's order cache")
s.msg("or", "c", "\"Order ORD-1203 placed\" + order card", ret=True)
s.note_over("c", "ar", "After confirmation the LLM can't change anything: commit carries only the token; a replay returns the same order", zone="sec")
save(s, "C5-orders.drawio")

# ---------------- C6 Refund ----------------
s = Sequence("C6 Refund", [("c", "Customer", "client"), ("or", "Orchestrator<br>(LangGraph)", "core"), ("rag", "RAG<br>(return policy)", "agent"),
                            ("om", "Order MCP", "agent"), ("re", "Refund rules<br>engine", "core"), ("ap", "Approver<br>(staff SSO)", "client"),
                            ("pay", "Payments", "ext"), ("kf", "Kafka → notify", "data")])
s.text("C6 · Refund — policy via RAG, eligibility by rules, auto-approval behind a switch, otherwise human approval", 40, 10, 1300, 30, 16, True)
s.msg("c", "or", "\"The headphones from ORD-1203 are faulty — I want a refund\"")
s.msg("or", "rag", "search_policy(\"return faulty item\")")
s.msg("rag", "or", "Return policy v2026.3 §4: 30 days; faulty → full refund (citations)", ret=True)
s.msg("or", "om", "check_refund_eligibility(ORD-1203)")
s.msg("om", "re", "window · item state · amount · prior refunds · risk flags")
s.msg("re", "om", "eligible · $899 · original payment method only", ret=True)
s.msg("or", "c", "explains the policy with citations — \"Submit a refund request?\"", ret=True)
s.msg("c", "or", "explicit \"Yes\"")
s.msg("or", "om", "request_refund(ORD-1203, reason=faulty)  Idempotency-Key: T-6002:refund")
s.msg("om", "re", "decide(amount, risk, refund.auto_approve)")
f1 = s.y + 20; s.y += 25
s.msg("re", "pay", "refund $899 to the original payment method")
s.msg("re", "om", "R-55 approved automatically", ret=True)
s.msg("or", "c", "\"Refund approved — 3–5 working days\"", ret=True)
s.frame("alt  switch ON and amount ≤ threshold", "c", "pay", f1, s.y + 20); s.y += 30
f2 = s.y + 20; s.y += 25
s.msg("re", "om", "R-55 pending approval (draft)", ret=True)
s.msg("or", "c", "\"Submitted — reviewed within 2 working days\"", ret=True)
s.msg("ap", "re", "approve R-55 (approver's own token; approver ≠ requester)")
s.msg("re", "pay", "refund to the original payment method")
s.frame("alt  switch OFF, above threshold, or risk flag", "c", "pay", f2, s.y + 20); s.y += 30
s.msg("re", "kf", "refund.completed")
s.msg("kf", "c", "SMS / push: refund issued", ret=True)
s.note_over("c", "kf", "The AI never decides eligibility or approves. Money only returns to the original payment method. Switch + threshold live in config/policy.yaml (reviewed PR).", zone="sec")
save(s, "C6-refund.drawio")

# ---------------- C7 Customer satisfaction ----------------
s = Sequence("C7 CSAT", [("c", "Customer", "client"), ("gx", "Genesys<br>(Architect survey flow)", "ext"), ("app", "App / Web /<br>WhatsApp", "client"),
                          ("or", "Orchestrator<br>(LangGraph)", "core"), ("kf", "Kafka", "data"), ("sv", "Survey service", "core"),
                          ("lf", "Langfuse · Grafana", "obs"), ("cs", "Staff<br>(callback · complaints)", "client")])
s.text("C7 · Customer satisfaction — one survey service for voice and app; questions are fixed, never LLM-generated", 40, 10, 1300, 30, 16, True)
s.msg("or", "kf", "session.ended (channel, handled_by: ai / ai→human / human, release, intents)")
s.msg("kf", "sv", "session.ended")
s.msg("sv", "sv", "invite? 7-day cap · call ≥ 20 s · not in complaint flow → survey_token (single use, 24 h, bound to session)")
f = s.y + 20; s.y += 25
s.msg("or", "gx", "AudioConnector ends with output variable survey=true")
s.msg("gx", "c", "fixed prompt: \"Rate us 1 to 5\" · \"Resolved? Press 1 yes, 2 no\"", ret=True)
s.msg("c", "gx", "DTMF 4 · 1")
s.msg("gx", "sv", "Data Action: conversationId, score=4, resolved=yes")
s.frame("alt  voice, AI handled", "c", "sv", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("gx", "c", "at transfer: \"Please stay on the line after the call to rate us\"", ret=True)
s.msg("c", "gx", "stays after the agent hangs up → same DTMF survey flow")
s.msg("sv", "c", "hung up instead → SMS link with survey_token", ret=True)
s.frame("alt  voice, handed to a human", "c", "sv", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("sv", "app", "show rating card (fixed UI component: stars + resolved + optional comment)")
s.msg("c", "app", "2 stars · not resolved · comment")
s.msg("app", "sv", "POST /surveys/{survey_token}  (single use)")
s.msg("sv", "c", "no rating → one push reminder only", ret=True)
s.frame("alt  app / web / WhatsApp", "c", "sv", f, s.y + 20); s.y += 30
s.msg("sv", "sv", "redact PII in comment (untrusted text) · store survey_responses")
s.msg("sv", "kf", "survey.submitted")
s.msg("kf", "lf", "Langfuse score on the session trace (release · prompt · model) · Grafana by channel / intent / release / handled_by")
f = s.y + 20; s.y += 25
s.msg("sv", "cs", "callback task (within 2 working days) + annotation queue")
s.msg("sv", "cs", "complaint keywords → formal complaints process")
s.frame("alt  score ≤ 2 or not resolved", "c", "cs", f, s.y + 20); s.y += 30
s.note_over("c", "cs", "Survey response rates are 10–20%: always read alongside implicit signals on 100% of sessions — handoff rate, repeat contact within 7 days, abandonment, judge-scored sentiment", zone="obs")
save(s, "C7-csat.drawio")

# ---------------- C8 Human handoff ----------------
s = Sequence("C8 Handoff", [("c", "Customer", "client"), ("or", "Orchestrator<br>(LangGraph)", "core"), ("hs", "Handoff service<br>(Postgres)", "core"),
                             ("gx", "Genesys<br>(ACD · messaging)", "ext"), ("ac", "Agent console<br>(agent desktop)", "client"),
                             ("bff", "Console BFF<br>(staff SSO)", "edge"), ("sor", "CRM · tasks ·<br>annotation queue", "data")])
s.text("C8 · Human handoff — context packet, routing, agent console, wrap-up", 40, 10, 1100, 30, 16, True)
s.msg("c", "or", "\"I want to talk to a person\"  (or any other trigger)")
s.msg("or", "or", "trigger: request · low retrieval · Appendix A limit · sentiment · 3rd repeat · out of scope · verification or ASR failure")
s.msg("or", "hs", "create packet: system facts (assurance, tasks, tool calls, citations) + 3-line summary (8B, fixed schema, marked AI)")
s.msg("hs", "or", "handoff_id H-311", ret=True)
f = s.y + 20; s.y += 25
s.msg("or", "gx", "end AudioConnector: next=handoff · participant data {handoff_id, intent, language, priority} — IDs only")
s.msg("gx", "c", "\"Connecting you to a colleague — about 2 minutes\"", ret=True)
s.frame("alt  voice", "c", "gx", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("or", "gx", "transfer the chat thread to the agent queue (handoff_id)")
s.frame("alt  chat", "c", "gx", f, s.y + 20); s.y += 30
s.msg("gx", "ac", "skills-based routing (intent · language · priority) → agent accepts")
s.msg("ac", "bff", "GET /handoffs/H-311  (agent's own SSO token)")
s.msg("bff", "bff", "check: role cs_agent · MFA · interaction assigned to this agent (Genesys)")
s.msg("bff", "hs", "fetch packet + full bot transcript")
s.msg("hs", "bff", "packet", ret=True)
s.msg("bff", "sor", "customer overview + open tasks (agent token, masked per role)")
s.msg("sor", "bff", "data", ret=True)
s.msg("bff", "ac", "render panels 1–7 · audit: agent U77 viewed H-311", ret=True)
s.note_over("c", "sor", "\"Verified by AI 10:02 (voice_otp_dob)\" is shown, so no re-verification in the same call. The customer's token is never passed to the agent.", zone="sec")
s.msg("ac", "c", "human conversation (voice / chat)")
s.msg("ac", "bff", "wrap-up: AI-drafted notes → agent edits · disposition · feedback on the AI (reason code)")
s.msg("bff", "sor", "notes → CRM · feedback → annotation queue → golden set")
s.msg("bff", "bff", "revoke access to this customer 30 min after wrap-up")
s.note_over("c", "sor", "No hand-back to the AI. Phase 2 agent assist only suggests; the AI never sends on the agent's behalf.", zone="obs")
save(s, "C8-handoff.drawio")

# ---------------- D1 Events & cross-channel ----------------
s = Sequence("D1 Events", [("or", "Orchestrator", "core"), ("kf", "Kafka", "data"), ("nt", "Notification svc", "core"),
                            ("crm", "CRM sync", "ext"), ("au", "Audit (WORM)", "sec"), ("bi", "Reporting", "obs"), ("cu", "Customer devices", "client")])
s.text("D1 · Events and cross-channel sync — clients never touch Kafka; events carry IDs, never tokens", 40, 10, 1100, 30, 16, True)
s.msg("or", "kf", "session.ended {customer_id, task_ids, channel, release}")
s.msg("kf", "nt", "consume")
s.msg("nt", "nt", "chat enabled? → message in chat thread; else push; no app → SMS")
s.msg("nt", "cu", "one post-call message (generic lock-screen text)", ret=True)
s.msg("kf", "crm", "consume → write interaction summary")
s.msg("kf", "au", "consume → append-only audit")
s.msg("kf", "bi", "consume → resolution / handoff / repeat-contact metrics")
s.note_over("or", "cu", "Backend = single source of truth (tasks, documents, status). No live transcript or recording links in the app.")
save(s, "D1-events-cross-channel.drawio")

# ---------------- D2 Release & rollback ----------------
s = Sequence("D2 Release", [("dev", "Engineer / PR", "client"), ("ci", "CI: golden set", "core"), ("cmp", "Compliance", "sec"),
                             ("gw", "Gateway weights", "edge"), ("old", "Release N (running)", "data"), ("new", "Release N+1", "model"),
                             ("mon", "Monitoring", "obs")])
s.text("D2 · Release bundle, golden-set gate, canary and rollback", 40, 10, 900, 30, 16, True)
s.msg("dev", "ci", "PR: prompt / model / retrieval / KB snapshot / agents.yaml / policy.yaml")
s.msg("ci", "ci", "golden set: binding commitments = 0, privilege escalation = 0, no regressions")
s.msg("ci", "cmp", "diff report")
s.msg("cmp", "ci", "sign-off", ret=True)
s.msg("ci", "new", "deploy release N+1 (immutable image tag)")
s.msg("gw", "new", "5% sticky by session_id / call_id")
s.msg("gw", "old", "95%")
s.msg("mon", "mon", "compare 24–48 h: citation failures, handoff, latency, cost")
s.frame("alt  red line hit", "gw", "mon", s.y + 20, s.y + 140)
s.y += 25
s.msg("mon", "gw", "auto rollback: weight → 0 (old still running)")
s.msg("gw", "old", "100% (seconds, no redeploy)")
s.y += 30
s.msg("gw", "new", "else 25% → 50% → 100%; free old GPUs after ~1 week")
save(s, "D2-release-rollback.drawio")
print("sequences done")

# ---------------- C9 WeChat channel (mainland China region profile) ----------------
s = Sequence("C9 WeChat channel", [("c", "Customer<br>(WeChat)", "client"), ("wx", "WeChat Customer Service<br>(Tencent platform)", "ext"),
                                   ("ad", "Messaging adapter", "edge"), ("bd", "Binding service<br>+ IdP", "sec"),
                                   ("or", "Orchestrator<br>(LangGraph)", "core"), ("mcp", "Account MCP", "agent"),
                                   ("hu", "Human agent<br>(WeCom reception)", "client")])
s.text("C9 · WeChat channel (mainland China region profile) — official Customer Service API, account binding once, minimal data, handoff", 40, 10, 1300, 30, 16, True)
s.note_over("c", "hu", "Everything on our side runs in the mainland region: adapter, core, models (Qwen on Bailian mainland or vLLM on-prem). Only official WeChat APIs.", zone="core")
f = s.y + 20; s.y += 25
s.msg("c", "wx", "opens the service chat (link or QR code in WeChat), sends a question")
s.msg("wx", "ad", "callback event (encrypted)")
s.msg("ad", "ad", "verify msg_signature · decrypt · reply 200 at once")
s.msg("ad", "wx", "sync_msg(cursor, token)")
s.msg("wx", "ad", "messages: external_userid, msgid, text", ret=True)
s.msg("ad", "ad", "dedupe by msgid · process in the background")
s.msg("ad", "bd", "binding for this external_userid?")
s.msg("bd", "ad", "none → anonymous", ret=True)
s.msg("ad", "or", "turn {channel: wechat, assurance: anonymous}")
s.msg("or", "ad", "general answer from RAG, with citations, no personal data", ret=True)
s.msg("ad", "wx", "send_msg (inside the reply window)")
s.msg("wx", "c", "answer", ret=True)
s.frame("first contact", "c", "or", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("c", "wx", "\"我的保单什么时候续期？\" (account question)")
s.msg("wx", "ad", "callback → sync_msg (as above)")
s.msg("ad", "or", "turn {anonymous}")
s.msg("or", "ad", "needs a verified customer → send the binding link", ret=True)
s.msg("ad", "wx", "send_msg: link card to the binding page")
s.msg("c", "bd", "opens the page inside WeChat (one-time bind_token, 10 min)")
s.msg("bd", "bd", "silent WeChat web authorisation → opener's unionid must match the chat's external_userid (blocks forwarded links)")
s.msg("c", "bd", "OIDC login at our IdP (SMS OTP to the registered mobile) · PIPL consent")
s.msg("bd", "bd", "bind external_userid + unionid ↔ customer_id · assurance: verified-low · audit")
s.msg("bd", "c", "SMS to the registered mobile: \"Linked to WeChat. Not you? Unlink.\"", ret=True)
s.msg("bd", "c", "\"Bound — go back to the chat\"", ret=True)
s.frame("bind once", "c", "or", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("wx", "ad", "next message (callback → sync_msg)")
s.msg("ad", "bd", "binding?")
s.msg("bd", "ad", "customer_id, verified-low", ret=True)
s.msg("ad", "or", "turn {assurance: verified-low, customer_id from the binding, never from the model}")
s.msg("or", "mcp", "get renewal date (token exchange; customer_id from the binding)")
s.msg("mcp", "or", "summary, masked", ret=True)
s.msg("or", "ad", "\"续期日是 3 月 1 日，详情已发到 App。\" — short answer only", ret=True)
s.msg("ad", "wx", "send_msg")
s.note_over("c", "mcp", "Changes and sensitive details need step-up in the app or web page, never in chat text. WeChat IDs alone never authorise anything; no tokens ever go to WeChat.", zone="sec")
s.frame("bound customer", "c", "mcp", f, s.y + 20); s.y += 30
f = s.y + 20; s.y += 25
s.msg("or", "ad", "handoff (handoff_id, reason)")
s.msg("ad", "wx", "service_state/trans → human reception")
s.msg("wx", "hu", "conversation assigned in WeCom")
s.msg("hu", "or", "agent console loads the packet by handoff_id (staff SSO)")
s.frame("handoff", "c", "hu", f, s.y + 20); s.y += 30
save(s, "C9-wechat-channel.drawio")
