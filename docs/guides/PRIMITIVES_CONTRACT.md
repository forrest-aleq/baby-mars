# Aleq Primitives Contract

**Version:** 1.1
**Status:** LOCKED
**Scope:** Frontend ↔ Baby MARS ↔ Stargate (NAOS-3)

---

## What This Is

These 20 primitives are the **complete set** of atomic operations that compose any Aleq scenario. Each scenario uses a **subset** of these primitives depending on input type (message vs webhook) and complexity.

Like a game engine doesn't know "Mario jumps on Goomba" - it knows collision detection, physics, sprite rendering. Aleq doesn't know "process lockbox" - it knows these primitives.

**Key insight:** Primitives 1, 2, 8 are currently broken. This blocks end-to-end testing of everything else.

---

## The Three Layers

```
┌─────────────────────────────────────────────────────────────┐
│  FRONTEND (Lemons)                                          │
│  - Renders UI, captures input, displays responses           │
│  - Manages local state (pills, drill-downs, mode)           │
└─────────────────────────────────────────────────────────────┘
                              ↕ WebSocket/REST
┌─────────────────────────────────────────────────────────────┐
│  BABY MARS (Brain)                                          │
│  - Cognitive loop, beliefs, autonomy decisions              │
│  - Interprets intent, routes to Stargate                    │
└─────────────────────────────────────────────────────────────┘
                              ↕ REST
┌─────────────────────────────────────────────────────────────┐
│  STARGATE (NAOS-3 / Hands)                                  │
│  - Executes capabilities against external systems           │
│  - 366 capabilities, 200 production-ready                   │
└─────────────────────────────────────────────────────────────┘
```

---

## The 20 Primitives

### Layer 1: Thread Management (Frontend ↔ MARS)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 1 | `thread.create` | Start new conversation | MARS | `POST /chat` (no thread_id) | ❌ Broken |
| 2 | `thread.load` | Resume existing conversation | MARS | `POST /chat` (with thread_id) | ❌ Broken |
| 3 | `thread.save` | Persist state after each turn | MARS | Automatic (LangGraph checkpoint) | ❓ Unclear |

**Note:** Primitive 3 is automatic - triggered by LangGraph after each node execution, not called explicitly.

### Layer 2: User Context (Frontend ↔ MARS)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 4 | `user.identify` | Who am I talking to (org_id + user_id) | MARS | Request payload | ✅ Works |
| 5 | `user.load_rapport` | Get relationship state (communication style, trust level) | MARS | Internal (Rapport graph) | ✅ Works |

### Layer 3: Context Loading (MARS internal)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 6 | `context.temporal` | What time/day/month-end, fiscal calendar | MARS | Internal | ✅ Works |
| 7 | `context.org` | What org, what services connected, what capabilities available | MARS | Internal | ✅ Works |

### Layer 4: Input Reception (External → MARS)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 8 | `input.receive_message` | Get user text from chat | MARS | `POST /chat` | ❌ Broken |
| 9 | `input.receive_webhook` | Get external trigger (email, bank event) | MARS | `POST /webhook/{type}` | ⚠️ Untested |
| 10 | `input.receive_approval` | Get HITL decision response | MARS | `POST /decisions/{id}/execute` | ⚠️ Untested |

**Input types are mutually exclusive per invocation:**
- User-initiated: Uses 8
- Automation-triggered: Uses 9
- Continuation after HITL: Uses 10

### Layer 5: Intent Processing (MARS internal)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 11 | `intent.classify` | Determine request type (query, action, analysis) | MARS | Appraisal node | ⚠️ Untested |
| 12 | `intent.extract_entities` | Extract vendors, amounts, dates, accounts | MARS | Appraisal node | ⚠️ Untested |

**Note:** 11 and 12 happen together in the appraisal node but answer different questions:
- 11: "What kind of request is this?" → lockbox_processing, reconciliation, query
- 12: "What are the specifics?" → vendor=Acme, amount=$500, invoice=INV-123

### Layer 6: Belief System (MARS internal)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 13 | `belief.lookup` | Retrieve relevant beliefs for this context | MARS | Belief graph | ✅ Works |
| 14 | `belief.confidence` | Get belief strength (0.0-1.0) for autonomy decision | MARS | Belief graph | ✅ Works |

