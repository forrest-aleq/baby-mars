# Story 6: GGHC Investment Management - Power BI Data Transformation to NetSuite Journal Entries
## **Difficulty Level: 3 (Very Hard)**

```json
{
  "story_metadata": {
    "bluebook_reference": {
      "row_number": 125,
      "canonical_role": "Senior Financial Analyst",
      "seniority_band": "Senior/Lead",
      "task_description": "Monthly client fee allocation and journal entry processing (Power BI to NetSuite)",
      "estimated_hours": 6.5,
      "fully_loaded_cost_usd": 520.00,
      "automation_susceptibility": 3
    },
    "process_complexity": {
      "total_workflow_steps": 78,
      "system_interactions": 9,
      "human_interactions": 4,
      "decision_points": 19,
      "exception_handling_scenarios": 12
    },
    "cognitive_load": {
      "simultaneous_systems": 6,
      "context_switching_events": 28,
      "regulatory_compliance_checks": 8,
      "cross_functional_coordination": 3
    },
    "interaction_patterns": {
      "phone_calls_required": 2,
      "email_escalations": 3,
      "slack_messages": 5,
      "approval_workflows": 4,
      "system_lookups": 31
    },
    "technical_complexity": {
      "software_applications_used": ["Power BI", "Excel", "NetSuite", "Chrome Browser", "PDF Viewer", "Email", "Power Query", "VBA Editor", "Calculator"],
      "transaction_codes_executed": ["Journal Entry Creation", "Client Fee Calculation", "Data Export", "Power Query Transform", "NetSuite Import"],
      "manual_calculations": 24,
      "data_validation_steps": 18
    },
    "time_pressure_factors": {
      "deadline_criticality": "High",
      "interruption_frequency": "Medium",
      "multitasking_requirements": "High",
      "error_recovery_complexity": "High"
    }
  }
}
```

### Rachel's Monthly Fee Allocation Engineering

Rachel Kim arrives at GGHC's Manhattan office at 7:30 AM on the third Tuesday of November, knowing she faces one of the most cognitively demanding tasks in investment management operations: transforming raw Power BI data into precise NetSuite journal entries for monthly fee allocations. As a Senior Analyst with a background in both finance and data engineering, Rachel has spent 26 months refining this process, but it still requires intense concentration and multiple system orchestrations that can take anywhere from 4 to 8 hours depending on data quality and month-end complexities.

Her workstation reflects the hybrid nature of her role: a 32-inch curved monitor for Power BI dashboards, a 27-inch secondary monitor for Excel manipulation, and a laptop dedicated to NetSuite access. The desk is organized with printed fee schedules, calculator, and a color-coded notebook that tracks her monthly allocation methodology.

**7:38 AM - The Power BI Data Extraction Ritual**

Rachel opens Chrome and navigates to powerbi.microsoft.com, logging in with her GGHC credentials. The GGHC investment operations team runs nightly ETL processes that aggregate data from:

- Custodian feeds (Charles Schwab, Fidelity, Interactive Brokers)
- Portfolio management system (PortfolioCenter)
- Performance attribution system (Advent APX)
- Client billing rates database (internal SQL server)

Rachel navigates to the "Fee Allocation Dashboard" workspace and opens the "October 2025 Fee Calculation" report. The dashboard loads showing:

- **Total AUM:** $11.6B as of October 31, 2025
- **Billable Assets:** $11.2B (excluding non-fee-paying assets)
- **Management Fees Due:** $8.47M (quarterly billing cycle)
- **Performance Fees Due:** $2.38M (annual calculation)
- **Client Count:** 238 active relationships

The Power BI report contains 14 different data tables that need to be exported and reconciled:

1. **Client_AUM_Detail:** Asset values by client and account type
2. **Fee_Rate_Matrix:** Current fee schedules by client relationship
3. **Performance_Fees:** Annual performance calculations where applicable
4. **Fee_Adjustments:** Manual adjustments and credits
5. **Custodian_Fees:** Third-party costs to be passed through
6. **New_Account_Proration:** Mid-month account openings requiring prorated billing
7. **Closed_Account_Final:** Final billings for closed relationships
8. **Minimum_Fee_Analysis:** Clients subject to minimum fee requirements
9. **Fee_Waiver_Exceptions:** Negotiated fee waivers and discounts
10. **Currency_Conversions:** FX rates for international client assets
11. **Tax_Adjustments:** State-specific fee tax calculations
12. **Regulatory_Reporting:** Fee disclosures required for SEC filings
13. **Client_Billing_Preferences:** Invoice format and delivery preferences
14. **Historical_Comparisons:** Month-over-month fee variance analysis

