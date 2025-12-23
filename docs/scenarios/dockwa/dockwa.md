Vertical SaaS platform for marina management and boater reservations, enabling digital booking, storage, and payments. Founded in 2014, headquartered in Newport, RI.

Industry: Vertical SaaS / Marina Management

Founded: 2014

Headquarters: Newport, Rhode Island

Funding: Series B (backed by Insight Partners and others)

Customers: Marinas, boatyards, yacht clubs, individual boaters

Core Products: Reservations, storage, dockage, payments, comms tools

Task Name: Lockbox PDF to Recurly & NetSuite

Quote (Rewritten):

"So we've got a bank lockbox set up, which is great because at least we don't have to physically pick up the checks anymore. The bank emails us a PDF with all the deposits. But right now it's still completely manual --- I have to open that PDF, pull out the check details, drop them into a spreadsheet just to keep it centralized, then I go into Recurly to apply the payments against subscriptions, and finally I log into NetSuite and key in the journal entries. If it's just one check, fine. But when it's 20 or 30, it's a total time sink. That's the part I'd love to automate end-to-end."

Category: Accounts Receivable / Cash Application

Process Type: Workflow → Lockbox Processing → Payment Application → Journal Entry

Typical Software Today: Bank lockbox portal, Excel, Recurly, NetSuite

From that Dockwa call, the CFO laid out a few distinct flows beyond the lockbox PDF → Recurly → NetSuite one. Here's each one rewritten in the same dictation style:

1\. Invoice Processing & PDF Parsing

Quote (Rewritten):

"I even tried writing a little AI script to read the lockbox PDFs and push them into a spreadsheet automatically. But the way the bank formats those PDFs is all over the place --- sometimes the invoice number is here, sometimes there, sometimes it doesn't even look like an invoice. So the script could never get it right. In the end, I'm still eyeballing it and retyping numbers, which defeats the purpose."

Category: Accounts Receivable / Automation

Process Type: Workflow → Data Extraction → Reconciliation

Typical Software Today: Custom scripts, OCR tools, Excel

2\. Vendor / Payment Processing

Quote (Rewritten):

"All of our payment processing runs through Stripe. That's been fine --- it works across all our properties. We're trying to be a true vertical SaaS, so Stripe is kind of the backbone there. But once the payments clear, we still have to make sure vendors get paid and everything reconciles correctly. That's where it gets messy, because we're still juggling Recurly, Stripe, and the accounting system separately."

Category: Accounts Payable / Payment Processing

Process Type: Workflow → Payment Processing & Vendor Management

Typical Software Today: Stripe, Recurly, QuickBooks/NetSuite

3\. Bank Reconciliation

Quote (Rewritten):

"Every month our controller goes into NetSuite, pulls the bank statements --- sometimes PDFs, sometimes Excel --- and does the reconciliation line by line. We're always on the lookout for unusual transactions or fraud, so it can't just be automated blindly. But the matching part, the mechanics of lining up deposits and withdrawals against the GL, that's still a very manual process."

Category: Accounting / Bank Reconciliation

Process Type: Workflow → Bank Statement Reconciliation

Typical Software Today: NetSuite, Excel

4\. Research & Analysis (FP&A / Investments)

Quote (Rewritten):

"A lot of where we've actually found AI helpful is in research --- almost like a junior analyst. We can ask ChatGPT to analyze companies, compare fundamentals, refine criteria, and it can pull insights that would normally take a junior person a week to crank out. Where it hasn't really helped yet is in the repetitive finance workflows --- the reconciliations, the journal entries --- those are still wide open."

Category: FP&A / Research & Analysis

Process Type: Information Access → Q&A & Analysis

Typical Software Today: ChatGPT, Excel, custom FP&A models


📊 FP&A & Manager Reporting Workflows
=====================================

* * * * *

### **1\. Budget-to-Actual Reporting for Managers**

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

* * * * *

