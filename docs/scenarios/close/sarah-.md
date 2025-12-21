# Sarah's Consolidation Day at Beacon Analytics

## A Finance Manager Outgrowing QuickBooks Online

Sarah Chen opens her laptop at 8:03 AM in Beacon Analytics' office in Austin, her third cup of coffee already empty. The 32-year-old Finance Manager has been at the Series B SaaS company for 18 months—long enough to know their QuickBooks Online setup is held together with duct tape and pivot tables, but not long enough to have convinced the board to approve a NetSuite migration.

Her desk has two monitors (she fought for three, got two), a stack of Post-it notes with entity abbreviations ("BCON-US", "BCON-UK", "BCON-ACQ"), and a mug that reads "I'm silently correcting your financial statements." Her background: three years at Deloitte, two years as a Senior Accountant at a public company, and now this—the impossible task of making a $15M ARR company with three entities look financially sophisticated using QuickBooks Online.

**8:07 AM - The Morning Consolidation Ritual**

Sarah opens her "Month-End Close - October 2025" folder. Inside are three separate QuickBooks Online companies:

1. **Beacon Analytics Inc.** (Delaware C-corp, main entity)
2. **Beacon Analytics UK Ltd.** (UK subsidiary for European operations)
3. **DataFlow Systems Inc.** (acquired company, still on separate QBO, integration pending)

She also opens Excel, specifically a file named "Consolidated_Financials_MASTER_v47_FINAL_ACTUAL.xlsx" that has 23 tabs and crashes if she tries to refresh all the pivot tables at once.

The CFO, Michael, wants consolidated financials by EOD for tomorrow's board meeting. Sarah knows this means she'll be here until 9 PM.

**8:14 AM - Entity #1: Beacon Analytics Inc. (Main)**

Sarah logs into the main Beacon Analytics QBO account. The dashboard loads. She navigates to Reports > Profit & Loss, selects October 1-31, 2025, and exports to Excel.

The P&L downloads with QBO's default formatting—merged cells, random bolding, categories that don't quite align with their board reporting format. She copies the data into her consolidation spreadsheet, then spends 8 minutes manually reformatting:

