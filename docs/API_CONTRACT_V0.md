# Aleq API Contract v0

**Status:** LOCKED
**Version:** 0.1.0
**Date:** December 2024

This document defines the contract between the Aleq frontend and Baby MARS backend. This is v0 - changes require a migration plan, not casual iteration.

---

## Philosophy

Aleq is a 25 year old finance hire. The API should feel like communicating with that person:

- **Responsive** - Acknowledges immediately, delivers thoughtfully
- **Transparent** - Shows its work, cites its sources
- **Humble** - Knows when to ask, admits uncertainty
- **Reliable** - Doesn't lose work, recovers gracefully
- **Respectful** - Respects your time, your authority, your attention

---

## 1. Conversation / Chat

### 1.1 Streaming Behavior

**Decision:** Interruptible streaming with graceful pivots.

When user sends a message while Aleq is responding:
- Stream continues for up to 2 more sentences to reach a natural pause
- Aleq acknowledges the interruption inline: "—actually, let me address what you just asked."
- New message is processed, response continues

This mirrors human conversation. You don't wait for someone to finish a monologue if you have something urgent.

If user sends "stop" or "wait" or "hold on":
- Stream stops within 1 sentence
- Aleq responds: "Stopped. What's up?" or similar
- Context is preserved, user can say "continue" to resume

**Edge case - rapid fire messages:**
Messages within 2 seconds of each other are batched and addressed together. User sending 3 quick messages gets one coherent response addressing all three, not three separate responses.

**Edge case - stream failure mid-response:**
- Partial response is preserved and shown
- Error indicator appended: "—[connection interrupted]"
- Automatic retry once after 3 seconds
- If retry fails, show: "I lost my train of thought. Here's what I had so far: [partial]. Want me to continue?"

### 1.2 Context Pills

**Decision:** Live references with intelligent budget management.

When user adds a context pill (e.g., `@invoice.DW-2025-0856`):
- Backend fetches the full object and holds it in working memory
- Object stays in context until explicitly removed or displaced
- Context has a budget: 10 items OR ~8K tokens, whichever hits first

When budget exceeded:
- Oldest item is displaced (not removed from UI, just dimmed)
- Aleq mentions it naturally: "I'm going to set aside the cash data to focus on these invoices"
- User can re-add displaced items (bumps something else)

**Context pill types:**
- `@widget.{id}` - Current state of a widget
- `@invoice.{id}` - Full invoice with line items
- `@customer.{id}` - Customer record with history summary
- `@task.{id}` - Task state and recent timeline
- `@belief.{id}` - Belief statement and evidence
- `@decision.{id}` - Past decision with reasoning snapshot

**Edge case - stale context:**
If a context pill references data that has changed since it was added:
- Backend detects staleness on next chat request
- Response notes it: "By the way, that invoice was paid since you added it to context. Want me to refresh?"

### 1.3 Widget Highlights

**Decision:** Semantic intent from backend, presentation from frontend.

Backend response includes a `references` array:
```
references: [
  {type: 'widget', id: 'cash', intensity: 'mention'},
  {type: 'widget', id: 'ar', intensity: 'focus'},
  {type: 'invoice', id: 'DW-2025-0856', intensity: 'critical'}
]
```

Intensity levels:
- `mention` - Aleq referenced it in passing (subtle highlight, 2 sec)
- `focus` - Aleq is talking about it (clear highlight, holds while relevant)
- `critical` - This is the key thing (strong highlight, pulses once, holds)

Frontend decides visual treatment. Backend declares intent.

**Edge case - multiple highlights:**
Maximum 3 simultaneous highlights. If more referenced, only top 3 by intensity shown. Others still linkable in text.

### 1.4 Conversation History

**Decision:** Persistent with intelligent decay and resurrection.

Conversations are stored per-org, indefinitely. But they have relevance decay:

- Last 24 hours: Full context available, Aleq remembers details
- Last 7 days: Summarized context, Aleq remembers themes
- Last 30 days: Key decisions and outcomes only
- Beyond 30 days: Searchable archive, not in active memory

