# Jordan's Vendor Payment Processing Day

## Dockwa Marina SaaS - Accounts Payable Workflow

Jordan Kim sits in the Dockwa office in Newport at 8:15 AM, watching the harbor through the large windows while her computer boots up. The 24-year-old accounts payable coordinator has been with the company for seven months, and Thursdays are always vendor payment days—the day when marina invoices, contractor bills, and subscription renewals pile up in her inbox like autumn leaves.

Her desk setup is meticulously organized: dual monitors (she fought hard for the second one), a mechanical keyboard that clicks loudly enough to annoy her coworkers, and a coffee mug that reads "I'm Not Arguing, I'm Just Explaining Why I'm Right"—a gift from her accounting professor.

**8:21 AM - The Invoice Inbox Avalanche**

Jordan opens Outlook and immediately feels overwhelmed. The AP inbox (ap@dockwa.com) has 47 new emails since yesterday at 5 PM. She starts scanning the subject lines:

- "INVOICE #8847 - Marina Electric Supply Co."
- "Monthly Software License - September 2025"
- "Re: OVERDUE - Lighthouse Marine Services"
- "Contracted Maintenance - Portsmouth Harbor"
- "FWD: Can you pay this ASAP? - Channel Markers Inc."

She opens the first email from Marina Electric Supply. The email body says: "Please find attached invoice for electrical repair work completed at Seabrook Marina on 9/15/25." The attachment is named "Invoice_8847.pdf."

Jordan downloads the PDF and opens it. The invoice shows:

- Invoice #8847
- Date: September 20, 2025
- Service: Emergency electrical panel replacement
- Amount: $3,247.50
- Terms: Net 30

**8:28 AM - The Entity Matching Game**

Jordan needs to figure out which Dockwa entity should pay this invoice. She opens her "Entity-Marina Mapping.xlsx" file—a spreadsheet she created to track which marinas are managed by which Dockwa legal entities.

She searches for "Seabrook Marina." It's managed by Dockwa New England LLC, which means payment should come from the New England checking account at Eastern Bank. Jordan makes a note on her processing checklist: "Marina Electric Supply - $3,247.50 - Dockwa NE LLC - Eastern Bank."

**8:33 AM - NetSuite Vendor Lookup**

