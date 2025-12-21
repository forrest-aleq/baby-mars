# 📊 GGHC Finance & Operations Workflows — Compliance-Grade Version

Manhattan–based investment advisory and broker-dealer firm, founded in 1968. Renowned for its discretionary growth stock strategies.

Industry: Investment Management / Broker-Dealer
Founded: 1968
Headquarters: New York, NY
AUM: \~\$11.6B (as of March 24, 2025)
Employee Count: \~88 employees (as of early 2025)
Holdings (13F): 238 positions with market value \~\$9.4B as of Q2 2025
Services: Portfolio management, retirement accounts, margin, bonds, ETFs
Approach: Independent money managers benefitting from shared research and trading infrastructure

---

# 📥 Accounting & FP\&A Workflows

### **1. Power BI → Excel → Journal Entry Allocation**

**Objective:** Transform BI and third-party fee data into compliant NetSuite journal entries.

**Workflow Steps:**

1. Access Power BI and run required financial/fee allocation reports.
2. Export into Excel with full metadata (time stamp, user ID, query parameters) for audit trail.
3. Collect third-party data (custodian files, fee schedules, performance reports) from secured SFTP or vendor portals.
4. Normalize all inputs:

   * Validate file integrity (hash check, source confirmation).
   * Standardize headers, date formats, and currency conversions.
5. Merge datasets in Excel, using documented allocation logic.
6. Apply allocation engine:

   * Percentages tied to governing agreements (fee schedules, prospectuses).
   * Maintain formula log separate from raw data.
7. Validate results:

   * Cross-check against AUM and contractual fee arrangements.
   * Perform dual-control review (analyst + controller).
8. Prepare NetSuite journal entry file:

   * Debit/credit with full line-item detail.
   * Include references to agreements and calculation sheets.
9. Log into NetSuite and post:

   * Ensure role-based segregation of duties (preparer vs. approver).
   * Attach Power BI, Excel, and third-party source files.
10. Controller signs off electronically (timestamp + compliance note).

---

### **2. Bank Reconciliation by Controller**

**Objective:** Ensure complete, accurate reconciliation of bank accounts to NetSuite GL with regulatory oversight.

**Workflow Steps:**

1. Retrieve monthly bank statements (PDF/Excel) directly from secured portals.
2. Import transactions into reconciliation software (NetSuite, Excel, or Blackline).
3. Match deposits to client contributions, settlements, or margin activity.
4. Match withdrawals to AP, payroll, clearing, and counterparty obligations.
5. Flag unmatched items:

   * Timing differences.
   * Unexplained fees.
   * Suspicious or unusual activity.
6. Investigate discrepancies:

   * Document research steps in reconciliation log.
   * Escalate to CFO if unresolved after 3 business days.
7. Attach supporting evidence (emails, wire confirmations, custodian records).
8. Controller signs off with digital approval in NetSuite/Blackline.
9. Compliance team reviews a random sample monthly for SEC/FINRA audit readiness.
10. Store completed reconciliations in WORM-compliant archive.

---

### **3. Accounts Payable Invoice Processing (Stampley)**

**Objective:** Automate invoice capture while preserving compliance and audit integrity.

**Workflow Steps:**

1. Vendor sends invoice to dedicated AP inbox.
2. Invoices ingested into Stampley:

   * OCR extracts vendor, invoice #, amount, dates, GL coding.
   * System applies historical learning.
3. AP staff validates extracted data:

   * Cross-check against vendor master file.
   * Confirm against approved contract or PO.
4. System routes invoice for approval based on delegation of authority policy.
5. Once approved, invoice syncs to NetSuite/Bill.com:

   * Payment scheduled per vendor terms.
   * Segregation of duties enforced (no single person handles intake, approval, and payment).
6. Execute payment via ACH/wire/check.
7. Payment file reviewed by controller before release.
8. Archive invoice, system logs, and payment confirmation in compliance vault.
9. Quarterly AP audit sample performed to ensure OCR accuracy and approval adherence.

---

# 📈 Investment Research & Strategy

### **4. Research & Analyst Support via AI**

**Objective:** Enhance analyst output while embedding compliance oversight.

**Workflow Steps:**

1. Define research scope (e.g., sector comps, screening criteria) — logged in research request system.
2. Query ChatGPT or AI assistant:

   * Extract fundamentals, peer comps, qualitative risks.
   * Generate draft memos.
3. Save AI queries and outputs into research log (timestamp, user ID, prompt, output).
4. Cross-reference with Bloomberg, Capital IQ, and official filings for verification.
5. Analysts refine models in Excel:

   * Document assumptions, methodologies, and sensitivity tests.
6. Draft report compiled with AI + validated data.
7. Submit to supervisory analyst for review under FINRA 2210/2241 requirements.
8. Compliance signs off before report is distributed internally.
9. Archive full chain (AI outputs, analyst edits, approvals) in WORM-compliant system.
10. Maintain record retention in line with SEC 17a-4.

---

# 🔑 Summary

GGHC’s workflows must balance **operational efficiency** with **regulatory rigor**:

* **Journal Entries:** Dual-control, source-file retention, allocation formula logs.
* **Bank Recs:** Controller sign-off, compliance sampling, WORM storage.
* **AP Processing:** OCR with human validation, approval routing per authority policy.
* **Research:** AI augmentation with mandatory logging, supervisory review, and compliance retention.

This hardened version is **audit-ready** and **regulator-proof**, ensuring workflows are both efficient and defensible under SEC and FINRA scrutiny.
