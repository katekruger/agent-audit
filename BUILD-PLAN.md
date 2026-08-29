# agent-audit — Build Plan

**A portable record binding what an agent proposed, what a human decided, what executed, and what it cost — as an OpenTelemetry semantic convention plus a thin emitter.**

Owner: Kate Kruger (`github.com/katekruger`)
Status: not started
Plan version: 1.0 — 28 Aug 2026
Research current as of: 28 Aug 2026

---

## 0. Handover context — read this first

This is the highest-leverage and highest-risk of the five projects, because the space moved *while the research was running*. Six things a fresh session must know:

1. **Do not build a wire protocol.** MCP's SEP-2577 (status: Final, revision `2026-07-28`) deprecates Roots, Sampling and Logging, and its stated rationale names OpenTelemetry as the correct alternative to an application-protocol logging channel. A proposed `audit/*` JSON-RPC method would be rejected on exactly those grounds. **Build a semantic convention, not a protocol.**

2. **The carrier is the OpenTelemetry Log Data Model, which is Stable** — unlike every `gen_ai.*` span attribute, all 72 of which are still `Development`. A LogRecord with a non-empty `EventName` is an Event, carries `TraceId`/`SpanId` so the record binds to the exact span it authorized, and gets every OTel exporter and backend for free.

3. **There is a direct competitor published nine days before this plan.** `draft-sharif-agent-audit-trail-01` (IETF, 2026-08-19, individual submission, expires 2027-02-19) already has `record_phase: pre_execution|post_execution|concurrent` and `outcome: success|failure|timeout|denied|escalated`. **Engage the author and align field names rather than shipping a fourth competing vocabulary.** Its gaps — no cost accounting, no approver identity, no MCP binding — are your three openings.

4. **There is a large platform competitor.** `microsoft/agent-governance-toolkit` — MIT, 6.1k stars, 5 languages, 10 RFC-2119 specs, ~992 conformance tests — already has `require_approval` policy actions, a Merkle audit, and a "Decision BOM." **Position explicitly as "the record, not the enforcer."** If you cannot articulate why someone uses `agent-audit` *alongside* AGT rather than instead of it, do not build this.

5. **The `agent-audit` name is taken on PyPI** (v0.19.2, MIT, a static security analyzer for AI agents). npm is free. **Pick a different Python distribution name before writing code.**

6. **Nothing anywhere records the cost of a rejected proposal.** Every observability platform models cost as tokens × model price. None can express the cost of inference you burned proposing something a human then denied. That metric is novel, demo-able, and is probably your best single piece of launch collateral.

---

## 1. The gap — occupied vs open

### Occupied. Do not build these.

| Thing | Owner |
|---|---|
| Wire transport for records | **OpenTelemetry** — and MCP explicitly deferred to it |
| Pause/resume mechanics for a gate | MCP **Tasks** extension (`input_required`), LangGraph `interrupt()`, Temporal |
| The ask-a-human round trip | MCP **elicitation** via MRTR |
| Post-hoc human scoring of outputs | Langfuse scores/annotation queues, OpenInference `annotation.*` |
| Policy engine + enforcement runtime | **Microsoft AGT** |
| Approval routing UX (Slack/email) | HumanLayer — though it has largely vacated OSS |
| LLM token → dollar cost | OpenInference `llm.cost.*`, every platform |
| Client-side permission decisions | Claude Code hooks `permissionDecision` |

### Open. This is the project.

1. **A portable record binding proposed → decided → executed as one correlated unit.** Kubernetes audit's staged model (`RequestReceived` / `ResponseComplete`, correlated by `auditID`) is the only real precedent and nobody has ported it to agents. MCP's `ElicitResult` and LangGraph's `Command(resume=)` both throw the decision away.
2. **Approver identity as a first-class field.** Not `annotator_kind: HUMAN` — an actual principal, with on-behalf-of (K8s `impersonatedUser`), timestamp, and the policy in force. LangGraph lacks it, the IETF draft lacks it, OTel lacks it.
3. **Cost of business actions, and cost of rejected proposals.** Nothing anywhere models either.
4. **An MCP binding.** OTel's `mcp.*` conventions are four attributes deep (`mcp.method.name`, `mcp.protocol.version`, `mcp.resource.uri`, `mcp.session.id`) and **lag the spec by two revisions** — their example value is `2025-06-18`. Contributing coverage here is low-hanging and buys standing.
5. **Server-side portability.** Claude Code hooks are client-side and Anthropic-specific; AGT is enforcement-side. A record an *MCP server* emits, that survives the client, is unclaimed.

