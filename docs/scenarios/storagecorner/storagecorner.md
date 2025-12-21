Vertically integrated real estate investment firm focused on self-storage and light industrial properties across the Mountain West. Top-100 U.S. storage owner with 1.14M sq ft under management.

Industry: Real Estate Investment / Self-Storage

Founded: 2015

Headquarters: Los Altos, CA

Portfolio: 23 properties, 6,000 units, 1.14M sq ft (2025)

Strategy: Hub-and-spoke ops, value-add projects, conversions, JV deals

Focus: Sustainability, community-based property management

### Task Name: Budget-to-Actual Reporting for Managers

Quote (Refined):

"For the property managers, I want them looking at their budget-to-actuals. Right now, I literally make them log into QuickBooks themselves and pull the reports, which is not scalable. They can get the high-level numbers, but their next question is always, 'Okay, where did I spend it?' Pulling that detail is extra work, so half the time they don't bother. I don't know if they've actually looked unless I go check or ask."

Category: FP&A, Manager Reporting

Process Type: Workflow → Reporting (Variance Analysis & Drill-Down)

Typical Software Today: QuickBooks, Excel

**Objective:** Provide property managers with clear, actionable variance reports that isolate their controllable expenses and highlight discrepancies in a structured way.

**Workflow Steps:**

1.  Log into QuickBooks and generate a monthly Profit & Loss report segmented by **Class** or **Location** (depending on how properties are structured in the chart of accounts).

2.  Export the report into Excel/Google Sheets with transaction-level detail enabled.

3.  Cross-reference each property manager's expense responsibility list (8--10 key categories such as travel, repairs, utilities, and auctions).

4.  Filter and reorganize the exported report so that only relevant categories are visible to each manager.

5.  Build a standardized manager-facing template:

    -   **Summary tab:** high-level budget vs. actuals with variance ($ and %).

    -   **Detail tab:** transaction-level breakdown for flagged categories.

6.  Apply conditional formatting (e.g., highlight variances over 10% or $500) to make issues obvious.

7.  Save each manager's report into a dedicated folder (cloud drive or BI dashboard).

8.  Push reports out via automated distribution (email/Slack integration with links).

9.  Store a central archive of all manager-facing reports for audit trail.

### Task Name: Report Distribution (Push vs. Pull)

Quote (Refined):

"Instead of forcing managers to log into QuickBooks every time, I'd rather push the reports out to them automatically. Right now it's all self-serve, and that creates friction. I want them to get the data they need without hunting for it."

Category: FP&A, Operations

Process Type: Workflow → Automated Report Distribution

Typical Software Today: QuickBooks (manual exports), Email, BI tools (Power BI, Tableau)

**Objective:** Automate delivery of manager reports to reduce friction and ensure timely review.

**Workflow Steps:**

1.  Set up recurring export schedules in QuickBooks (weekly/monthly, depending on cadence).

2.  Use middleware (Zapier, Power BI scheduled refresh, or Python script) to auto-export data.

3.  Pipe the exported data into a processing layer (Excel macros, Google App Script, or BI transformation).

4.  Generate personalized reports per manager with filters already applied.

5.  Convert reports into PDFs or dashboard links for read-only access.

6.  Automate email distribution:

    -   Subject line standardized: "Monthly Budget Report -- [Property Name]"

    -   Body includes summary stats + link to detailed file.

7.  Embed tracking (read receipts, link tracking, or dashboard logins) to confirm delivery.

### Task Name: Manager-Level Expense Awareness

Quote (Refined):

"Each manager only really controls eight to ten expense lines --- things like travel, repairs, utilities, auctions. They don't need the whole chart of accounts. But QuickBooks doesn't make it easy to isolate just those lines, so they either drown in irrelevant data or don't look at anything at all."

Category: FP&A, Expense Management

Process Type: Informational Access → Contextualized Reporting / Filtering

Typical Software Today: QuickBooks, Excel
**Objective:** Provide managers with visibility only into their controllable expenses, reducing noise and improving accountability.

**Workflow Steps:**

1.  Define expense categories for each manager (document in master responsibility matrix).

2.  In QuickBooks, create **memorized/saved reports** with category filters locked for each manager.

3.  Export filtered data automatically or manually each period.

