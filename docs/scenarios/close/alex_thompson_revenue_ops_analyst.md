# Story 1: Dockwa Revenue Operations - Lockbox PDF to Recurly & NetSuite Reconciliation
## **Difficulty Level: 2 (Hard)**

```json
{
  "story_metadata": {
    "bluebook_reference": {
      "row_number": 89,
      "canonical_role": "Revenue Operations Analyst",
      "seniority_band": "Mid-Level",
      "task_description": "Lockbox PDF reconciliation and payment processing (daily batch)",
      "estimated_hours": 3.5,
      "fully_loaded_cost_usd": 245.00,
      "automation_susceptibility": 4
    },
    "process_complexity": {
      "total_workflow_steps": 52,
      "system_interactions": 6,
      "human_interactions": 3,
      "decision_points": 14,
      "exception_handling_scenarios": 8
    },
    "cognitive_load": {
      "simultaneous_systems": 4,
      "context_switching_events": 18,
      "regulatory_compliance_checks": 3,
      "cross_functional_coordination": 2
    },
    "interaction_patterns": {
      "phone_calls_required": 1,
      "email_escalations": 2,
      "slack_messages": 3,
      "approval_workflows": 2,
      "system_lookups": 23
    },
    "technical_complexity": {
      "software_applications_used": ["Chrome Browser", "First Republic Bank Portal", "Recurly", "Excel", "Slack", "Email", "PDF Viewer"],
      "transaction_codes_executed": ["Payment Application", "Customer Lookup", "Invoice Search", "Account Balance Check"],
      "manual_calculations": 12,
      "data_validation_steps": 16
    },
    "time_pressure_factors": {
      "deadline_criticality": "High",
      "interruption_frequency": "Low",
      "multitasking_requirements": "Medium",
      "error_recovery_complexity": "Medium"
    }
  }
}
```

### Alex's Daily Digital Detective Work

Alex Thompson pulls her MacBook Pro open at exactly 8:47 AM, the familiar Apple startup chime barely audible through her AirPods Pro. She's been Dockwa's Revenue Operations Analyst for 18 months now, and every morning starts the same way: checking her Gmail for the dreaded lockbox PDF from First Republic Bank. As a 26-year-old former accounting major who thought she'd escaped manual data entry when she landed this "operations analyst" role, Alex has learned that SaaS revenue operations is 70% spreadsheet archaeology and 30% system integration headaches.

Her iPhone buzzes with a Slack notification from Kevin, the engineering manager: "Morning Alex! Any ETA on the September ARR reconciliation? Sarah's asking about the board deck numbers again."

Alex types back quickly: "Working on it now. Lockbox came in with 23 payments yesterday - should have everything reconciled by lunch 🤞"

But she knows "by lunch" is optimistic. The lockbox process that should take 30 minutes somehow always stretches into 3+ hours of cross-system detective work.

**8:52 AM - The Gmail Hunt**

Alex opens Chrome and navigates to gmail.com. She types "alex.thompson@dockwa.com" and hits enter, then waits the usual 3 seconds for the password manager popup. She clicks on her saved password and Gmail loads with 47 unread emails since yesterday at 6 PM.

She immediately hits Command+F and searches for "lockbox" to filter through the noise. Two results appear:

1. "Daily Lockbox Report - September 30, 2025" from lockbox@firstrepublic.com (received 5:23 AM)
2. "Re: Lockbox Processing Question" from Sarah Martinez, Dockwa's CFO (received 7:41 AM)

Alex clicks on the CFO email first: "Alex - quick question about yesterday's lockbox. Did that $4,750 payment from Marina Bay get applied to the right subscription? Their customer success manager is asking. -Sarah"

Alex makes a mental note to double-check Marina Bay's payment after she processes today's batch. She clicks on the lockbox email and sees the familiar PDF attachment: "DockwaLockbox_20250930.pdf (247 KB)."

**9:01 AM - The PDF Download Dance**

Alex clicks on the PDF attachment and waits for the preview to load in Gmail's viewer. The document opens showing "First Republic Bank - Commercial Lockbox Services" at the top, followed by a table that makes her heart sink: 23 line items representing individual check deposits from marina customers.

