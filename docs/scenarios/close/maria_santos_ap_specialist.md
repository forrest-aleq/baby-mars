# Story 2: Dockwa AP Operations - Invoice Processing & PDF Parsing Chaos
## **Difficulty Level: 3 (Very Hard)**

```json
{
  "story_metadata": {
    "bluebook_reference": {
      "row_number": 16,
      "task_id": "AR-002",
      "canonical_role": "AP AR Clerk",
      "parent_task": "Apply Cash Receipt",
      "task_description": "Apply incoming cash—ACH, checks, wires, card settlements—to open invoices, handling partial payments, discounts, and unidentified receipts (47 payments from lockbox PDFs)",
      "base_cycle_time_hours": 0.12,
      "actual_cycle_time_hours": 5.64,
      "complexity_multiplier": 47.0,
      "base_cost_per_task_usd": 6.05,
      "fully_loaded_cost_usd": 284.26,
      "automation_susceptibility": 3,
      "variance_explanation": "Base task is 0.12hr per cash receipt. Maria processes 47 payments from 6 PDFs requiring OCR extraction, customer name matching, and invoice reconciliation. OCR replaces manual PDF reading but doesn't change the core task of applying cash to invoices."
    },
    "process_complexity": {
      "total_workflow_steps": 58,
      "system_interactions": 7,
      "human_interactions": 6,
      "decision_points": 21,
      "exception_handling_scenarios": 14
    },
    "cognitive_load": {
      "simultaneous_systems": 5,
      "context_switching_events": 31,
      "regulatory_compliance_checks": 3,
      "cross_functional_coordination": 4
    },
    "interaction_patterns": {
      "phone_calls_required": 4,
      "email_escalations": 3,
      "slack_messages": 8,
      "approval_workflows": 5,
      "system_lookups": 24
    },
    "technical_complexity": {
      "software_applications_used": ["Chrome Browser", "Stampli", "Outlook", "QuickBooks Online", "Slack", "PDF Viewer", "Phone System", "OCR Engine"],
      "transaction_codes_executed": ["OCR Processing", "Invoice Approval", "Vendor Lookup", "GL Coding", "Payment Processing", "Data Validation"],
      "manual_calculations": 12,
      "data_validation_steps": 18
    },
    "time_pressure_factors": {
      "deadline_criticality": "Medium",
      "interruption_frequency": "High",
      "multitasking_requirements": "High",
      "error_recovery_complexity": "High"
    }
  }
}
```

### Maria's OCR Wrestling Match

Maria Santos stares at her dual monitor setup at 9:23 AM, surrounded by the familiar chaos of Dockwa's accounts payable operation. Empty coffee cups from the past three days line her desk, and her desk calendar shows "PDF PROCESSING DAY" written in red ink with three exclamation marks. As Dockwa's AP Specialist for the past 14 months, Maria has earned a reputation as the "PDF whisperer" - the only person who can consistently extract meaningful data from the bank's inconsistently formatted lockbox PDFs.

Her MacBook Pro 14-inch sits open next to a Windows desktop workstation that runs the OCR software stack she's assembled through months of trial and error. The Windows machine exists solely because the best OCR tools still don't play nicely with macOS, and Maria learned early in her tenure that manual data entry was a recipe for burnout.

**9:31 AM - The Email Avalanche**

Maria opens Outlook and immediately sees 14 new emails from lockbox@firstrepublic.com, each containing PDFs from different bank processing times throughout the night. The email subject lines tell a story of inconsistency:

- "Lockbox Batch 001 - 20251001" (3 payments)
- "Daily Processing Summary - October 1" (12 payments)
- "Overnight Deposit Report - 10/01/25" (7 payments)
- "URGENT: Late Deposit Processing" (2 payments)

Maria clicks on the first email and downloads "LockboxBatch001_20251001.pdf" to her Desktop. She then methodically downloads all 14 PDFs, creating a folder called "Oct01_Processing" to keep them organized.

**9:44 AM - The OCR Software Boot-Up Ritual**

Maria switches to her Windows workstation and double-clicks the desktop shortcut for "ABBYY FineReader 15." The software takes 47 seconds to load - she's timed it dozens of times while waiting. The splash screen shows "Loading OCR Engine..." with a progress bar that seems to move in slow motion.

While waiting, she opens her Excel template on the Mac: "Invoice_Processing_Master_2025.xlsx." The spreadsheet contains multiple worksheets:

- **Raw_OCR_Output:** Direct paste from ABBYY
- **Cleaned_Data:** Manually corrected customer names and amounts
- **Reconciliation:** Cross-reference with Recurly and NetSuite
- **Error_Log:** Documentation of all OCR failures and manual corrections

FineReader finally loads, and Maria clicks "Open PDF" from the toolbar. She navigates to her Oct01_Processing folder and selects the first PDF.

**9:52 AM - The First OCR Attempt**

The PDF opens in FineReader, showing a typical First Republic lockbox report. Maria can see immediately that this batch will be problematic - the document appears to be a scanned copy rather than a native PDF, meaning the text isn't selectable.

She clicks "Recognize Text" from the toolbar. FineReader analyzes the document for 23 seconds, then displays the results in its editing window. Maria reviews the OCR output:

**Original PDF Text:**
```
HARTWELL MARINA INC    CK# 4729    $2,850.00    INV: DW-2025-0847
SeaBreeze Yacht Club   Check: 1847  $1,200.00   Invoice DW-2025-0923
Marina del Rey Storage 3829         875.00      DW-2025-0856
```

**ABBYY OCR Output:**
```
HARTWELL MARINA INC    CK# 4729    $2,B50.00   INV: DW-2025-0B47
SeaBl'eeze Yacht Club  Check: 1B47  $1,200.00   Invoice DW-2025-0923
Marina del Ray Storage 3B29         B75.00      DW-2025-0B56
```

Maria immediately spots the OCR errors - the software consistently misreads "8" as "B" and struggles with punctuation in business names. This is exactly why her previous attempt at full automation failed.

**10:07 AM - The Manual Correction Marathon**

Maria clicks "Edit Text" and begins the painstaking process of correcting each OCR error:

1. Changes "2,B50.00" to "2,850.00"
2. Changes "DW-2025-0B47" to "DW-2025-0847"
3. Changes "SeaBl'eeze" to "SeaBreeze"
4. Changes "1B47" to "1847"
5. Changes "del Ray" to "del Rey"
6. Changes "3B29" to "3829"
7. Changes "B75.00" to "875.00"
8. Changes "DW-2025-0B56" to "DW-2025-0856"

Each correction requires her to:
- Double-click on the incorrect text
- Manually type the correction
- Click outside the text box to confirm
- Visually verify the change was applied

**10:23 AM - The Excel Export Process**

Once all corrections are made, Maria selects all the text in FineReader and copies it to the clipboard. She switches back to her Mac and pastes the data into the "Raw_OCR_Output" worksheet. The data pastes as unformatted text in a single column, requiring additional manipulation.

Maria uses Excel's "Text to Columns" feature to separate the data:
1. She selects the pasted data column
2. Clicks Data → Text to Columns
3. Chooses "Delimited" and clicks Next
4. Selects "Space" as the delimiter
5. Clicks Finish

The data spreads across multiple columns, but the formatting is still messy because business names with spaces get split incorrectly. "Marina del Rey Storage" becomes four separate columns instead of being recognized as a single business name.

**10:38 AM - The Data Cleaning Nightmare**

Maria switches to the "Cleaned_Data" worksheet and begins the manual reconstruction process. She knows from experience that this step can't be automated because every PDF format is different, and business names don't follow consistent patterns.

For the first entry, she manually types:
- **A2:** Hartwell Marina Inc
- **B2:** Check #4729
- **C2:** 2850.00
- **D2:** DW-2025-0847
- **E2:** =TODAY()

For the second entry, she notices an issue. The OCR correctly captured "SeaBreeze Yacht Club" but when she looks up this customer in their system, she remembers they're actually listed as "SB Yacht Club LLC." This name variation is exactly why automation fails.

**10:51 AM - The Customer Name Matching Challenge**

Maria opens Chrome and navigates to app.recurly.com to cross-reference customer names. She searches for "SeaBreeze" and gets no results. She tries "SB Yacht" and finds "SB Yacht Club LLC."

She opens a new tab and navigates to their customer management database (a custom internal tool built on Airtable) to see if there's a name mapping record. She searches for "SeaBreeze" and finds an entry:

**Customer Name Variations:**
- Legal Name: SB Yacht Club LLC
- DBA: SeaBreeze Yacht Club
- Check Writing Name: SeaBreeze Yacht Club
- Recurly Account: SB Yacht Club LLC
- Invoice Name: SeaBreeze Yacht Club