**Note:** 13 and 14 are typically done together - lookup returns belief content AND confidence. Separated here because they answer different questions:
- 13: "What do I know?" → "SeaBreeze is alias for SB Yacht Club LLC"
- 14: "How sure am I?" → 0.85

### Layer 7: Autonomy Decision (MARS internal)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 15 | `routing.autonomy` | Decide execution mode based on confidence | MARS | Action selection node | ✅ Works |

**Autonomy modes:**
- `guidance_seeking` (confidence < 0.4): Ask user what to do
- `action_proposal` (0.4 ≤ confidence < 0.7): Propose action, wait for approval
- `autonomous` (confidence ≥ 0.7): Execute without asking

### Layer 8: Work Execution (MARS → Stargate)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 16 | `work.decompose` | Break intent into ordered capability calls | MARS | Execution node | ⚠️ Untested |
| 17 | `stargate.execute` | Call Stargate with capability_key + args | Stargate | `POST /api/v1/execute` | ✅ Works |

**Note:** Primitive 17 may be called multiple times per request (e.g., OCR → search → apply → journal)

### Layer 9: Learning (MARS internal)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 18 | `learn.update_belief` | Adjust belief strength from execution outcome | MARS | Feedback node | ✅ Works |
| 19 | `learn.update_rapport` | Adjust relationship from interaction pattern | MARS | Feedback node | ✅ Works |

### Layer 10: Response (MARS → Frontend)

| # | Primitive | What It Does | Owner | Endpoint | Status |
|---|-----------|--------------|-------|----------|--------|
| 20 | `respond.generate` | Craft response in user's communication style | MARS | Response node → SSE | ✅ Works |

---

## Primitive Dependencies

Primitives must execute in order. Later primitives depend on earlier ones:

```
INPUT PHASE
┌─────────────────────────────────────────────────────────┐
│ 1/2 (thread) → 4 (user) → 5 (rapport) → 6,7 (context)  │
│                    ↓                                    │
│              8 OR 9 OR 10 (input)                       │
└─────────────────────────────────────────────────────────┘
                         ↓
PROCESSING PHASE
┌─────────────────────────────────────────────────────────┐
│ 11,12 (intent) → 13,14 (beliefs) → 15 (autonomy)       │
│                                         ↓               │
│                         ┌───────────────┴────────────┐  │
│                         │ guidance_seeking: STOP     │  │
│                         │ action_proposal: WAIT →10  │  │
│                         │ autonomous: CONTINUE       │  │
│                         └────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         ↓
EXECUTION PHASE
┌─────────────────────────────────────────────────────────┐
│ 16 (decompose) → 17 (execute) → 17 → 17 → ...          │
│                                   ↓                     │
│                        18,19 (learn) → 20 (respond)     │
└─────────────────────────────────────────────────────────┘
```

---

## Current Status Summary

| Status | Count | Primitives |
|--------|-------|------------|
| ✅ Works | 11 | 4, 5, 6, 7, 13, 14, 15, 17, 18, 19, 20 |
| ❌ Broken | 3 | 1, 2, 8 |
| ⚠️ Untested | 5 | 9, 10, 11, 12, 16 |
| ❓ Unclear | 1 | 3 |

**Critical Path Blocker:** Primitives 1, 2, 8 (thread management + message input) are broken. Message-triggered scenarios cannot be tested until these work.

**Webhook path (9) is untested but potentially unblocked** - could test automation scenarios independently.

---

## Stargate Contract (Primitive #17)

Stargate's job is simple: execute primitive #17 reliably.

### Request Format

```json
POST /api/v1/execute
Content-Type: application/json
X-API-Key: {api_key}

{
  "capability_key": "recurly.payment.apply",
  "org_id": "dockwa",
  "user_id": "maria",
  "args": {
    "invoice_id": "inv_123",
    "amount": 875.00,
    "payment_method": "check"
  }
}
```

### Success Response