### The one-sentence wedge

> The most widely-deployed human-in-the-loop gate in the ecosystem records the decision but not the decider.

---

## 2. Positioning

**One line:** the record, not the enforcer.

**How it relates to what exists:**

| Layer | Owner | `agent-audit`'s relationship |
|---|---|---|
| Policy & enforcement | Microsoft AGT, OPA, Cedar | **Emits into** `agent-audit` |
| Gate mechanics | MCP Tasks, LangGraph, Temporal | **Rides on** — never competes |
| Ask-a-human | MCP elicitation | **Records the outcome of** |
| Transport | OpenTelemetry | **Is a convention over** |
| Backends | Langfuse, Phoenix, Braintrust, any OTLP sink | **Lands in**, unchanged |

**What it is NOT:** a policy engine, a runtime, an approval UI, a sandbox, or a new backend.

**Explicit anti-goal:** if `agent-audit` ever needs its own storage, its own server, or its own dashboard to be useful, the design has failed.

---

## 3. Scope

### v0.1 — the convention (target: 2 weeks)

The deliverable is **a specification document plus a JSON Schema**, not a library. Ship the vocabulary first, with a reference emitter proving it works.

| In | Out |
|---|---|
| The three-phase event model, specified | Multi-language SDKs |
| JSON Schema, versioned, immutably URL'd | A UI |
| Python emitter (~200 lines over the OTel SDK) | Policy evaluation |
| Claude Code hooks integration (zero-code install path) | Storage |
| A worked example: proposal → denial → cost of the denial | Enforcement |

### v0.2 — the MCP binding (target: +2 weeks)

- An MCP server middleware/decorator that emits the record automatically
- Reference integration into one of Kate's existing servers (`n8n-operator` is the obvious pick — it already has the approval semantics, just not the portable record)
- CloudEvents envelope for cross-boundary hops
- A **PR to `open-telemetry/semantic-conventions-genai`** extending `mcp.*` coverage

### v0.3 — the standard play (target: +4 weeks)

- TypeScript emitter
- OpenLineage-style namespaced facets so a Salesforce connector can add CRM-specific fields without forking the schema
- A `cost-of-denied-proposals` reporter — the launch metric
- Engagement with the IETF draft author toward field-name alignment

### Explicit non-goals, permanently

- A `audit/*` JSON-RPC method or any MCP protocol change.
- Cryptographic signing and hash chains in v1. The IETF draft has `prev_hash`/`signature`; adopt them only if a real user needs tamper-evidence. Do not lead with it.
- Restating `gen_ai.usage.*` or `llm.cost.*`. **Reuse them.**

---

## 4. The event model — specified

Three OTel LogRecord Events, correlated by one `agent_audit.action.id`, carrying `TraceId`/`SpanId` to bind to the authorized span.

| `EventName` | When | Required |
|---|---|---|
| `agent_audit.proposed` | The agent has determined an action and is about to seek authorization | action id, actor, target, arguments (level-gated), declared annotations |
| `agent_audit.decided` | A decision was reached — by a human, a policy, or a timeout | action id, decision, principal, policy in force, latency |
| `agent_audit.executed` | The action ran, or was abandoned | action id, outcome, effect, cost |

**Not every action produces all three.** An auto-allowed read produces `proposed` + `executed`. A denial produces `proposed` + `decided` and **no** `executed` — and that asymmetry is precisely what makes denied-proposal cost computable.

### Core attributes (v0.1)

```
agent_audit.action.id            string   correlates the three events (UUIDv4)
agent_audit.action.phase         string   proposed | decided | executed
agent_audit.schema_url           string   immutable, versioned
agent_audit.level                string   metadata | request | request_response   ← from K8s
```

**Actor** — who proposed:
```
agent_audit.actor.id             string   reuse gen_ai.agent.id where present
agent_audit.actor.type           string   agent | human | policy | system
agent_audit.actor.on_behalf_of   string   ← K8s impersonatedUser. Auditors ask this first.
```

**Target** — what was acted on:
```
agent_audit.target.system        string   e.g. salesforce, n8n, gmail
agent_audit.target.resource      string
agent_audit.target.operation     string
agent_audit.target.arguments     any      gated by agent_audit.level
```

