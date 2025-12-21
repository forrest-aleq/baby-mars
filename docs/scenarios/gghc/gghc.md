
# 📊 GGHC Finance & Operations Workflows

Manhattan–based investment advisory and broker-dealer firm, founded in 1968. Renowned for its discretionary growth stock strategies.

Industry: Investment Management / Broker-Dealer
Founded: 1968
Headquarters: New York, NY
AUM: \~\$11.6B (as of March 24, 2025)
Employee Count: \~88 employees (as of early 2025)
Holdings (13F): 238 positions with market value \~\$9.4B as of Q2 2025
Services: Portfolio management, retirement accounts, margin, bonds, ETFs
Approach: Independent money managers benefitting from shared research and trading infrastructure

Task Name: Power BI → Excel → Journal Entry Allocation

Quote: “I have to go into so we have, Power BI reports. Right? Business reports, business analytic reports. I get a file from there. I then to sort through the data and similar process to what you’re describing. Right? Just a different data format. And then I export into Excel, then I take the Excel sheet, and then there’s other data reports coming from other third parties where I kinda have to match things up. And then all that kinda translates into some allocation logic of percentage base. So I have some engine that’s a fees of of percentage logic that I have to apply. And then it’s the output, and then that output needs to turn into a journal entry. Right? Ultimately, I’m keying in those numbers, you know, like, twenty twenty rows into the NetSuite.”

Category: FP&A, Accounting

Process Type: Workflow → Data Transformation & Journal Entry Preparation

Typical Software Today: Power BI, Excel, NetSuite, possibly RPA (UiPath, Automation Anywhere)

Task Name: Bank Reconciliation by Controller

Quote: “Some of the mundane things like bank reconciliations. I have our controller currently looks at bank statements, PDF bank statements, generally speaking, or maybe they’re Excel files, and then they’ll match up numbers. NetSuite, great product. I think this is the second time we’ve implemented this firm. I’ve done it somewhere else too. There’s nothing so special about it.”

Category: Treasury, Accounting

Process Type: Workflow → Reconciliation

Typical Software Today: NetSuite, Excel, Bank Portals, Blackline

Task Name: Accounts Payable Invoice Processing (Stampley)

Quote: “They also have AI built in. And they really rely on, like, OCR technology to review PDFs and understand the the key, reference data points, like the total cost, the invoice numbers, the date, due dates, the memos on the invoices… And then you when you update it, it learns. So it’s a learning mechanism. So then they know for that invoice when they see it, they know to pull the right information.”

Category: Accounts Payable

Process Type: Workflow → Invoice Capture & Data Entry Automation

Typical Software Today: Stampley, Bill.com, Ramp, Expensify

Task Name: Research & Analyst Support via AI

Quote: “I think what we found AI to be extremely helpful for is a lot of the research analyst function. Right? We’re dealing with picking the right investments, doing fundamental qualitative analysis, scouring through data and and learning things, and then trying to make decisions based off that. Look. Chat GPT is quite powerful. You know? You can ask it to analyze companies, say getting across these companies and why. And, you know, you can tell it to refine different parameters.”

Category: Investment Research, Strategy

Process Type: Informational Access → Analytical Q&A / Research Assistance

Typical Software Today: ChatGPT, Capital IQ, Bloomberg Terminal, Excel


---

# 📥 Accounting & FP\&A Workflows

### **1. Power BI → Excel → Journal Entry Allocation**

**Objective:** Convert raw BI and third-party data into journal entries for NetSuite.

**Workflow Steps:**

1. Access Power BI dashboard and run monthly/quarterly financial or fee allocation reports.
2. Export report output into Excel (CSV or XLSX).
3. Collect additional third-party data reports (custodian files, performance feeds, fee schedules).
4. Normalize formats:

   * Standardize headers, currency formats, and date formats.
   * Align transaction IDs across sources.
5. Merge datasets in Excel using lookup/match logic.
6. Apply allocation engine:

   * Define allocation percentages (e.g., fee splits across funds).
   * Apply percentage formulas across merged dataset.
7. Validate results:

   * Check subtotals align with source data.
   * Reconcile allocation outputs against AUM/fee base.
8. Prepare NetSuite-ready journal entry template:

   * Debit/credit lines itemized (20–30 rows typical).
   * Reference supporting calculations.
9. Log into NetSuite:

   * Create manual journal entry.
   * Paste allocation data line by line.
   * Attach Excel/Power BI reports as backup.
10. Submit for review/approval in NetSuite workflow.

---

### **2. Bank Reconciliation by Controller**

**Objective:** Reconcile bank statements with NetSuite GL monthly.

**Workflow Steps:**

1. Download monthly bank statements (PDF/Excel) from banking portals.
2. Import or manually copy transactions into reconciliation template.
3. Retrieve NetSuite GL balances for the same accounts.
4. Match deposits to client inflows, margin postings, and settlements.
5. Match withdrawals to AP, payroll, clearing costs, and transfers.
6. Flag unmatched items:

   * Timing differences (in-transit wires, ACH delays).
   * Fees or unexpected charges.
   * Fraud/anomalies.
7. Investigate discrepancies:

   * Contact banks or counterparties if required.
   * Trace GL entries back to source docs.
8. Document reconciliation notes with explanations.
9. Submit reconciliation package to CFO/controller for sign-off.
10. Store in accounting archive for audit and regulatory purposes.

---

### **3. Accounts Payable Invoice Processing (Stampley)**

**Objective:** Automate invoice capture, coding, and posting.

**Workflow Steps:**

1. Vendor sends invoice (PDF, email attachment).
2. Upload invoice into Stampley or integrated AP tool.
3. OCR engine scans invoice and extracts key fields:

   * Vendor name, invoice #, amount, dates, GL code suggestions.
4. System “learns” from prior corrections and improves over time.
5. AP clerk reviews extracted data:

   * Confirms coding.
   * Corrects errors (e.g., misread amounts, duplicate invoices).
6. Approved invoice exported to NetSuite/Bill.com for posting.
7. Set up payment schedule:

   * ACH, wire, or check.
   * Based on vendor payment terms.
8. Payment execution through integrated platform (Bill.com, Ramp, Expensify).
9. Update AP aging report with cleared status.
10. Store invoice and confirmation in vendor file.

---

# 📈 Investment Research & Strategy

### **4. Research & Analyst Support via AI**

**Objective:** Accelerate analyst workflow with AI-assisted research and analysis.

**Workflow Steps:**

1. Define research scope (e.g., equity screening, peer comps, sector trends).
2. Use ChatGPT/AI tools to:

   * Summarize company fundamentals.
   * Compare financial ratios across peer set.
   * Highlight qualitative risk factors.
   * Generate first-pass memos.
3. Cross-reference with structured data sources (Capital IQ, Bloomberg Terminal).
4. Export AI outputs into Excel or internal research templates.
5. Analysts refine assumptions:

   * Adjust valuation multiples.
   * Reassess revenue/earnings projections.
6. Run scenario/sensitivity models in Excel.
7. Compile outputs into research deck for PM review.
8. Log AI queries, outputs, and analyst commentary for compliance/audit trail.
9. Use insights to support portfolio rebalancing or new investment recommendations.

