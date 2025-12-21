# Story 8: GGHC Investment Management - Monthly Client Fee Allocation
## **Difficulty Level: 3 (Moderate)**

### Jordan's Month-End Allocation Routine

Jordan Reeves opens her laptop at exactly 8:00 AM on the first Monday of October, knowing she has a full day ahead of her. As GGHC's billing analyst for the past 11 months, Jordan has refined the monthly client fee allocation process into a predictable routine, but "predictable" doesn't mean "easy." The process still requires careful attention to detail, cross-referencing multiple data sources, and ensuring every dollar of the $347,000 in September management fees gets allocated to the correct client accounts.

Jordan's desk is organized like a military operation: dual monitors, printed client fee schedules in alphabetical order, a calculator within arm's reach, and her trusty green highlighter for marking completed allocations. She has exactly three days to complete September's billing before the CFO review on Thursday.

**8:03 AM - The Power BI Data Pull**

Jordan opens Chrome and navigates to GGHC's Power BI dashboard. The investment operations team runs nightly portfolio valuations that feed into the billing system, and Jordan needs September 30th's final asset values to calculate management fees.

She clicks on "Client Portfolio Valuations" and filters the report:
- Date: September 30, 2025
- Account Status: Active
- Portfolio Type: All (Discretionary, Advisory, Retirement)

The report loads showing 238 client accounts with total assets under management of $11.6 billion. Jordan exports the data to Excel: "Portfolio_Values_Sep30_2025.xlsx."

**8:11 AM - The Fee Schedule Cross-Reference**

Jordan opens her "Master_Fee_Schedule_2025.xlsx" file, which contains the negotiated fee rates for each client. The structure varies significantly:

- **Hartwell Industries:** 0.75% annually on first $10M, 0.60% on amounts above $10M
- **Morrison Family Trust:** 1.25% annually (flat rate)
- **Coastal Pension Fund:** 0.85% annually, with performance bonus eligible
- **Tech Startup Holdings:** 1.50% annually (minimum $25,000)

Each client's fee arrangement was negotiated individually, and Jordan has learned that no two agreements are exactly alike.

**8:22 AM - The Allocation Engine Setup**

Jordan opens her billing template: "Fee_Allocation_Template_Oct2025.xlsx." The spreadsheet has evolved over months of refinement and includes:

- **Client Data Tab:** Names, account numbers, fee rates, minimum fees
- **Portfolio Values Tab:** September 30 asset values (imported from Power BI)
- **Calculation Tab:** Automated formulas linking client data to portfolio values
- **Allocation Summary Tab:** Final fee amounts ready for NetSuite import
- **Variance Analysis Tab:** Month-over-month fee comparisons

Jordan starts by copying the Power BI export data into the "Portfolio Values" tab. She uses VLOOKUP formulas to match client account numbers between the valuation data and her fee schedule.

**8:34 AM - The First Calculation Issues**

Jordan's VLOOKUP formula returns #N/A errors for three client accounts. She checks the account numbers:

- Account #GGHC-4729: Shows in Power BI but not in her fee schedule
- Account #GGHC-8847: Shows in fee schedule but not in Power BI
- Account #GGHC-2938: Account number format doesn't match

Jordan opens her email and checks recent communications from client services. She finds an email from September 28th: "Account #GGHC-4729 (Patterson LLC) was opened 9/29/25 after month-end. Please exclude from September billing."

For account #GGHC-8847, Jordan searches her email for "Riverside Holdings" (the client name). She finds a September 15th email: "Riverside Holdings closed their account effective 9/15/25. Final billing prorated through 9/15."

**8:47 AM - The Proration Calculation**

For Riverside Holdings, Jordan needs to calculate a prorated fee for partial month service. The client's average September balance was $2.4M at a 1.0% annual fee rate, but they closed on September 15th.

Standard monthly fee: ($2.4M × 1.0%) ÷ 12 = $2,000
Prorated fee (15 days): $2,000 × (15 ÷ 30) = $1,000

