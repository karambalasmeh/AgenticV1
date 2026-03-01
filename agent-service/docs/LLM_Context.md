# GovTower — Agent Service (Team 2) Context Pack (v0.1)

**Purpose:** This document is a self-contained context pack for an LLM to assist with development of the `agent-service` microservice.  
It includes project architecture, scope boundaries, runtime flow (diagram-aligned), endpoints, schema expectations, codebase conventions, and current implementation status.

---

## 1) Project Overview (GovTower / Jordan National Policy Intelligence Platform)

This is a government-grade multi-agent AI platform to analyze, monitor, and explain Jordan’s national policies and modernization programs.  
It is **not a chatbot prototype**. It is a **modular microservice-based** enterprise system with auditability, governance, and human-in-the-loop.

### Architectural Mandate

- Each team owns **one independent microservice**.
- APIs must be **well-defined** and **service-isolated**.
- Features must be **self-contained reusable modules**.
- Must be **deployment-ready**, **observable**, and **audit-ready**.
- Backend: **FastAPI**. Frontend: **React + TS + Tailwind**.
  
  

---

## 2) Microservices and Responsibilities (High-level)

### Team 1 — knowledge-service

**Owns:** ingestion, chunking, embeddings, metadata tagging, version tracking, vector retrieval, source filtering, evidence ranking.  
**APIs:** `/ingest`, `/retrieve`, `/sources`, `/versions`, `/health`.

### Team 2 — agent-service (this service)

**Owns:** orchestration logic and multi-agent workflow.  
**Modules:** Router agent, specialist agents, tool abstraction, confidence scoring, delegation engine, escalation triggers, self-verification, citation enforcement.  
**APIs:** `/query`, `/delegate`, `/confidence`, `/validate`, `/explain_decision`.  
**Important boundary:** agent-service coordinates retrieval via Team 1 but does NOT implement retrieval/embeddings/chunking.

### Team 3 — governance-service

**Owns:** guardrails, evaluation, audit/logging pipeline, compliance, CI/CD governance.

### Team 4 — workflow-service

**Owns:** HITL operations: tickets, escalation workflows, assignment, SLA, RBAC.

### Team 5 — frontend-app

**Owns:** UI (chat, citations, confidence view, escalation view, dashboards).

---

## 3) Agent-Service Runtime Flow (Diagram-Aligned)

Agent-service implements this logic (flowchart):

1. **START:** receive user question → `POST /query`
2. **Router Agent:** classify intent/topic + detect complexity + detect missing required params
3. **Complex?**
   - If complex → Delegation Engine splits into subtasks (multi-agent)
   - If simple → run single specialist agent
4. **Specialist Agent(s):** generate draft answer + identify evidence needed
5. **Tool Abstraction:** (later) call knowledge-service/tools → evidence pack + metadata
6. **Validate + Self-Verify:** ensure evidence supports claims, structure completeness
7. **Valid + citations present?**
   - If no → **Repair Loop** (re-run specialists / adjust / re-validate)
   - If yes → proceed
8. **Confidence scoring:** compute score 0..1 + reasons
9. **Confidence low / conflicting evidence?**
   - If yes → escalation payload (HITL)
   - If no → return final answer
10. **END:** return answer + citations + confidence + explain_decision

### Clarification Scenario (Missing Required Parameters)

If request is missing required parameters (e.g., timeframe for comparison/monitoring) return a structured clarification response:

- status = `failed`
- response asks for missing fields (e.g., sector/timeframe)

---

## 4) Current Implementation Status (What Works Today)

### Implemented (MVP)

- FastAPI service runs locally.
- `POST /query` runs end-to-end using **Mock LLM**.
- Router detects **complex** multi-sector questions (e.g., energy + water).
- Delegation engine builds a plan:
  - `SectorExplainAgent` per sector
  - `RiskImpactAgent`
  - `MergeAgent`
