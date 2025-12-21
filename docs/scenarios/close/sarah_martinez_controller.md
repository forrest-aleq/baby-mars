# Story 4: Dockwa Financial Control - Monthly Bank Reconciliation Process
## **Difficulty Level: 2 (Hard)**

### Sarah's Month-End Truth-Finding Mission

Sarah Martinez arrives at the Dockwa office at 7:45 AM on the first Monday of November, carrying her usual extra-large cold brew and the mental weight of month-end closing. As Dockwa's Controller for the past 3 years, Sarah has refined the month-end process into a precise choreography of data validation, but bank reconciliation remains her most dreaded task. It's the moment when the theoretical world of accounting systems meets the messy reality of actual bank transactions, and discrepancies have a way of revealing themselves at the worst possible moments.

Her desk setup reflects 15 years of accounting experience: dual monitors (one portrait for long spreadsheets), a calculator that's seen three different companies, and a color-coded filing system that would make Marie Kondo proud. Her MacBook Pro sits next to a Windows laptop dedicated exclusively to bank portals and legacy financial systems that refuse to work properly on macOS.

**7:52 AM - The Monthly Reconciliation Preparation Ritual**

Sarah opens her task management system (Monday.com) and reviews her November 1st checklist:

- [ ] Download October bank statements from all accounts (4 banks, 7 accounts)
- [ ] Export October transactions from NetSuite GL
- [ ] Reconcile Chase operating account (primary focus)
- [ ] Reconcile Stripe clearing account (most complex)
- [ ] Reconcile First Republic lockbox account
- [ ] Investigate and document all discrepancies
- [ ] Prepare reconciliation reports for audit
- [ ] Submit month-end close package to CFO

The process typically takes 6-8 hours when everything goes smoothly, but Sarah has learned to block the entire day because "everything going smoothly" is more wishful thinking than reality.

**8:01 AM - The Multi-Bank Login Marathon**

Sarah starts with the bank statement downloads, a process that requires logging into four different banking platforms with their own unique authentication requirements.

**Chase Business Banking (Primary Operating Account):**
Sarah opens Chrome and navigates to chase.com/business. She enters her credentials:
- User ID: smartinez_dockwa
- Password: [retrieved from 1Password]
- Security question: "What's your mother's maiden name?" → "Rodriguez"

Chase loads her dashboard showing the primary operating account ending in 4829. October's ending balance: $347,293.18. She clicks "View Statements" and downloads "October_2025_Statement.pdf" (47 pages).

**First Republic Bank (Lockbox Account):**
In a new tab, Sarah navigates to firstrepublic.com and goes through their login process:
- Username: dockwa_corp
- Password: [from 1Password]
- SMS 2FA code: 847293 (sent to her phone)

The lockbox account statement shows 247 individual deposits totaling $156,847.32. She downloads "October_2025_Lockbox_Statement.pdf."

**Silicon Valley Bank (Payroll Account):**
Next tab: svb.com business login
- Username: sarah.martinez@dockwa.com
- Token-based authentication from mobile app: 192847

October payroll account activity: $89,247.18 in outflows, $92,000 in transfers from operating account. She downloads "SVB_October_Statement.pdf."

**Stripe Express Account (Payment Processing):**
Final tab: dashboard.stripe.com
- Google SSO authentication (seamless)

Stripe's dashboard shows October processing volume: $2.4M gross, $2.34M net after fees. But the "balance" concept in Stripe is complex - it's not a traditional bank account but rather a clearing mechanism. She exports "October_Stripe_Activity.csv."

**8:23 AM - The NetSuite Data Export Challenge**

With bank statements downloaded, Sarah needs to export corresponding data from NetSuite. She logs into their NetSuite instance and navigates to Reports → Financial → General Ledger.

She creates a custom GL report with the following parameters:
- Date Range: October 1-31, 2025
- Accounts: All bank and cash accounts (1100-1199)
- Transaction Detail: Full detail including journal entries, bill payments, deposits
- Format: Excel export for analysis

The report takes 3 minutes and 47 seconds to generate (she times it every month). The exported file "NetSuite_GL_October_2025.xlsx" contains 1,847 individual transactions across all cash accounts.

**8:31 AM - The Primary Account Reconciliation Setup**

Sarah opens Excel and creates her monthly reconciliation workbook: "Bank_Reconciliation_October_2025.xlsx." The template includes multiple worksheets:

- **Chase_Operating:** Main operating account reconciliation
- **Stripe_Clearing:** Payment processing reconciliation
- **Lockbox_Deposits:** Customer payment reconciliation
- **Payroll_Account:** Payroll transaction reconciliation
- **Reconciliation_Summary:** Master summary and variances
- **Outstanding_Items:** Unmatched transactions requiring investigation

Sarah starts with the Chase operating account, which handles the majority of Dockwa's business transactions. She imports the NetSuite GL data into one column and manually types the bank statement transactions into another column.

**Bank Statement Balance (October 31):** $347,293.18
**NetSuite GL Balance (October 31):** $344,847.32
**Variance:** $2,445.86

The $2,445.86 discrepancy is exactly why Sarah dreads bank reconciliation. This variance could represent:
- Outstanding checks that haven't cleared
- Deposits in transit
- Bank fees not recorded in NetSuite
- Data entry errors
- Fraud or unauthorized transactions

**8:47 AM - The Transaction Matching Process**

Sarah begins the tedious process of matching individual transactions between the bank statement and NetSuite records. She uses Excel's conditional formatting to highlight matched items:

**October 2: Bank Deposit $47,832.15 → NetSuite Journal Entry JE-2025-4392**
**October 3: Bank Withdrawal $4,200.00 → NetSuite Bill Payment BP-2025-1847 (AquaTech)**
**October 3: Bank Withdrawal $25.00 → NetSuite Expense EX-2025-2847 (Wire fee)**

The matching process is straightforward for large, unique transactions but becomes problematic with:
- Multiple transactions of the same amount on the same day
- Bank fees that don't automatically appear in NetSuite
- Vendor payments that clear days after NetSuite records them
- Stripe payouts that aggregate multiple days of processing

**9:23 AM - The Stripe Reconciliation Nightmare**

Sarah moves to the most complex part: reconciling Stripe activity with their clearing account. Stripe's business model creates unique reconciliation challenges:

- Customer payments come in throughout the day
- Stripe holds payments for 2-7 business days depending on risk
- Daily payouts to bank accounts aggregate multiple payment days
- Fees are deducted from gross payments before payout
- Chargebacks and disputes can affect payouts weeks after the original transaction

Sarah opens the Stripe CSV export and immediately sees the complexity:

**October 1 Payout:** $46,443.72 (net of fees)
- Represents payments from September 28-29
- Gross payments: $47,832.15
- Stripe fees: $1,388.43
- Net payout: $46,443.72

But in NetSuite, this appears as a single deposit of $46,443.72 on October 1. Sarah needs to trace this back to the original customer payments to ensure revenue recognition is accurate.

She cross-references the Stripe data with Recurly (their subscription billing system) to verify that each customer payment was properly recorded:

**Hartwell Marina:** $2,850 payment on Sept 28 → Included in Oct 1 payout
**SeaBreeze Yacht Club:** $1,200 payment on Sept 29 → Included in Oct 1 payout
**Pacific Coast Storage:** $875 payment on Sept 29 → Included in Oct 1 payout

The reconciliation requires matching 247 individual customer payments across a 2-day collection period to a single bank deposit. This process alone takes 45 minutes.

**10:17 AM - The Outstanding Items Investigation**

Sarah's matching process reveals several unmatched transactions that require investigation:

**Unmatched Bank Items:**
1. **October 15:** Bank deposit $3,200.00 (no corresponding NetSuite entry)
2. **October 22:** Bank withdrawal $847.32 (no corresponding NetSuite entry)
3. **October 28:** Bank fee $45.00 (monthly account maintenance)