**7:52 AM - The Export Orchestration Process**

Rachel begins the tedious but critical export process, clicking through Power BI's interface to extract the data she needs. The Client_AUM_Detail table comes first - she hovers over the visual and selects "Export data" from the three-dot menu that appears. The system asks whether she wants underlying data or just the summary, and she chooses underlying data to capture all 238 client records, even though it means waiting 43 seconds for the export to process.

While that first file downloads as "Client_AUM_Detail_20251101.xlsx," Rachel moves on to the Fee_Rate_Matrix. This one makes her more careful - it contains the sensitive fee percentages that determine how much GGHC charges each client type. She deliberately selects "Summarized data" only, knowing that the detailed rates are proprietary information that shouldn't be floating around in random Excel files.

The rhythm becomes almost meditative: click, export, wait, download, repeat. Fourteen tables total, each requiring its own decision about data depth and sensitivity. Rachel finds herself checking her phone during the longer exports, scrolling through LinkedIn posts about "digital transformation" and "automation" - ironic, considering she's manually exporting data that should probably flow automatically between systems.

**8:17 AM - The Excel Data Integration Challenge**

With all Power BI data exported, Rachel navigates to Excel to create her fee allocation workbook:

**Software Navigation - Excel Workbook Creation:**
Rachel opens Microsoft Excel and begins workbook setup:
- **Application Launch:** Clicks Excel icon in taskbar
- **New Workbook:** "File" → "New" → "Blank workbook"
- **Save As:** Ctrl+S → types "GGHC_Fee_Allocation_November_2025.xlsx" → saves to "Monthly Allocations" folder
- **Worksheet Creation:** Right-clicks "Sheet1" tab → "Rename" → types "Raw_Data"
- **Additional Sheets:** Right-clicks worksheet tabs, selects "Insert" for each new sheet:
  - **Client_Master:** Normalized client information with unique identifiers
  - **Fee_Calculations:** Formulas applying fee rates to asset values
  - **Performance_Fees:** Complex performance bonus calculations
  - **Adjustments:** Manual corrections and special situations
  - **NetSuite_Export:** Final data formatted for journal entry import
  - **Reconciliation:** Cross-checks and variance analysis
  - **Documentation:** Audit trail and supporting calculations

**Software Navigation - Data Import Process:**
With all her exports collected, Rachel opens Excel and creates a new workbook - "GGHC_Fee_Allocation_November_2025.xlsx" - then begins importing the first Power BI file. She navigates to the Data tab, clicks "Get Data," and selects the Client_AUM_Detail file from her Downloads folder. The Power Query editor opens, previewing the data structure, and Rachel immediately sees problems that make her stomach drop slightly.

**8:34 AM - Rachel Encounters the Data Quality Nightmare**

As Rachel scrolls through the imported client data, she starts noticing the inconsistencies that will turn this into a longer day than planned. "Hartwell Industries LLC" appears in some rows, but "Hartwell Industries, LLC" with a comma shows up in others - the same client, but Excel will treat them as completely different entities. The Morrison Family Trust has asset values showing up as text instead of numbers, probably because someone formatted them with currency symbols in the source system.

Even worse, she spots three clients with duplicate entries that have different account type classifications. How is the same trust classified as both "High Net Worth Individual" and "Family Office" in the same data set? And of course, the date fields came through in MM/DD/YYYY format when NetSuite expects YYYY-MM-DD.

Rachel sighs and opens the Client_Master worksheet to begin the tedious cleaning process. She starts with Find & Replace, systematically hunting down "Hartwell Industries, LLC" and replacing it with the standardized "Hartwell Industries LLC." Then she tackles the trailing spaces that somehow got attached to "Morrison Family Trust " - invisible characters that will cause headaches later if she doesn't catch them now.