- Validation uses `basic_validate` with a **repair loop** (`run_with_repair`).
- Confidence uses `basic_confidence` rubric.
- `request_id` in JSON response matches `X-Request-ID` header (audit-friendly).
- `output_controls.include_evidence=false` forces `citations=[]`.
- `output_controls.include_decision_trace=false` forces `decision_trace=[]`.

### Not Implemented Yet (Planned)

- Real Tool Abstraction integration with:
  - Team 1: `/retrieve` `/sources` `/versions`
  - Team 4: `/tickets` `/escalate`
  - Team 3: `/guardrail_check` `/audit` `/logs`
- Real citation enforcement (currently citations are empty because knowledge-service not connected).
- “Docs missing?” logic aligned with diagram (planned).
- Real conflict detection from evidence packs (planned).

---

## 5) Agent-Service Endpoints (Current)

Base path: `/api/v1`

### `GET /health`

Returns service status.

### `POST /query`

Main orchestration entrypoint.  
Input: `QueryRequest` (Pydantic).  
Output: `QueryResponse` including:

- answer (structured)
- citations (can be empty)
- confidence (score + rationale)
- validation (issues)
- decision_trace (optional)
- escalation status (triggered or not)

### Other endpoints exist as stubs or placeholders (depending on repo state):

- `POST /delegate`
- `POST /validate`
- `POST /confidence`
- `POST /explain_decision`

---

## 6) Core Schemas (Conceptual)

### QueryRequest (high-level)

- question: string
- language: ar|en|auto
- user_context: role, department, clearance_level
- session: session_id, conversation_id
- tasking: response_type (answer|briefing|comparison|monitoring_summary), priority
- constraints: time_range, source_filters, max_evidence
- output_controls: include_decision_trace, include_evidence, include_validation_report

### QueryResponse (high-level)

- request_id
- status: success|needs_escalation|failed
- answer: summary + sections
- citations: list (may be empty)
- confidence: score, level, rationale, signals
- validation: passed, issues
- decision_trace: list of (step, component, reason) if enabled
- escalation: triggered, reason, ticket(optional)

---

## 7) Internal Artifacts Contract (Critical for Team Work)

The orchestration passes a mutable `artifacts` dict between agents.

### Standard keys used today

- `question` (str): original question
- `topic` (str): router topic guess
- `sector` (str): sector for sector agent
- `sector_drafts` (list[str]): accumulated sector analysis sections
- `risk_draft` (str): risk/impact output from RiskImpactAgent
- `answer_draft` (str): final draft answer (must be set before validation)
- `citations` (list[Citation]): evidence references (empty until Team1 integration)
- `repair_instructions` (str): populated by repair loop for next run

### Important rule

Agents that produce *partial* content must not overwrite `answer_draft` unless they are the final composer (e.g., MergeAgent).  
Example:

- SectorExplainAgent appends to `sector_drafts`
- RiskImpactAgent stores in `risk_draft`
- MergeAgent writes final `answer_draft`

---

## 8) Validation & Repair Loop (Current)

### Validation

`basic_validate(draft, citations, require_citations)` checks:

- empty draft → high severity issue
- missing citations only if `REQUIRE_CITATIONS=True` (currently False)

### Repair Loop

If invalid:

- attach `repair_instructions` to artifacts
- re-run the same specialist plan
- re-validate
- max attempts = 2 (configurable)

If still invalid after attempts:

- escalate (status `needs_escalation`)

---

## 9) Confidence Scoring (Current)

`score_confidence(valid, issues, is_complex, citations_count)` returns:

- score 0..1
- level: low|medium|high
- rationale: list[str]
- signals: dict (validation_passed, issues_count, is_complex, citations_count)

Confidence is currently penalized when:

- complex query
- no citations available

---

## 10) Escalation (Current)

Escalation is triggered when:

- output remains invalid after repair loop, OR
- confidence level is low

Escalation payload integration with Team 4 is planned (ticket creation, HITL).

---

## 11) Configuration (Environment Variables)

Primary config lives in `.env` (template in `.env.example`):