4.  Reformat into a one-page summary report:

    -   Show only relevant categories.

    -   Include prior month comparison and year-to-date totals.

5.  Deliver as PDF or dashboard link.

6.  Provide optional drill-down tab with transaction-level details but only for those specific accounts.

7.  Ensure consistency across periods to allow managers to track trends.

### Task Name: Expense Variance Investigation

Quote (Refined):

"Say a manager sees they spent $1,000 when their budget was $500. Their next question is always, 'Okay, but where did I spend it?' They need to drill down into the details, check individual transactions, and figure out if it's miscoded or legitimate. Right now that's a manual chase."

Category: FP&A, Accounting

Process Type: Workflow → Variance Investigation & Reconciliation

Typical Software Today: QuickBooks, Excel

**Objective:** Help managers identify and explain causes of budget overruns or miscoded transactions.

**Workflow Steps:**

1.  Run budget-to-actual report for each property with variance thresholds flagged.

2.  Highlight line items exceeding variance thresholds (e.g., >10% or >$500).

3.  Drill into QuickBooks for transaction-level details for those categories.

4.  Export flagged transactions into Excel/Google Sheets.

5.  Categorize each transaction:

    -   Legitimate expense (explainable).

    -   Potential miscoding (needs correction).

    -   Unknown/unverified (requires manager follow-up).

6.  Share variance detail file with manager, requesting explanations for each flagged item.

7.  Collect manager input via shared comments or email responses.

8.  Update QuickBooks coding if corrections are valid.

9.  Record outcomes in a variance tracker for future audit reference.


### Task Name: Feedback & Accountability Gap

Quote (Refined):

"I don't have any feedback loop to know if managers have actually reviewed their reports. I either have to check myself or ask them. There's no system telling me, yes, they opened it, reviewed it, and acknowledged the numbers."

Category: FP&A, Operations

Process Type: Workflow → Review Tracking & Confirmation

Typical Software Today: N/A (manual follow-up, email)

**Objective:** Create a feedback loop that confirms managers reviewed their reports.

**Workflow Steps:**

1.  Attach a digital acknowledgment form to every distributed report (Google Form, Airtable, or workflow task in Asana).

2.  Require managers to check a box confirming review and add optional notes ("Reviewed on [date] -- No issues" or "Reviewed -- Variances flagged").

3.  Responses automatically log into a centralized tracker.

4.  Build a compliance dashboard showing:

    -   % of managers who reviewed reports.

    -   Time taken to respond.

    -   Outstanding acknowledgments.

5.  Send automated reminders to non-responders after 3 business days.

6.  Use acknowledgment data during quarterly reviews to enforce accountability.

### Task Name: Hiring a Report Monitor

Quote (Refined):

"I was literally about to hire a person just to sit between QuickBooks and the managers. Their whole job would be to pull the reports, chase down explanations for odd expenses, and then update QuickBooks. That's how inefficient the loop is today."

Category: FP&A, Operations

Process Type: Workflow → Manual Oversight / Exception Handling

Typical Software Today: N/A (human resource stopgap)

**Objective:** Insert a human resource to bridge the gap between QuickBooks and managers.

**Workflow Steps:**

1.  Assign monitor to run monthly QuickBooks budget-to-actual reports.

2.  Format each report to match manager-level categories.

3.  Distribute reports by email or shared drive.

4.  Follow up with managers directly (phone/email) for explanations of flagged variances.

5.  Record manager responses in variance tracker.

6.  Correct miscoded entries in QuickBooks.

7.  Provide summarized variance log to leadership monthly.

### Task Name: Weekly Bank Balance Collection

Quote (Refined):

"Every week I go through 68 bank accounts across Chase, Glacier/FCB, and Heritage. I pull the current balances one by one and drop them into my worksheet. It's purely manual, so it only happens weekly --- if it were automated, I'd do it daily."

Category: Treasury

Process Type: Workflow → Data Retrieval (Balances)

Typical Software Today: Bank Portals, Excel

### Task Name: Cash Forecast Preparation

Quote (Refined):

"Once I've got all the balances, I drop them into a worksheet so I can compare across accounts. Then based on that activity, I move funds between banks or accounts as needed. It's a manual workflow: gather balances → populate worksheet → decide interbank transfers."

Category: Treasury, FP&A