For the Morrison currency formatting issue, Rachel selects the problematic cells and uses Excel's Text to Columns feature to strip out the dollar signs and commas, then reformats them as proper numbers. The values had been showing as "$1,247,392.18" which Excel treats as text, but she needs clean numbers like 1247392.18 for her calculations to work. She creates a helper column with the formula =VALUE(SUBSTITUTE(SUBSTITUTE(B2,"$",""),",","")) to strip out the formatting, then copies and pastes the values back to replace the original messy data.

**Step 3: Duplicate Detection and Resolution**
Rachel uses Excel's conditional formatting to highlight duplicate client entries:
- Identifies "Coastal Pension Fund" with entries for both "Managed Account" and "Advisory Account"
- Determines these are legitimate separate account types requiring different fee calculations
- Tags them as "Coastal Pension Fund - Managed" and "Coastal Pension Fund - Advisory"

**9:07 AM - The Third-Party Data Integration**

Rachel's fee allocation process requires integrating data from external sources that don't flow through Power BI:

**Custodian Fee Reports:**
- Downloads Charles Schwab fee report: "Schwab_Custody_Fees_October_2025.pdf"
- Downloads Fidelity fee report: "Fidelity_October_Fees.xlsx"
- Downloads Interactive Brokers statement: "IB_Monthly_Statement_Oct2025.pdf"

Each custodian reports fees in different formats requiring manual extraction and standardization.

**Charles Schwab PDF Processing:**
Rachel opens the Schwab PDF and manually extracts fee data:
- Custody fees: $14,247.32 (to be passed through to clients)
- Transaction fees: $3,892.15 (absorbed by GGHC)
- Advisory fees: $847.23 (revenue sharing with Schwab)

She manually enters this data into her "Custodian_Fees" worksheet.

**Fidelity Excel Processing:**
The Fidelity file imports cleanly but uses different client identifiers:
- GGHC uses client numbers (GGHC-0001, GGHC-0002, etc.)
- Fidelity uses account numbers (4792-8847-X, 3847-2938-Y, etc.)

Rachel maintains a cross-reference table to map between systems:
```
GGHC_ID         Fidelity_Account
GGHC-0001       4792-8847-X
GGHC-0002       3847-2938-Y
GGHC-0003       9384-7463-Z
```

Using VLOOKUP formulas, she matches Fidelity fees to GGHC client identifiers.

**9:41 AM - The Fee Calculation Engine Development**

With clean data assembled, Rachel builds the core fee calculation logic. GGHC's fee structure includes multiple complexity layers:

**Basic Management Fees:**
Most clients pay tiered management fees:
- First $5M: 1.00% annually
- Next $5M: 0.85% annually
- Next $10M: 0.70% annually
- Above $20M: 0.60% annually

Rachel creates a complex Excel formula:
```
=IF(AUM<=5000000, AUM*0.01/4,
  IF(AUM<=10000000, (5000000*0.01 + (AUM-5000000)*0.0085)/4,
    IF(AUM<=20000000, (5000000*0.01 + 5000000*0.0085 + (AUM-10000000)*0.007)/4,
      (5000000*0.01 + 5000000*0.0085 + 10000000*0.007 + (AUM-20000000)*0.006)/4)))
```

**Performance Fees (Annual Calculation):**
Certain clients pay performance fees based on excess returns:
- High water mark methodology
- 20% of returns above 8% annually
- Calculated annually but accrued quarterly

For Coastal Pension Fund's performance fee:
- Beginning value (1/1/2025): $47.3M
- Ending value (12/31/2024): $52.8M
- Distributions: $1.2M
- Gross return: 15.1%
- Excess return: 7.1% (above 8% hurdle)
- Performance fee: $47.3M × 7.1% × 20% = $671,766

**Minimum Fee Adjustments:**
Some smaller clients have minimum quarterly fees:
- Tech Startup Holdings: $25,000 minimum (calculated fee: $18,750)
- Wilson Advisory: $5,000 minimum (calculated fee: $4,200)

Rachel's formula checks if calculated fees exceed minimums:
```
=MAX(Calculated_Fee, Minimum_Fee)
```

**10:18 AM - The Fee Adjustment and Exception Processing**

Rachel reviews the "Fee_Adjustments" data from Power BI and identifies several exceptions requiring manual handling:

**Client Credits and Adjustments:**
- Morrison Family Trust: $2,500 credit for Q3 billing error
- Hartwell Industries: Fee waiver for October due to service interruption
- Green Energy Fund: 50% fee reduction (negotiated discount for AUM commitment)

**New Account Proration:**
- Patterson LLC opened account on October 15th (requires 16-day proration)
- Riverside Holdings transferred additional assets on October 22nd (requires partial month billing)

**Closed Account Final Billing:**
- Marina Investment Partners closed account on October 8th (requires 8-day final billing)

Rachel creates manual calculation entries for each exception:

**Patterson LLC Proration:**
- Full monthly fee would be: $3,247.18
- Prorated fee (16/31 days): $3,247.18 × (16/31) = $1,676.64

**10:44 AM - The NetSuite Data Format Preparation**

With all fee calculations complete, Rachel must format the data for NetSuite import. NetSuite requires specific data structure and formatting:

**Required NetSuite Fields:**
- Entity (Client ID in NetSuite format)
- Account (Fee Revenue GL account code)
- Debit/Credit amounts
- Department (Investment Management)
- Class (Client relationship type)
- Memo (Descriptive text)
- Transaction Date
- Reference Number

Rachel creates the "NetSuite_Export" worksheet and uses formulas to transform her calculated data:

**Example NetSuite Entry for Hartwell Industries:**
```
Entity: 1001 (Hartwell Industries LLC)
Account: 4100 (Management Fee Revenue)
Credit: 28750.00
Department: 100 (Investment Management)
Class: 200 (Discretionary Clients)
Memo: Q4 2025 Management Fee - 0.75% annual rate
Date: 2025-10-31
Reference: MGT-2025-Q4-001
```

Rachel's transformation formulas concatenate and format data appropriately:
```
="MGT-2025-Q4-"&TEXT(ROW()-1,"000")  (for reference numbers)
=TEXT(Date_Cell,"YYYY-MM-DD")        (for date formatting)
=ROUND(Fee_Amount,2)                 (for currency precision)
```

**11:23 AM - The Complex Performance Fee Allocation**

Performance fees require more sophisticated NetSuite entries because they involve multiple GL accounts and potential accrual adjustments:

**Coastal Pension Fund Performance Fee Entry:**
The $671,766 annual performance fee must be:
1. Accrued quarterly ($167,942 per quarter)
2. Allocated across multiple investment strategies
3. Adjusted for any quarterly true-ups

Rachel creates multiple journal entry lines:
```
Line 1: Debit - Accrued Performance Fee Receivable: $167,942
Line 2: Credit - Performance Fee Revenue - Equity Strategy: $125,956
Line 3: Credit - Performance Fee Revenue - Fixed Income: $41,986
```

The allocation between strategies is based on the client's asset mix and performance attribution by strategy.

**11:47 AM - The Reconciliation and Quality Control Process**

Before exporting to NetSuite, Rachel performs comprehensive reconciliation:

**Total Fee Reconciliation:**
- Sum of all management fees: $8,470,293.18
- Sum of all performance fees: $2,380,447.92
- Sum of all adjustments: -$127,450.38
- **Total Billing:** $10,723,290.72

**Power BI vs. Excel Reconciliation:**
- Power BI dashboard total: $10,723,291.00
- Excel calculation total: $10,723,290.72
- **Variance:** $0.28 (acceptable rounding difference)

**Client Count Verification:**
- Power BI clients: 238
- Excel processed clients: 238
- Clients with $0 fees: 3 (fee waivers)
- **Net billing clients:** 235

**12:15 PM - The Third-Party Data Cross-Validation**

Rachel validates her fee calculations against external systems:

**PortfolioCenter Validation:**
- Exports client AUM report from PortfolioCenter
- Compares asset values to Power BI data
- Identifies and investigates variances >$50,000

**Custodian Statement Validation:**
- Cross-references largest client balances with custodian statements
- Verifies that fee calculations use correct asset values
- Documents any timing differences between systems

**Prior Month Trend Analysis:**
- Compares total fees to September 2025: $10.2M
- Variance: +$523K (+5.1% increase)
- Primary drivers: Market appreciation ($380K) and new clients ($143K)