She clicks the download icon and the file saves to her Downloads folder as "DockwaLockbox_20250930.pdf." Alex opens Finder, navigates to Downloads, and double-clicks the PDF. It opens in Preview, and she immediately notices the inconsistent formatting that's plagued her for months:

**Row 1:** HARTWELL MARINA INC | CK# 4729 | $2,850.00 | INV: DW-2025-0847
**Row 2:** SeaBreeze Yacht Club | Check Number: 1847 | Amount: $1,200.00 | Invoice DW-2025-0923
**Row 3:** Marina del Rey Storage | 3829 | 875.00 | DW-2025-0856
**Row 4:** PACIFIC HARBOR | CHECK 2847 | $3,200.00 | DW-2025-0901

The formatting chaos is exactly why her "AI script experiment" failed spectacularly three months ago. Every bank formats these PDFs differently, and even within the same bank, the format changes based on how customers write their checks.

**9:08 AM - The Excel Setup Ritual**

Alex Command+Tab switches to Excel and opens her template: "Lockbox_Processing_Template_2025.xlsx" from her Desktop. The spreadsheet has evolved over 18 months into a sophisticated tracking system:

- **Column A:** Date Processed
- **Column B:** Bank Reference Number
- **Column C:** Customer Name (cleaned)
- **Column D:** Check Number
- **Column E:** Amount
- **Column F:** Invoice Number (if found)
- **Column G:** Recurly Customer ID (lookup)
- **Column H:** Recurly Status (Applied/Pending/Error)
- **Column I:** NetSuite Journal Entry #
- **Column J:** Notes/Issues

She scrolls to the next empty row (Row 247) and starts the tedious manual entry process. For the first entry, she types:

**A247:** =TODAY()
**B247:** FRBK-20250930-001
**C247:** Hartwell Marina Inc
**D247:** 4729
**E247:** 2850
**F247:** DW-2025-0847

But when she gets to column G (Recurly Customer ID), she needs to switch systems.

**9:17 AM - The Recurly Deep Dive**

Alex opens a new Chrome tab and navigates to app.recurly.com. The login page loads and she clicks "Sign in with Google" since Dockwa uses Google Workspace SSO. After a 4-second authentication dance, she lands on Recurly's dashboard showing:

- **Active Subscriptions:** 2,847
- **September MRR:** $347,293
- **Churn Rate:** 6.8%

Alex clicks on "Customers" in the left sidebar, then uses the search box to look up "Hartwell Marina." Three results appear:

1. Hartwell Marina Inc (ID: cus_hartwell_marina_inc_2023)
2. Hartwell Marine Services (ID: cus_hartwell_marine_2024)
3. Hartwell Holdings LLC (ID: cus_hartwell_holdings_2025)

This is the first decision point that requires human judgment. Alex clicks on the first result and reviews the account details:

- **Address:** 1247 Harbor Way, Sausalito, CA 94965
- **Subscription:** Premium Marina Management ($285/month)
- **Status:** Active
- **Last Payment:** August 30, 2025 ($285.00)

The $2,850 payment represents 10 months of subscription fees, suggesting either a prepayment or they're catching up on overdue invoices. Alex clicks on the "Billing" tab and sees several unpaid invoices dating back to January 2025. This explains the large payment.

She clicks on invoice DW-2025-0847 (matching the reference from the check) and confirms it's for $285.00 from September. But the $2,850 payment should cover multiple invoices.

**9:31 AM - The Payment Application Chess Game**

Alex navigates Recurly's payment application interface:

**Software Navigation - Payment Application:**
Alex works within the Recurly customer account interface:
- **Button Click:** "Apply Payment" button in top right of customer account screen
- **Payment Modal:** Pop-up window opens with payment application form
- **Field Entry:**
  - **Amount Field:** Types "$2,850.00" (auto-formats with currency)
  - **Payment Method Dropdown:** Selects "Check" from dropdown list
  - **Check Number Field:** Types "4729"
  - **Date Picker:** Clicks calendar icon → navigates to September 2025 → clicks "30"
  - **Reference Field:** Types "FRBK-20250930-001"
- **Auto-Allocation:** Clicks "Suggest Allocation" button
- **System Processing:** Recurly algorithm runs for 3-4 seconds, shows loading spinner