**Resurrection:** If user references something old ("remember when we talked about Texas nexus?"):
- Aleq searches archive
- Pulls relevant conversation back into active context
- "Yes, that was 3 weeks ago. You were at $485K against the $500K threshold. You've since crossed it - $512K now."

**Edge case - conversation across sessions:**
Session breaks don't matter. If user closes browser and returns 4 hours later, Aleq can reference the earlier conversation naturally. "Before you left, we were looking at AR aging. Acme still hasn't paid."

**Edge case - multiple users in same org:**
Each user has their own conversation history. But decisions and tasks are shared. If Sarah and Mike both chat with Aleq about the lockbox task, they see their own conversations but the same task state.

---

## 2. Tasks

### 2.1 Task Creation

**Decision:** Three sources with unified structure.

**System-triggered:**
- Lockbox file arrives → task created
- Invoice overdue → collection task created
- Month-end date reached → close tasks created
- Anomaly detected → review task created

**User-requested:**
Natural language in chat: "Create a task to follow up with Acme in 3 days"
- Aleq confirms: "Got it. I'll remind you about Acme on Thursday."
- Task created with type `user_requested`, due date set

**Aleq-proposed:**
Aleq notices something: "AR aging jumped 15% this week. Want me to start collection outreach on the top 5?"
- User can approve (task created) or dismiss
- If approved, task has type `aleq_proposed`

All three converge to the same task structure. Source is metadata, not a different system.

### 2.2 Task Lifecycle

**Decision:** Tree structure with clear states.

Tasks can have sub-tasks. A lockbox task might spawn:
- 6 PDF processing sub-tasks
- 3 decision sub-tasks (one per exception)

Parent completes when all children complete.

**States:**
- `pending` - Queued, not started
- `running` - Aleq is actively working
- `blocked` - Waiting on external (decision, data, human)
- `paused` - User explicitly paused ("not now")
- `completed` - Done successfully
- `failed` - Unrecoverable error
- `superseded` - Replaced by newer task

**Transitions:**
- Forward: `pending → running → completed`
- Blocking: `running → blocked → running` (when unblocked)
- Pausing: Any state → `paused` → original state (on resume)
- Failure: Any state → `failed`
- Reopening: `completed → running` (if new exception found, creates child task)

**Edge case - zombie tasks:**
Task stuck in `running` for >1 hour with no progress:
- Auto-transitions to `blocked`
- Reason: "Appears stuck. Waiting for investigation."
- Alert to on-call if configured

### 2.3 Multi-User on Tasks

**Decision:** Soft presence, no hard locks.

When viewing a task:
- You see who else is viewing (avatars)
- You see who's actively in a decision flow (Sarah is reviewing...)

When making a decision:
- Your "Approve" click is optimistic - UI shows "Posting..."
- If someone else decided in the meantime, you get: "Sarah just approved this. Your click wasn't needed."
- No error, just information. The work got done.

**Real-time updates:**
When Sarah approves in her tab:
- Your task panel updates within 500ms
- Toast notification: "Sarah approved. 45 payments posted."
- Decision button state updates (disabled or shows "Decided by Sarah")

**Edge case - simultaneous clicks:**
Two people click "Approve" within 100ms. Backend processes first one, second returns `{already_decided: true, decided_by: 'sarah'}`. Neither sees an error. Work happened once.

### 2.4 Long-Running Tasks (Stargate)

**Decision:** SSE progress stream with meaningful milestones.

Connection: Single SSE endpoint per active long-running task.

Progress events are hierarchical:
```
event: progress
data: {
  stage: 3,
  stage_name: 'Entity Resolution',
  stage_total: 8,
  stage_progress: 0.45,
  detail: {
    processed: 540,
    total: 1200,
    found: 47,
    auto_resolved: 38,
    pending_decision: 9
  },
  message: '540 of 1,200 customers processed. 9 duplicates need your input.'
}
```