Process Type: Workflow → Forecasting & Cash Positioning

Typical Software Today: Excel, Bank Portals

**Objective:** Gather balances from 68 bank accounts across multiple banks.

**Workflow Steps:**

1.  Log into Chase, Glacier/FCB, and Heritage bank portals individually.

2.  Navigate to account summary page for each bank.

3.  Copy balances manually into Excel worksheet.

4.  Verify totals match online dashboards.

5.  Date-stamp worksheet and save into treasury folder.

6.  Consolidate all balances into one master tab for total liquidity view.

### Task Name: Gap in Balance Aggregation Tools

Quote (Refined):

"I've tried several tools that claim to pull balances across banks, but none of them meet my needs. Either they don't support my mix of Chase, Glacier, and Heritage, or they're full FP&A suites that start at $30--40k a year. All I want is: pull my balances daily, drop them in a sheet. That's it. Apparently that's too simple for anyone to build."

Category: Treasury, Technology Gap

Process Type: Informational Access → Balance Aggregation

Typical Software Today: FP&A suites (Anaplan, Adaptive), TMS (Expensive), Excel (manual)

**Objective:** Use balances to plan interbank transfers and anticipate obligations.

**Workflow Steps:**

1.  Import balances from weekly collection sheet into forecast model.

2.  Compare actual balances against forecasted expectations.

3.  Update model with recent inflows/outflows (loan payments, distributions, utilities, etc.).

4.  Identify accounts short of required minimums.

5.  Decide whether to transfer funds between accounts or banks.

6.  Initiate transfers using bank portals.

7.  Record transfers in the forecast model to maintain alignment.

### Task Name: Investor Distributions

Quote (Refined):

"I have to do monthly distributions for our investors. The way it works now is I go into QuickBooks, pull the balance, check cash available, and then decide what can go out. It's manual -- I have to cross-check each account and make sure I've got enough liquidity before I push the payments. Then I calculate everyone's portion, run the numbers in a spreadsheet, and finally go into Roam to execute the distribution. The idea is to keep investors happy, so it's not optional. But it's a lot of little steps every month."
Investor Distributions”

⸻

Weekly Cash Forecasting

“Every week, I sit down and pull balances from all 68 of our bank accounts across Chase, Glacier/FCB, and Heritage. I literally log in, grab the numbers, drop them into a worksheet, and then start comparing across accounts. That gives me a sense of whether I’ve got enough to cover loan payments or distributions coming due. It takes about an hour before I can even think about moving money around or making decisions. If this was automated, I’d do it daily, but because it’s manual, it only gets done once a week.”

⸻

Cash Reconciliation

“Once I’ve got those balances, I basically reconcile them against my forecast. I check, okay, here’s what I thought I’d have, here’s what I actually have. If something’s off, I have to figure out why — sometimes it’s just timing, sometimes a distribution hit early. Then I’ll make transfers between accounts to make sure each one is where it needs to be. Again, the time sink is in pulling the balances, but the actual reconciliation is straightforward once I have the data.”

⸻

Expense Reporting / Clarifications

“So today, employees swipe their Ramp cards, and then they upload a receipt and pick a category. That goes into QuickBooks. At the end of the month, I run detailed reports. And then I see things like: travel budget was $500, but they spent $1,000. Then the conversation starts. Where did the extra $500 go? Was it miscoded? Was it legit? I have to ask them, sometimes call them directly, and then I update the record. It’s tedious because it’s detective work — just trying to get clarity so the books are right.”

⸻

Budget-to-Actual Reporting for Managers

“For the property managers, I want them looking at their budget-to-actuals — but right now, I force them to log into QuickBooks themselves and pull their own reports. They can get a high-level report, but then their next question is always, ‘Okay, but where did I spend it?’ Then they have to pull detail, which they rarely do because it takes too much time. So they either don’t review it at all, or they come back to me confused. I don’t get a feedback loop. I don’t know if they’ve actually looked at their numbers unless I ask. Honestly, I was about to hire someone just to sit in the middle, pull the reports, go through them with each manager, and clean up mismatches in QuickBooks.”

⸻

Manager-Level Expense Awareness