**12:38 PM - The NetSuite Import Process**

Rachel exports her NetSuite-formatted data as "GGHC_Fee_JE_November_2025.csv" and logs into NetSuite. She navigates to:

Transactions → General → Import Journal Entries

**NetSuite Import Steps:**
1. **Template Download:** Downloads NetSuite's journal entry import template
2. **Data Mapping:** Maps her Excel columns to NetSuite fields
3. **File Upload:** Uploads the CSV file for validation
4. **Error Resolution:** Addresses any import validation errors
5. **Preview Review:** Reviews the journal entry preview before posting
6. **Batch Processing:** Processes the import (creates JE-2025-1147)

**Import Validation Results:**
- Total Lines Processed: 487
- Successful Imports: 487
- Errors: 0
- Warnings: 3 (minor formatting issues, auto-corrected)

The journal entry creates a single transaction with 487 line items totaling $10,723,290.72 in fee revenue.

**12:54 PM - The Audit Documentation Process**

Rachel's final task is creating comprehensive audit documentation:

**Documentation Package Includes:**
1. **Source Data Files:** All Power BI exports with timestamps
2. **Calculation Workbook:** Excel file with all formulas and logic
3. **Reconciliation Reports:** Variance analysis and validation checks
4. **Exception Documentation:** Supporting details for all manual adjustments
5. **NetSuite Import File:** Final CSV and import confirmation
6. **Process Checklist:** Verification that all steps were completed

Rachel saves all files to the network drive: "G:/Finance/Fee_Allocation/2025/November/Monthly_Close/"

**1:08 PM - The Process Improvement Documentation**

Rachel updates her "Fee Allocation Process Improvements" log with observations from this month:

**Issues Encountered:**
1. Power BI client name inconsistencies caused 23 minutes of manual cleanup
2. Custodian fee report format changes required manual extraction (Schwab)
3. New client proration calculation required manual override of standard formula

**Process Optimizations Implemented:**
1. Created data validation rules in Excel to catch common formatting issues
2. Built cross-reference table for custodian account mapping
3. Enhanced reconciliation formulas to automatically flag variances >$1,000

**Proposed Automation Opportunities:**
1. Direct API connection between Power BI and NetSuite (eliminate Excel manipulation)
2. Automated custodian fee import using RPA tools
3. Client name standardization rules built into Power BI ETL process

**1:17 PM - The Stakeholder Communication**

Rachel prepares her completion summary for the finance team:

"Subject: November Fee Allocation Complete - $10.7M Total Billing

Finance Team,

November fee allocation processing is complete. Summary:

**Key Metrics:**
- Total fees allocated: $10,723,290.72
- Management fees: $8,470,293.18
- Performance fees: $2,380,447.92
- Net billing clients: 235
- Processing time: 5 hours, 39 minutes

**Notable Items:**
- Coastal Pension performance fee: $671,766 (annual calculation)
- 3 client fee waivers totaling $127,450
- New client Patterson LLC prorated billing: $1,677

**Quality Control:**
- All reconciliations completed with <$1 variance
- Audit documentation saved to network drive
- NetSuite journal entry posted (JE-2025-1147)

**Next Month Improvements:**
- Implementing automated custodian fee import
- Enhanced data validation rules in Excel template

Rachel"

**1:23 PM - The Human Expertise Reflection**

As Rachel saves her work and prepares for lunch, she reflects on the complexity of fee allocation processing. Despite sophisticated tools like Power BI and NetSuite, the process still requires extensive human judgment:

- **Data Quality Assessment:** Identifying and correcting inconsistencies across multiple systems
- **Business Logic Application:** Understanding complex fee structures and exception handling
- **Regulatory Compliance:** Ensuring fee calculations meet SEC and state requirements
- **Client Relationship Management:** Handling negotiated fee arrangements and service credits
- **Cross-System Integration:** Bridging data formats and timing differences between platforms

The technology handles data aggregation and calculation speed, but Rachel's expertise ensures accuracy, compliance, and audit readiness. Tomorrow, December transactions will begin accumulating, and in 30 days, she'll repeat this comprehensive process to ensure GGHC's fee revenue is accurately captured and properly allocated across their $11.6B investment management business.
