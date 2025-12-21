# Maya's Power BI to NetSuite Journal Entry Journey

## GGHC Investment Management - Fee Allocation Workflow

Maya Patel arrives at the GGHC office at 7:45 AM, her usual 15 minutes early. The 28-year-old senior analyst has been handling fee allocations for two years, and month-end means one thing: the dreaded Power BI to NetSuite journal entry marathon. She settles into her corner desk on the 31st floor, Manhattan stretching out below in the early morning light.

**7:52 AM - The Coffee Ritual**

Maya starts her laptop and heads to the kitchen while it boots up. The office coffee machine (a fancy Italian thing that the partners insisted on) is temperamental. She presses the button for a cappuccino and waits for the grinding sounds. Nothing. She tries again. The machine's display shows "DESCALE REQUIRED." Of course it does, on month-end day.

She settles for the backup Keurig and grabs a French Vanilla pod—not her favorite, but it'll do. Back at her desk, her laptop has finally loaded Windows, and she can see her desktop wallpaper: a photo from her recent trip to the Amalfi Coast.

**8:03 AM - Power BI Login Dance**

Maya opens Chrome and navigates to GGHC's Power BI portal. The login screen appears, and she enters her credentials: mpatel@gghc.com and her password (a complex string involving her cat's name and her college graduation year). The system immediately redirects to Microsoft's authentication page.

"Sign in with your organization account," the page reads. Maya clicks the button and waits. And waits. Microsoft's servers are apparently having a slow morning. After 47 seconds (she counts), the page loads asking for her email again. She types it in and hits enter.

Now comes the two-factor authentication. Maya pulls out her phone and opens the Microsoft Authenticator app. She taps "Approve" on the notification, and finally—FINALLY—Power BI loads.

**8:09 AM - Navigating the Dashboard Maze**

The GGHC Power BI workspace appears with 23 different dashboards. Maya needs the "Fee Allocation & AUM Analysis" dashboard, which is buried somewhere in the middle. She scrolls down, past "Client Performance Summary," "Portfolio Holdings Deep Dive," and "Trading Activity Monitor."

There it is: "Fee Allocation & AUM Analysis." She clicks it and the dashboard starts loading. Power BI's loading animation appears—a series of blue dots bouncing back and forth. Maya has learned that this animation can last anywhere from 15 seconds to 3 minutes, depending on the data volume.

Today it takes 1 minute and 22 seconds. The dashboard finally appears, showing a complex array of charts, tables, and filters for September 2025 fee calculations.

**8:15 AM - Filter Configuration Nightmare**

The dashboard has filters for:

- Date Range (currently set to "Last 30 Days")
- Client Type (All, Institutional, Retail, Family Office)
- Fee Structure (Management, Performance, Both)
- Account Status (Active, Closed, Suspended)

Maya needs September-specific data, so she clicks on the Date Range filter. A calendar appears, but it's defaulted to some random date in August. She clicks on September 1st, then tries to click September 30th. But clicking the second date just changes the start date instead of setting an end date range.

She tries clicking and dragging across the September dates. That doesn't work either. Finally, she notices the tiny "Custom Range" text at the bottom of the calendar popup. She clicks it, manually types "09/01/2025" and "09/30/2025," and hits Apply.

The dashboard starts refreshing. More bouncing blue dots.

**8:23 AM - Export Chaos**

When the data finally loads, Maya sees the Fee Allocation Summary table showing 847 rows of client fee calculations. She needs to export this to Excel for her allocation formulas. She hovers over the table until the three-dot menu appears in the top right corner.

Click. "Export data" appears in the dropdown. Click. Another menu appears: "Summarized data" or "Underlying data." Maya needs underlying data for her calculations, so she clicks that option.

A dialog box appears: "Export underlying data to Excel? This may take several minutes for large datasets." Maya clicks "Export" and immediately gets another dialog: "Your export is being prepared. You will receive an email notification when ready."

Great. Now she waits. Maya checks her watch: 8:26 AM. In her experience, these exports usually take 3-7 minutes, depending on how busy Power BI's servers are.

**8:31 AM - Third-Party Data Collection**

While waiting for the Power BI export, Maya needs to collect custodian fee schedules and performance reports. She opens a new Chrome tab and navigates to Northern Trust's institutional portal. Login: mpatel@gghc, password, and—naturally—two-factor authentication via SMS.

The SMS arrives: "Your Northern Trust security code is 847291." She enters it and waits for the portal to load. Northern Trust's interface looks like it was designed in 2003 and never updated. Maya navigates to Reports → Fee Schedules → September 2025.

The report generates as a PDF. She downloads it: "NT_Fee_Schedule_092025.pdf" saves to her Downloads folder. Next, she needs the performance attribution report. Navigate to Reports → Performance → Attribution Analysis. Date range: September 1-30, 2025. Generate Report.

This time the system hangs. The loading indicator spins for 2 minutes before timing out: "Report generation failed. Please try again."

Maya sighs and tries again. Same result. She picks up her desk phone and dials Northern Trust's support line.