Recurly's auto-allocation feature suggests applying the payment across the 10 oldest unpaid invoices, which totals exactly $2,850. Alex reviews the suggested allocation in the allocation table:

- January invoice: $285
- February invoice: $285
- March invoice: $285
- April invoice: $285
- May invoice: $285
- June invoice: $285
- July invoice: $285
- August invoice: $285
- September invoice: $285
- October invoice: $285

Alex clicks "Apply Payment" and Recurly processes the allocation. The customer's account now shows $0 outstanding balance and their subscription status remains "Active."

She switches back to Excel and updates her tracking:

**G247:** cus_hartwell_marina_inc_2023
**H247:** Applied - 10 invoices cleared

**9:43 AM - The NetSuite Journal Entry Marathon**

Now comes the accounting side. Alex opens another Chrome tab and navigates to netsuite.com. She enters her login credentials:

- **Email:** alex.thompson@dockwa.com
- **Password:** [she types her complex password from memory]
- **Account:** Dockwa_Production

NetSuite's loading screen appears with the familiar "Loading your data..." progress bar. After 8 seconds, she lands on the dashboard showing September's financial snapshot.

Alex navigates to Transactions → General → Journal Entries and clicks "New." The journal entry form loads, and she begins the accounting work:

**Journal Entry #2025-3847:**

**Line 1:**
- Account: 1100 - Cash - First Republic Checking
- Debit: $2,850.00
- Memo: Lockbox deposit - Hartwell Marina Inc Check #4729

**Line 2:**
- Account: 1200 - Accounts Receivable - Customers
- Credit: $2,850.00
- Customer: Hartwell Marina Inc
- Memo: Payment application - Invoices Jan-Oct 2025

Alex saves the journal entry and it gets assigned number JE-2025-3847. She switches back to Excel and updates:

**I247:** JE-2025-3847

**9:58 AM - The Second Entry Complexity**

Alex moves to the second lockbox entry: SeaBreeze Yacht Club for $1,200. She follows the same Recurly lookup process but hits an immediate snag. When she searches "SeaBreeze" in Recurly, she gets zero results.

She tries variations:
- "Sea Breeze" (no results)
- "Seabreeze" (no results)
- "Yacht Club" (47 results - too many to review)

This is a common problem: customers write checks with slightly different business names than their Recurly account names. Alex tries a different approach. She looks up invoice DW-2025-0923 directly by entering it in Recurly's invoice search.

The invoice appears linked to "SB Yacht Club LLC" (Customer ID: cus_sb_yacht_club_2024). The invoice is for $120/month marina management software, and this $1,200 payment represents 10 months of prepayment.

**10:14 AM - The Prepayment Accounting Dilemma**

Alex applies the $1,200 payment in Recurly, but realizes she needs to handle the accounting differently. Since this is a prepayment for future services, she can't record it all as current revenue. She needs to create a journal entry that recognizes only October's $120 as revenue and the remaining $1,080 as deferred revenue.

In NetSuite, she creates journal entry JE-2025-3848:

**Line 1:**
- Account: 1100 - Cash - First Republic Checking
- Debit: $1,200.00

**Line 2:**
- Account: 1200 - Accounts Receivable - Customers
- Credit: $120.00
- Customer: SB Yacht Club LLC

**Line 3:**
- Account: 2400 - Deferred Revenue
- Credit: $1,080.00
- Customer: SB Yacht Club LLC
- Memo: Prepayment for Nov 2025 - Aug 2026 service

**10:31 AM - The Data Quality Nightmare**

By the fourth entry, Alex encounters what she calls "data quality hell." The lockbox shows:

**Marina del Rey Storage | 3829 | 875.00 | DW-2025-0856**

When she searches for this invoice in Recurly, it doesn't exist. DW-2025-0856 was never issued. Alex opens her phone and calls the customer success team.

"Hey Jessica, it's Alex from Revenue Ops. I've got a check for $875 from Marina del Rey Storage referencing invoice DW-2025-0856, but that invoice doesn't exist in Recurly. Can you help me figure out what this payment is for?"

Jessica responds: "Oh, Marina del Rey! Yeah, they're on our legacy billing system still. We've been trying to migrate them to Recurly for months, but they have a custom integration that's been problematic. Their invoices are still generated manually and tracked in the old system."

Alex sighs. "So how do I process this payment?"