This is exactly why Maria maintains this database - customers often write checks using different business names than their legal entity names, and the OCR software can't make these connections automatically.

**11:17 AM - The Cross-System Reconciliation**

Maria updates her Excel sheet with the correct standardized names and moves to the reconciliation process. She opens another Chrome tab and logs into NetSuite to verify that each invoice exists and hasn't already been paid.

For invoice DW-2025-0847 (Hartwell Marina), she searches NetSuite's invoice database:
- Status: Outstanding
- Amount: $285.00
- Customer: Hartwell Marina Inc
- Due Date: September 15, 2025

But wait - the check is for $2,850.00, not $285.00. Maria realizes this is a payment for multiple invoices. She searches for all outstanding Hartwell Marina invoices and finds 10 unpaid invoices totaling exactly $2,850.00.

This requires a judgment call: should she apply the payment to the specific invoice referenced (DW-2025-0847) or distribute it across all outstanding invoices? She makes a note to ask Alex in Revenue Operations about the preferred allocation method.

**11:34 AM - The Second PDF Disaster**

Maria opens the second PDF in ABBYY FineReader. This one is formatted completely differently - it's a table-based layout instead of the line-by-line format from the first PDF. The OCR engine struggles even more with tables, producing output that looks like:

```
Customer    Amount    Reference
HARTWELL   2850.00   DW-2025
MARINA INC           0847
SeaBreeze   1200.00  DW-2025
Yacht Club           0923
```

The OCR software has split single entries across multiple lines and failed to recognize that invoice numbers were broken. Maria realizes she'll need to manually reconstruct this entire PDF.

**11:49 AM - The Manual Reconstruction Process**

Maria decides to abandon OCR for this PDF and manually transcribe the data. She opens the PDF in Preview on her Mac and arranges the windows side-by-side with Excel. She manually types each entry while constantly referring back to the PDF:

**Line 1:**
- Customer: Hartwell Marina Inc (she has to read this carefully - the PDF quality is poor)
- Amount: $2,850.00 (she triple-checks this number)
- Reference: DW-2025-0847 (she has to piece together the split invoice number)

**Line 2:**
- Customer: SeaBreeze Yacht Club (but she knows to enter "SB Yacht Club LLC" in the reconciliation sheet)
- Amount: $1,200.00
- Reference: DW-2025-0923

This manual process takes 4 minutes per entry compared to the 45 seconds per entry when OCR works correctly.

**12:15 PM - The Error Discovery**

While manually transcribing the third PDF, Maria notices something that would have been missed by automated processing: two different customers have very similar names:

- "Marina del Rey Storage LLC"
- "Marina del Rey Services LLC"

The check is written by "Marina del Rey Storage" but the invoice number (DW-2025-0856) belongs to "Marina del Rey Services LLC." This is likely a subsidiary payment or an accounting error that requires investigation.

Maria opens Slack and messages the customer success team: "Quick question - we received a check from Marina del Rey Storage for invoice DW-2025-0856, but that invoice belongs to Marina del Rey Services. Are these related entities? How should I apply the payment?"

The response comes back 8 minutes later: "Yes, they're sister companies. Storage handles all the check writing for both entities. Go ahead and apply to Services - this happens monthly."

**12:31 PM - The Aggregation and Summary Process**

After processing 6 PDFs (taking over 3 hours), Maria has extracted data for 47 individual payments totaling $73,924.50. She creates a summary worksheet with the cleaned data:

- **Total Payments:** 47
- **Total Amount:** $73,924.50
- **OCR Success Rate:** 23% (only 11 entries required no manual correction)
- **Customer Name Mismatches:** 12 (requiring database lookup)
- **Invoice Discrepancies:** 5 (requiring investigation)
- **Manual Transcription Required:** 3 PDFs (poor scan quality)

**12:44 PM - The Recurly Bulk Upload Attempt**

Maria exports her cleaned data as a CSV file and attempts to upload it to Recurly's bulk payment processing feature. She navigates to Recurly → Transactions → Import Payments and uploads her CSV.

Recurly's validation engine immediately flags 8 entries with errors:
- 3 customers not found in system (name matching issues)
- 2 invoice numbers don't exist
- 2 amount mismatches (invoice amount vs. payment amount)
- 1 duplicate payment (already processed yesterday)