Milestones (bigger moments):
```
event: milestone
data: {
  type: 'stage_complete',
  stage: 2,
  stage_name: 'Profiling',
  summary: 'Analysis complete. Found 12 data quality issues.',
  next_stage: 'Entity Resolution',
  requires_action: false
}
```

Decisions needed:
```
event: decision_needed
data: {
  decision_id: 'dup-cluster-7',
  type: 'duplicate_resolution',
  summary: '3 records look like Acme Corp',
  confidence: 0.78,
  blocking: true
}
```

**Edge case - connection drop:**
Client reconnects with `Last-Event-ID` header. Server replays events since that ID (up to 100). If too far behind, sends `event: resync` with full current state.

**Edge case - user navigates away:**
SSE connection closes. Task continues. When user returns, fresh state is fetched, SSE reconnects for future updates.

### 2.5 Task Failure

**Decision:** Graceful degradation with clear recovery options.

Partial failure (3 of 6 PDFs processed):
```
{
  status: 'partially_completed',
  completed: [pdf1, pdf2, pdf4],
  failed: [
    {id: 'pdf3', error: 'OCR failed - image quality too low', recoverable: true},
    {id: 'pdf5', error: 'Encrypted file', recoverable: false},
    {id: 'pdf6', error: 'Timeout', recoverable: true}
  ],
  message: 'Processed 3 of 6 files. 2 can be retried, 1 needs manual handling.',
  actions: [
    {label: 'Retry failed', action: 'retry_failed'},
    {label: 'Continue without', action: 'continue_partial'},
    {label: 'Upload replacements', action: 'upload_replacement'}
  ]
}
```

External system failure (ERPNext down):
- Task pauses gracefully
- State is checkpointed
- User sees: "ERPNext is temporarily unavailable. I've saved progress - this will resume automatically when it's back."
- Background retry every 5 minutes
- When ERPNext returns, task resumes from checkpoint

**Edge case - unrecoverable failure:**
- Task moves to `failed`
- Full audit log preserved
- User sees: "This task couldn't be completed. Here's what happened: [detailed explanation]. Options: [Start over] [Get help]"
- Never a dead end. Always a next action.

---

## 3. Decisions

### 3.1 Idempotency

**Decision:** Decision ID + optimistic UI + backend deduplication.

Every decision has a unique `decision_id` generated by backend when decision is presented.

Request: `POST /decisions/{decision_id}/execute`

- First request: Executes, returns `{executed: true, was_replay: false}`
- Subsequent requests: Returns `{executed: true, was_replay: true}` with same result