“Each manager doesn’t need to see the whole chart of accounts. It’s really only about 8–10 expense lines they control: travel, repairs, utilities, auctions, stuff like that. But the problem is QuickBooks doesn’t make it easy to isolate just those lines for them. So they either drown in irrelevant data or don’t look at anything.”

⸻

Debt Covenant & Expense Ratio Analysis

“Quarterly, we do P&L reviews. That’s where I have to massage the numbers to reflect reality — strip out one-off CapEx, smooth lumpy stuff like property taxes, and put it in what I call a quasi-accrual format. Then from there I check debt covenants, expense ratios, coverage ratios, whether we’re distributing too much or too little. It’s not just pulling data. It’s manipulating it so I can actually compare across quarters and not get thrown off by a one-time spike.”

⸻

What-If Scenarios

“Something I don’t do today — but should — is run what-if scenarios. Like, if we hit our business plan, what happens to our distribution coverage ratios? What if revenues come in light? I don’t have a system that projects that for me. QuickBooks just sits there. To do this now, I’d have to build separate models in Excel, and I just don’t have the bandwidth.”

⸻

Email Triage for Payment Requests

“We’ve got a general inbox where anyone who wants to get paid sends their invoice. Right now, someone has to sit in there and sort: these are autopays we can ignore, these ones need to be keyed into Roam for manual payment, do we have the right tax info, do we have an approval. It’s a terrible job. All day sorting through a pile of emails just to figure out what actually needs action.”

⸻

Bill Payment Workflow

“We used to be on Bill.com. That was decent because you could forward an invoice to an email address and it would parse it, upload, and try to match the vendor. But now we’re on Roam. Roam has a similar feature, but we don’t use it because it doesn’t know which entity to pay from. If PG&E bills come in, we have ten different locations all with PG&E. Roam doesn’t know whether to pay from Pacifica’s account or Marina’s. So we still end up deleting and rekeying because the context isn’t there.”

⸻

Entity & Bank Account Matching

“Take PG&E as the example. All my California sites use them. I get the bills, and unless you know the exact property, you could easily pay it out of the wrong entity. Right now, that’s all human judgment. Somebody has to look at the bill, figure out which property it belongs to, and then pay from the right bank account. If a system could just recognize that and route it correctly, that’d save a ton of headaches.”

⸻

P&L Review – Manager Involvement

“When managers do look at their reports, half the time they tell me, ‘Yeah, I coded it here, but it could have gone there. What do you want me to do?’ They don’t always know the right classification. I end up being the referee. It works, but it wastes cycles, and I’m the bottleneck.”

⸻

Hiring Human Report Monitor

“I was literally considering hiring a person just to sit between QuickBooks and the managers. Their whole job would be to pull the reports, chase down explanations for odd expenses, and update QuickBooks. That’s how inefficient this loop is today.”

⸻

Gap in Balance Aggregation Tools

“I’ve looked at a bunch of tools that claim to aggregate balances across banks. Either they don’t work with the mix of Chase, Glacier, and Heritage we use, or they’re FP&A suites that start at $30–40k a year. All I want is: pull my balances daily, drop them into a sheet. That’s it. But apparently, that’s not enticing enough for anyone to build.”


🏦 Distributions & Reconciliations
==================================

### **10\. Investor Distributions**

**Objective:** Execute monthly investor payouts while ensuring liquidity sufficiency.

**Workflow Steps:**

1.  Pull latest balances from QuickBooks and bank portals.

2.  Confirm operating expenses and loan obligations are covered.

3.  Calculate distributable cash using waterfall rules (reserve requirements, covenants).

4.  In Excel, calculate each investor's share based on ownership percentages.

5.  Review allocation for compliance with partnership agreements.

6.  Create payment batch in Roam with investor account details.

7.  Approve and release payments.

8.  Archive distribution allocation sheet and Roam payment confirmations.

* * * * *

### **11\. Weekly Cash Forecasting**

**Objective:** Provide rolling view of cash position across all entities.

**Workflow Steps:**

1.  Pull balances from 68 accounts.

2.  Input balances into forecast model.

3.  Compare to forecasted balances from prior week.

4.  Analyze discrepancies and annotate causes.

5.  Update forward-looking forecast for next week's expected inflows/outflows.

6.  Share summarized forecast with leadership team.

* * * * *

### **12\. Cash Reconciliation**