### **2\. Report Distribution (Push vs. Pull)**

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

* * * * *

### **3\. Manager-Level Expense Awareness**

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

* * * * *

### **4\. Expense Variance Investigation**

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

* * * * *

### **5\. Feedback & Accountability Gap**

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

* * * * *

### **6\. Hiring a Report Monitor (Stopgap)**

**Objective:** Insert a human resource to bridge the gap between QuickBooks and managers.

**Workflow Steps:**

1.  Assign monitor to run monthly QuickBooks budget-to-actual reports.

2.  Format each report to match manager-level categories.

3.  Distribute reports by email or shared drive.

4.  Follow up with managers directly (phone/email) for explanations of flagged variances.

5.  Record manager responses in variance tracker.

6.  Correct miscoded entries in QuickBooks.

7.  Provide summarized variance log to leadership monthly.

* * * * *

💵 Treasury Workflows
=====================

### **7\. Weekly Bank Balance Collection**

**Objective:** Gather balances from 68 bank accounts across multiple banks.

**Workflow Steps:**

1.  Log into Chase, Glacier/FCB, and Heritage bank portals individually.

2.  Navigate to account summary page for each bank.

3.  Copy balances manually into Excel worksheet.

4.  Verify totals match online dashboards.

5.  Date-stamp worksheet and save into treasury folder.

6.  Consolidate all balances into one master tab for total liquidity view.

* * * * *

### **8\. Cash Forecast Preparation**

**Objective:** Use balances to plan interbank transfers and anticipate obligations.

**Workflow Steps:**

1.  Import balances from weekly collection sheet into forecast model.

2.  Compare actual balances against forecasted expectations.

3.  Update model with recent inflows/outflows (loan payments, distributions, utilities, etc.).

4.  Identify accounts short of required minimums.

5.  Decide whether to transfer funds between accounts or banks.

6.  Initiate transfers using bank portals.

7.  Record transfers in the forecast model to maintain alignment.

* * * * *

### **9\. Gap in Balance Aggregation Tools**

**Objective:** Document inefficiency due to lack of multi-bank aggregation solution.

**Workflow Steps:**

1.  Attempt to use balance aggregation tools (Anaplan, Adaptive, Trovata, etc.).

2.  Verify whether Chase, Glacier/FCB, and Heritage are supported.

3.  Record gaps in tool coverage and/or pricing issues.

4.  Maintain fallback manual workflow (weekly pulls, consolidated Excel file).

5.  Explore potential lightweight custom script (e.g., Plaid + Google Sheets) for automation.

* * * * *

⚓ Dockwa Finance & Operations Workflows
=======================================

Vertical SaaS platform for marina management and boater reservations, enabling digital booking, storage, and payments.

Industry: Vertical SaaS / Marina Management\
Founded: 2014\
Headquarters: Newport, Rhode Island\
Funding: Series B (backed by Insight Partners and others)\
Customers: Marinas, boatyards, yacht clubs, individual boaters\
Core Products: Reservations, storage, dockage, payments, comms tools

* * * * *

📥 Accounts Receivable Workflows
================================

### **1\. Lockbox PDF → Recurly → NetSuite**

**Objective:** Automate end-to-end lockbox processing, payment application, and journal entry creation.

**Workflow Steps:**

1.  Receive daily lockbox PDF from bank via secure email channel.

2.  Open PDF and review deposit details (payer name, check number, amount, date).

3.  Manually enter details into Excel to centralize tracking.

4.  Log into Recurly:

    -   Search for matching subscription/invoice number.

    -   Apply payment against correct customer subscription.

    -   Save confirmation.

5.  Log into NetSuite:

    -   Create journal entry reflecting deposit.

    -   Debit cash, credit accounts receivable.

    -   Attach lockbox PDF and Excel entry as backup.

6.  Save journal entry and reconcile against deposit amount.

7.  Repeat for each check in the lockbox batch (10--30+ checks typical).