**Declared vs effective** — the MCP annotations trap:
```
agent_audit.declared.read_only       boolean   ← MCP readOnlyHint, recorded as UNTRUSTED INPUT
agent_audit.declared.destructive     boolean   ← MCP destructiveHint (spec default: TRUE)
agent_audit.declared.idempotent      boolean
agent_audit.declared.open_world      boolean   ← spec default: TRUE
agent_audit.effective.read_only      boolean   ← what the policy actually concluded
```
The MCP spec states twice that all `ToolAnnotations` are **hints**, not guaranteed faithful, and that clients should never make decisions based on annotations from untrusted servers. So the record captures both: the hint as an untrusted input, and the effective policy conclusion as the justification. **Never let the hint be the justification.** CloudTrail's `readOnly` is recorded as *fact*; MCP's `readOnlyHint` is a *claim*. That contrast is a good line for the README.

**Decision:**
```
agent_audit.decision             string   allow | deny | defer | cancel | timeout | auto_allow | auto_deny
agent_audit.decision.reason      string
agent_audit.decision.principal.id    string
agent_audit.decision.principal.type  string   human | policy | timeout | default
agent_audit.decision.policy.id       string
agent_audit.decision.policy.version  string
agent_audit.decision.latency_ms      int
```

The decision enum must express both upstream vocabularies:

| Source | Values | Maps to |
|---|---|---|
| MCP `ElicitResult.action` | `accept` / `decline` / `cancel` | `allow` / `deny` / `cancel` |
| Claude Code `permissionDecision` | `allow` / `deny` / `deferToUser` | `allow` / `deny` / `defer` |
| IETF draft `outcome` | `denied` / `escalated` | `deny` / `defer` |

**Execution:**
```
agent_audit.outcome              string   success | failure | timeout | not_executed
agent_audit.not_executed_reason  string   denied | cancelled | expired | superseded
agent_audit.effect.records_changed   int
agent_audit.effect.reversible        boolean
agent_audit.effect.undo_token        string
```

**Cost — the novel part:**
```
agent_audit.cost.amount          double   monetary or unit quantity
agent_audit.cost.currency        string   ISO 4217, or null for non-monetary
agent_audit.cost.unit            string   usd | api_calls | credits | seat_hours | quota
agent_audit.cost.component       string   inference | action | total
agent_audit.cost.wasted          boolean  TRUE when the proposal was denied  ← the launch metric
```
For the inference component, **reuse `gen_ai.usage.input_tokens` / `.output_tokens` and OpenInference's `llm.cost.total` / `.prompt` / `.completion`** rather than restating them. OpenInference is Apache-2.0, so the vocabulary can be lifted freely (unlike Phoenix itself, which is Elastic License 2.0). Note OpenInference's cost fields are USD-implicit with no currency field — `agent_audit.cost.currency` fills that gap.

### The `level` dial

Borrowed from Kubernetes audit policy: `metadata` / `request` / `request_response`. Whether you record full CRM request and response bodies or only metadata is a compliance and PII decision that must be **policy, not a hardcoded schema choice**. K8s got this right in 2017; the agent space has not caught up.

### Facets

Borrowed from OpenLineage: a small stable core plus namespaced, independently versioned, immutably-schema'd extensions that can graduate into the standard. A Salesforce connector adds `agent_audit.facet.salesforce.*` with its own `_schemaURL` and never forks the core schema.

---

## 5. Feature inventory, scoped