```json
{
  "status": "success",
  "capability_key": "recurly.payment.apply",
  "tool_used": "recurly.apply_payment",
  "outputs": {
    "invoice_id": "inv_123",
    "state": "paid",
    "amount_applied": 875.00,
    "closed_at": "2025-12-26T12:00:00Z"
  },
  "logs": ["Payment applied successfully"],
  "timestamp": "2025-12-26T12:00:00.123456"
}
```

### Error Response

```json
{
  "status": "error",
  "capability_key": "recurly.payment.apply",
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No credentials found for recurly",
  "retry_strategy": "human_intervention",
  "details": {
    "service": "recurly",
    "org_id": "dockwa",
    "user_id": "maria"
  },
  "timestamp": "2025-12-26T12:00:00.123456"
}
```

### Error Codes & Retry Strategies

| error_code | retry_strategy | MARS Action |
|------------|---------------|-------------|
| `CREDENTIAL_MISSING` | `human_intervention` | Surface "Connect {service}" card |
| `CREDENTIAL_INVALID` | `human_intervention` | Surface "Reconnect {service}" card |
| `VALIDATION_ERROR` | `none` | Surface error, don't retry |
| `NOT_FOUND` | `none` | Surface error, don't retry |
| `RATE_LIMIT` | `backoff` | Exponential backoff, retry |
| `EXTERNAL_API_ERROR` | `backoff` | Exponential backoff, retry |

### Pre-flight Credential Check

```json
POST /api/v1/credentials/status
{
  "org_id": "dockwa",
  "user_id": "maria",
  "capability_key": "recurly.payment.apply"
}

// Response
{
  "credential_available": true,
  "credential_type": "customer",
  "requires_setup": false,
  "token_expiry": "2025-12-27T12:00:00Z"
}
```

---

## MARS → Stargate Protocol

When MARS executes work (primitives 16 → 17):

```python
def execute_work_unit(work_unit: WorkUnit) -> ExecutionResult:
    """Execute a single capability call via Stargate."""

    # 1. Pre-flight credential check
    cred_status = stargate.post("/api/v1/credentials/status", {
        "org_id": state.org_id,
        "user_id": state.user_id,
        "capability_key": work_unit.capability_key
    })

    if not cred_status["credential_available"]:
        # Primitive 15: Route to HITL
        return ExecutionResult(
            status="blocked",
            decision_needed=DecisionCard(
                type="connect_service",
                service=work_unit.service,
                message=f"Please connect {work_unit.service} to continue"
            )
        )

    # 2. Execute capability
    result = stargate.post("/api/v1/execute", {
        "capability_key": work_unit.capability_key,
        "org_id": state.org_id,
        "user_id": state.user_id,
        "args": work_unit.args
    })

    # 3. Handle result by retry_strategy
    if result["status"] == "success":
        return ExecutionResult(
            status="success",
            outputs=result["outputs"]
        )

    retry_strategy = result.get("retry_strategy", "none")

    if retry_strategy == "backoff":
        # Retry with exponential backoff
        return retry_with_backoff(work_unit, max_attempts=3)

    elif retry_strategy == "human_intervention":
        # Surface to user
        return ExecutionResult(
            status="blocked",
            decision_needed=DecisionCard(
                type="error",
                message=result["error_message"]
            )
        )

    else:  # retry_strategy == "none"
        # Don't retry, surface error
        return ExecutionResult(
            status="failed",
            error=result["error_message"]
        )
```

---

## Frontend → MARS Protocol

### Send Message (Primitives 1, 2, 8)

```json
POST /chat
Content-Type: application/json

{
  "thread_id": "thread_abc123",  // Omit for new thread (primitive 1)
                                 // Include to resume (primitive 2)
  "org_id": "dockwa",
  "user_id": "maria",
  "message": "Process the lockbox from First Republic"
}
```

### Receive Events (SSE)

```
GET /events?thread_id={thread_id}
Accept: text/event-stream

event: task:created
data: {"task_id": "task_123", "type": "lockbox_processing", "summary": "Processing lockbox from First Republic"}

event: task:updated
data: {"task_id": "task_123", "stage": "extracting", "progress": "Extracting payments from 6 PDFs"}

event: aleq:message
data: {"message": "Found 47 payments totaling $73,924.50"}

event: task:decision_needed
data: {"task_id": "task_123", "decision_id": "dec_456", "summary": "Entity mismatch needs resolution"}

event: task:completed
data: {"task_id": "task_123", "duration_seconds": 168}
```