**Objective:** Match actual balances against forecast and correct mismatches.

**Workflow Steps:**

1.  Import latest actual balances into reconciliation sheet.

2.  Compare side-by-side with forecasted values.

3.  Investigate differences:

    -   Timing issues (e.g., deposit cleared later than expected).

    -   Unexpected expenses or distributions.

4.  Annotate reason codes for each variance.

5.  Adjust forecast model assumptions.

6.  Transfer funds to rebalance accounts as needed.

* * * * *

📑 Expense Management Workflows
===============================

### **13\. Expense Reporting / Clarifications**

**Objective:** Validate Ramp/QuickBooks expenses and correct misclassifications.

**Workflow Steps:**

1.  At month-end, export Ramp card transaction detail (with receipts).

2.  Sync or import transactions into QuickBooks.

3.  Run detailed monthly expense report by category.

4.  Identify categories with budget overages.

5.  Review flagged transactions manually.

6.  Contact employees for missing receipts or clarifications.

7.  Record employee responses and decide if expense is legitimate or miscoded.

8.  Update QuickBooks coding as required.

9.  Save annotated expense report in central folder.

* * * * *

### **14\. Debt Covenant & Expense Ratio Analysis**

**Objective:** Ensure compliance with loan covenants on a quarterly basis.

**Workflow Steps:**

1.  Pull quarterly P&L and Balance Sheet reports.

2.  Adjust numbers to quasi-accrual format (remove CapEx, smooth property taxes).

3.  Consolidate across properties into master Excel file.

4.  Calculate required ratios:

    -   Debt service coverage ratio.

    -   Expense-to-revenue ratios.

    -   Distribution coverage ratio.

5.  Compare to thresholds in loan agreements.

6.  Highlight any covenant breaches or risk areas.

7.  Share analysis with leadership and lenders (if required).

* * * * *

### **15\. What-If Scenarios**

**Objective:** Build models to test different operating assumptions.

**Workflow Steps:**

1.  Duplicate base Excel forecast model.

2.  Create assumption tabs (occupancy, rent growth, expense inflation).

3.  Input scenario adjustments (e.g., --5% occupancy, +10% utilities).

4.  Recalculate outputs: coverage ratios, distribution amounts.

5.  Compare results across multiple scenarios in dashboard format.

6.  Present findings to leadership for decision-making.

* * * * *

💳 AP / Payment Workflows
=========================

### **16\. Email Triage for Payment Requests**

**Objective:** Sort invoices in AP inbox into appropriate processing queues.

**Workflow Steps:**

1.  Monitor AP inbox daily.

2.  Categorize incoming emails:

    -   Autopay confirmation (archive).

    -   Manual payment request (to Roam).

    -   Missing tax/approval info (flag for follow-up).

3.  Forward manual payments to AP processing queue.

4.  Request missing info from vendor if incomplete.

5.  Update AP tracker with invoice status.

* * * * *

### **17\. Bill Payment Workflow (Roam)**

**Objective:** Ensure invoices are paid correctly through Roam.

**Workflow Steps:**

1.  Receive invoice (from email or upload).

2.  Parse vendor, property, and amount.

3.  Identify correct entity and bank account for payment.

4.  Input invoice into Roam.

5.  Route for manager/lead approval if required.

6.  Approve and release payment.

7.  Save confirmation file to AP archive.

* * * * *

### **18\. Entity & Bank Account Matching**

**Objective:** Avoid misallocating payments to the wrong property/entity.

**Workflow Steps:**

1.  When invoice is received, check service address or account number.

2.  Match details against entity-property mapping database.

3.  Confirm correct bank account tied to entity.

4.  Code payment in Roam with verified entity.

5.  Route for approval and release.

6.  Record mapping logic for audit trail.

* * * * *

### **19\. P&L Review -- Manager Involvement**

**Objective:** Resolve coding disputes with managers to improve accuracy.

**Workflow Steps:**

1.  Distribute P&L report with flagged categories to manager.

2.  Schedule review meeting or request written feedback.

3.  Walk through questionable line items.

4.  Allow manager to suggest alternate coding.

5.  Finance lead makes final classification decision.

6.  Update QuickBooks coding accordingly.

7.  Save meeting notes or correspondence in variance tracker.

* * * * *