Maria realizes she'll need to process the problem entries manually through Recurly's individual payment interface.

**1:02 PM - The Manual Payment Application**

For each flagged entry, Maria navigates through Recurly's payment application workflow:

1. Search for customer by name
2. If not found, try variations (abbreviations, DBA names, etc.)
3. Locate the correct invoice
4. Verify payment amount matches invoice amount
5. Apply payment and add notes about discrepancies
6. Generate payment confirmation

The process takes an average of 3 minutes per payment when everything goes smoothly, but problematic entries can take 10+ minutes each.

**1:31 PM - The NetSuite Journal Entry Creation**

With all payments applied in Recurly, Maria needs to create the corresponding journal entries in NetSuite. She logs into NetSuite and navigates to Transactions → General → Journal Entries.

She creates a single journal entry for the entire batch:

**Journal Entry JE-2025-4001:**

**Debit:**
- Account: 1100 - Cash - First Republic Checking
- Amount: $73,924.50
- Memo: Lockbox deposits - October 1, 2025 (47 payments)

**Credit:**
- Account: 1200 - Accounts Receivable - Customers
- Amount: $73,924.50
- Memo: Customer payments applied per Recurly batch upload

She attaches her cleaned Excel file and the original PDFs as supporting documentation.

**1:47 PM - The Daily Summary Report**

Maria creates her daily processing summary email:

"Subject: Daily Lockbox Processing Complete - Oct 1 ($73,924.50)

AP Team + Finance,

October 1 lockbox processing complete. Here's the summary:

**Processing Metrics:**
- PDFs processed: 6
- Individual payments: 47
- Total amount: $73,924.50
- Processing time: 4 hours, 16 minutes
- OCR accuracy: 23% (lower than usual due to scan quality)

**Manual Interventions Required:**
- 12 customer name lookups (business name variations)
- 5 invoice discrepancy investigations
- 3 PDFs required full manual transcription
- 8 Recurly upload errors resolved manually

**Issues for Follow-up:**
- First Republic scan quality declining (recommend discussion with bank)
- Customer name standardization project still needed
- Consider upgrading OCR software (current version struggling with new PDF formats)

**Next Steps:**
- NetSuite journal entry posted (JE-2025-4001)
- All supporting documents saved to shared drive
- Outstanding invoice aging report updated

Maria"

**1:53 PM - The Process Improvement Brainstorm**

As Maria finally takes her first real break of the day, she opens her OneNote "Process Improvement Ideas" section and adds today's observations:

**Immediate Wins:**
- Build customer name mapping database with all known variations
- Create standardized PDF processing checklist
- Set up automated email sorting for different PDF formats

**Medium-term Projects:**
- Evaluate newer OCR engines (Azure Computer Vision, AWS Textract)
- Build custom PDF preprocessing to improve OCR accuracy
- Create Recurly customer lookup API integration

**Long-term Vision:**
- End-to-end automation with human exception handling only
- Real-time payment processing instead of batch processing
- Integrated workflow between bank, OCR, and accounting systems

**2:01 PM - The Reality Check**

Maria texts her supervisor: "Oct 1 processing done. 47 payments, $73K total. OCR accuracy was terrible today - had to manually fix 77% of extractions. We really need to prioritize the automation upgrade project."

The response comes back quickly: "Great work as always. Let's schedule time next week to review the ROI analysis for better OCR tools. In the meantime, keep documenting these time sinks - makes the business case stronger."

Maria laughs and types back: "Trust me, I have PLENTY of documentation 😅"

As she closes her laptop and finally heads to the break room for a proper lunch, Maria reflects on the morning's work. What should theoretically be an automated data extraction process required constant human intervention:

- OCR software that can't handle real-world document variations
- Customer naming conventions that don't match between systems
- Invoice references that require business context to interpret correctly
- Amount discrepancies that need investigation and judgment calls
- System integrations that fail when data doesn't match exactly

She opens her iPhone and dictates a voice memo: "Day 427 of trying to automate invoice processing. Today's lesson: OCR is only as good as its input, and real-world business documents are chaos. The technology exists to do this better, but it requires custom development and system integration that's way beyond our current budget. For now, I remain the human bridge between inconsistent PDFs and structured accounting data."

Maria saves the voice memo to her "AP Automation Research" folder and heads to lunch, knowing that tomorrow morning will bring another batch of PDFs with their own unique formatting challenges.