* Delete merged cells
* Remove QBO's auto-generated subtotals
* Align account names to match the board format
* Separate out their new "DataFlow" class (they used QBO Classes to track the acquisition, but it's imperfect)

She notices something odd. Revenue shows $1,347,289 for October, but she knows from Stripe it should be closer to $1.4M. She clicks back into QBO and realizes the integration with Stripe didn't catch the last two days of the month. Fantastic.

**8:29 AM - The Stripe Revenue Reconciliation**

Sarah opens Stripe in a new tab. She navigates to their "balance transactions" report, exports October transactions, and starts matching them against QBO entries.

She finds the issue: Stripe processed $73,482 in transactions on October 30-31 that never made it to QBO because their Zapier integration hit its monthly limit and stopped syncing. She never got an alert.

She manually creates a journal entry in QBO:

* DR: Stripe Clearing Account - $73,482
* CR: Subscription Revenue - $73,482
* Memo: "Manual entry - Stripe sync failure Oct 30-31"

She makes a note in her "Issues Log" spreadsheet: "Stripe integration failed again. Need better solution or higher Zapier tier ($$$)."

**8:44 AM - The Revenue Recognition Problem**

Now she needs to handle revenue recognition. Beacon Analytics sells annual contracts with monthly and annual billing options. Their revenue recognition should follow ASC 606, but QBO doesn't have native rev rec functionality.

Sarah maintains a separate spreadsheet called "Revenue_Recognition_Tracker_2025.xlsx" with every customer contract:

* Customer name
* Contract value
* Start date
* End date
* Monthly recognition amount
* Billing terms

She has formulas that calculate how much revenue should be recognized each month, then she manually creates journal entries in QBO to move cash to deferred revenue and recognize the appropriate amount each month.

For October, she has 247 contracts to review. She filters for new contracts, expanded contracts, and churned contracts. She calculates:

* Total cash received: $1,421,334
* Amount to defer: $847,293
* Amount to recognize from previous deferrals: $673,248
* Net revenue for October: $1,247,289

She creates the journal entries in QBO:

* DR: Cash - $1,421,334 / CR: Deferred Revenue - $1,421,334 (cash received)
* DR: Deferred Revenue - $673,248 / CR: Subscription Revenue - $673,248 (recognition)

This process takes 37 minutes. She knows NetSuite or Sage Intacct could do this automatically. She's mentioned it in every monthly meeting with Michael for six months.

**9:26 AM - Entity #2: Beacon Analytics UK Ltd.**

Sarah logs out of the US QBO and logs into the UK entity's QBO account. Different company, different login, different chart of accounts (they tried to keep them consistent but failed around month three).

The UK entity handles all European customers for GDPR/data sovereignty reasons. It's a separate legal entity, separate bank accounts, separate everything—except it rolls up to the US parent for consolidation.

She exports the UK P&L for October. Revenue: £287,483. She needs to convert this to USD for consolidation.

She opens XE.com and checks the average GBP/USD exchange rate for October 2025: 1.2847. She multiplies: £287,483 × 1.2847 = $369,314 USD.

But wait—should she use the average rate for the month, or the spot rate at month end? She checks her notes from the external auditor's comments last year: "Use average rate for P&L, ending rate for balance sheet."

She makes the conversion and copies the UK figures into her consolidation spreadsheet under "BCON-UK" columns. Then she has to manually eliminate intercompany transactions:

The US entity charges the UK entity for platform fees ($47,000/month). This shows as revenue in the US and expense in the UK, but for consolidated reporting it needs to be eliminated. She creates an elimination column in her spreadsheet:

* Eliminate US intercompany revenue: ($47,000)
* Eliminate UK intercompany expense: $47,000

**9:52 AM - Entity #3: DataFlow Systems Inc. (The Acquisition)**

Three months ago, Beacon Analytics acquired DataFlow Systems, a smaller analytics company, for $8.5M. The deal closed on August 1, so October is only their third month of consolidated reporting.

DataFlow is still on its own QBO account because the "integration" keeps getting pushed back. Sarah was promised they'd migrate DataFlow to the main Beacon QBO by September. It's now late October.

She logs into the DataFlow QBO account (she had to request access three times before getting login credentials). The account is... a mess. Their previous bookkeeper apparently didn't believe in account descriptions or consistent categorization.

October P&L shows:

* Revenue: $197,482
* But she sees a category called "Other Income" with $45,000 in it

She clicks into the transaction detail. It's actually product revenue that someone miscategorized. She makes a note to fix it, but she doesn't have time to reclassify everything today—board deck takes priority. She adjusts it manually in her consolidation spreadsheet.

**10:18 AM - The Consolidation Spreadsheet**

Sarah now has data from three entities in her master Excel file. Time to consolidate.

Her spreadsheet has columns for:

* Account Name
* BCON-US (main entity)
* BCON-UK (converted to USD)
* DataFlow (acquired entity)
* Eliminations
* **Consolidated Total**

She starts copying and pasting data, making sure accounts align. The UK entity uses different account names for the same things:

* US calls it "Sales & Marketing", UK calls it "Marketing Expense"
* US has "Research & Development", UK has "Product Development"
* DataFlow calls everything "Operating Expenses" with unclear subcategories

Sarah spends 20 minutes manually mapping accounts so they align for board reporting. She knows a real consolidation system would have mapped these once and automated it. Instead, she maintains a separate "Account Mapping" tab and does it manually every month.

**10:43 AM - The Intercompany Elimination Hell**

Beyond the platform fee, there are other intercompany transactions to eliminate:

1. **Management fee** : US charges UK a $12,000/month management fee
2. **Software licensing** : UK licenses software to US for $8,000/month
3. **Shared services** : DataFlow charges US $5,000/month for data infrastructure
4. **Loan interest** : US entity has a $1M intercompany loan to UK, charging 5% interest

Sarah has a separate tab called "Intercompany Tracker" where she's supposed to log all intercompany transactions. But people forget to tell her about them, so she discovers them during consolidation and has to retroactively fix prior months.

Today she discovers a new one: DataFlow apparently paid $15,000 to Beacon US for "consulting services" in October. This wasn't in her intercompany tracker. She makes a note to ask the DataFlow team about it, adds it to her eliminations, and updates her tracker.

The elimination entries in her spreadsheet:

* US Intercompany Revenue: $(80,000)
* UK Intercompany Expense: $67,000
* DataFlow Intercompany Expense: $20,000
* Intercompany Interest Income: $(4,167)
* Intercompany Interest Expense: $4,167

She triple-checks the math to make sure intercompany entries net to zero. They don't. She's off by $7,000. She spends 15 minutes tracing through transactions until she finds it: the consulting fee from DataFlow was actually $22,000, not $15,000. Someone sent her the wrong number.

**11:14 AM - The Budget vs. Actuals Nightmare**

Michael (CFO) wants a budget vs. actuals analysis for the board deck. The problem: their budget lives in a different spreadsheet, created in January, that doesn't perfectly align with their current chart of accounts (they've added accounts since then).