- `SERVICE_NAME`, `SERVICE_VERSION`, `ENV`, `LOG_LEVEL`
- `REQUEST_TIMEOUT_S`
- `LLM_PROVIDER=mock|vertex`
- `VERTEX_PROJECT_ID`, `VERTEX_LOCATION`, `VERTEX_MODEL`
- `REQUIRE_CITATIONS` (default False until Team1 integrated)
- Downstream service URLs placeholders:
  - `KNOWLEDGE_SERVICE_URL`
  - `WORKFLOW_SERVICE_URL`
  - `GOVERNANCE_SERVICE_URL`

---

## 12) Running Locally (Windows)

Recommended Python: 3.11 (project may currently be running on 3.10 venv, but CI/standards should align to 3.11).

Run server:

Swagger:

- http://127.0.0.1:8002/docs  
  Health:
- http://127.0.0.1:8002/api/v1/health

---

## 13) LLM Provider Notes (Vertex Gemini)

LLM integration uses a provider-agnostic gateway:

- `mock` provider for deterministic local dev/testing.
- Vertex provider is supported (Gemini model), but requires:
  - Vertex credentials (ADC) and project configuration.

For local dev: keep `LLM_PROVIDER=mock` unless Vertex is configured.

---

## 14) Example Test JSONs (Copy/Paste)

### A) Multi-sector (Energy + Water)

```json
{
  "question": "Explain energy and water modernization impacts",
  "language": "en",
  "user_context": {"role": "unknown"},
  "session": {"session_id": "s1", "conversation_id": "c1"},
  "tasking": {"response_type": "answer", "priority": "normal"},
  "constraints": {"max_evidence": 10},
  "output_controls": {
    "include_decision_trace": true,
    "include_evidence": true,
    "include_validation_report": false
  }
}

### B) No evidence output

{
  "question": "Explain energy and water modernization impacts",
  "language": "en",
  "user_context": {"role": "unknown"},
  "session": {"session_id": "s2", "conversation_id": "c2"},
  "tasking": {"response_type": "answer", "priority": "normal"},
  "constraints": {"max_evidence": 10},
  "output_controls": {
    "include_decision_trace": true,
    "include_evidence": false,
    "include_validation_report": false
  }
}



### C) Clarification required (comparison without timeframe)

{
  "question": "Compare policy A vs policy B in water modernization",
  "language": "en",
  "user_context": {"role": "unknown"},
  "session": {"session_id": "s3", "conversation_id": "c3"},
  "tasking": {"response_type": "comparison", "priority": "high"},
  "constraints": {"max_evidence": 10},
  "output_controls": {
    "include_decision_trace": true,
    "include_evidence": true,
    "include_validation_report": false
  }
}

15) Future Direction: Domain Specialized Agents (Plugin-ready)

--------------------------------------------------------------

The system is expected to support domain-specific specialists in the future:

* Legal / Courts specialist agent

* Investors / Ministry of Economy specialist agent

* etc.

Design expectation:

* New agents should be addable as plug-ins (capability descriptors) without breaking the orchestration core.

* Agents must rely on tool abstraction and stable schemas.

* * *

16) Collaboration Rules (to avoid merge conflicts)

--------------------------------------------------

* `app/schemas/*` and `app/core/*` are shared: changes require team approval.

* Agents and orchestration can evolve, but must keep:
  
  * stable artifact keys (`answer_draft`, `sector_drafts`, `risk_draft`, etc.)
  
  * stable decision_trace semantics

* * *

17) TODO Backlog (Next high-impact items)

-----------------------------------------

1. Implement “Docs missing?” scenario and escalation reasons aligned with the diagram.

2. Add tool clients + mocks for knowledge/workflow/governance services.

3. Replace basic validation with structured claim/citation checks (once evidence exists).

4. Add minimal unit/integration tests (clarification path, repair loop path, escalation path).

5. Upgrade runtime environment to Python 3.11 consistently across dev/CI.