8.  Maintain lockbox reconciliation file for monthly close.

* * * * *

### **2\. Invoice Processing & PDF Parsing**

**Objective:** Extract invoice and payment details from variable-format bank PDFs.

**Workflow Steps:**

1.  Receive PDF from bank lockbox.

2.  Attempt automated parsing via OCR/custom script:

    -   Extract invoice number, payer name, amount, check date.

    -   Populate temporary CSV/Excel file.

3.  Review extracted data:

    -   Flag fields missing/incorrect due to inconsistent formatting.

    -   Manually correct entries.

4.  Cross-reference extracted details against Recurly invoices:

    -   Match payments to subscriptions.

    -   Log unmatched entries separately.

5.  Apply payments in Recurly and reconcile totals.

6.  Push validated data into NetSuite journal entry template.

7.  Store corrected spreadsheet as audit backup.

* * * * *

💳 Accounts Payable Workflows
=============================

### **3\. Vendor / Payment Processing**

**Objective:** Manage outgoing payments to vendors after Stripe collections.

**Workflow Steps:**

1.  Customer payments processed through Stripe (card, ACH).

2.  Funds settle in Stripe clearing account.

3.  Recurly syncs subscription data with Stripe (billing/receipts).

4.  At payout, Stripe disburses net funds to company operating accounts.

5.  For vendor payments:

    -   AP team compiles vendor invoices (utilities, marina services, contractors).

    -   Cross-check invoices against operating accounts funded by Stripe.

    -   Code invoices in accounting system (NetSuite or QuickBooks).

    -   Schedule payments (ACH/wire/check) from operating account.

6.  Reconcile vendor payments back to NetSuite/QuickBooks.

7.  Track outstanding vendor balances in AP aging report.

* * * * *

🏦 Treasury & Accounting Workflows
==================================

### **4\. Bank Reconciliation**

**Objective:** Align monthly bank statements with NetSuite GL to confirm completeness and detect anomalies.

**Workflow Steps:**

1.  Download monthly bank statements (PDF/Excel) from each financial institution.

2.  Import bank transactions into reconciliation template in Excel or NetSuite.

3.  Match deposits against Stripe/Recurly records and lockbox batches.

4.  Match withdrawals against vendor payments, payroll, and operating expenses.

5.  Investigate unmatched transactions:

    -   Timing differences (in-transit items).

    -   Fraudulent or duplicate charges.

    -   Misclassified entries.

6.  Document reconciliation notes for each discrepancy.

7.  Obtain controller approval on reconciled statement.

8.  Save reconciled files to central accounting archive.

* * * * *

📊 FP&A & Research Workflows
============================

### **5\. Research & Analysis (FP&A / Investments)**

**Objective:** Use AI and models to accelerate financial research and investment analysis.

**Workflow Steps:**

1.  Define research question (e.g., competitor benchmarks, market sizing, investment screening).

2.  Query ChatGPT or similar AI tool to generate first-pass insights:

    -   Company comparisons.

    -   Industry fundamentals.

    -   Financial ratios.

3.  Validate AI outputs by cross-referencing with source data (SEC filings, Crunchbase, PitchBook).

4.  Compile results in Excel or custom FP&A model.

5.  Refine analysis (adjust assumptions, sensitivity checks).

6.  Present findings in structured report to leadership.

7.  Document inputs, assumptions, and outputs for reproducibility.

* * * * *

🔑 Summary
==========

Dockwa's finance team currently manages a hybrid environment across **bank lockbox feeds, Stripe, Recurly, and NetSuite**. Their workflows break down into four core categories:

-   **Accounts Receivable:** Lockbox PDF parsing, payment application, journal entries.

-   **Accounts Payable:** Vendor invoice coding, payment processing, reconciliation.

-   **Treasury & Accounting:** Bank reconciliations and fraud checks.

-   **FP&A:** AI-enabled research and investment analysis.