Jordan adds a manual entry to her calculation tab for the prorated billing.

**8:56 AM - The Performance Fee Complexity**

Jordan reaches Coastal Pension Fund's allocation and encounters the quarterly performance bonus calculation. Their agreement includes a 10% performance fee on returns exceeding 8% annually.

She needs Coastal's performance data from the investment operations team. Jordan calls the senior analyst, Marcus Chen.

"Hi Marcus, it's Jordan from billing. I need Coastal Pension's Q3 performance numbers for the quarterly bonus calculation."

"Sure, let me pull that up... Coastal was up 11.2% gross for the quarter, which annualizes to about 14.8%. Their net return after fees was 13.9% annualized."

"So they're well above the 8% hurdle. What's their average quarterly balance for the performance fee calculation?"

"Their average balance was $47.3M for Q3. The performance fee should be calculated on the excess return above 8%."

Jordan calculates: (13.9% - 8.0%) × $47.3M × 10% = $27,917 performance bonus

**9:18 AM - The Minimum Fee Adjustments**

Jordan's template automatically flags accounts where calculated fees fall below contractual minimums:

- **Tech Startup Holdings:** Calculated fee $18,750, Minimum $25,000 (difference: $6,250)
- **Wilson Advisory:** Calculated fee $4,200, Minimum $5,000 (difference: $800)
- **Green Energy Fund:** Calculated fee $8,900, Minimum $10,000 (difference: $1,100)

Jordan updates these accounts to charge the minimum fees and makes notes in the "Comments" field: "Minimum fee adjustment - per client agreement."

**9:31 AM - The Reconciliation Check**

Jordan runs her first reconciliation to ensure her allocation totals match the expected management fee revenue:

**Calculated Total Fees:** $344,750
**Expected Fee Revenue (from accounting):** $347,000
**Variance:** -$2,250

Jordan needs to identify the missing $2,250. She creates a variance analysis comparing this month to prior months:

- Hartwell Industries: September $28,750 vs August $29,200 (-$450)
- Morrison Family Trust: September $15,600 vs August $16,200 (-$600)
- Several smaller accounts showing similar decreases...

The pattern suggests portfolio values declined in September, reducing fee calculations.

**9:47 AM - The Market Decline Investigation**

Jordan calls the portfolio management team to understand September's performance.

"Hey Sarah, it's Jordan. My fee calculations are running about $2,250 below expectations. Were there significant market declines in September?"

"Yeah, we had a rough last week of September. The S&P was down about 3.2% for the month, and our growth-oriented portfolios were hit harder—probably down 4-5% on average."

This explains the fee variance. Jordan documents: "September fee variance due to market decline. Client portfolios averaged -4.1% in September, reducing AUM for fee calculations."

**10:02 AM - The Client Communication Prep**

Jordan reviews clients whose fees changed significantly from August:

- **Hartwell Industries:** -$450 (portfolio decline)
- **Morrison Family Trust:** -$600 (portfolio decline + withdrawal)
- **Coastal Pension:** +$27,917 (performance bonus)
- **Tech Venture Partners:** +$8,400 (new contribution)

Jordan prepares notes for the client services team about significant fee changes, particularly Coastal Pension's performance bonus which will likely generate questions.

**10:17 AM - The NetSuite Export Preparation**

Jordan's allocation is complete, and she needs to format the data for NetSuite import. She creates a new tab called "NetSuite_Import" with the required columns:

- Client_ID
- Client_Name
- Fee_Amount
- Fee_Type (Management, Performance, Minimum Adjustment)
- Billing_Period
- GL_Account_Code

Jordan uses Excel formulas to populate these columns from her calculation data:
`=CONCATENATE("MGMT-",B2,"-",TEXT(TODAY(),"YYYYMM"))`

**10:33 AM - The Final Reconciliation**

Before exporting to NetSuite, Jordan runs a final check:

**Fee Allocation Summary:**
- Management Fees: $316,833
- Performance Fees: $27,917
- Minimum Fee Adjustments: $8,150
- **Total Allocated:** $352,900

Wait—this total is now $5,900 higher than the expected $347,000. Jordan realizes she double-counted some minimum fee adjustments.

**10:41 AM - The Error Correction**

Jordan reviews her minimum fee calculations and finds the issue. For accounts with minimum fee adjustments, she added both the calculated fee AND the minimum adjustment, instead of replacing the calculated fee with the minimum.

She corrects the formulas:
`=IF(Calculated_Fee<Minimum_Fee,Minimum_Fee,Calculated_Fee)`

**Corrected Total:** $347,000 exactly.

**10:52 AM - The NetSuite Import**

Jordan logs into NetSuite and navigates to the billing module. She clicks "Import Fee Allocations" and uploads her CSV file. The system validates the data format and shows:

- 238 records processed
- 0 errors
- Total amount: $347,000
- Ready for posting: Yes

Jordan clicks "Post Allocations" and NetSuite creates the journal entries:

**Debit:** Accounts Receivable - $347,000
**Credit:** Management Fee Revenue - $347,000

**11:07 AM - The Client Billing Generation**

With allocations posted in NetSuite, Jordan can generate client invoices. She navigates to "Generate Client Bills" and runs the October billing cycle.

NetSuite produces 238 individual invoices, each formatted according to client preferences:
- PDF format for most clients
- Excel format for institutional clients
- Detailed portfolio summaries for high-fee clients
- Simple summary invoices for smaller accounts

**11:24 AM - The Quality Control Review**

Jordan spot-checks several generated invoices:

**Hartwell Industries Invoice:**
- Management Fee: $28,750 (0.75% on first $10M + 0.60% on excess)
- Portfolio Value: $47.3M as of 9/30/25
- Payment Terms: Net 15

**Coastal Pension Invoice:**
- Management Fee: $33,415
- Performance Bonus: $27,917
- Total: $61,332
- Portfolio Value: $47.3M as of 9/30/25

The invoices look accurate and include the appropriate detail level for each client type.

**11:39 AM - The Distribution Process**

Jordan exports the completed invoices and uploads them to GGHC's client portal. Clients with portal access will receive automatic notifications, while others will receive invoices by email or mail according to their preferences.

She creates distribution lists:
- **Email invoices:** 189 clients
- **Portal notifications:** 156 clients (some overlap)
- **Printed invoices:** 23 clients (mostly older individual clients)

**11:51 AM - The Documentation and Archival**

Jordan saves all supporting documents to the shared drive structure:
- "Monthly_Billing/2025/October/Fee_Calculations/"
- "Monthly_Billing/2025/October/Client_Invoices/"
- "Monthly_Billing/2025/October/NetSuite_Import_Files/"

She also updates her billing log with key metrics:
- Total fees billed: $347,000
- Number of clients: 238
- Performance bonuses: 1 client ($27,917)
- Minimum fee adjustments: 8 clients
- Billing completion time: 3 hours, 51 minutes

**11:58 AM - The Month-End Summary**

Jordan prepares her summary email for the CFO and client services team:

"Subject: October Billing Complete - September Fee Allocations

Hi team,

September fee allocations are complete and client invoices have been generated:

**Summary:**
- Total management fees: $347,000
- Clients billed: 238
- Notable items: Coastal Pension performance bonus ($27,917)
- Fee variance: $0 vs. expected revenue

**Next Steps:**
- Client portal notifications sent
- Email invoices distributed
- Printed invoices ready for mailing
- Collections tracking begins tomorrow

Please let me know if you need any additional detail or have questions about specific client billings.

Jordan"

Jordan sends the email and marks "September Fee Allocation" as complete in her task management system. The process took just under four hours—exactly within her target range. Tomorrow she'll start monitoring collections and handling client questions about their October invoices, but for now, she's earned a proper lunch break.