| # | Feature | Fills what gap | Effort | Verdict |
|---|---|---|---|---|
| 1 | The three-phase event model + JSON Schema | The entire project | 4d | **v0.1** |
| 2 | Decision enum expressing MCP + Claude Code + IETF vocabularies | Interop, not a fourth dialect | 1d | **v0.1** |
| 3 | Approver identity + `on_behalf_of` | Nobody has this | 1d | **v0.1** |
| 4 | Declared-vs-effective annotation capture | The hints-are-not-facts problem | 1d | **v0.1** |
| 5 | `level` dial (metadata / request / request_response) | PII/compliance is policy, not schema | 1d | **v0.1** |
| 6 | Cost model with currency + non-monetary units | Nothing anywhere has this | 2d | **v0.1** |
| 7 | `cost.wasted` on denied proposals | **The launch metric** | 1d | **v0.1** |
| 8 | Python emitter over the OTel SDK | Proves the convention works | 3d | **v0.1** |
| 9 | Claude Code hooks integration | Zero-code install; hooks already fire | 2d | **v0.1** |
| 10 | Worked example + a 20s terminal GIF | Distribution | 1d | **v0.1** |
| 11 | MCP server middleware/decorator | Server-side portability — unclaimed | 4d | v0.2 |
| 12 | Reference integration into `n8n-operator` | Dogfooding; also proves the abstraction | 2d | v0.2 |
| 13 | CloudEvents envelope | Cross-boundary hops | 2d | v0.2 |
| 14 | PR to `semantic-conventions-genai` extending `mcp.*` | Standing in the standards body | 3d | v0.2 |
| 15 | TypeScript emitter | Reach | 3d | v0.3 |
| 16 | OpenLineage-style facets | Extension without forking | 3d | v0.3 |
| 17 | `cost-of-denied-proposals` reporter | Launch collateral | 2d | v0.3 |
| 18 | Langfuse / Phoenix / Braintrust verification | Prove records land in real backends unmodified | 2d | v0.3 |
| 19 | AGT interop doc + emitter adapter | Turns the competitor into a consumer | 3d | v0.3 |
| 20 | Hash chain + signing (`prev_hash`, ECDSA P-256) | Tamper-evidence, per the IETF draft | 4d | Deferred — only on real demand |
| 21 | LangGraph `interrupt()` adapter | The gap named in one sentence | 2d | v0.3 |
| 22 | Temporal / Inngest adapters | Durable pending-approval substrates | 3d | Deferred |
| 23 | A dashboard | Anti-goal | — | **Never** |

---

## 6. Integration targets, ranked

### 1. Claude Code hooks — the best first target

The richest event vocabulary anyone has shipped, and it maps one-to-one onto the three phases:

| Hook | Phase |
|---|---|
| `PreToolUse` | `proposed` |
| `PermissionRequest` / `PermissionDenied` | `decided` |
| `PostToolUse` / `PostToolUseFailure` | `executed` |

`PreToolUse` input already carries `session_id`, `prompt_id`, `cwd`, `permission_mode`, `agent_id`, `agent_type`, `tool_name`, `tool_input`, `tool_use_id`. Output carries `hookSpecificOutput.permissionDecision` ∈ `allow | deny | deferToUser` plus `permissionDecisionReason`.

**There is no built-in persistent audit log** — the docs explicitly tell you to write your own hook or POST to an external service. HTTP hooks with `allowedEnvVars` give a zero-code install path. This is a ready-made distribution channel.

### 2. MCP Tasks extension

Negotiated as `io.modelcontextprotocol/tasks`. Lifecycle `working` → `input_required` → `completed|failed|cancelled`. `CreateTaskResult` is **durably created before the response is sent**, and the docs name approval gates explicitly as the use case.

**Tasks is the transport for the pause. It is not the record of the decision.** A task is TTL-bounded and disposable; an audit record must outlive it. Clean division of labor — ride on Tasks, never compete.

### 3. MCP elicitation

`ElicitResult.action` ∈ `accept | decline | cancel` is the closest thing in all of MCP to an approval record — and it has **no approver identity, no timestamp, no durable record.** It is an ephemeral RPC result. That is the gap, stated precisely.

