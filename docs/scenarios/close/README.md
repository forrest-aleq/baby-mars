# Reactive Conversation - 33 Scenarios

**Status**: These 33 scenarios work for **REACTIVE conversation only** (user asks → Aleq calls tool → answers). They do NOT use proactive intelligence (AttentionalAgent, PatternDetector, Scheduler).

## What "Reactive Conversation" Means

Aleq can handle these scenarios when a user explicitly asks, using:

1. **Main Graph** tool calling system that invokes any Stargate capability
2. **Stargate** 340 capabilities across 27 platforms (QuickBooks, Plaid, Stripe, etc.)
3. **Conversation intelligence** to ask clarifying questions
4. **Learning loop** (`consolidate_memory`) for entity resolution

**Critical Limitation:** This is NOT the full brain - just conversation + tools + learning

## Example: Treasury/Cash Management

**What Works Today (Reactive):**
```
User: "What's our cash balance?"
Aleq: *calls plaid.balance.get*
Aleq: "You have $45,230 across 3 accounts."

User: "Can we cover Friday's $28k payroll?"
Aleq: *calls plaid.transactions.sync*
Aleq: "$45k available, $8k pending. Net: $37k. ✅ Safe."
```

**What's Missing (Proactive):**
```
User: "What's our cash balance?"
Aleq: *calls plaid.balance.get*
Aleq: "$45,230 across 3 accounts."

[AttentionalAgent detects query priority: MEDIUM]
[PatternDetector runs in background...]
[Finds pattern: Cash dropped 18% week-over-week (p=0.03)]

Aleq: "⚠️ Also noticed: Your cash dropped 18% this week ($55k → $45k).
That's unusual - your 90-day average is 2% weekly decline.
Want me to investigate what changed?"
```

**This folder contains scenarios that work REACTIVELY but need proactive intelligence to be production-ready.**

## Capabilities Used

| Category | Stargate Capabilities | Examples |
|----------|----------------------|----------|
| **Banking** | 63 capabilities | `plaid.balance.get`, `plaid.transactions.sync`, `brex.get_account_balance` |
| **QuickBooks** | 31 capabilities | `invoice.list_outstanding`, `payment.apply_to_invoice`, `budget.get`, `report.profitloss.detail` |
| **Stripe** | 20+ capabilities | `customer.search`, `subscription.list`, `invoice.retrieve` |
| **Other** | 226 capabilities | Bill.com, NetSuite, Recurly, Mercury, Chase, etc. |

## Scenarios Breakdown

**AP/AR Processing** (11 scenarios):
- Maria Santos (fully implemented subgraph exists)
- Marco Thompson, Kevin Chen, Lisa Chen
- Diana Rodriguez, Sarah Chen, etc.

**Treasury/Cash** (5 scenarios):
- Lisa Rodriguez, Angela Park, Michael Davis
- Rachel Torres, David Kim

**Analytics/Reporting** (9 scenarios):
- Rachel Kim (variance), Alex Thompson (revenue)
- Jordan Blake, Jessica Kim, Robert Kim
- David Park, Michael Torres, etc.

**Real Estate** (6 scenarios):
- Jennifer Walsh, Patricia Santos, Samantha Lee
- Marcus Rodriguez, Carlos Martinez, Thomas Chen

**Other** (2 scenarios):
- Sarah Martinez (controller), Sarah (company example)

## What's NOT in This Folder

**3 scenarios that need custom development** (in parent folders):
1. **amanda_torres_covenant_analyst** - Debt covenant monitoring (needs ratio calculation engine)
2. **elena_martinez_entity_specialist** - Complex multi-entity allocation (needs allocation rules)
3. **jonathan_walsh_fund_manager** - Fund accounting (needs fund-specific GL logic)

Plus summary files: `dockwa.md`, `gghc.md`, `storagecorner.md`, `gghc-level3.md`

## Reality Check: What Actually Works

### Reactive Capabilities (100% Implemented)
- ✅ **Stargate capabilities**: 340 tools registered and working
- ✅ **Main Graph tool calling**: Conversational orchestration works
- ✅ **Conversation intelligence**: 3-turn opening, rapport hooks, readiness scoring
- ✅ **Learning loop**: Entity resolution with [:IS_ALIAS_FOR] relationships

### Proactive Intelligence (NOT Implemented)
- ❌ **AttentionalAgent**: 948 lines exist, NOT deployed
- ❌ **PatternDetector**: 1915 lines exist, NOT integrated into Main Graph
- ❌ **Scheduler Service**: Designed but NOT implemented
- ❌ **Background monitoring**: No proactive alerts, pattern detection, or automation

### Honest Scenario Breakdown

| Implementation Level | Count | % | What Works | What's Missing |
|---------------------|-------|---|------------|----------------|
| **Fully Works** | 14 | 35% | Simple reactive queries, entity resolution | Nothing (for reactive use) |
| **Partially Works** | 19 | 48% | Reactive conversation | Proactive intelligence, patterns, alerts |
| **Doesn't Work** | 7 | 18% | Nothing | Background monitoring, automation, scheduling |

**Examples of "Fully Works" (14 scenarios):**
- "What's my bank balance?" → plaid.balance.get
- "Show outstanding invoices" → invoice.list_outstanding
- "Who is vendor X?" → vendor.list + entity resolution

**Examples of "Partially Works" (19 scenarios):**
- Budget variance: ✅ User asks → calculates variance | ❌ Monthly auto-report, variance alerts
- Cash monitoring: ✅ User asks → checks balance | ❌ Trend alerts, burn rate warnings
- Expense analysis: ✅ User asks → shows expenses | ❌ Fraud detection, anomaly alerts

**Examples of "Doesn't Work" (7 scenarios):**
- Covenant monitoring (needs scheduled ratio checks)
- Fund accounting (needs daily NAV calculations)
- Treasury analysis (needs daily liquidity monitoring)
- Strategic insights (needs quarterly pattern analysis)

## Next Steps: Activate the Brain (NOT Stamp Out 33 Scenarios)

**DO NOT build 33 specialized subgraphs.** Focus on proving the architecture works end-to-end, THEN activate proactive intelligence.

### Phase 1: Prove the Vertical Slice (Maria Santos)
1. ✅ Entity Resolution (5-step cascade) - DONE
2. ✅ Payment Allocation (6 strategies) - DONE
3. ✅ Learning Loop (consolidate_memory) - DONE
4. ❌ Gmail Integration - Gmail webhook code exists, needs 1-time watch setup
5. ❌ E2E Test - Second email must process autonomously (proves learning)

**Why Maria Santos First:** Proves all three pillars (trust, skills, intelligence) of Definition of Done.

### Phase 2: Activate Proactive Intelligence (7-10 weeks)
1. **Wire up PatternDetector** (2-3 weeks)
   - Integrate into Main Graph as background job
   - Connect to insight_synthesis node
   - Test with cash balance scenario (detect 18% drop pattern)

2. **Deploy AttentionalAgent** (2-3 weeks)
   - Start as separate service
   - Wire up EventBus communication
   - Enable background cognitive triage

3. **Build Scheduler Service** (3-4 weeks)
   - Implement monthly/weekly/daily triggers
   - Connect to workflow automation
   - Enable proactive reports

**THEN** these 33 scenarios will work with full proactive intelligence.

---

**Last Updated**: 2025-11-10
**Reality**: 14 scenarios (35%) fully work, 19 (48%) partially work, 7 (18%) don't work
**Current State**: Fancy chatbot with API access + learning
**Target State**: Proactive colleague with pattern detection (requires brain activation)