"Let me check their account... okay, they owe $175 for each of the last five months - May through September. That's $875 total. You can create a manual invoice in Recurly to match and then apply the payment."

**10:47 AM - The Manual Invoice Creation**

Alex navigates to Recurly's invoice creation page and manually creates invoice DW-2025-0856:

- **Customer:** Marina del Rey Storage
- **Amount:** $875.00
- **Description:** May-Sept 2025 Marina Management Software (5 months @ $175/month)
- **Service Period:** May 1 - Sept 30, 2025

She saves the invoice and immediately applies the $875 payment against it. Then she creates the corresponding NetSuite journal entry.

**11:15 AM - The Bulk Processing Acceleration**

Alex realizes she's only processed 4 out of 23 payments and it's already been over 2 hours. She shifts into "bulk mode" - accepting slightly less precision for speed. For the remaining 19 payments, she:

1. Groups similar payment amounts (multiple $285 payments likely represent standard monthly subscriptions)
2. Uses Excel's VLOOKUP function to match customer names against a pre-built Recurly customer database export
3. Applies payments in batches where possible

**11:52 AM - The Reconciliation Reality Check**

Alex finishes processing all 23 payments and runs her reconciliation check:

**Lockbox Total:** $23,847.50
**Recurly Payments Applied:** $23,847.50 ✓
**NetSuite Journal Entries:** $23,847.50 ✓

The numbers match, but Alex knows she needs to verify that each payment was applied to the correct customer. She exports a payment report from Recurly and cross-references it against her Excel tracking sheet.

She finds two discrepancies:
1. A $285 payment was applied to the wrong Hartwell entity
2. A $450 payment was split across two invoices when it should have been applied to one

**12:18 PM - The Error Correction Process**

Alex reverses the incorrect Recurly payment applications and reapplies them correctly. This requires:

1. Voiding the original payment applications in Recurly
2. Creating new payment applications with correct customer/invoice mapping
3. Updating the NetSuite journal entries to reflect the corrections
4. Documenting the changes in her Excel tracking sheet

**12:41 PM - The Documentation and Communication**

Alex creates her daily lockbox summary email:

"Subject: Daily Lockbox Processing Complete - Sept 30 ($23,847.50)

Hi team,

September 30 lockbox processing is complete. Summary:

**Key Metrics:**
- Total deposit: $23,847.50
- Number of payments: 23
- Average payment: $1,036.85
- Processing time: 3 hours, 54 minutes

**Notable Items:**
- Hartwell Marina caught up on 10 months of outstanding invoices ($2,850)
- SeaBreeze Yacht Club made 10-month prepayment (requires deferred revenue accounting)
- Marina del Rey Storage payment required manual invoice creation (legacy system issue)

**Next Steps:**
- September ARR reconciliation in progress
- Board deck numbers will be ready by 2 PM

**Issues for Follow-up:**
- Marina del Rey migration to Recurly still pending (Jessica CC'd)
- Consider automated prepayment handling for large subscription customers

All supporting documents saved to: Shared Drive/Finance/Lockbox/2025/September/

Alex"

**12:48 PM - The Reflection**

As Alex closes her laptop for a much-delayed lunch, she reflects on the morning's work. What should be a 30-minute automated process took nearly 4 hours and required dozens of judgment calls that no script could handle:

- Customer name variations and matching logic
- Invoice reference errors and lookups
- Prepayment vs. current revenue accounting decisions
- Legacy system integration workarounds
- Error correction and audit trail maintenance

She opens her Notes app and adds to her running list of "Lockbox Process Improvement Ideas":

- Build customer name fuzzy matching database
- Create prepayment detection logic
- Automate simple 1:1 invoice payment applications
- Integrate legacy billing system with Recurly
- Add payment application approval workflow

But she knows that until Dockwa invests in serious process automation, tomorrow morning will start exactly the same way: Gmail, PDF download, Excel setup, and 3+ hours of digital detective work that somehow keeps a $12M ARR SaaS business running smoothly.

Alex texts her boyfriend: "Lunch at 1 PM? Had to process 23 check payments manually this morning 🙃"

He responds: "Wait, people still write checks in 2025?"

Alex laughs and types back: "Welcome to B2B SaaS revenue operations..."