**8:42 AM - Customer Service Roulette**

"Thank you for calling Northern Trust Institutional Services. Your call is important to us. Current wait time is approximately 7 minutes."

Maya puts the phone on speaker and continues working. The hold music is a generic jazz instrumental that gets old very quickly. At 8:49 AM, a human voice appears:

"Northern Trust, this is Derek. How can I help you?"

"Hi Derek, this is Maya Patel from GGHC. I'm trying to run a performance attribution report for September and the system keeps timing out."

"Let me check our system status... yeah, we're having some issues with the reporting server this morning. Reports are taking longer than usual or failing entirely. Can I email you the report directly?"

"That would be great. My email is mpatel@gghc.com. I need the performance attribution for September 2025."

"I'll have that to you within the hour. Anything else I can help with?"

Maya thanks Derek and hangs up. She makes a note in her Excel tracking file: "NT performance report - Derek sending via email by 9:45 AM."

**8:53 AM - Power BI Export Finally Arrives**

Maya's email notification chimes. "Your Power BI export is ready for download." She clicks the link in the email, which takes her back to Power BI's export page. The file is listed as "Fee_Allocation_Summary_092025.xlsx - 2.3 MB - Ready for download."

She clicks "Download" and the file saves to her Downloads folder. Maya immediately renames it to something more descriptive: "GGHC_Fee_Calc_Sep2025_PowerBI_Export.xlsx."

**8:56 AM - Excel Data Validation**

Maya opens the exported file. It contains 847 rows and 23 columns of fee calculation data:

- Client Name
- Account Number
- AUM (Beginning of Period)
- AUM (End of Period)
- Average AUM
- Management Fee Rate
- Performance Fee Rate
- Calculated Management Fee
- Calculated Performance Fee
- Total Fee

She spot-checks a few calculations manually. Client "Hartwell Industries" shows:

- Average AUM: $47,500,000
- Management Fee Rate: 0.75%
- Calculated Management Fee: $356,250

Maya opens her phone's calculator app: $47,500,000 × 0.0075 = $356,250. ✓

She spot-checks three more clients. All calculations look correct. But Maya notices something odd—client "Morrison Family Trust" shows a management fee rate of 1.25%, but she remembers their contract was recently amended to 1.00%.

**9:08 AM - Contract Verification Deep Dive**

Maya opens the shared drive (mapped as the S: drive) and navigates to Client_Contracts → M → Morrison_Family_Trust. The folder contains 14 files with names like "Morrison_Agreement_2023.pdf" and "Morrison_Amendment_Mar2025.pdf."

She opens the most recent amendment. On page 3, it clearly states: "Management fee reduced from 1.25% to 1.00% effective September 1, 2025." But Power BI is still using the old rate.

Maya grabs her phone and calls James in Client Services.

"James Mitchell," he answers.

"Hi James, it's Maya in Finance. I'm doing the September fee calculations and Morrison Family Trust is still showing the old 1.25% rate instead of the new 1.00% rate. Did the rate change get updated in the system?"

"Oh, that's my fault," James says immediately. "I updated their contract file but forgot to update the fee rate in our billing system. Let me do that now... okay, I'm in the client master file... changing the management fee from 1.25% to 1.00%... saved. But that probably won't show up in Power BI until tomorrow's data refresh."

Maya checks her watch. She needs these calculations today for month-end close. "Can you tell me what their September fee should be? I'll manually adjust it in my allocation."

"Sure, let me calculate... their average September AUM was $23,750,000, so at 1.00% that's $237,500 instead of $296,875."

Maya makes a note: "Morrison Family Trust - manual adjustment from $296,875 to $237,500 due to rate change."

**9:21 AM - Building the Allocation Engine**

Maya opens her master allocation template: "Fee_Allocation_Master_Template_2025.xlsx." This file contains all her allocation formulas and logic, built over months of refinement.

She creates a new tab labeled "September 2025" and starts copying data from the Power BI export. First, she pastes the client list and calculated fees. Then she adds columns for:

- Allocation Percentage (based on governing agreements)
- Management Company Allocation
- Investment Advisory Allocation
- Performance Fee Split

The allocation percentages come from a separate master file: "Client_Allocation_Rules_2025.xlsx." Maya opens this file and starts a series of VLOOKUP formulas to match each client with their specific allocation rules.

Client "Hartwell Industries": 60% to Management Company, 40% to Investment Advisory
Client "Newport Capital": 75% to Management Company, 25% to Investment Advisory
Client "Morrison Family Trust": 50/50 split

**9:43 AM - Formula Validation Horror**

Maya's VLOOKUP formula for the 47th client returns #N/A. She double-clicks the cell to see the formula: =VLOOKUP(B47,AllocationRules!A:D,2,FALSE)

The client name in B47 is "J&M Morrison LLC" but when she checks the AllocationRules file, it's listed as "J & M Morrison LLC" (with spaces around the ampersand). Maya manually corrects the client name and the formula works.

She continues down the list, finding and fixing similar naming inconsistencies:

- "Newport Capital, LLC" vs "Newport Capital LLC"
- "Hartwell Industries Inc." vs "Hartwell Industries, Inc."
- "Smith Family Trust" vs "The Smith Family Trust"

By 10:17 AM, Maya has cleaned up all the naming issues and her allocation formulas are working correctly.

**10:21 AM - NetSuite Journal Entry Prep**

Maya's allocation calculations show:

- Total Management Fees: $2,847,592.18
- Total Performance Fees: $1,294,750.00
- Management Company Allocation: $2,485,305.31
- Investment Advisory Allocation: $1,657,036.87

She needs to create journal entries in NetSuite for these allocations. Maya opens a new Chrome tab and navigates to NetSuite. Login: mpatel@gghc, password, two-factor authentication via phone app.

NetSuite loads and Maya navigates to Transactions → Make Journal Entry. She starts building the entry:

**Entry 1 - Management Fee Recognition:**

- Debit: Accounts Receivable - Management Fees: $2,847,592.18
- Credit: Revenue - Management Fees: $2,847,592.18

**Entry 2 - Performance Fee Recognition:**

- Debit: Accounts Receivable - Performance Fees: $1,294,750.00
- Credit: Revenue - Performance Fees: $1,294,750.00

**10:35 AM - The Attachment Struggle**

Maya needs to attach her Excel allocation file and Power BI export as supporting documentation. She clicks "Attach Files" in NetSuite and selects her allocation file.

The upload starts... 23%... 51%... 78%... 91%... and then fails. "Network error. Please try again."

Maya checks her file size: 4.7 MB. That should be fine. She tries again. Same error. She compresses the file into a ZIP folder, reducing it to 1.2 MB, and tries again. This time it works.

**10:44 AM - Controller Review Process**

With the journal entries prepared, Maya needs controller approval before posting. She saves the entries as drafts and sends an email to Janet Kowalski:

"Subject: September Fee Allocation Journal Entries - Ready for Review

Hi Janet,

September fee allocation entries are ready for your review:

- Management fees: $2,847,592.18
- Performance fees: $1,294,750.00
- Total revenue recognized: $4,142,342.18

Notes:

- Morrison Family Trust rate manually adjusted per James Mitchell (contract amendment)
- Northern Trust performance report delayed due to system issues
- All allocations reconciled to Power BI export

Entries are saved as drafts in NetSuite. Please review and approve when ready.

Thanks,
Maya"

**10:51 AM - Unexpected Complication**

Maya's phone rings. It's Janet.

"Maya, I'm reviewing your entries and I have a question about the Morrison adjustment. If we changed their rate manually, don't we need to adjust our AUM calculations too? Their performance fee might be affected."

Maya's stomach drops. She hadn't thought about the performance fee impact. "You're right. Let me recalculate their performance fee with the correct management fee base..."

She opens her allocation file and finds Morrison's performance calculation. Performance fees are calculated on gains above a hurdle rate, but the hurdle rate is adjusted for management fees paid. With the lower management fee, their performance fee should be slightly higher.

After recalculating: Morrison's performance fee increases from $47,250 to $49,180—a difference of $1,930.

"Janet, you're absolutely right. The performance fee adjustment is $1,930. Should I revise the journal entries?"

"Yes, please revise and resubmit. Better to get it right the first time."

**11:07 AM - Revision and Final Approval**

Maya updates her allocation calculations, revises the NetSuite journal entries, and resubmits them to Janet. This time, Janet reviews and approves them within 10 minutes.

"Entries approved and posted," Janet emails back. "Nice catch on the Morrison issue. Always think through the downstream impacts."

Maya updates her process documentation with a note: "Remember to check performance fee impacts when management fees are manually adjusted."

**11:23 AM - Documentation and Archive**

Maya creates a folder on the shared drive: "Fee_Allocations_September_2025" and saves:

- Power BI export file
- Allocation calculation file
- Supporting custodian reports
- Email correspondence about Morrison adjustment
- Screenshots of NetSuite journal entries

She updates her monthly tracking log: "September 2025 fee allocation: COMPLETE. Total revenue: $4,142,342.18. Manual adjustments: Morrison Family Trust rate change."

Maya leans back in her chair and checks her calendar. Next up: preparing accruals for October management fees. But first, she's definitely getting a proper cappuccino from the coffee shop downstairs—assuming she can convince the Italian machine to work, or she'll just walk two blocks to the good café.

**11:34 AM - Process Improvement Notes**

Before moving on, Maya opens a document called "Process_Improvements_Ideas.docx" and adds today's learnings:

1. Need automated client name standardization between Power BI and allocation rules
2. Consider setting up automated alerts when contract amendments affect fee rates
3. Research whether NetSuite file upload limits can be increased
4. Document performance fee recalculation process when management fees change
5. Investigate Power BI export scheduling to avoid morning traffic

She saves the document and adds a calendar reminder to discuss these improvements with Janet next week. For now, September's fee allocation is complete, reconciled, and documented. Maya allows herself a small smile—another month-end challenge conquered.