### HITL Decision (Primitive 10)

```json
POST /decisions/{id}/execute
{
  "action": "apply_to_services",  // User's choice
  "user_id": "maria"
}

// Response
{
  "decision_id": "dec_456",
  "action": "apply_to_services",
  "executed_at": "2025-12-26T12:00:00Z",
  "result": "success"
}
```

---

## Scenario Traces

Each scenario maps to a specific sequence of primitives. Not all 20 are used in every scenario.

### Maria's Lockbox (Poison Dart) - Webhook Triggered

```
CONTEXT LOADING
  4  → user.identify (org: dockwa, user: system)
  6  → context.temporal (date: Oct 1, not month-end)
  7  → context.org (services: Recurly, NetSuite, Gmail)

INPUT
  9  → input.receive_webhook (email from First Republic with 6 PDFs)

INTENT
  11 → intent.classify → lockbox_processing
  12 → intent.extract_entities → {bank: First Republic, pdf_count: 6}

BELIEFS
  13 → belief.lookup → "First Republic lockbox format", "Customer aliases"
  14 → belief.confidence → 0.92 (high - done this before)

EXECUTION
  16 → work.decompose → [ocr, match_customers, match_invoices, apply_payments, journal]

  17 → stargate.execute (ocr.gemini.extract) → 47 payments extracted
  13 → belief.lookup → "SeaBreeze" = "SB Yacht Club LLC"
  17 → stargate.execute (recurly.invoice.search) → 46 of 47 matched

AUTONOMY (exception detected)
  14 → belief.confidence → 0.35 (low - entity mismatch)
  15 → routing.autonomy → guidance_seeking

HITL
  [Decision card surfaces: "MdR Storage paid for MdR Services invoice"]
  10 → input.receive_approval (action: apply_to_services)

RESUME EXECUTION
  17 → stargate.execute (recurly.payment.apply) × 47
  17 → stargate.execute (netsuite.journal.create)

LEARNING
  18 → learn.update_belief → "MdR Storage pays for MdR Services" (strength: 0.70)

RESPONSE
  20 → respond.generate → "Processed 47 payments ($73,924.50). JE-2025-4001 created."
```

**Primitives used:** 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20 (14 of 20)
**Not used:** 1, 2, 3, 5, 8, 19

### Akshay's Bank Reconciliation - Message Triggered

```
THREAD
  1  → thread.create (new conversation)

CONTEXT LOADING
  4  → user.identify (org: dockwa, user: akshay)
  5  → user.load_rapport (Akshay: prefers detailed explanations)
  6  → context.temporal (date: Oct 31, month-end)
  7  → context.org (services: Plaid, NetSuite)

INPUT
  8  → input.receive_message ("Reconcile Chase account for October")

INTENT
  11 → intent.classify → bank_reconciliation
  12 → intent.extract_entities → {bank: Chase, account: checking, period: October}

BELIEFS
  13 → belief.lookup → "Chase checking is account 1001"
  14 → belief.confidence → 0.88

EXECUTION
  16 → work.decompose → [get_bank_txns, get_gl_txns, match, journal_adjustments]

  17 → stargate.execute (plaid.transactions.get) → 342 transactions
  17 → stargate.execute (netsuite.query) → 338 GL entries
  16 → work.decompose (matching algorithm) → 335 matched, 7 exceptions

AUTONOMY
  14 → belief.confidence → 0.55 (medium - some exceptions)
  15 → routing.autonomy → action_proposal

  [Decision card: "7 transactions need review. Create adjustment JE for $1,247.50?"]
  10 → input.receive_approval (action: approve)

RESUME EXECUTION
  17 → stargate.execute (netsuite.journal.create) → JE-2025-4089

LEARNING
  18 → learn.update_belief → "Chase reconciliation pattern" (strength +0.05)
  19 → learn.update_rapport → Akshay: approved quickly, increase trust

THREAD SAVE
  3  → thread.save (checkpoint for resume)

RESPONSE
  20 → respond.generate → "Reconciled 342 transactions. 335 matched, 7 adjusted. JE-2025-4089 created."
```