Sarah opens "2025_Operating_Budget_BOD_Approved.xlsx" and starts copying budget figures into her consolidation file. The budget was built at the parent company level, so she needs to:

1. Take consolidated actuals from her master file
2. Compare to budget
3. Calculate variances
4. Add variance explanations for anything >10%

She creates a new tab: "Budget_vs_Actuals_Oct2025"

Key variances she needs to explain:

* **Revenue** : Budget was $1.35M, Actual is $1.42M (+5.2%, good!)
* **Sales & Marketing** : Budget was $425K, Actual is $487K (+14.6%, over budget)
* **R&D** : Budget was $380K, Actual is $412K (+8.4%, slightly over)
* **G&A** : Budget was $245K, Actual is $289K (+18%, significantly over)

She starts drafting explanations:

* "S&M over budget due to additional headcount hired in Q3 (4 AEs vs. planned 2) to support accelerated growth"
* "R&D over budget due to contractor costs for DataFlow integration project"
* "G&A over budget due to: (1) legal fees for acquisition $27K, (2) accounting fees for audit prep $15K, (3) insurance increase $12K"

**11:47 AM - The Department Budget Check-In**

Sarah's Slack lights up. It's from James, the VP of Engineering:

"Hey Sarah, can you send me my department's spend for October? Need to see where we are against budget."

Sarah sighs. Every department head asks this question, usually the day before month-end close. She has to:

1. Go back into QBO
2. Filter by Department (they use Classes for departments)
3. Export the report
4. Manually allocate shared expenses (rent, insurance, etc.)
5. Compare to their department budget
6. Send a nice formatted summary

For Engineering, she filters QBO by Class "Engineering", exports October expenses: $412,847.

But this doesn't include:

* Allocated rent (based on headcount: 18 eng / 47 total × $28K rent = $10,787)
* Allocated insurance
* Allocated software (like Slack, Google Workspace)
* Engineering's share of their AWS bill (she has to check AWS directly because the bill shows up as one line item)

She opens her "Overhead_Allocation_Model.xlsx" and calculates Engineering's true October spend: $447,923.

Budget was $435,000. They're over by $12,923 (3%).

She creates a quick summary and Slacks it to James: "Engineering Oct spend: $447.9K vs budget $435K. Overage due primarily to AWS increase (new customers = more compute) and contractor for DataFlow migration."

**12:03 PM - The Cash Flow Realization**

While pulling department numbers, Sarah notices something concerning. She opens the Balance Sheet in QBO.

Cash balance across all entities:

* BCON-US: $2,847,392
* BCON-UK: £423,847 (~$544,442 USD)
* DataFlow: $384,293

Total consolidated cash: ~$3.8M

She knows their monthly burn rate is around $1.2M. That's about 3 months of runway. But they just raised a $12M Series B in August—where did the money go?

She pulls up the bank statements and starts tracing:

* $8.5M to DataFlow acquisition (cash portion)
* $1.2M to escrow for acquisition earnout
* $847K to pay down the line of credit
* Monthly burn of $1.2M × 3 months = $3.6M

She does the math: $12M - $8.5M - $1.2M - $847K - $3.6M = -$2.147M. They're burning more than she thought.

She makes a note to discuss with Michael: "Need to review cash runway analysis. Current burn may require raising again sooner than planned."

**12:24 PM - The SaaS Metrics Calculation**

The board deck needs SaaS metrics. QBO doesn't calculate these, so Sarah maintains another spreadsheet: "SaaS_Metrics_Dashboard.xlsx"

She needs to calculate:

* **MRR (Monthly Recurring Revenue)** : She pulls this from their "Customer_Contract_List" spreadsheet, summing all active monthly contract values
* **ARR (Annual Recurring Revenue)** : MRR × 12
* **Net Revenue Retention** : She needs to compare October 2024's cohort to October 2025, accounting for upgrades, downgrades, and churn
* **CAC (Customer Acquisition Cost)** : Total S&M spend / new customers acquired
* **LTV (Lifetime Value)** : Average contract value × (1/churn rate) × gross margin
* **LTV:CAC Ratio** : Should be >3.0 to make the board happy

She spends 30 minutes pulling data from:

* Salesforce (new customer count)
* Stripe (actual subscription data)
* QBO (S&M expenses)
* Her revenue recognition spreadsheet (for churn calculations)
* A separate spreadsheet someone in RevOps maintains (for upgrade/downgrade tracking)

October metrics:

* MRR: $1,247,392
* ARR: $14,968,704
* NRR: 118% (good!)
* CAC: $42,847 / 47 new customers = $912/customer
* LTV: Using their model: ~$8,400
* LTV:CAC: 9.2x (excellent!)

But she's not confident in these numbers because they're pulled from 6 different sources and manually assembled. If an investor asks "how do you calculate this?" she has to explain her Frankenstein process.

**1:02 PM - Lunch Break (Not Really)**

Sarah microwaves leftover pad thai from last night and eats at her desk while reviewing the board deck draft. Michael sent her the latest version this morning with a note: "Need financials inserted by EOD."

The deck has placeholder slides:

* Slide 8: "Consolidated P&L - October 2025" [INSERT SARAH'S DATA]
* Slide 9: "Budget vs. Actuals" [INSERT SARAH'S DATA]
* Slide 10: "SaaS Metrics Dashboard" [INSERT SARAH'S DATA]
* Slide 11: "Cash Position & Runway" [INSERT SARAH'S DATA]

She also sees a note from Michael: "Board asking about gross margin by customer segment. Can we break out Enterprise vs. SMB?"

Sarah's heart sinks. They don't track COGS by customer segment in QBO. They barely track COGS accurately at all. Their "Cost of Revenue" account includes:

* Hosting costs (AWS, which varies by customer usage but isn't tagged by customer segment)
* Support team salaries (not allocated by customer segment)
* Data provider fees (flat monthly fee, not customer-specific)

She can't provide accurate gross margin by segment without spending 10 hours building a new allocation model. She Slacks Michael: "For accurate segment-level gross margin, I'd need 1-2 days to build the allocation model. Can we show overall GM and add segment breakout to next month's board deck?"

Michael responds: "Let's do blended GM this month. But we need segment-level for next quarter. Add to your project list."

Project list. Sarah's "project list" is currently 23 items long, all variations of "things QBO can't do that we need."

**1:34 PM - The Audit Prep Reminder**

Email from their external auditor, Deloitte: "Hi Sarah, friendly reminder that we'll be starting your 2025 year-end audit fieldwork in late January. We'll need the following ready:

1. Trial balances for all entities
2. Consolidation workpapers with elimination entries
3. Revenue recognition schedules with contract support
4. Intercompany reconciliation and eliminations
5. Fixed asset rolls
6. Debt schedules
7. Equity roll-forward
8. Flux analysis for all accounts >$50K variance YoY

Can you confirm you'll have these ready by January 15th?"

Sarah looks at her current process:

* Trial balances: Easy to export from QBO
* Consolidation workpapers: She maintains them in Excel, but they're a mess
* Rev rec schedules: Excel spreadsheet, manually updated
* Intercompany: Tracked in Excel, frequently incomplete
* Fixed assets: QBO tracks them, but depreciation categories are wrong
* Debt: Small enough to track manually
* Equity: Should be straightforward

She responds: "Yes, we'll have everything ready. One question: for consolidation workpapers, what format do you prefer?"

She knows what the auditor will say: "We typically see clients use consolidation software or NetSuite's consolidation module."

**1:49 PM - The NetSuite Conversation (Again)**

Sarah opens the email thread from three months ago titled "Accounting System Evaluation - NetSuite vs. Sage Intacct."

Back in July, she put together a business case for upgrading from QuickBooks Online:

**Current Pain Points with QBO:**

* Manual consolidation across 3 entities (10-15 hours/month)
* No native revenue recognition (5-8 hours/month manual work)
* No intercompany eliminations (3-5 hours/month)
* Limited reporting (custom reports built in Excel)
* No budgeting functionality (maintain parallel budget in Excel)
* No department-level reporting without manual work
* Poor multi-currency handling
* No audit trail for journal entry approvals
* Can't handle more complexity as we grow

**Solutions Evaluated:**

1. **NetSuite** :

* Pros: Comprehensive, handles everything, scalable to IPO
* Cons: $60K-$100K first year implementation, $30K/year ongoing, 4-6 month implementation

1. **Sage Intacct** :

* Pros: Good for SaaS companies, strong multi-entity, $20K-$40K implementation
* Cons: Less scalable than NetSuite, still significant cost

1. **Workday Financials** :

* Pros: Modern UI, great reporting
* Cons: Overkill for current size, very expensive

**ROI Calculation:**

* Current time spent on manual work: ~30 hours/month
* Sarah's loaded cost: ~$75/hour
* Monthly cost of manual work: $2,250
* Annual: $27,000 in labor cost alone (not counting error risk, missed insights, opportunity cost)

She sent this to Michael in July. His response: "Great analysis. Let's revisit after Series B closes and we know our runway."

Series B closed in August. It's now late October. Every time she brings it up, there's a reason to delay:

* "We're still integrating DataFlow"
* "Q3 close is too busy"
* "Board meeting prep takes priority"
* "Holiday season is coming"

**2:07 PM - The Department Budget Request**

Sarah's Slack lights up again. This time it's from Priya, VP of Marketing:

"Sarah! Quick question - I want to hire a contractor for a project. Budget is $15K. Do I have room in my Q4 budget?"

Sarah doesn't have a real-time budget tracking system. She has to:

1. Open her master budget spreadsheet
2. Find Marketing's Q4 budget
3. Pull YTD actuals from QBO
4. Calculate remaining budget
5. Factor in known committed spend

She opens "2025_Operating_Budget_BOD_Approved.xlsx" and navigates to the Marketing tab:

* Q4 Marketing Budget: $387,000
* Oct Actual: $124,800 (she just calculated this)
* Nov-Dec Budget remaining: $262,200

But she also knows:

* Two planned events in November: $45K
* Planned agency fees Nov-Dec: $38K
* New headcount starting in November: ~$25K/month

Remaining discretionary budget: $262K - $45K - $38K - $50K = $129K

Sarah Slacks back: "You have ~$129K discretionary budget left in Q4. $15K contractor should fit, but it's getting tight. What's the project?"

Priya: "Want to create case study videos for top customers. High ROI."

Sarah: "Sounds good. Can you send me the contractor info so I can add them to our vendor list?"

**2:23 PM - The Vendor Setup Process**

Adding a vendor to QBO. Should be simple. But Sarah has a checklist:

1. Verify vendor is legitimate (Google search, check website)
2. Get W-9 form for tax reporting
3. Set up vendor in QBO with correct payment terms
4. Determine correct expense category
5. Add to "Approved Vendor List" for the team
6. Set up in Bill.com if they use it (they don't, another system they should have)

She sends Priya a form email: "Great! Please have them complete the attached W-9 and send their invoices to ap@beaconanalytics.com. What GL account should this charge to - Marketing Programs or Marketing Agency?"

Priya: "Uh... which one is for video production?"

Sarah: "Marketing Programs is for events, content, videos. Marketing Agency is for retainer-based agency work."

Priya: "Marketing Programs then!"

Sarah makes a mental note: They need a better chart of accounts. Half the company doesn't understand which accounts to use.

**2:41 PM - Back to the Board Deck**

Sarah returns to the consolidation work. She needs to finish the board deck slides. She starts copying data from her master spreadsheet into PowerPoint:

**Slide 8: Consolidated P&L**
She pastes her consolidated numbers, formatted nicely:

* Revenue: $1,421K
* Gross Profit: $1,124K (79% margin)
* Operating Expenses: $947K
* Net Income: $177K (12.5% margin)

She adds a note: "First profitable month in company history!"

**Slide 9: Budget vs. Actuals**
She pastes her variance analysis with color coding:

* Green: Revenue (+5.2% vs. budget)
* Yellow: R&D (+8.4% vs. budget)
* Red: G&A (+18% vs. budget)

She adds her variance explanations as footnotes.

**Slide 10: SaaS Metrics**
She creates a nice dashboard-style slide:

* ARR: $14.97M (+23% YoY)
* NRR: 118%
* New Customers: 47 in October
* Churn: 2.3% (low, good!)
* CAC: $912
* LTV: $8,400
* LTV:CAC: 9.2x

**Slide 11: Cash & Runway**
This is the concerning one:

* Cash: $3.8M
* Monthly Burn: $1.2M
* Runway: 3.2 months

She adds a note: "Current runway is 3.2 months based on October burn. Recommend revisiting fundraising timeline."

**3:14 PM - The "One More Thing" Slack**

Michael Slacks her: "Sarah, one more thing for the board deck - can you add a slide showing our revenue mix by customer segment? Enterprise vs. Mid-Market vs. SMB?"

Sarah wants to scream. This is exactly the segment analysis she said would take days to build properly.

She has two choices:

1. Say "I don't have this data readily available, need time to build"
2. Pull together something rough from Salesforce tags

She chooses option 2 because the board meeting is tomorrow.

She logs into Salesforce, exports all active customers with their "Company Size" tag, matches them to her revenue recognition spreadsheet (manually, because the data doesn't auto-sync), and creates a rough breakdown:

* Enterprise (>500 employees): $687K MRR (55%)
* Mid-Market (50-500 employees): $374K MRR (30%)
* SMB (<50 employees): $186K MRR (15%)

She adds a footnote: "Segment classification based on Salesforce employee count data, matched to subscription revenue. May not reflect 100% accuracy due to manual matching process."

Translation: "These numbers are directionally correct but don't drill into them too deeply."

**3:47 PM - The Realization**

Sarah sits back and looks at what she's accomplished today:

✓ Consolidated three entities manually in Excel
✓ Fixed a Stripe integration failure
✓ Calculated revenue recognition for 247 contracts manually
✓ Converted UK financials with exchange rates
✓ Eliminated intercompany transactions
✓ Built budget vs. actuals analysis
✓ Calculated SaaS metrics from 6 different sources
✓ Responded to 4 different department budget questions
✓ Created segment analysis from manually matched data
✓ Assembled complete board deck financials

Time spent: 7 hours 44 minutes (so far, not done yet)

She thinks about her friend Katie who's a Finance Manager at a similar-sized company that uses Sage Intacct. Katie does her monthly close in about 8 hours total and spends the rest of her time on analysis, forecasting, and strategic projects.

Sarah spends 30+ hours on manual data aggregation and consolidation every month. She barely has time for actual analysis.

**4:03 PM - The Email to Michael**

Sarah drafts an email:

"Michael,

Board deck financials are complete and inserted into slides 8-11. Numbers are final pending your review.

I want to raise something for discussion: our current accounting infrastructure is limiting our ability to provide timely, accurate financial reporting. Today's board deck prep took me ~8 hours, most of which was manual data consolidation, currency conversion, and intercompany elimination.

I've documented 23 different manual processes we perform each month that could be automated with proper accounting software. Beyond the time savings, the manual process creates:

* Risk of errors (we're not seeing them yet, but we will as we scale)
* Delayed close timeline (can't close books quickly)
* Limited visibility into real-time performance
* Inability to provide ad-hoc analysis quickly
* Audit risk (manual Excel workpapers aren't ideal)

I put together a business case for NetSuite or Sage Intacct in July. Since then, we've:

* Acquired DataFlow (adding more complexity)
* Grown international operations (UK entity revenue up 40%)
* Raised Series B (board expectations increasing)
* Hired more department heads asking for budget visibility

The current setup won't scale to $30M ARR or beyond. We need to make a decision on upgrading our systems.

I propose we:

1. Revisit the business case in our next 1:1
2. Get quotes from 2-3 implementation partners
3. Plan for Q1 2026 implementation start
4. Budget ~$75K for implementation + $35K annual licenses

I know this is a big decision, but I genuinely believe we're at the point where the manual process is costing us more than the software would.

Happy to discuss.

Sarah"

She hovers over the Send button. She's raised this before. She knows Michael knows it's an issue. But she needs to be more forceful this time.

She clicks Send.

**4:19 PM - Michael's Response**

Michael responds in 8 minutes:

"Sarah,

You're 100% right. I've been kicking this can down the road because I know it's a big project, but we're past the point where we can manage on QBO.

Let's schedule 90 minutes next week to:

1. Review your original business case
2. Decide between NetSuite and Intacct
3. Get budget approval from the board
4. Plan implementation timeline

My preference is to start implementation in Q1 so we're on the new system for Q2 close. Sound good?

Also - great work on the board deck. The segment analysis is particularly helpful (even if it's manually assembled). This is exactly the kind of analysis the board wants, and we should be able to pull it in 5 minutes, not 5 hours.

Thanks for pushing on this.

Michael"

Sarah reads the email three times. Is this real? Is it finally happening?

She responds: "Absolutely. I'll update the business case with current numbers and send it by Friday. Let me know what day/time works for the meeting."

**4:27 PM - The Small Victory**

Sarah updates her task list:

* ✓ Complete board deck financials
* ✓ Consolidate three entities
* ✓ Calculate SaaS metrics
* ✓ Make the case (again) for new accounting system
* ✓ **Actually get Michael to agree to move forward**

She stands up, stretches, and walks to the kitchen to make her fourth coffee. As she waits for it to brew, she texts her friend Katie:

"I think we're finally going to get real accounting software"

Katie: "YESSSS! About time. Welcome to the 21st century 😂"

Sarah: "I feel like I've been banging my head against a wall for 18 months"

Katie: "You have been. But you'll be SO much more effective once you're on a real system. Trust me."

**4:41 PM - The Afternoon Slack Storm**

While Sarah was celebrating her small victory, 7 new Slack messages arrived:

1. **James (VP Engineering)** : "Sarah, AWS bill is higher than expected. Can you break down by team/project?"

* *Sarah's thought: AWS bills don't map cleanly to teams without tagging, which no one does*

1. **Priya (VP Marketing)** : "Contractor sent invoice. Where do I send it?"

* *Sarah's thought: We've had this conversation 100 times. Need to document this.*

1. **Random employee** : "My Brex card was declined. What's up?"

* *Sarah's thought: They probably hit their card limit. Have to check.*

1. **DataFlow team lead** : "We paid for new software. Which entity do we expense it to?"

* *Sarah's thought: Great question. Nobody told me about new software.*

1. **Michael (CFO)** : "Board member asking about our SaaS benchmark metrics. Do we track them?"

* *Sarah's thought: Define "track." I calculate them manually every month.*

1. **External recruiter** : "Need to invoice for placement fee. Who do I send it to?"

* *Sarah's thought: ap@beaconanalytics.com, like everyone else*

1. **CEO** : "Can you pull customer count by contract size for tomorrow's all-hands?"

* *Sarah's thought: Yes, but it'll take an hour to manually compile from Salesforce + Stripe*

Sarah takes a deep breath and starts responding to each one:

 **To James** : "AWS doesn't natively tag by team. I can see total spend by service (EC2, S3, etc.) but not by project. Would need engineering to implement tagging in AWS console for detailed breakdowns."

 **To Priya** : "Send to ap@beaconanalytics.com with subject line 'Invoice - [Vendor Name]' - I'll process within 3 business days."

 **To random employee** : "Checking your card limits now. Give me 5 min."

 **To DataFlow lead** : "New software purchases should be expensed to Beacon Analytics Inc. (main entity) going forward. We'll handle allocation in consolidation."

 **To Michael** : "Yes, I track the standard SaaS benchmarks monthly. Which specific metrics is the board member asking about? I can pull together a comparison to industry benchmarks."

 **To recruiter** : "ap@beaconanalytics.com - include candidate name and start date in invoice."

 **To CEO** : "Yes, can do. Need it by what time tomorrow?"

**5:08 PM - The Brex Card Limit Issue**

Sarah opens Brex to check why the employee's card was declined. She finds the issue: they're a new hire who was issued a card with a $1,000 monthly limit (the default for new employees). They tried to buy a $1,200 monitor.

She increases their limit to $2,500 and Slacks them: "Limit increased. You should be good now."

But this reveals a bigger issue: they don't have a formal policy for card limits by role. They've been setting them ad-hoc. Sarah adds to her growing "Process Documentation Needed" list:

* Corporate card limits by role/department
* Pre-approval requirements for purchases >$X
* Expense policy documentation

**5:24 PM - The Customer Count Analysis**

Sarah starts pulling customer count by contract size for the CEO's all-hands presentation tomorrow.

She exports all active customers from Stripe, copies into Excel, and categorizes by ACV (Annual Contract Value):

* <$5K ACV: 147 customers (38% of customer count, 12% of revenue)
* $5K-$25K ACV: 89 customers (23% of customer count, 31% of revenue)
* $25K-$100K ACV: 34 customers (9% of customer count, 37% of revenue)
* > $100K ACV: 11 customers (3% of customer count, 20% of revenue)
  >

Total: 281 customers, $14.97M ARR

She creates a quick slide with a bar chart and emails it to the CEO: "Customer segmentation by contract size attached. Let me know if you need anything else for tomorrow."

**5:49 PM - The Reflection**

Sarah looks at her task list for the day:

**Completed:**

* ✓ Monthly consolidation (3 entities)
* ✓ Revenue recognition calculations
* ✓ Board deck financial slides
* ✓ Budget vs. actuals analysis
* ✓ SaaS metrics dashboard
* ✓ Customer segment analysis (2 different cuts)
* ✓ Department budget responses (4)
* ✓ Vendor setup request
* ✓ Card limit issue resolution
* ✓ Made the case for new accounting software
* ✓ Got Michael to finally agree to move forward

**Still To Do:**

* Month-end accruals (probably 2 hours of work)
* Reconcile credit card statements
* Review AP aging report
* Fix the intercompany tracking for DataFlow
* Update department cost allocation model

Time check: 5:49 PM. She's been here for nearly 10 hours. The month-end accruals can wait until tomorrow.

**6:02 PM - The Win**

As Sarah packs up her laptop, she reflects on the day. Yes, she spent 10 hours doing work that should take 3 hours in a proper system. Yes, she's exhausted from manually stitching together data from 8 different sources. Yes, she's frustrated that her skills are being used for data aggregation instead of analysis.

But she got Michael to commit to an accounting system upgrade. In Q1, they'll start implementing either NetSuite or Sage Intacct. By Q2, she'll be able to:

* Close books in 5 days instead of 12
* Consolidate with a button click instead of 8 hours of Excel work
* Provide real-time budget vs. actuals to department heads
* Run revenue recognition automatically
* Eliminate intercompany transactions systematically
* Actually spend time on analysis instead of data compilation

She thinks about the job posting that brought her to Beacon: "Finance Manager - Series A SaaS Company - Build Financial Infrastructure."

For 18 months, she's been building infrastructure in Excel and QuickBooks because they didn't have the right tools. Now, finally, she'll get to build it properly.

As she walks to her car, she checks her email one last time. New message from Michael:

"Sarah - I just emailed our board about the accounting system upgrade. Framed it as: 'Essential infrastructure investment to support continued growth and reporting requirements.' They all agreed. Let's move forward. Thanks for being persistent on this."

Sarah smiles. The persistence paid off.

Tomorrow she'll spend another 10 hours on manual consolidation work. But in a few months, this will all be automated, and she can focus on what she was actually hired to do: strategic finance.

**6:34 PM - The Evening Email**

As Sarah pulls into her apartment parking lot, her phone buzzes one more time. Email from Deloitte (their auditor):

"Sarah,

Following up on our earlier email about year-end audit prep. One additional item: we'll need detailed documentation of your revenue recognition methodology, including:

* Contract review process
* Identification of performance obligations
* Allocation of transaction price
* Recognition timing decisions
* System controls around revenue recognition

Can you walk us through your current process on a call next week?

Best,
Jennifer"

Sarah laughs. Her current process:

* Revenue recognition happens in Excel
* She manually reviews 247 contracts
* No system controls because it's all manual
* The only "control" is her double-checking her own work

She responds: "Happy to walk through our process. Fair warning: we're currently doing rev rec manually in Excel but will be migrating to NetSuite or Intacct in Q1, which will add proper system controls. Let me know what day works for the call."

She adds one more item to her "Why We Need New Accounting Software" list: "Auditors will have a heart attack when they see our Excel-based rev rec process."

**7:12 PM - Home**

Sarah heats up dinner (more leftovers), opens her laptop one more time, and updates her "Accounting System Business Case" document with everything she learned today:

**Updated ROI Calculation:**

**Current state (QuickBooks Online):**

* Monthly consolidation: 8 hours
* Revenue recognition: 5 hours
* Department budget analysis: 3 hours
* SaaS metrics calculation: 2 hours
* Ad-hoc analysis requests: 6 hours
* Month-end close: 12 days
* **Total: 24+ hours of manual work per month**

**Future state (NetSuite or Sage Intacct):**

* Monthly consolidation: 1 hour (automated + review)
* Revenue recognition: 30 minutes (automated + review)
* Department budget analysis: 30 minutes (real-time dashboards)
* SaaS metrics: 15 minutes (automated reports)
* Ad-hoc analysis: 2 hours (can pull data easily)
* Month-end close: 5 days
* **Total: ~5 hours of manual work per month**

**Time savings: 19 hours per month = 228 hours per year**

At her $130K salary (loaded cost ~$180K), that's:

* $86/hour loaded cost
* 228 hours × $86 = $19,608 in labor savings annually
* Plus: reduced error risk, faster close, better insights, audit-ready financials

**System cost:**

* Implementation: ~$60K one-time
* Annual licenses: ~$35K
* **Payback period: ~3 years on labor savings alone**
* **Intangible value: Strategic finance work instead of data entry**

She saves the document and emails it to Michael: "Updated business case attached with today's experience factored in. Ready for next week's meeting."

**8:03 PM - The End**

Sarah closes her laptop for real this time. She thinks about Katie, her friend with Sage Intacct, who closes her books by the 3rd business day of each month and spends her time building forecasting models and conducting scenario analysis.

Sarah wants that. She wants to be a strategic finance partner, not an Excel consolidation specialist.

But today, for the first time in 18 months, she has a clear path forward.

She texts her partner: "Big win today - we're finally getting real accounting software. I might become a human being with normal work hours again."

Her partner responds: "Does this mean you won't spend every month-end weekend in Excel? 🎉"

Sarah: "That's the dream. By Q2 I should actually have my nights and weekends back."

Tomorrow she'll wake up and do it all again—manually consolidating three entities, calculating revenue recognition in spreadsheets, responding to budget questions without real-time data.

But it won't be forever.

By Q2 2026, she'll be running a modern accounting operation with proper tools, automated processes, and time for actual financial analysis.

For now, though, she's earned a glass of wine and an episode of something mindless on Netflix.

The Excel workbooks can wait until tomorrow.