UI behavior:
- Button disables immediately on click
- Shows "Posting..." state
- If duplicate detected, silently succeeds (user doesn't see error)

**Edge case - network timeout:**
User clicks, request times out, user clicks again.
- First request might have succeeded (backend processed) or failed (never arrived)
- Second request either executes (if first failed) or deduplicates (if first succeeded)
- User eventually sees success either way

Backend tracks decision execution for 24 hours. After that, re-execution would be a new decision.

### 3.2 Undo

**Decision:** Soft commit window for reversible decisions.

Decision types:
- **Soft decisions** - Can be undone within 30 seconds (payment posting, categorization)
- **Hard decisions** - Cannot be undone, require explicit confirmation (month-end close, period lock)

Soft decision flow:
1. User clicks "Approve"
2. UI shows "Posted" with "Undo" link (30 second countdown)
3. Backend stages the change but doesn't commit
4. If undo clicked: Rollback, no trace in books
5. If 30 seconds pass: Commit finalizes
6. After commit: "Undo" disappears, change is permanent

Hard decision flow:
1. User clicks "Close September"
2. Modal: "This will close September. Journal entries will be locked. This cannot be undone. [Cancel] [Close September]"
3. If confirmed: Executes immediately, no undo

**Edge case - undo after related action:**
User posts payment (soft). Within 30 seconds, user starts another action referencing that payment.
- Undo is still available
- If undone, second action is warned: "The payment you referenced was undone. Continue anyway?"

### 3.3 Partial Failure

**Decision:** Atomic core with async periphery.

A decision has three effects:
1. **Core** - ERPNext write (the actual accounting action)
2. **Learning** - Belief update (Aleq learns from outcome)
3. **Audit** - Log entry (permanent record)

Execution order:
1. Audit log written first (always succeeds - append-only, local)
2. ERPNext write attempted
3. If ERPNext succeeds: Belief update queued
4. If ERPNext fails: Nothing else happens, clean failure

**States:**
- `executed` - Core succeeded, everything succeeded
- `executed_learning_pending` - Core succeeded, belief update queued (rare, async lag)
- `failed` - Core failed, nothing happened

**Edge case - ERPNext succeeds, belief update fails:**
- Decision is `executed_learning_pending`
- Belief update retried in background
- User is not blocked or notified (this is internal learning)
- If retry fails 3x, alert to engineering, belief update is skipped
- Books are correct (that's what matters). Learning is best-effort.

### 3.4 Decision Timeout

**Decision:** Escalating attention, never auto-decide.

Pending decisions age gracefully:

**Days 1-3: Normal**
- Yellow indicator in task dots
- Appears in normal task list

**Days 4-7: Elevated**
- Mentioned in morning briefing (if enabled): "Still waiting on that Marina payment decision from 5 days ago"
- Badge on task dot shows age

**Days 7-14: Escalated**
- If escalation configured: Notify next authority level (Controller → CFO)
- Escalation is notification only, not reassignment
- Original person can still decide

**Days 14+: Intervention**
- Aleq asks directly: "This Marina payment has been waiting 15 days. What would you like to do?"
- Options: Decide now, Reassign, Skip (moves to next month), Get help

**Never:** Auto-decide, silently expire, disappear

**Edge case - vacation/absence:**
User can set "away" status. Pending decisions are auto-escalated to backup immediately, not after 7 days.

---

## 4. Beliefs & Thresholds

### 4.1 Belief Mutability

**Decision:** Challenge system, not direct edit.

Users cannot directly edit belief statements. But they can challenge:

**Challenge flow:**
1. User sees belief reference: "Entity Relationship #B-8821"
2. User clicks: "This doesn't seem right"
3. Aleq shows evidence:
   - "Matched TIN suffix (94-xxxx82)"
   - "6 prior cross-entity payments"
   - "User confirmed Oct 12"
4. User can:
   - Accept (nothing changes)
   - Dispute with reason: "They split into separate companies last month"
5. If disputed:
   - Belief strength significantly decreases (e.g., 0.85 → 0.40)
   - Related pending decisions are flagged for review
   - Belief enters "disputed" state
6. Next evidence either way adjusts strength (could recover or further decline)

**Admin capability:**
Admins can directly edit belief statements for:
- Correcting obvious errors
- Seeding new knowledge
- Bulk updates during migration

All admin edits are logged with reason.

### 4.2 Threshold Changes

**Decision:** Thresholds are policy beliefs with formal change process.

Thresholds (like "$500 cross-entity auto-apply limit") are stored as beliefs with:
- `category: 'threshold'`
- `strength: 1.0` (policy-set, not learned)
- `source: 'admin'`
- `requires_role: 'controller'` (who can change)

**Change process:**
1. Authorized user requests change
2. Reason required: "Client requested higher limit for efficiency"
3. Optional: Effective date (can be future-dated: "starting next month")
4. Audit logged: Who, when, old value, new value, reason
5. Notification to affected users: "Cross-entity threshold increased from $500 to $1,000 by Sarah (Controller)"

**Retroactivity:** Changes are NOT retroactive.
- Pending decisions keep the threshold they were created under
- New decisions use new threshold
- User can see which threshold applies: "Evaluated against $500 limit (changed to $1,000 on Nov 1)"

### 4.3 Belief Versioning

**Decision:** Snapshot at decision time, current for exploration.

**When viewing a past decision:**
- Shows the belief AS IT WAS when decision was made
- "Decided using B-8821 v3 (strength: 0.72)"
- Link to see current state if different

**When exploring beliefs now:**
- Shows current state
- History available: "3 versions - [View history]"
- History shows: Each version, what changed, when, why (if from decision outcome)

**Edge case - belief deleted:**
Beliefs are never hard-deleted. They can be:
- `active` - Current and used
- `superseded` - Replaced by newer belief
- `invalidated` - Proven wrong, no replacement
- `archived` - No longer relevant

Past decisions always show the snapshot they used, even if belief is now invalidated.

---

## 5. Data / Widgets

### 5.1 Data Freshness

**Decision:** Tiered freshness with transparency.

**Tier 1 - Critical (Cash, Bank):**
- Real-time when widget is in focus
- 30-second refresh when visible but not focused
- Push update on significant change (payment posted)

**Tier 2 - Important (AR, AP, Revenue):**
- 5-minute cache
- Refresh on widget interaction (click)
- Push update on decision completion

**Tier 3 - Computed (Runway, Ratios):**
- Hourly recomputation
- Manual refresh available
- Real-time only in "what-if" mode

**Transparency:**
Every widget shows freshness on hover: "Updated 2 min ago"
If stale (>10 min for Tier 1, >30 min for Tier 2): Shows "Refreshing..." indicator

**Edge case - ERPNext lag:**
If ERPNext data is stale at source (sync delay from bank):
- Show the data we have
- Add note: "Bank data as of 6:00 AM" (source timestamp, not our cache time)

### 5.2 Computed Values

**Decision:** Backend owns truth, frontend can explore.

**Official values (backend computed):**
- Runway: Calculated hourly, based on cash balance and 3-month burn average
- Burn rate: Rolling 3-month average
- Growth rate: Month-over-month comparison

Backend returns both the number AND the inputs:
```
runway: {
  months: 18.2,
  inputs: {
    cash: 1247000,
    burn_rate: 68400,
    burn_method: '3mo_average'
  },
  computed_at: '2024-12-22T10:00:00Z'
}
```

**What-if mode (frontend computed):**
User can adjust inputs: "What if burn was $75K?"
- Frontend recalculates instantly
- Shows as "scenario" not "actual"
- Can save as a named View

**Edge case - inputs changed since computation:**
If cash balance changed since runway was computed:
- Show the official number with asterisk
- Tooltip: "Based on $1.2M cash. Current balance is $1.3M. [Refresh]"

### 5.3 Drill-Down Data

**Decision:** Lazy loading with counts upfront.

**Level 1 (Widget view):**
```
GET /data/cash
→ {
    total: 1247000,
    change: 84000,
    accounts: [
      {id: 'chase', name: 'Chase', balance: 890000, transaction_count: 47},
      {id: 'svb', name: 'SVB', balance: 357000, transaction_count: 23}
    ]
  }
```

**Level 2 (Account detail):**
```
GET /data/cash/accounts/chase
→ {
    id: 'chase',
    name: 'Chase Operating',
    balance: 890000,
    available: 885000,
    pending: 5000,
    recent_transactions: [...first 10...],
    total_transactions: 47
  }
```

**Level 3 (Transaction list):**
```
GET /data/cash/accounts/chase/transactions?limit=20&offset=0
→ {
    transactions: [...],
    total: 47,
    has_more: true
  }
```

Frontend shows count ("47 transactions") immediately from L1 data. Loads actual transactions on demand.

**Edge case - count changes between L1 and L3:**
L1 said 47 transactions. User drills down, L3 says 48.
- Show the new count
- No error, no reconciliation attempt
- Data is eventually consistent, that's fine

---

## 6. Real-Time

### 6.1 Update Mechanism

**Decision:** SSE for events, WebSocket only for streaming chat.

**SSE connection:**
Single connection per session at `/events`

Event types:
- `task:created` - New task appeared
- `task:updated` - Task status changed
- `task:decision_needed` - Decision surfaced
- `decision:made` - Someone decided (with who, what)
- `data:changed` - Widget data changed (with widget_id)
- `presence:update` - Who's viewing what
- `aleq:message` - Aleq proactively saying something

All events include `event_id` for resume and `timestamp`.

**WebSocket:**
Only for chat streaming. Used for:
- Bidirectional (user can interrupt)
- Backpressure (pause streaming if client slow)

**Why not WebSocket for everything:**
- SSE is simpler, more reliable
- Works better through corporate proxies
- Auto-reconnects cleanly
- Most events are server→client only

### 6.2 Multi-Tab

**Decision:** Client-side coordination + server confirmation.

Same user, same browser, multiple tabs:
- Tabs coordinate via BroadcastChannel API (instant, no server)
- Action in Tab 1 broadcasts to Tab 2 immediately
- Server event confirms shortly after

Different users, same org:
- Server events only (no client shortcut)
- Sub-second latency via SSE

**Optimistic UI:**
- Your own actions: Update immediately, confirm async
- Others' actions: Wait for server event, then update

**Edge case - conflict:**
Tab 1 shows "Approve" button. User clicks. Meanwhile Tab 2 (from Sarah) approved.
- Tab 1's request returns `{already_decided: true, decided_by: 'sarah'}`
- Tab 1 updates to show decided state
- No error modal, just graceful resolution

**Edge case - stale tab:**
User has tab open for 8 hours (SSE connection died silently).
- On any user action, frontend checks connection
- If stale, reconnects and fetches fresh state before proceeding
- User might see brief "Syncing..." state

---

## 7. Auth / Multi-Tenant

### 7.1 Auth Mechanism

**Decision:** JWT + refresh token with secure storage.

**Tokens:**
- Access token: 15 minute expiry, stored in memory only
- Refresh token: 7 day expiry, httpOnly secure cookie

**Flow:**
1. Login → Returns access token (body) + refresh token (cookie)
2. Every request: Access token in `Authorization: Bearer {token}` header
3. Token expires: Silent refresh using cookie
4. Refresh fails: Soft logout

**Soft logout:**
- User sees "Session expired. Sign in to continue."
- Current page state preserved
- One-click re-auth (email pre-filled)
- On success, return to exactly where they were

**Edge case - refresh token stolen:**
Refresh tokens are rotated on use. Using a token invalidates it and issues new one.
If attacker uses stolen token, legitimate user's next refresh fails → triggers re-auth.
All sessions can be invalidated from security settings.

### 7.2 Org Context

**Decision:** Org in token, switchable without re-auth.

JWT payload includes:
```
{
  user_id: 'user_123',
  org_id: 'org_456',
  role: 'controller',
  permissions: ['approve_payments', 'view_reports', ...],
  orgs: ['org_456', 'org_789']  // all accessible orgs
}
```

Every API request is scoped to token's `org_id` automatically.

**Org switching:**
```
POST /auth/switch-org
{org_id: 'org_789'}
→ New access token with updated org_id
```

No re-auth needed if user has access. UI shows org switcher in header.

**Edge case - removed from org while active:**
User's access to org is revoked while they're using it.
- Next API call returns 403 with `{code: 'ORG_ACCESS_REVOKED'}`
- Frontend shows: "You no longer have access to [Org]. Contact admin."
- Auto-redirects to org picker if they have other orgs

### 7.3 Roles

**Decision:** API enforces roles with helpful errors.

Roles:
- `viewer` - Read-only access
- `staff` - Can execute decisions up to their limits
- `controller` - Can execute any decision, change some thresholds
- `admin` - Full access including user management

Limits are per-role AND per-user:
- Controller role has $50K approval limit
- But Sarah (Controller) might have custom $25K limit

**API enforcement:**
Every mutation endpoint checks:
1. Role has permission for this action type
2. User's limit (if applicable) covers this amount
3. If either fails: 403 with explanation

```
{
  error: {
    code: 'EXCEEDS_AUTHORITY',
    message: 'This payment exceeds your approval authority',
    details: {
      action: 'approve_payment',
      amount: 75000,
      your_limit: 50000,
      required_role: 'admin'
    },
    suggestion: 'Request approval from an admin, or split into smaller payments'
  }
}
```

### 7.4 Impersonation

**Decision:** Shadow mode + full impersonation with audit.

**Shadow mode (read-only):**
- Support can see exactly what user sees
- No actions possible
- User is NOT notified
- Audit logged: "Support shadowed user at [time]"

**Full impersonation:**
- Support acts as user
- Every action logged: "Action by [support] as [user] - [reason]"
- User is notified (email): "Your account was accessed by Support on [date]. Ticket: #1234"
- Requires:
  - Support role
  - Active ticket ID (linked in audit)
  - Time limit: 1 hour, can extend with justification

**Edge case - support makes mistake while impersonating:**
Audit trail clearly shows who actually did it. User can point to audit: "That wasn't me, it was support ticket #1234."

---

## 8. Errors

### 8.1 Error Format

**Decision:** Structured, actionable, severity-tagged.

Every error response:
```
{
  error: {
    code: 'INVOICE_ALREADY_PAID',           // Machine-readable
    message: 'This invoice was paid on Oct 1',  // Human-readable
    details: {                               // Context
      invoice_id: 'DW-2025-0856',
      paid_date: '2025-10-01',
      payment_id: 'PMT-1234'
    },
    severity: 'warning',                     // info | warning | error | critical
    recoverable: true,                       // Can user retry/continue?
    actions: [                               // What can they do?
      {label: 'View payment', href: '/payments/PMT-1234'},
      {label: 'Apply to different invoice', action: 'select_invoice'}
    ]
  }
}
```

**Severity levels:**
- `info` - Not really an error (e.g., "Already done")
- `warning` - Unexpected but handled (e.g., "Partial success")
- `error` - Failed but recoverable (e.g., "Invalid input")
- `critical` - Failed, needs attention (e.g., "Data corruption detected")

### 8.2 Retry Guidance

**Decision:** Explicit retry contract in error response.

Retryable errors include:
```
{
  error: {
    code: 'ERPNEXT_TIMEOUT',
    retryable: true,
    retry: {
      after_seconds: 30,
      max_attempts: 3,
      strategy: 'exponential'  // or 'fixed'
    }
  }
}
```

Non-retryable errors:
```
{
  error: {
    code: 'INSUFFICIENT_FUNDS',
    retryable: false,
    actions: [
      {label: 'Reduce amount', action: 'edit_amount'},
      {label: 'Transfer funds first', href: '/transfers/new'}
    ]
  }
}
```

Client can auto-retry based on contract. User sees: "Connection issue. Retrying... (2 of 3)"

### 8.3 Graceful Degradation

**Decision:** Clear capability matrix during outages.

**Health endpoint:**
```
GET /health
→ {
    status: 'degraded',
    services: {
      baby_mars: 'healthy',
      erpnext: 'unavailable',
      claude: 'healthy',
      database: 'healthy'
    },
    capabilities: {
      chat: 'full',
      view_tasks: 'full',
      execute_decisions: 'queued',   // Will execute when ERPNext back
      view_widgets: 'cached',
      drill_down: 'unavailable'
    }
  }
```

**UI adapts:**
- ERPNext down: Widgets show cached data with "Offline" badge. Decisions queue with "Will post when connected" message.
- Claude down: Chat shows "I'm having trouble thinking right now. Use widgets directly." Widgets work fine.
- Database down: Everything fails. Full outage page.

**System status:**
Footer or settings page shows current status. During degradation, banner appears: "Some features limited. [Details]"

---

## 9. Offline / Edge

### 9.1 Offline Behavior

**Decision:** Read from cache, write to queue, sync on reconnect.

**When offline:**
- Read operations: Serve from IndexedDB cache if available
- Write operations: Queue in IndexedDB with "pending" indicator

**When back online:**
- Queued writes sync automatically
- If conflict: Don't silently fail

**Conflict resolution:**
User approved payment offline. Meanwhile, Sarah approved it online.
On sync: "This payment was already approved by Sarah while you were offline. Your action wasn't needed."

**Offline indicators:**
- Global: "Offline - changes will sync when connected"
- Per-item: Pending items show "Syncing..." when back online

**Edge case - offline for days:**
Cache might be very stale. On reconnect:
- Sync pending writes first
- Then full refresh of visible data
- User might see significant changes: "A lot happened while you were away. [View summary]"

### 9.2 Mobile

**Decision:** Same API, adaptive responses.

Client header: `X-Client-Type: mobile` (or `desktop`, `tablet`)

**API adaptations for mobile:**
- Default pagination reduced (10 vs 20)
- Heavy nested data excluded by default (add `?expand=true` if needed)
- Attachment thumbnails instead of full files
- Push notification tokens managed

**No separate endpoints.** Same contract, client declares its constraints.

**Edge case - mobile on slow network:**
Client can add `X-Network-Type: slow` header.
- API returns minimal payloads
- Images/attachments replaced with placeholders
- "Load more" instead of auto-pagination

---

## Appendix A: Endpoint Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Send message, get streaming response |
| `/chat/interrupt` | POST | Interrupt current stream |
| `/tasks` | GET | List tasks (filterable by status) |
| `/tasks/{id}` | GET | Full task detail with timeline |
| `/tasks/{id}/timeline` | GET | Just timeline (for refresh) |
| `/decisions/{id}` | GET | Decision detail |
| `/decisions/{id}/execute` | POST | Execute decision |
| `/decisions/{id}/undo` | POST | Undo (if within window) |
| `/beliefs/{id}` | GET | Belief detail with history |
| `/beliefs/{id}/challenge` | POST | Dispute a belief |
| `/thresholds` | GET | List thresholds |
| `/thresholds/{id}` | PUT | Update threshold (auth required) |
| `/data/{widget}` | GET | Widget data |
| `/data/{widget}/{drill_path}` | GET | Drill-down data |
| `/events` | GET (SSE) | Real-time event stream |
| `/health` | GET | System health |
| `/auth/login` | POST | Login |
| `/auth/refresh` | POST | Refresh token |
| `/auth/switch-org` | POST | Switch org context |

---

## Appendix B: Event Types

| Event | Payload | When |
|-------|---------|------|
| `task:created` | `{task_id, type, summary}` | New task |
| `task:updated` | `{task_id, status, summary}` | Status change |
| `task:decision_needed` | `{task_id, decision_id, summary}` | Decision surfaced |
| `task:progress` | `{task_id, stage, progress, detail}` | Long-running progress |
| `decision:made` | `{decision_id, made_by, action}` | Someone decided |
| `data:changed` | `{widget_id, change_type}` | Widget needs refresh |
| `presence:update` | `{task_id, users}` | Who's viewing |
| `aleq:message` | `{message, references}` | Proactive communication |

---

## Appendix C: Decision on Controversial Choices

**Why SSE over WebSocket for events:**
Simpler client, better proxy compatibility, automatic reconnection. We only need server→client for events. The chat stream is the exception (needs backpressure), and that's one WebSocket.

**Why not GraphQL:**
REST is simpler, our data model isn't deeply nested, and we don't have mobile bandwidth constraints that require precise field selection. REST with JSON is understood by every engineer.

**Why 30-second undo window:**
Long enough to catch mistakes, short enough to not create uncertainty. Financial actions need to feel final-ish. Accounting systems downstream might pick up changes within minutes.

**Why no batch endpoints:**
YAGNI. If we need them later, we add them. Single-resource endpoints are easier to reason about, cache, and rate-limit.

---

*This contract is locked as of v0.1.0. Changes require a migration plan documenting: what changes, why, impact on clients, and transition period.*