**Primitives used:** 1, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20 (18 of 20)
**Not used:** 2, 9

### Angela's Cash Position - Simple Query

```
THREAD
  2  → thread.load (continuing conversation)

CONTEXT LOADING
  4  → user.identify (org: storagecorner, user: angela)
  5  → user.load_rapport (Angela: prefers concise summaries)
  6  → context.temporal (date: Dec 26, not month-end)
  7  → context.org (services: Plaid)

INPUT
  8  → input.receive_message ("What's our total cash position?")

INTENT
  11 → intent.classify → query
  12 → intent.extract_entities → {metric: cash_position, scope: all_entities}

BELIEFS
  13 → belief.lookup → "StorageCorner has 5 bank accounts across 3 entities"
  14 → belief.confidence → 0.95 (just retrieving data)

AUTONOMY
  15 → routing.autonomy → autonomous (query, no action needed)

EXECUTION
  17 → stargate.execute (plaid.balance.get) × 5 accounts

RESPONSE
  20 → respond.generate → "Total cash: $4.2M across 5 accounts. Main: $2.1M (Chase), Reserve: $1.8M (Glacier)"
```

**Primitives used:** 2, 4, 5, 6, 7, 8, 11, 12, 13, 14, 15, 17, 20 (13 of 20)
**Not used:** 1, 3, 9, 10, 16, 18, 19

---

## Testing Strategy

### Phase 1: Fix Critical Blockers
1. Fix primitives 1, 2, 8 (thread management + message input)
2. This unblocks message-triggered scenarios (Akshay, Angela)

### Phase 2: Test Webhook Path
1. Test primitive 9 (webhook input) independently
2. If working, can test Maria scenario without fixing chat

### Phase 3: End-to-End
1. Run Poison Dart (Maria's lockbox) - validates 14 primitives
2. Run Akshay's reconciliation - validates 18 primitives
3. Run Angela's query - validates 13 primitives

### Coverage Matrix

| Primitive | Maria | Akshay | Angela |
|-----------|-------|--------|--------|
| 1 thread.create | - | ✓ | - |
| 2 thread.load | - | - | ✓ |
| 3 thread.save | - | ✓ | - |
| 4 user.identify | ✓ | ✓ | ✓ |
| 5 user.load_rapport | - | ✓ | ✓ |
| 6 context.temporal | ✓ | ✓ | ✓ |
| 7 context.org | ✓ | ✓ | ✓ |
| 8 input.receive_message | - | ✓ | ✓ |
| 9 input.receive_webhook | ✓ | - | - |
| 10 input.receive_approval | ✓ | ✓ | - |
| 11 intent.classify | ✓ | ✓ | ✓ |
| 12 intent.extract_entities | ✓ | ✓ | ✓ |
| 13 belief.lookup | ✓ | ✓ | ✓ |
| 14 belief.confidence | ✓ | ✓ | ✓ |
| 15 routing.autonomy | ✓ | ✓ | ✓ |
| 16 work.decompose | ✓ | ✓ | - |
| 17 stargate.execute | ✓ | ✓ | ✓ |
| 18 learn.update_belief | ✓ | ✓ | - |
| 19 learn.update_rapport | - | ✓ | - |
| 20 respond.generate | ✓ | ✓ | ✓ |

**Running all 3 scenarios covers all 20 primitives.**

---

## Stargate Production Status

Primitive #17 (stargate.execute) is production ready with 200 capabilities:

| Category | Capabilities | Services |
|----------|-------------|----------|
| Pure utilities | 17 | Financial Calculator (6), Summarizer (5), Web Search (4), OCR Gemini (2) |
| API key services | 84 | Stripe (61), Recurly (12), Plaid (11) |
| OAuth services | 99 | QuickBooks (45), NetSuite (15), Gmail (25), Slack (6), HubSpot (4), Bill.com (9) |

**Stargate is ready. MARS primitives 1, 2, 8 are the blocker.**