Jordan opens NetSuite in Chrome (she's learned that Firefox doesn't play well with NetSuite's interface). Login: jkim@dockwa, password, two-factor authentication via SMS. The code arrives: "Your NetSuite verification code is 582739."

In NetSuite, she searches for "Marina Electric Supply" in the vendor list. The vendor exists with payment terms set to Net 30 and their bank account information on file. Good—that'll make payment easier.

But she notices something odd. The vendor's address in NetSuite shows "123 Harbor Rd, Portsmouth, NH" but the invoice shows "456 Marine Blvd, Portsmouth, NH." Jordan frowns. Same vendor, different addresses.

She picks up her phone and calls Marina Electric Supply directly.

"Marina Electric, this is Bob."

"Hi Bob, this is Jordan from Dockwa. I'm processing your invoice #8847 and I noticed the address on the invoice is different from what we have in our system. Did you guys move?"

"Oh yeah, we moved last month to the Marine Boulevard location. I've been meaning to send address change notices to all our customers. Sorry about that."

"No problem. Can you email me the updated address and any other contact info that changed? I'll update our vendor file."

"Will do. I'll send that over in a few minutes."

**8:42 AM - The Approval Routing Puzzle**

Jordan needs to get this $3,247.50 invoice approved before she can pay it. According to Dockwa's approval matrix, anything over $2,500 needs manager approval, and anything over $5,000 needs CFO approval.

She forwards the invoice email to her manager, Lisa Chen, with the subject line: "APPROVAL NEEDED - Marina Electric Supply - $3,247.50 - Emergency Repair."

The email body reads: "Hi Lisa, attached invoice for emergency electrical work at Seabrook Marina. Amount is $3,247.50, requires your approval per company policy. Verified this is legitimate emergency repair per marina manager. Please approve when ready. Thanks, Jordan"

**8:47 AM - Processing Invoice #2**

While waiting for Lisa's approval, Jordan moves to the next email. It's from "CloudFlare Inc." with subject "Monthly Service Invoice - September 2025."

Jordan opens the attachment: "CloudFlare_Invoicecl_Sep2025.pdf." The invoice shows $847/month for CDN and security services. This is a recurring invoice that she's seen every month, but it requires coding to the correct expense account.

She opens NetSuite and navigates to the Chart of Accounts. Is this "Computer Software" (account 6420) or "Website Services" (account 6425)? Jordan checks previous months' coding by searching for CloudFlare in the transaction history. July and August were coded to 6425 - Website Services. She'll keep it consistent.

**8:54 AM - The Stripe Connection**

Jordan's processing invoices when her phone buzzes with a Slack message from Marcus in Engineering: "Hey Jordan, just FYI - that CloudFlare payment needs to come from our Stripe clearing account, not the main operating account. They're integrated with our payment processing."

Jordan pauses. She's been paying CloudFlare from the main Bank of America operating account for months. She messages back: "When did this change? I've been paying from main account since I started."

Marcus responds: "It's been that way since like March, but maybe nobody told AP? Check with Lisa - we set up automatic sweeping from Stripe to cover tech vendors."

Jordan adds this to her growing list of questions for Lisa: "CloudFlare payment source - Stripe vs BOA operating?"

**9:08 AM - The OVERDUE Drama**

Jordan opens the email marked "OVERDUE - Lighthouse Marine Services." The email is from someone named Tony and it's... not friendly.

"This invoice has been outstanding for 60 days. We provided dock maintenance services in July and still haven't been paid. This is unacceptable. Please remit payment immediately or we will pursue other collection options."

Attached is invoice #LMS-2847 for $1,850, dated July 15, 2025, for "Dock repair and piling replacement at Newport Harbor Marina."

Jordan's heart rate increases. She definitely doesn't remember seeing this invoice before. She searches her email for "Lighthouse Marine" and finds the original invoice from July 16th, sitting in her inbox, unprocessed. Somehow she completely missed it.

She immediately calls Lisa.

"Lisa, I need to talk to you about something urgent. I found an overdue invoice that I somehow missed in July. Lighthouse Marine Services, $1,850, now 60 days past due. The vendor is threatening collection action."

"Oh no," Lisa replies. "Can you pay it today? And forward me that email so I can call Tony and smooth things over."

"Yes, I'll prioritize it. But Lisa, I'm worried about our invoice tracking process. How did this slip through?"

"We'll talk about process improvements after we fix this. For now, just get Tony paid and I'll handle the relationship management."

**9:17 AM - Emergency Payment Processing**

Jordan immediately switches gears to process the Lighthouse Marine payment. She opens NetSuite and searches for "Lighthouse Marine Services" in the vendor list. They're not there. Of course they're not—she never set them up as a vendor because she never processed their original invoice.

She clicks "New Vendor" and starts entering their information:

- Company Name: Lighthouse Marine Services
- Contact: Tony Marcello
- Address: (from the invoice) 789 Dock Street, Newport, RI
- Phone: (401) 555-0847
- Payment Terms: Net 30

For payment method, she selects "ACH" and enters their banking information from the invoice. But NetSuite requires vendor W-9 information for tax reporting. Jordan doesn't have a W-9 from Lighthouse Marine.

She calls Tony back.

"Tony, this is Jordan from Dockwa. I'm processing your payment today to get you caught up. I need to send you a W-9 form for our tax records. Can I email that to you?"

Tony's tone is still irritated but slightly warmer: "Yeah, fine. Send it to tony@lighthousemarine.com. How soon will I get paid?"

"I'm processing it today, so you should see it in your account tomorrow or Monday at the latest. And I'm really sorry about the delay."

**9:31 AM - The W-9 Email Dance**

Jordan opens her "Vendor Setup Templates" folder and finds the W-9 form. She emails it to Tony with a note: "Hi Tony, attached W-9 form for our vendor setup. Please complete and return ASAP so I can process your $1,850 payment today. Thanks for your patience."

While waiting for the W-9, Jordan processes what she can. She creates the vendor record in NetSuite with all available information and saves it as "Pending W-9."

**9:44 AM - Approval Status Check**

Jordan checks her email for Lisa's approval on the Marina Electric Supply invoice. Nothing yet. She opens Slack and messages Lisa: "Hi, did you get the Marina Electric approval email? $3,247.50 invoice from this morning."

Lisa responds: "Sorry, crazy morning. Reviewing now... approved. You can process payment."

Jordan opens NetSuite and navigates to Enter Bills. She creates a new bill:

- Vendor: Marina Electric Supply Co.
- Invoice #: 8847
- Date: September 20, 2025
- Amount: $3,247.50
- Account: 6350 - Repairs & Maintenance
- Entity: Dockwa New England LLC

She saves the bill and adds it to her "Approved for Payment" list.

**9:52 AM - The CloudFlare Confusion**

Jordan messages Lisa about the CloudFlare payment source question. "Lisa, Marcus said CloudFlare should be paid from Stripe clearing account, not main BOA account. Is this correct? I've been paying from BOA."

Lisa responds: "Yes, that changed in March. Stripe automatically funds our tech vendor payments. Let me show you how to set that up... can you come to my desk for 5 minutes?"

Jordan walks over to Lisa's desk, bringing her laptop. Lisa pulls up NetSuite and navigates to Banking → Bank Accounts. There are multiple accounts listed:

- Bank of America Operating (main account)
- Eastern Bank New England (regional account)
- Stripe Clearing Account
- Stripe Reserve Account

"See the Stripe Clearing Account?" Lisa points. "That's where tech payments come from. CloudFlare, GitHub, Slack, all our SaaS tools. Stripe automatically transfers funds from our main processing to this account to cover those bills."

Lisa shows Jordan how to select the correct bank account when entering bills in NetSuite. "When you create the bill, make sure you select 'Stripe Clearing' as the account to pay from."

**10:07 AM - Bulk Payment Setup**

Back at her desk, Jordan starts setting up payments for all her approved invoices. She opens NetSuite's "Pay Bills" function and sees her list:

- Marina Electric Supply: $3,247.50 (BOA Operating)
- CloudFlare: $847.00 (Stripe Clearing)
- Lighthouse Marine: $1,850.00 (BOA Operating) - pending W-9

She selects the first two and chooses payment dates. Marina Electric gets paid today (Thursday), CloudFlare gets paid Monday (to align with their monthly billing cycle).

**10:19 AM - The W-9 Returns**

Jordan's email chimes with a response from Tony at Lighthouse Marine. The W-9 form is attached, properly completed and signed. She immediately uploads it to NetSuite under Lighthouse Marine's vendor record and creates their bill:

- Vendor: Lighthouse Marine Services
- Invoice #: LMS-2847
- Date: July 15, 2025
- Amount: $1,850.00
- Account: 6350 - Repairs & Maintenance

She adds it to today's payment batch with a note: "URGENT - 60 days overdue."

**10:27 AM - Payment Execution**

Jordan has three payments ready to go:

1. Marina Electric Supply: $3,247.50 via ACH
2. CloudFlare: $847.00 via ACH
3. Lighthouse Marine: $1,850.00 via ACH

Total payments: $5,944.50 across two bank accounts.

She clicks "Process Payments" in NetSuite. The system asks for final confirmation and warns: "You are about to process 3 payments totaling $5,944.50. This action cannot be undone."

Jordan double-checks each payment amount and bank account, then clicks "Confirm."

NetSuite processes the payments and generates confirmation numbers:

- Payment #DW-20250910-001: Marina Electric Supply
- Payment #DW-20250910-002: CloudFlare
- Payment #DW-20250910-003: Lighthouse Marine Services

**10:35 AM - Reconciliation and Documentation**

Jordan immediately emails payment confirmations to each vendor:

"Hi Bob [Marina Electric],
Your invoice #8847 for $3,247.50 has been processed for payment. You should receive ACH transfer by end of business tomorrow. Payment reference: DW-20250910-001.
Thanks for updating your address information.
Best regards, Jordan"

She sends similar emails to CloudFlare's billing team and Tony at Lighthouse Marine, with an extra apology note for Tony about the delay.

**10:44 AM - The Recurring Subscription Challenge**

Jordan notices another email in the AP inbox: "GitHub Enterprise - Annual Renewal Notice." The attached invoice shows $12,500 for the annual subscription renewal, due October 1st.

This creates a dilemma. It's over the $5,000 threshold, so it needs CFO approval. But their CFO, Sarah Martinez, is at a conference in Boston this week. Jordan checks the company calendar—Sarah returns Monday.

But the invoice is due October 1st (next Tuesday). If Jordan waits for Sarah's return and approval, the payment might be late.

She calls Lisa for guidance.

"Lisa, I have a GitHub renewal for $12,500 that needs CFO approval, but Sarah's at the Boston conference and the invoice is due next Tuesday. What should I do?"

"Email Sarah directly with the invoice and explain the timing issue. She can approve via email from the conference. Just make sure you document the email approval in NetSuite."

**10:52 AM - Executive Email**

Jordan drafts an email to Sarah:

"Subject: URGENT APPROVAL NEEDED - GitHub Enterprise Renewal - $12,500

Hi Sarah,

Hope your conference is going well. I need CFO approval for our GitHub Enterprise annual renewal:

- Amount: $12,500
- Due Date: October 1, 2025
- Vendor: GitHub, Inc.
- Service: Annual subscription renewal for development team

This is a critical service for our engineering team. Can you provide email approval so I can process payment before the due date?

Invoice attached. Please reply with approval or any questions.

Thanks,
Jordan"

She attaches the GitHub invoice and sends the email.

**11:08 AM - Process Documentation**

While waiting for responses, Jordan updates her AP tracking spreadsheet. For each processed payment, she records:

- Date processed
- Vendor name
- Invoice number
- Amount
- Payment method
- Approval received from
- Notes/issues

Today's entries include notes like "Address change required" for Marina Electric and "60-day overdue - relationship issue resolved" for Lighthouse Marine.

**11:23 AM - Unexpected Follow-up**

Jordan's phone rings. It's Bob from Marina Electric Supply.

"Hi Jordan, I got your payment confirmation email. Just wanted to say thanks for being so professional about the address change. Some companies make it a huge hassle."

"No problem at all, Bob. We want to make sure our vendor information is accurate. Thanks for the quick turnaround on the updated details."

"Also, just so you know, we might have another invoice coming next week for preventive maintenance at the same marina. Just giving you a heads up."

Jordan makes a note: "Marina Electric - expect additional invoice next week for Seabrook preventive maintenance."

**11:31 AM - Sarah's Quick Response**

Jordan's email chimes with a response from Sarah, sent from her iPhone:

"Jordan - GitHub renewal approved. This is a critical service, good catch on the timing issue. Process payment Monday so it clears before the due date. -Sarah"

Jordan immediately updates the GitHub invoice in NetSuite with "CFO APPROVED - Email 9/10/25" and schedules it for payment processing on Monday.

**11:38 AM - Cleanup and Planning**

Jordan processes three more routine invoices from her inbox:

- Office supply company: $247.50
- Internet service provider: $156.00
- Cleaning service: $850.00

All are under the approval threshold and routine monthly expenses. She codes them to the appropriate accounts and adds them to Monday's payment batch.

**11:52 AM - Process Improvement Reflection**

Before wrapping up her AP session, Jordan opens a document called "AP_Process_Improvements.docx" and adds today's learnings:

1. Need better invoice tracking system - missed Lighthouse Marine invoice entirely
2. Vendor address changes should trigger system updates automatically
3. Consider approval workflow for time-sensitive payments when executives travel
4. Create checklist for new vendor setup to avoid missing W-9 requirements
5. Set up recurring payment reminders for subscription renewals

**11:58 AM - Daily Summary**

Jordan creates her daily AP summary for Lisa:

"AP Processing Summary - September 10, 2025:

Payments Processed Today: 3 payments, $5,944.50 total

- Marina Electric Supply: $3,247.50 (emergency repair)
- CloudFlare: $847.00 (monthly service)
- Lighthouse Marine: $1,850.00 (overdue - relationship repaired)

Scheduled for Monday: 4 payments, $1,253.50 total

+ GitHub renewal pending Monday processing: $12,500

Issues Resolved:

- Lighthouse Marine 60-day overdue invoice - vendor relationship restored
- Marina Electric address update completed
- CloudFlare payment routing corrected to Stripe clearing account

Outstanding Approvals: None

Next Week Priorities:

- GitHub renewal payment (due Oct 1)
- Follow up on Marina Electric preventive maintenance invoice
- Review AP tracking process to prevent missed invoices"

Jordan sends this summary to Lisa and copies the CFO. She saves all processed invoices and payment confirmations to the shared drive under "AP_Documentation/September_2025."

**12:05 PM - Lunch Break**

Jordan closes her laptop and heads to lunch, satisfied that she's caught up on payments, resolved the overdue issue, and improved several vendor relationships. This afternoon she'll tackle expense report approvals and month-end accruals, but for now, she's earned a proper lunch break at the harbor-side café down the street.

As she walks past the marina, she can see some of the boats that use Dockwa's reservation system. It's a nice reminder that behind all the invoices and payment processing, they're helping people enjoy time on the water—even if she rarely gets to see that side of the business from her AP coordinator position from her AP coordinator desk.

As she walks past the marina, she can see some of the boats that use Dockwa's reservation system. It's a nice reminder that behind all the invoices and payment processing, they're helping people enjoy time on the water—even if she rarely gets to see that side of the business from her AP coordinator position.

**12:43 PM - The Afternoon Email Check**

Jordan returns from lunch with a fresh iced coffee and checks her AP inbox. Three new invoices have arrived during her lunch break:

* "Monthly Fuel Delivery - Harbor Marine" for $2,847.50
* "Legal Services - Maritime Law Associates" for $4,750.00
* "Software Maintenance - Navigation Systems Inc." for $1,200.00

Jordan sighs. The legal services invoice is over the $2,500 threshold requiring manager approval, but Lisa is in back-to-back meetings until 3 PM according to her calendar.

**12:49 PM - The Entity Matching Challenge Returns**

Jordan opens the Harbor Marine fuel delivery invoice and immediately encounters her familiar challenge. The invoice shows delivery to "Newport Marina Facility" but Dockwa manages three different marinas in Newport. She needs to determine which specific location received the fuel.

She calls Harbor Marine directly: "Hi, this is Jordan from Dockwa. I'm processing your fuel delivery invoice from September 9th. Can you confirm which Newport location this was delivered to?"

"Let me check our delivery logs... that was delivered to the main Dockwa facility at 47 Bowen's Wharf."

"Perfect, that's our Newport Harbor location. Thanks for the clarification."

Jordan updates her processing notes: "Harbor Marine - $2,847.50 - Newport Harbor - Dockwa Rhode Island LLC."

**1:02 PM - The Legal Services Investigation**

The Maritime Law Associates invoice is more complex. It's for "Contract review and negotiation services - Marina partnership agreement" but doesn't specify which marina partnership. Jordan searches her email for recent communications about legal work and finds a thread from August discussing a potential partnership with Block Island Marina.

She emails the legal firm: "Hi, I'm processing your September invoice #MLA-2847 for contract review services. Can you confirm this relates to the Block Island Marina partnership agreement we discussed in August?"

The response comes back quickly: "Yes, that's correct. This covers our review of the partnership terms and lease negotiations for the Block Island facility."

**1:18 PM - The Subscription Renewal Calendar**

Jordan opens her "Recurring Subscriptions Calendar" spreadsheet to update it with the GitHub renewal she processed earlier. She notices several other renewals coming up in October:

* Microsoft Office 365: $2,400 (due October 15)
* Salesforce CRM: $8,900 (due October 22)
* AWS Web Services: $3,200 (due October 28)

She makes a note to send Lisa advance notice about these upcoming renewals, especially the Salesforce renewal which will require CFO approval.

**1:34 PM - The Process Improvement Follow-up**

Jordan's phone buzzes with a Slack message from Lisa: "Saw your process improvement doc. Let's schedule 30 minutes tomorrow to discuss the AP tracking system upgrade. Good catch on the Lighthouse Marine issue."

Jordan responds: "Sounds good. I've been thinking about a shared tracker that shows invoice status in real-time. Maybe something in Airtable or Monday.com?"

Lisa replies: "Exactly what I was thinking. We need visibility into what's pending, what's approved, what's paid. Let's explore options tomorrow."

**1:47 PM - The Vendor Relationship Management**

Jordan receives an email from Tony at Lighthouse Marine: "Jordan, just wanted to thank you for getting that payment processed so quickly today. I know there was a mix-up, but you handled it professionally. We'd like to continue working with Dockwa and will make sure future invoices have clearer marina location details."

Jordan forwards the email to Lisa with a note: "Vendor relationship successfully repaired. Tony appreciated our quick response once we identified the issue."

**2:03 PM - The Month-End Preparation**

Jordan starts preparing for month-end close procedures. She opens her "September AP Close Checklist":

* [ ] All invoices processed through September 30
* [ ] Outstanding approvals cleared
* [ ] Vendor statements reconciled
* [ ] Accruals recorded for services received but not yet invoiced
* [ ] AP aging report updated and reviewed
* [ ] Expense coding verified for all payments

She's on track to complete everything by the September 30 deadline, but the improved tracking system Lisa mentioned would make this much smoother next month.

**2:19 PM - The Final Invoice Batch**

Jordan processes the three afternoon invoices:

* Harbor Marine fuel: $2,847.50 (pending Lisa's approval)
* Legal services: $4,750.00 (pending Lisa's approval)
* Software maintenance: $1,200.00 (under threshold, approved for Monday payment)

She creates the bills in NetSuite and adds them to her approval queue for Lisa to review when her meetings end.

**2:31 PM - The Reflection and Learning**

As Jordan organizes her desk for the end of the day, she reflects on the lessons learned:

Today demonstrated both the complexity and importance of her role. A simple mistake—missing one email in July—nearly damaged a vendor relationship and could have escalated to collection action. But quick, professional response turned a potential crisis into an opportunity to strengthen the relationship.

The process improvements she identified aren't just efficiency gains—they're risk mitigation. Better tracking prevents missed invoices. Automated address updates reduce manual errors. Standardized approval workflows prevent delays when executives travel.

**2:44 PM - End of Day Summary**

Jordan completes her daily summary:

"Thursday AP Processing - Final Update:

Total Payments Processed: $5,944.50 (3 payments)
Payments Scheduled Monday: $14,953.50 (5 payments including GitHub)
Pending Approvals: 2 invoices totaling $7,597.50
Process Improvements Identified: 5 items
Vendor Relationships: 1 repaired, 1 enhanced

Key Accomplishment: Resolved 60-day overdue invoice situation while maintaining positive vendor relationship.

Tomorrow's Priorities: Process improvement planning session with Lisa, October subscription renewal preparations, month-end close procedures."

Jordan saves her work, closes her applications, and shuts down her computer. As she walks out of the office at 2:51 PM, she feels the satisfaction that comes from turning a potentially chaotic day into organized progress.

The harbor is busy with late afternoon boat traffic—customers using Dockwa's platform to find slips for the night. Jordan smiles, reminded that her meticulous attention to vendor payments and process improvements helps keep the entire ecosystem running smoothly, one invoice at a time.