Note elicitation now flows through **MRTR** (Multi Round-Trip Requests) because `2026-07-28` made the protocol stateless: server returns `resultType: "input_required"`, client retries with `inputResponses`. Two modes: `form` and `url` (the latter added to keep sensitive data out of the model's context).

### 4. LangGraph

`interrupt(payload)` pauses, `Command(resume=True/False)` approves/rejects, state persisted by the checkpointer against a `thread_id`. **The documentation does not address audit logging or recording who approved.** One adapter, one sentence of positioning.

---

## 7. Competitive posture

### vs. Microsoft AGT (MIT, 6.1k stars)

AGT is a **governance platform**: policy engine (YAML/OPA/Cedar), Agent OS gates, Agent Mesh, sandboxing and privilege rings, kill switches, MCP Security Gateway, ~992 conformance tests across five languages. It already has `require_approval`, tamper-evident records, a Merkle audit, and a "Decision BOM."

**It covers a large fraction of the stated goal. Be honest about that in the README.**

The differentiation must be structural, not feature-level:

| | AGT | agent-audit |
|---|---|---|
| Shape | Platform | **Schema + ~200-line emitter** |
| Requires | Adopting a policy engine and runtime | Nothing |
| Enforces | Yes | **Never** |
| Storage | Its own | **Any OTLP sink you already run** |
| Lock-in | Real | None |
| Answers | "Should this be allowed?" | **"What happened, and what did it cost?"** |

**The test:** AGT should be able to emit `agent_audit` records. If it can, they compose. If your design makes that impossible, the design is wrong.

### vs. `draft-sharif-agent-audit-trail-01`

Published 2026-08-19. Individual submission, no working group, expires 2027-02-19, motivated by EU AI Act Article 12's automatic-recording requirement (effective August 2026).

Its mandatory fields: `record_id`, `timestamp`, `agent_id`, `session_id`, `action_type`, `outcome` (incl. `denied`, `escalated`), `record_phase` (`pre_execution` / `post_execution` / `concurrent`), `parent_record_id`, `prev_hash`. Optional: `signature`, `input_hash`, `output_hash`, `risk_score`, `model_id`, `latency_ms`, `deny_reasons`.

**`record_phase` is literally the proposed-vs-executed axis. `outcome: denied|escalated` is the approval axis.**

Three openings remain — **no cost accounting, no approver identity, no MCP binding** — and an expired-in-six-months individual draft with no WG is not a standard.

**Action: email the author (Raza Sharif, CyberSecAI Ltd) in week one.** Align field names, offer the three missing pieces, cite the draft in your README either way. Shipping a competing vocabulary without contacting him is the single worst move available.

---

## 8. Repo structure

```
agent-audit/                       # npm name is free; PYTHON DIST NAME MUST DIFFER (PyPI taken)
├── README.md                      # positioning vs AGT in the first screen
├── LICENSE                        # Apache-2.0
├── CHANGELOG.md · CONTRIBUTING.md · SECURITY.md
├── spec/
│   ├── SPECIFICATION.md           # RFC 2119 language; THE deliverable
│   ├── schema/
│   │   └── v1/agent-audit.schema.json     # immutable URL, versioned
│   ├── mappings/
│   │   ├── mcp.md                 # elicitation, Tasks, annotations
│   │   ├── claude-code-hooks.md
│   │   ├── ietf-draft-sharif.md   # field-by-field crosswalk
│   │   └── otel-genai.md          # what we reuse vs define
│   └── facets/                    # OpenLineage-style extension registry
├── py/                            # package name TBD — NOT `agent-audit`
│   └── src/.../{emitter,phases,cost,hooks}.py
├── ts/                            # v0.3
├── integrations/
│   ├── claude-code-hooks/         # drop-in hook config + HTTP receiver
│   ├── mcp-middleware/            # v0.2
│   └── langgraph/                 # v0.3
├── examples/
│   ├── denied-proposal/           # the flagship worked example
│   └── n8n-operator/              # dogfooding
└── docs/
    ├── why-not-a-protocol.md      # cites SEP-2577 — the credibility doc
    ├── vs-agent-governance-toolkit.md
    └── cost-of-denied-proposals.md
```

---

## 9. Milestones

| # | Deliverable | Done when |
|---|---|---|
| M0 | **Name decision + IETF author contact** | Python dist name chosen; email sent to the draft author |
| M1 | `SPECIFICATION.md` + JSON Schema v1 | Three phases fully specified with RFC 2119 language |
| M2 | Crosswalk docs | Every MCP, Claude Code and IETF field maps explicitly, including what does not map |
| M3 | Python emitter | Emits valid OTLP LogRecords; validates against the schema in CI |
| M4 | Claude Code hooks integration | A denied tool call produces `proposed` + `decided`, no `executed`, with `cost.wasted=true` |
| M5 | Backend verification | Records land unmodified in a local Langfuse and a local Phoenix |
| M6 | **v0.1.0 + the GIF** | Terminal recording: agent proposes a CRM write → human denies → record shows the wasted inference cost |
| M7 | MCP middleware | An arbitrary MCP server emits records with a decorator |
| M8 | `n8n-operator` integration | Dogfooded; the abstraction survives contact with a real server |
| M9 | OTel `mcp.*` PR | PR open at `open-telemetry/semantic-conventions-genai` |

---

## 10. Distribution

1. **Lead with EU AI Act Article 12.** Effective August 2026, requires automatic recording. It is the IETF draft's own motivation and it is the strongest adoption argument available — a compliance deadline beats a technical argument every time.
2. **The launch metric is cost-of-denied-proposals.** "We spent $4,100 last quarter on proposals humans rejected" is a number no existing tool can produce and every finance team will want.
3. **A PR to `open-telemetry/semantic-conventions-genai`** extending `mcp.*` coverage. It lags the spec by two revisions; fixing that is cheap, visible, and buys standing before you propose anything larger.
4. **awesome-mcp-servers** and the **MCP Registry**.
5. **The `why-not-a-protocol.md` post.** "MCP just told the ecosystem to stop logging over the protocol" (SEP-2577) is a genuinely newsworthy observation most of the ecosystem has not noticed.
6. **HumanLayer's vacated position.** 11.3k stars, now largely deprecated and redirecting to a hosted rebuild. The category leader leaving OSS is both an opportunity and a caution about the business model — say so publicly and honestly.

---

## 11. Open questions to resolve before M1

1. **Pick the Python distribution name.** `agent-audit` on PyPI is taken (v0.19.2, actively versioned, different purpose, same ecosystem). Candidates: `agent-audit-record`, `agentaudit-otel`, `openagentaudit`. npm `agent-audit` is free — check whether keeping the repo name while differing on PyPI is more confusing than helpful.
2. **Email the IETF draft author before writing the spec**, not after.
3. **Confirm `gen_ai.tool.type` well-known enum values** — the attribute was verified, its enum was not.
4. **Verify Braintrust and W&B Weave schemas.** Only marketing comparison pages surfaced; Weave's repo has no LICENSE at root.
5. **Verify the AWS CloudTrail field list and OpenID SSF draft status** before citing either in the README — both currently rest on background knowledge, not fetched sources.
6. **Watch SEP-1763 (Interceptors)** — proposes validation/mutation/observability interceptors including "log all MCP operations for compliance." Currently open, Draft, no sponsor. It is the most likely place this work collides with core protocol, but it is nowhere near acceptance.
7. **Decide whether hash-chaining ships in v1.** The IETF draft has it. Recommendation: no — it is the kind of feature that makes a schema look serious and makes an emitter hard to adopt. Add it when a user asks.

---

## 12. Sources

- [MCP spec 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) · [schema.ts](https://raw.githubusercontent.com/modelcontextprotocol/modelcontextprotocol/main/schema/2026-07-28/schema.ts) · [SEP-2577 (deprecate roots/sampling/logging)](https://modelcontextprotocol.io/seps/2577-deprecate-roots-sampling-and-logging) · [SEP-1763 (interceptors)](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1763) · [MCP Tasks](https://modelcontextprotocol.io/extensions/tasks/overview) · [ext-tasks](https://github.com/modelcontextprotocol/ext-tasks)
- [OTel GenAI attribute registry](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/registry/attributes/gen-ai.md) · [OTel MCP attributes](https://raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/registry/attributes/mcp.md) · [OTel agentic systems issue #35](https://github.com/open-telemetry/semantic-conventions-genai/issues/35) · [OTel Log Data Model (Stable)](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
- [OpenInference semantic conventions](https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md) · [Langfuse data model](https://langfuse.com/docs/observability/data-model) · [Langfuse public API (ingestion sunset 16 Nov 2026)](https://langfuse.com/docs/api-and-data-platform/features/public-api) · [ClickHouse acquires Langfuse](https://clickhouse.com/blog/clickhouse-acquires-langfuse-open-source-llm-observability)
- [Claude Code hooks](https://code.claude.com/docs/en/hooks) · [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) · [HumanLayer](https://github.com/humanlayer/humanlayer) · [agentcontrolplane](https://github.com/humanlayer/agentcontrolplane)
- [microsoft/agent-governance-toolkit](https://github.com/microsoft/agent-governance-toolkit) · [draft-sharif-agent-audit-trail](https://datatracker.ietf.org/doc/draft-sharif-agent-audit-trail/)
- [CloudEvents spec](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md) · [OpenLineage facets](https://openlineage.io/docs/spec/facets/) · [Kubernetes auditing](https://kubernetes.io/docs/tasks/debug/debug-cluster/audit/) · [RFC 8417 (SET)](https://www.rfc-editor.org/rfc/rfc8417.html) · [PyPI agent-audit (name taken)](https://pypi.org/pypi/agent-audit/json)
