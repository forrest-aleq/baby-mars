# Real-World Finance Workflows: Three Stories

## Story 1: GGHC Investment Management
### Riley's Bank Reconciliation Monday

Riley Martinez adjusts her monitor for the third time this morning, the September Manhattan sun hitting her desk just wrong through the 32nd-floor windows. At 23, she's been GGHC's junior controller for exactly four months, and bank reconciliation Mondays still make her stomach flutter a bit. Coffee in hand (black, because the office Keurig ran out of her usual vanilla pods again), she opens her laptop and waits for the familiar Windows login chime.

**8:47 AM - Getting Started**

Riley clicks the Chrome icon, her muscle memory already typing "chase.com" before the browser fully loads. The Chase login screen appears, and she reaches for the yellow sticky note under her keyboard—not for her password (she's memorized that), but for the security token code that changes every 30 seconds. The little plastic device sits next to her stapler, blinking its six-digit code: 847291.

She types her username (rmartinez@gghc), password, and the token code. The page refreshes. *Please check your email for a verification code.* Riley sighs—Chase updated their security protocols last month, and now every login requires this extra step.

**8:49 AM - Email Two-Step Dance**

Alt-tabbing to Outlook, she refreshes her inbox. Nothing yet. She clicks refresh again. Still nothing. She counts to ten (a trick her supervisor taught her) and refreshes once more. There it is: "Chase Security Code: 739204." She clicks back to Chase, enters the code, and finally—success. The account dashboard loads, showing GGHC's primary operating account with a balance of $2,847,392.18.

Riley opens her Excel reconciliation template from the shared drive (mapped as the K: drive on her machine). The file name reads "GGHC_Bank_Rec_September_2025_TEMPLATE.xlsx"—all caps because her predecessor apparently had strong feelings about file naming conventions.

**8:54 AM - The Reconciliation Begins**

She starts downloading statements. Chase makes this annoying—you can't bulk download, so she has to do each account individually. Operating account: click "Statements," select "September 2025," wait for the PDF to generate, download. The file saves to her Downloads folder as "September_2025_Statement_8472.pdf"—Chase's random numbering system that makes no sense to anyone.

Next account: the money market. Same process. Then the payroll account. By 9:12 AM, she has seven PDFs sitting in her Downloads folder, each with Chase's cryptic naming convention.

**9:15 AM - Data Entry Reality**

Riley opens the first statement PDF. The September operating account shows 847 transactions. She starts with deposits, cross-referencing each one against her NetSuite general ledger export. The first deposit: $125,000 on September 3rd. She checks NetSuite—there it is, a client fee payment from Hartwell Industries. Check mark in her Excel reconciliation sheet.

Second deposit: $47,850 on September 5th. She searches NetSuite. Nothing matches exactly. She tries different search terms: "47850," "September 5," "Hartwell." Still nothing. Her heart rate picks up slightly—unmatched items always make her nervous.

**9:31 AM - The First Puzzle**

Riley grabs her phone and scrolls to her supervisor's contact. She starts typing a text, then deletes it. Too informal. She opens Outlook instead and drafts an email: "Hi Janet, I'm working on the September bank rec and have an unmatched deposit of $47,850 from 9/5. I checked NetSuite but can't find a corresponding entry. Could this be a timing difference from late August processing?"

She hesitates before hitting send. Janet always says to exhaust all options first. Riley goes back to NetSuite and tries searching late August entries. Bingo—there's a $47,850 client fee from August 30th that must have processed after month-end close. She deletes her draft email and adds a note in her reconciliation: "Timing difference - Aug 30 fee processed Sep 5."

**9:48 AM - The Unexpected Error**

Riley's moving through the reconciliation systematically when NetSuite suddenly throws an error: "Session timeout. Please log in again." She groans audibly. The person at the desk behind her (Marcus from Research) chuckles sympathetically. "NetSuite again?"

"Always at the worst possible time," Riley mutters, navigating back to NetSuite's login page. Username, password, and—of course—another two-factor authentication code to her phone. The SMS arrives: "Your NetSuite verification code is 582739." She enters it and waits for the system to reload.

When NetSuite finally comes back up, her GL export has to be regenerated. She clicks Reports → Financial → General Ledger Detail, selects the date range (September 1-30, 2025), chooses all accounts, and hits "Generate." The little spinning wheel appears with "Processing... this may take several minutes."

**10:17 AM - Withdrawal Investigation**

While waiting for NetSuite, Riley continues with bank statement withdrawals. Most are routine: payroll (every other Friday), rent ($28,000 on the 1st), utilities. But there's a $15,000 wire transfer on September 18th to "CLEARWATER CONSULTING LLC" that she doesn't recognize.

This time she doesn't hesitate—she picks up her desk phone and dials Janet's extension.

"Janet Kowalski," her supervisor answers in her characteristic crisp tone.

"Hi Janet, it's Riley. I'm doing the September bank rec and there's a $15,000 wire to Clearwater Consulting on the 18th. I can't find any corresponding AP entry or approval. Do you know what this might be?"

"Hmm," Janet pauses. "Let me check my email from that week. Can you send me the wire details?"

Riley takes a screenshot of the bank statement line item and emails it to Janet. While waiting, she continues with other withdrawals, but her focus keeps drifting to that $15,000. In a $2.8 million account, it's not huge, but unexplained wires make her nervous.

**10:31 AM - The Plot Thickens**

Janet calls back. "Riley, I found it. That was the payment for the new compliance software implementation. Legal approved it last month, but it looks like AP coded it to the wrong account. Check account 5280—Professional Services."

Riley searches NetSuite for account 5280 and finds the entry: "Clearwater Consulting - Compliance Software Setup - $15,000." The date matches, the amount matches, but it was coded as an expense instead of flowing through the normal AP process. She makes a note: "Wire matches GL entry 5280-001847, coding issue resolved."

**11:15 AM - The Final Stretch**

By 11:15, Riley has worked through all deposits and withdrawals. Her reconciliation shows three outstanding checks (normal—they're dated September 29th and probably cleared in October) and two deposits in transit. The adjusted bank balance matches NetSuite exactly: $2,847,392.18.

She completes her reconciliation template, adding notes for each timing difference and investigation. The final step is Janet's review and approval. Riley saves the file as "GGHC_Bank_Rec_September_2025_FINAL_RM.xlsx" and emails it to Janet with the subject line: "September Bank Reconciliation - Ready for Review."

**11:33 AM - Documentation and Archive**

While waiting for Janet's approval, Riley creates the compliance folder for September. She saves all the bank statement PDFs, her reconciliation file, and screenshots of the NetSuite queries into a shared drive folder labeled "2025_09_Bank_Reconciliations." The folder structure is specific: GGHC's auditors expect to find everything in exactly this format.

Her phone buzzes with a text from Janet: "Rec looks good. Approved in NetSuite. Nice catch on the Clearwater coding issue."

Riley allows herself a small smile and marks "September Bank Reconciliation" as complete in her task list. She opens her calendar—next up is the October month-end journal entry prep. But first, she's earned another cup of coffee.

---

## Story 2: Dockwa (Marina SaaS)
### Sam's Lockbox Processing Adventure

Sam Chen stares at his phone alarm for exactly three seconds before swiping it off. 6:47 AM in Newport, Rhode Island, and the harbor fog is still thick enough that he can barely see the water from his apartment window. At 25, Sam handles accounts receivable for Dockwa, and Tuesday mornings mean one thing: lockbox processing. He grabs his worn Patagonia hoodie and heads to the office, stopping for his usual large cold brew at The Corner Café.

**8:23 AM - The Email Hunt**

Sam settles into his desk—a standing desk he convinced the facilities team to get him—and opens his laptop. The office is still quiet; most of the engineering team doesn't roll in until 9:30. He opens Outlook and searches for emails from bankdep@rhodeislandtrust.com. There it is, timestamped 7:42 AM: "Daily Lockbox Report - September 10, 2025."

The email has a PDF attachment: "LOCKBOX_RPT_091025.pdf." Sam downloads it and immediately renames it to something actually useful: "RI_Trust_Lockbox_Sep10_2025.pdf." He opens the PDF and his heart sinks a little—34 checks today. That's going to take a while.

**8:26 AM - The PDF Wrestling Match**

The lockbox PDF is formatted terribly, as usual. Rhode Island Trust's system spits out a document that looks like it was designed in 1987. Each check entry has:
- Payer name (sometimes truncated)
- Check number
- Amount
- Date received
- Invoice number (when the payer actually wrote it on the memo line)

Sam opens his "Lockbox Processing Template.xlsx" file and starts manually transcribing the first entry:

**Check #1:** "NEWPORT YACHT CLUB" - $847.50 - Check #2847 - Invoice memo: "Aug dock fees"

He copies this into his Excel tracker, then opens a new Chrome tab and navigates to Recurly. The Dockwa admin panel loads, and Sam logs in with his credentials. The system immediately prompts for two-factor authentication—he opens Google Authenticator on his phone and enters the six-digit code: 847291.

**8:34 AM - The Recurly Detective Work**

In Recurly, Sam searches for "Newport Yacht Club." The search returns three results—apparently they have multiple accounts for different services. He clicks on each one, looking for an August invoice matching $847.50. The first account shows "August Dockage - $847.50 - Invoice #DW-08-4729 - Status: Pending Payment." Bingo.

Sam clicks "Record Payment," selects "Check" as the payment method, enters the check number (2847), and marks the payment date as September 10th. He hits "Save" and the invoice status changes to "Paid." One down, 33 to go.

**8:41 AM - When Things Get Complicated**

Check #7 is from "J. MORRISON" for $234.00 with no memo line. Sam searches Recurly for "Morrison" and gets 12 results. He starts clicking through them:
- Morrison Marine Services (commercial account)
- Jim Morrison (individual boater)
- Morrison Family Trust (yacht club membership)
- J&M Morrison LLC (marina management)

None of them have a pending invoice for exactly $234.00. Sam checks amounts close to it: $243.00, $224.00, $234.50. Nothing matches perfectly.

**8:47 AM - Calling for Backup**

Sam picks up his phone and calls his manager, Lisa.

"Hey Sam," Lisa answers. "Let me guess—lockbox mysteries?"

"Yeah, I've got a J. Morrison check for $234 and I can't find a matching invoice. Multiple Morrisons in the system."

"Can you send me the lockbox line? I'll check if there were any partial payments or adjustments last month."

Sam takes a screenshot of the PDF line item and texts it to Lisa. While waiting, he moves on to the next check, making a note in his Excel tracker: "J. Morrison $234 - PENDING INVESTIGATION."

**9:12 AM - The Plot Twist**

Lisa calls back. "Found it. Jim Morrison made a partial payment last month and still owes $234. But his account shows $234.50. Check if the PDF amount is actually $234.50—sometimes their OCR cuts off the cents."

Sam squints at the PDF. Sure enough, what looked like "$234.00" is actually "$234.50"—the ".50" is just really faint. He updates his Excel tracker and applies the payment in Recurly.

**9:31 AM - The NetSuite Journey**

After processing 18 checks in Recurly, Sam needs to create the corresponding journal entries in NetSuite. He opens another Chrome tab and navigates to NetSuite's login page. Username: schen@dockwa.com. Password. Two-factor authentication via SMS: "Your NetSuite code is 748291."

NetSuite loads (slowly, as always), and Sam navigates to Transactions → Make Journal Entry. He needs to create one journal entry for the entire lockbox deposit. Total amount: $8,473.50. He sets up the entry:

**Debit:** Cash in Bank - Rhode Island Trust - $8,473.50
**Credit:** Accounts Receivable - $8,473.50

In the memo field, he writes: "Lockbox deposit 9/10/25 - 34 checks processed - See attached backup."

**9:44 AM - The Attachment Dance**

Sam needs to attach his Excel tracking file and the original PDF to the NetSuite journal entry. He saves his Excel file as "Lockbox_Processing_Sep10_2025_SC.xlsx" and clicks the "Attach File" button in NetSuite.

The file upload window opens. Sam clicks "Choose File," navigates to his Downloads folder, and selects his Excel file. The upload bar crawls along... 47%... 68%... 89%... and then NetSuite throws an error: "File upload failed. Please try again."

"Are you kidding me?" Sam mutters under his breath. He tries again. Same error. He checks the file size—only 247KB, well under the limit. He tries a third time, and finally it works.

**9:51 AM - The Final Reconciliation**

With the journal entry saved, Sam needs to reconcile his work. He adds up all the payments he entered in Recurly: $8,473.50. He checks his Excel tracker total: $8,473.50. He looks at the NetSuite journal entry: $8,473.50. Everything matches.

But Sam has one more step—he needs to mark these invoices as processed in Dockwa's internal tracking system. He opens yet another tab and logs into the company's custom admin panel. Under "Payment Processing," he uploads his Excel file to mark all these invoices as "Lockbox Processed."

**10:18 AM - Unexpected Hiccup**

Just as Sam is about to mark the lockbox processing as complete, he gets an email from Recurly: "Payment Application Failed - Invoice DW-08-4731." It's one of the payments he just processed.

Sam clicks the link in the email and sees the error: "Customer account suspended - overdue balance on secondary invoice." Apparently, Newport Yacht Club has another overdue invoice that's blocking the payment application.

He calls the customer service team. "Hey Maria, it's Sam in accounting. I need to temporarily unsuspend Newport Yacht Club's account so I can apply a lockbox payment."

"Sure thing," Maria replies. "What's the account ID?"

"DW-CUST-8847."

"Okay, I'm unsuspending them now. You should be able to process the payment."

Sam refreshes Recurly and tries to apply the payment again. This time it works.

**10:34 AM - Wrapping Up**

Sam creates his final reconciliation summary:
- 34 checks processed
- Total deposited: $8,473.50
- 33 payments applied successfully
- 1 customer account issue resolved
- All amounts reconciled between Recurly and NetSuite

He saves all his files to the shared drive in a folder called "Daily_Lockbox_Processing/2025/September" and sends Lisa a quick Slack message: "Sep 10 lockbox complete - 34 checks, $8,473.50, all reconciled. One customer account suspension issue but resolved."

Lisa responds with a thumbs-up emoji.

Sam leans back in his standing desk and checks his calendar. Next up: following up on overdue accounts. But first, he's definitely earned that second cold brew.

---

## Story 3: Real Estate Portfolio Management
### Alex's Manager Reporting Marathon

Alex Nguyen sits in her Honda Civic in the parking lot of a Dunkin' Donuts, laptop balanced on her steering wheel, phone hotspot activated. It's 7:23 AM on a Wednesday, and she's about to tackle the monthly manager reporting for 47 different properties across her real estate portfolio. At 26, Alex has been the company's FP&A analyst for eight months, and she's learned that property managers are... particular about their reports.

The coffee shop's WiFi was down, hence the parking lot office setup. She needs to get these reports out before managers start calling, and they always start calling early.

**7:31 AM - QuickBooks Roulette**

Alex opens QuickBooks Online in Chrome and immediately gets the spinning wheel of death. Her phone's hotspot is struggling. She waits. And waits. Finally, the login screen loads. She enters her credentials and—naturally—QuickBooks wants two-factor authentication. She waits for the SMS, enters the code, and finally gets into the system.

She navigates to Reports → Profit & Loss. The page loads slowly, showing the default P&L for all properties combined. Alex needs to run this report 47 times—once for each property—filtered by class. She starts with Ashworth Gardens, the property that generates the most manager complaints.

In the report filters, she selects Class: "Ashworth Gardens," Date Range: "September 1-30, 2025," and hits "Run Report." The system thinks for 30 seconds, then displays a P&L with 43 line items. Alex clicks "Export to Excel" and waits another 20 seconds for the download.

**7:47 AM - The Template Transformation**

Alex opens the exported file: "ProfitLoss_AshworthGardens_Sep2025.xlsx." QuickBooks' export is ugly—random formatting, unnecessary columns, and no budget comparison. She opens her master template: "Manager_Report_Template_2025.xlsx" and starts the copy-paste dance.

She copies the revenue lines first: Rental Income ($47,850), Utility Reimbursements ($3,240), Late Fees ($450). Then expenses: Property Management ($2,875), Maintenance ($8,493), Utilities ($6,750). Each number gets pasted into her template's "Actual" column.

Next, she needs the budget figures. These are stored in a separate Excel file that she maintains manually: "2025_Budget_Master.xlsx." She opens it and finds Ashworth Gardens' September budget: Rental Income ($48,000), Maintenance ($7,500), Utilities ($6,500). She types these into the "Budget" column.

**8:08 AM - Excel Formula Magic**

Alex's template automatically calculates variances. The maintenance variance shows +$993 (over budget), and utilities are +$250 over. But rental income is -$150 under budget. She highlights anything over 10% variance in red—maintenance definitely qualifies at 13% over budget.

Her template has a second tab called "Transaction Detail" where she'll paste the actual transactions for categories that are significantly over budget. She goes back to QuickBooks, clicks on the maintenance expense line ($8,493), and exports the detail to see what drove the overage.

The transaction detail shows:
- HVAC repair: $3,247 (September 15)
- Plumbing emergency: $1,850 (September 8)
- Landscaping: $2,146 (September 22)
- Painting supplies: $1,250 (September 28)

**8:21 AM - Manager Communication Begins**

Alex's phone rings. The caller ID shows "Mike Fletcher" - the property manager for Ashworth Gardens.

"Alex, hey, it's Mike. I saw you're working on the September reports. I wanted to give you a heads up about that HVAC repair—the unit completely died during the heat wave and we had to replace it emergency. I've got the receipts if you need them."

"Perfect timing, Mike. I'm looking at your report right now. The maintenance category is about $1,000 over budget. Can you email me the HVAC receipts? And what about the plumbing emergency?"

"Yeah, that was a burst pipe in unit 4B. Flooded the downstairs neighbor too. I'll send you both receipts."

Alex makes notes in her template: "HVAC replacement - emergency during heat wave. Burst pipe 4B - emergency repair." She'll include these explanations in the final report.

**8:34 AM - The Printing Fiasco**

Alex finishes the Ashworth Gardens report and needs to save it as a PDF. She clicks File → Save As → PDF, but her laptop throws an error: "Printer not available." She's not trying to print, just save as PDF, but somehow her laptop thinks she needs a printer connected.

She tries again. Same error. She googles "Excel save PDF without printer" and finds a workaround: File → Export → Create PDF/XPS. This time it works, creating "Ashworth_Gardens_Sep2025_Report.pdf."

**8:41 AM - Email Distribution Setup**

Alex opens Outlook and starts composing an email to Mike Fletcher:

"Subject: September Budget Report - Ashworth Gardens

Hi Mike,

Attached is your September budget-to-actual report. Key highlights:
- Rental income: $47,850 (slight miss vs $48K budget)
- Maintenance: $8,493 (over budget due to HVAC and plumbing emergencies)
- Overall performance: Within normal range given emergency repairs

Please review and let me know if you have any questions or if any transactions appear miscoded.

Thanks,
Alex"

She attaches the PDF and sends it. One down, 46 to go.

**8:54 AM - The Automation Attempt**

Alex realizes she'll be here all day if she does this 46 more times manually. She opens QuickBooks and tries to set up a memorized report for each property. She creates the P&L report for Birchwood Apartments, applies the class filter, and clicks "Memorize."

QuickBooks asks for a report name: "Birchwood - Monthly P&L." She saves it and tries to schedule it to run automatically. But QuickBooks Online's automation features are limited—she can't auto-export to Excel or auto-email the results. She'll still need to run each report manually.

**9:17 AM - The Bulk Processing Strategy**

Alex decides to batch the work. She opens 10 browser tabs and starts running reports for 10 properties simultaneously. Tab 1: Ashworth (done). Tab 2: Birchwood. Tab 3: Cedar Point. Tab 4: Driftwood Manor.

Her laptop fan starts whirring loudly—10 QuickBooks tabs are apparently too much. Tab 7 freezes entirely. Alex closes a few tabs and sticks to 5 at a time.

**9:43 AM - The Missing Data Mystery**

While processing Elmwood Estates, Alex notices something odd. The September P&L shows $0 for property management fees, but the budget expects $3,200. She checks other months—July and August show the proper $3,200 management fee. September is definitely missing.

She calls the main office. "Hey Jennifer, it's Alex. I'm doing the September reports and Elmwood Estates is missing its management fee entry. Did something not get processed?"

"Oh shoot," Jennifer replies. "We had an issue with the automatic billing in September. Let me check if Elmwood got missed... Yeah, here it is. The payment got stuck in our system. I'll process it now, but it'll show up in October's books."

Alex makes a note: "Management fee timing difference - will appear in October." She decides to manually add the $3,200 to September's report with a footnote explaining the timing issue.

**10:31 AM - The Coffee Shop Rescue**

Alex's phone hotspot finally gives up—she's burned through her monthly data allowance. She packs up her laptop and heads into the Dunkin' Donuts. The WiFi is back up, so she orders another coffee and finds a corner table.

Reconnecting to QuickBooks, she discovers she's been automatically logged out. Username, password, two-factor authentication via SMS again. She's now on attempt #4 of the day with QuickBooks logins.

**11:15 AM - The Bulk Email Challenge**

By 11:15, Alex has completed reports for 23 properties. She has 23 PDF files sitting in her Downloads folder with names like "Ashworth_Gardens_Sep2025_Report.pdf" and "Birchwood_Sep2025_Report.pdf." Now she needs to email them to the right managers.

She opens her "Property Manager Contact List.xlsx" file and starts composing emails. But each email needs to be personalized—Mike Fletcher manages 3 properties, Sarah Chen manages 5, and David Park manages 2. She can't just BCC everyone.

Alex starts writing individual emails:

"Hi Sarah, attached are your September reports for Cedar Point, Driftwood Manor, and Elmwood Estates. Note the management fee timing issue on Elmwood (explained in the report). Please review and let me know if you have questions."

**11:47 AM - The Variance Investigation Call**

Alex's phone rings again. This time it's Sarah Chen.

"Alex, I'm looking at the Cedar Point report and the utilities are way over budget. Like, really over. $4,200 against a $2,800 budget. I don't understand what happened."

Alex pulls up Cedar Point's transaction detail in QuickBooks. "Let me see... I show three utility payments in September: electric for $1,840, gas for $970, and water for $1,390. Does that sound right?"

"The electric and gas sound normal, but $1,390 for water? That's usually around $400. Let me check my records... Oh wait, I think I know what happened. We had a leak in the irrigation system that ran for like two weeks before anyone noticed. I reported it to facilities but maybe it didn't get coded properly."

Alex makes a note to follow up with facilities about whether the irrigation leak should be coded as maintenance instead of utilities.

**12:23 PM - The Final Push**

Alex takes a quick break to grab a sandwich and assess her progress. 31 reports completed, 16 to go. Her system is working, but it's tedious. Each report takes about 8-10 minutes: run the QuickBooks report, export to Excel, transfer data to her template, calculate variances, investigate anything unusual, save as PDF, and email to the manager.

She puts on her headphones and pushes through the remaining 16 properties. By 2:47 PM, she's sent the final email to David Park with his reports for Riverside Gardens and Sunset Terrace.

**2:51 PM - The Follow-Up System**

Alex creates a tracking spreadsheet: "September_Manager_Reports_Status.xlsx." For each property, she logs:
- Report sent date/time
- Manager email address
- Any variance issues noted
- Follow-up required (yes/no)
- Manager acknowledgment received (pending)

She sets up a calendar reminder for Friday to follow up with any managers who haven't acknowledged their reports.

**3:08 PM - The Improvement Ideas**

Exhausted but satisfied, Alex opens a new document: "Manager_Reporting_Process_Improvements.docx." She starts jotting down ideas:

1. Investigate QuickBooks alternatives with better automation
2. Create a simple web form for manager acknowledgments
3. Set up budget vs actual alerts in QuickBooks to catch issues earlier
4. Explore BI tools that could automate the template formatting

She saves the document and sends it to her manager with a note: "Completed September manager reports. Attached are some ideas for streamlining the process. Let's discuss next week?"

Alex closes her laptop, finishes her coffee, and heads back to the office. Tomorrow she'll start following up on manager questions and preparing for October's budget-to-actual cycle. But for now, she's earned the rest of her Wednesday afternoon.