**Unmatched NetSuite Items:**
1. **October 29:** Bill payment $2,400.00 (check hasn't cleared bank yet)
2. **October 30:** Journal entry $1,850.00 (deposit in transit)
3. **October 31:** Bill payment $595.86 (ACH processing delay)

Sarah needs to investigate each discrepancy:

**Mystery Deposit ($3,200.00):**
Sarah reviews the bank statement detail and sees: "WIRE TRANSFER - PACIFIC MARINA VENTURES - PARTNERSHIP DISTRIBUTION." This isn't a customer payment but rather a distribution from one of Dockwa's partnership investments. She needs to create a journal entry to record this income.

**Mystery Withdrawal ($847.32):**
The bank statement shows: "ACH DEBIT - DEPT OF LABOR - QUARTERLY FILING." This is a quarterly employment tax payment that was processed directly by their payroll service but not recorded in NetSuite. Sarah needs to create an expense entry.

**10:44 AM - The Journal Entry Creation Process**

Sarah logs back into NetSuite to create correcting journal entries for the unmatched transactions:

**Journal Entry JE-2025-4501 (Partnership Distribution):**
- Debit: Cash - Chase Operating Account $3,200.00
- Credit: Partnership Income $3,200.00
- Memo: Q3 distribution from Pacific Marina Ventures partnership

**Journal Entry JE-2025-4502 (Employment Tax):**
- Debit: Payroll Tax Expense $847.32
- Credit: Cash - Chase Operating Account $847.32
- Memo: Q3 employment tax filing - processed by ADP

**Journal Entry JE-2025-4503 (Bank Fees):**
- Debit: Bank Fees Expense $45.00
- Credit: Cash - Chase Operating Account $45.00
- Memo: October account maintenance fee - Chase Operating

**11:18 AM - The Fraud Detection Review**

One of Sarah's critical responsibilities during reconciliation is fraud detection. She reviews all transactions for unusual patterns:

- Duplicate payments to the same vendor
- Round-number transactions without supporting documentation
- Payments to new vendors without proper approval
- Unusual transaction timing (weekend transfers, after-hours activity)
- Large or unusual amounts

Sarah flags two transactions for additional review:

**October 12:** Wire transfer $5,000.00 to "Harbor Tech Solutions"
**October 19:** ACH payment $2,750.00 to "Marina Systems LLC"

Both vendors are new to the system, and the payments were processed outside normal approval workflows. Sarah opens her email and searches for corresponding invoices and approvals.

For Harbor Tech Solutions, she finds an email chain with Kevin (AP Manager) and the CEO approving an emergency server upgrade. The payment is legitimate but was processed urgently without following standard procedures.

For Marina Systems LLC, she finds no supporting documentation. Sarah immediately calls Kevin: "Kevin, I'm reviewing October reconciliation and found a $2,750 payment to Marina Systems LLC. Do you have the invoice and approval for this?"

Kevin responds: "Oh yeah, that was for the emergency dock management software license. Let me forward you the approval email chain - it came through late Friday afternoon."

**11:41 AM - The Lockbox Reconciliation Deep Dive**

Sarah moves to reconciling the First Republic lockbox account, which handles customer check payments. This account should be the simplest - deposits go in, transfers to operating account go out - but customer payment processing creates complications.

**October Lockbox Activity:**
- Customer deposits: $156,847.32 (247 individual checks)
- Transfer to operating account: $156,847.32
- Account fees: $247.00 (per-item processing fees)

The lockbox should have a near-zero balance, but Sarah's reconciliation shows:

**Bank Balance:** $247.00 (fees held by bank)
**NetSuite Balance:** $0.00

Sarah realizes the lockbox fees haven't been recorded in NetSuite. She creates another journal entry:

**Journal Entry JE-2025-4504 (Lockbox Fees):**
- Debit: Bank Fees Expense $247.00
- Credit: Cash - Lockbox Account $247.00
- Memo: October lockbox processing fees - 247 items @ $1.00 each

**12:15 PM - The Reconciliation Summary Preparation**

With all accounts reconciled and correcting entries made, Sarah updates her reconciliation summary:

**October 2025 Bank Reconciliation Summary:**

**Chase Operating Account:**
- Beginning Balance: $298,439.82
- Ending Balance: $347,293.18
- Reconciling Items: 3 (now resolved)
- Final Variance: $0.00

**Stripe Clearing Account:**
- October Gross Processing: $2,401,847.32
- Fees and Holdbacks: $72,555.43
- Net Payouts to Operating: $2,329,291.89
- Final Variance: $0.00

**Lockbox Account:**
- Customer Deposits: $156,847.32
- Processing Fees: $247.00
- Net Transfer to Operating: $156,600.32
- Final Variance: $0.00

**Payroll Account:**
- Payroll Funding: $92,000.00
- Payroll Disbursements: $89,247.18
- Remaining Balance: $2,752.82
- Final Variance: $0.00

**12:34 PM - The Audit Documentation Process**

Sarah's final task is preparing documentation for the external auditors. She creates a comprehensive reconciliation package:

**Folder: October_2025_Bank_Reconciliation/**
- Bank_Statements/ (all PDF statements)
- NetSuite_Exports/ (GL reports and journal entries)
- Reconciliation_Workbooks/ (Excel analysis files)
- Supporting_Documentation/ (invoices, approvals, correspondence)
- Summary_Report.pdf (executive summary for management)

Each reconciling item is documented with:
- Description of the variance
- Root cause analysis
- Correcting action taken
- Reference to supporting documentation
- Process improvement recommendations

**12:47 PM - The CFO Briefing Preparation**

Sarah prepares her month-end briefing for the CFO:

"Subject: October 2025 Bank Reconciliation Complete

Hi [CFO Name],

October bank reconciliation is complete. All accounts are reconciled with zero variances.

**Key Findings:**
- Partnership distribution ($3,200) wasn't recorded - now corrected
- Employment tax payment ($847) from payroll service - now recorded
- Two new vendor payments flagged for review - both legitimate with approval
- Lockbox processing fees not being recorded automatically - created JE

**Process Improvements Needed:**
- Automate lockbox fee recording in NetSuite
- Improve new vendor payment approval workflow documentation
- Consider daily Stripe reconciliation instead of monthly to reduce complexity

**Next Steps:**
- All correcting journal entries posted and approved
- Audit documentation package prepared and saved to shared drive
- November reconciliation scheduled for December 1st

Total reconciliation time: 4 hours, 52 minutes

Sarah"

**12:51 PM - The Monthly Process Reflection**

As Sarah saves all her work and prepares for lunch, she reflects on the morning's reconciliation process. What should theoretically be a simple comparison of bank records to accounting records requires extensive detective work:

- **Multi-system coordination:** NetSuite, Stripe, Recurly, and multiple bank portals all contain pieces of the transaction puzzle
- **Timing differences:** Payments are recorded when initiated but clear banks days later
- **Fee complexity:** Different fees from different providers that don't automatically flow to accounting systems
- **Business context:** Understanding whether unusual transactions are legitimate requires knowledge of business operations
- **Fraud vigilance:** Reconciliation is the primary control for detecting unauthorized transactions

Sarah opens her ongoing "Process Improvement Ideas" document and adds today's observations:

**Immediate Improvements:**
- Set up automatic journal entries for recurring bank fees
- Create standardized templates for common reconciling items
- Improve documentation requirements for urgent payments

**Technology Improvements:**
- Investigate bank API integrations for automatic statement import
- Research reconciliation software that can handle Stripe complexity
- Consider daily reconciliation automation for high-volume accounts

**Process Improvements:**
- Standardize new vendor payment approval workflows
- Create monthly recurring journal entries for predictable fees
- Implement daily cash reporting to catch discrepancies faster

**1:02 PM - The Compliance Documentation**

Before heading to lunch, Sarah updates Dockwa's compliance documentation. As a SaaS company handling customer payment data, they're subject to various regulatory requirements that make bank reconciliation more than just an accounting exercise.

She updates the "Internal Controls Documentation" with this month's reconciliation evidence:
- All bank accounts reconciled within 2 business days of month-end
- All discrepancies investigated and resolved with supporting documentation
- Fraud detection procedures performed and documented
- Segregation of duties maintained (Sarah reconciles, CFO reviews and approves)

**1:07 PM - The Human Element**

As Sarah closes her laptop and heads to the office kitchen, she reflects on why bank reconciliation remains such a manual process despite advances in financial technology. The challenge isn't technical complexity - it's the human element:

- Vendors change their payment preferences without notice
- Customer payments come with incomplete or incorrect reference information
- Bank fees and timing create reconciling items that require business judgment
- New business activities (partnerships, investments, emergency purchases) create unusual transactions
- Multiple systems of record create data synchronization challenges

Sarah texts her team: "October reconciliation complete ✅ All accounts balanced, audit package ready. Found 2 process improvements for next month."

She grabs her lunch from the office fridge and thinks about how satisfying it is when all the numbers finally add up. In a world of estimates and projections, bank reconciliation provides definitive truth - the actual cash position that will fund Dockwa's growth and operations. Even though the process is tedious, it's the foundation that ensures accurate financial reporting and maintains investor confidence.

Tomorrow, November transactions will start accumulating, and in 30 days, Sarah will repeat this entire process. But for now, all the numbers balance, the discrepancies are explained, and Dockwa's financial controls have passed another monthly test.
