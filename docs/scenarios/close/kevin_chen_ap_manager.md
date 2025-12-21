# Story 3: Dockwa AP Management - Vendor Payment Processing Through the Stripe Ecosystem
## **Difficulty Level: 2 (Hard)**

### Kevin's Payment Orchestration Ballet

Kevin Chen opens his laptop at 8:15 AM sharp, a ritual he's maintained as Dockwa's AP Manager for the past 22 months. His standing desk setup in the Newport office faces the harbor, and on clear mornings like this, he can see the boats that use Dockwa's platform for their marina reservations. The irony isn't lost on him - while Dockwa has built elegant software to automate marina operations, their own back-office payment processing still feels like steering a sailboat through choppy waters.

Kevin's MacBook Air M2 boots up alongside his secondary Windows laptop that runs legacy AP software integrations. His iPhone 14 Pro buzzes with a Slack notification from Sarah, the CFO: "Morning Kevin! Can you prioritize the AquaTech invoice today? They're threatening to pause our marina IoT sensors if we don't pay by end of business."

Kevin types back quickly: "On it. I'll process their invoice first thing - is it the $4,200 one from last week?"

"Yes, that's the one. Thanks!"

Kevin takes a sip of his cold brew and mentally prepares for another day of payment orchestration across Dockwa's increasingly complex vendor ecosystem.

**8:23 AM - The Stripe Dashboard Reality Check**

Kevin opens Chrome and navigates to dashboard.stripe.com. He logs in using his saved Google Workspace credentials, and the Stripe dashboard loads showing yesterday's settlement activity:

- **Gross Volume:** $47,832.15
- **Fees:** $1,388.43
- **Net Payout:** $46,443.72
- **Payout Status:** Scheduled for 8 AM (any minute now)

Kevin checks his phone for the time: 8:24 AM. The payout should hit their operating account within the next few minutes, providing the liquidity he needs to process today's vendor payments. Dockwa's cash flow is healthy, but timing is everything when managing payments across multiple systems.

He clicks on the "Payouts" tab and sees the familiar pattern:
- Daily payouts to their primary operating account (Chase Business)
- Reserve holds for chargebacks and disputes (currently $12,847)
- Split payouts to marina partners who use Dockwa's payment processing

The complexity comes from Dockwa's revenue model: they process payments on behalf of marinas but need to separate their SaaS fees from the marina's direct revenue before disbursing funds to partners.

**8:31 AM - The Vendor Invoice Triage**

Kevin opens his shared AP inbox: ap@dockwa.com. The inbox contains 23 unread emails since yesterday evening:

- AquaTech Marina Solutions: $4,200.00 (IoT sensors - priority)
- AWS: $3,847.23 (October hosting bill - autopay failed)
- Maritime Legal Services: $2,850.00 (contract review)
- Newport Office Management: $1,200.00 (office rent)
- 19 smaller vendor invoices ranging from $45 to $890

Kevin's first stop is always the "high-risk" vendors - those who could disrupt Dockwa's operations if not paid promptly. AquaTech falls into this category because their IoT sensors provide real-time slip availability data that feeds directly into Dockwa's reservation system.

**8:38 AM - The AquaTech Payment Priority Process**

Kevin opens the AquaTech email and downloads the PDF invoice: "AquaTech_Invoice_AT-2025-1047.pdf." He quickly reviews the line items:

- Marina Sensor Maintenance (15 locations): $2,800
- Data Integration License (October): $900
- Emergency Sensor Replacement (Newport Marina): $500

Total: $4,200.00
Terms: Net 15
Due Date: October 15, 2025 (today)

Kevin needs to process this payment immediately. He opens a new tab and navigates to Dockwa's payment processing platform: app.bill.com. They migrated to Bill.com six months ago to centralize vendor payments, but the integration with their Stripe-based cash flow still requires manual coordination.

**8:44 AM - The Bill.com Payment Setup**

Kevin logs into Bill.com and clicks "New Bill" from the dashboard. He begins entering the AquaTech invoice:

- **Vendor:** AquaTech Marina Solutions (already in system)
- **Invoice #:** AT-2025-1047
- **Invoice Date:** September 30, 2025
- **Amount:** $4,200.00
- **GL Account:** 5200 - Professional Services
- **Location:** Multiple (marina locations)

Kevin attaches the PDF invoice and moves to the approval workflow. AquaTech payments require dual approval: Kevin's initial review plus Sarah's CFO approval for amounts over $3,000.

He clicks "Submit for Approval" and the invoice gets queued in Sarah's approval inbox. Kevin immediately sends her a Slack message: "AquaTech invoice ($4,200) is in your Bill.com queue for approval. They need payment today to avoid service interruption."

Sarah responds within 2 minutes: "Approved. Go ahead and process."

**8:52 AM - The Payment Execution Challenge**

With approval secured, Kevin needs to execute the payment. Here's where Dockwa's cash flow architecture gets complex: they can't pay directly from their Stripe account balance. Instead, they need to:

1. Confirm the Stripe payout has hit their Chase operating account
2. Verify sufficient funds for vendor payments
3. Execute ACH or wire transfer through Bill.com
4. Update internal accounting records

Kevin opens another tab and logs into Chase Business Online. The login process requires two-factor authentication:
- Username: kevin.chen@dockwa.com
- Password: [complex password from password manager]
- SMS code: 847392 (sent to his phone)

The Chase dashboard loads showing their primary operating account balance: $187,432.18. The morning Stripe payout of $46,443.72 cleared at 8:17 AM, providing ample liquidity for today's payments.

**9:07 AM - The ACH vs. Wire Decision Matrix**

Back in Bill.com, Kevin reviews AquaTech's payment preferences:
- **ACH:** 2-3 business days, $1.50 fee
- **Wire Transfer:** Same day, $25.00 fee
- **Check:** 5-7 business days, $3.00 fee

Given the urgency (payment due today), Kevin selects wire transfer despite the higher fee. AquaTech's banking details are already stored in Bill.com from previous payments:

- **Bank:** Silicon Valley Bank
- **Routing:** 121140399
- **Account:** 4829-381-9847
- **Account Type:** Business Checking

Kevin schedules the wire for immediate processing and gets confirmation number WR-2025-10-001. The payment will be executed at 11 AM during the next wire processing window.

**9:18 AM - The AWS Autopay Failure Investigation**

Kevin moves to the second priority: the failed AWS autopay. This is particularly concerning because AWS hosting powers Dockwa's entire platform, and service interruptions could affect thousands of marina customers.

He opens the AWS email and sees the familiar "Payment Failed" notification:

"Your automatic payment for $3,847.23 failed on October 1, 2025. Reason: Insufficient funds in linked account. Please update your payment method or add funds to avoid service interruption."

Kevin immediately checks which payment method AWS has on file. He logs into the AWS billing console and navigates to Payment Methods. The linked payment method shows:

- **Card:** **** **** **** 4829 (Stripe-issued corporate card)
- **Expiration:** 08/2025
- **Status:** EXPIRED

"Shit," Kevin mutters under his breath. The Stripe corporate card expired last month, and somehow AWS didn't get the updated card information. This is exactly the kind of integration failure that causes weekend emergency calls.

**9:27 AM - The Emergency Card Update Process**

Kevin needs to update AWS with their current corporate card. He opens his password manager and retrieves the new Stripe card details:

- **Card Number:** 4242 4242 4242 1234
- **Expiration:** 03/2027
- **CVV:** 847

He updates the AWS payment method and immediately processes a manual payment for $3,847.23. AWS confirms the payment within 30 seconds, and Kevin breathes a sigh of relief.

He opens his task management app (Asana) and creates a reminder: "Quarterly review of all autopay methods - check for expiring cards."

**9:39 AM - The Batch Processing Strategy**

With the two urgent payments handled, Kevin shifts to batch processing mode for the remaining 19 vendor invoices. He exports a list of all pending invoices from Bill.com and creates a payment priority matrix in Excel:

**High Priority (Same Day):**
- Maritime Legal Services: $2,850 (net 15, due today)
- Newport Office Management: $1,200 (rent - always priority)

**Medium Priority (2-3 days):**
- Office supplies: $347
- Insurance payment: $892
- Software licenses: $645

**Low Priority (5-7 days):**
- Marketing materials: $156
- Conference registration: $250
- Office equipment: $423

Kevin processes the high-priority payments via ACH (faster than checks, cheaper than wires) and schedules the medium-priority payments for Thursday. The low-priority payments get scheduled for next Monday to optimize cash flow timing.

**10:14 AM - The Reconciliation Preparation**

As Kevin finishes processing payments, he needs to prepare the data for NetSuite reconciliation. This is where Dockwa's payment architecture shows its complexity:

- Stripe processes customer payments and holds reserves
- Bill.com executes vendor payments from Chase operating account
- NetSuite tracks all financial activity for accounting purposes
- Multiple bank accounts and payment methods create reconciliation challenges

Kevin exports payment reports from:
1. Stripe (customer receipts and payouts)
2. Bill.com (vendor payments and fees)
3. Chase (bank account activity)

He'll need to match these three data sources in NetSuite to ensure accurate financial reporting.

**10:31 AM - The NetSuite Journal Entry Creation**

Kevin logs into NetSuite and navigates to the AP module. He creates journal entries for today's vendor payments:

**Journal Entry JE-2025-4015 (AquaTech Wire):**
- Debit: Professional Services Expense $4,200.00
- Credit: Chase Operating Account $4,225.00 (includes $25 wire fee)

**Journal Entry JE-2025-4016 (AWS Manual Payment):**
- Debit: Hosting Expense $3,847.23
- Credit: Stripe Corporate Card $3,847.23

**Journal Entry JE-2025-4017 (Batch ACH Payments):**
- Debit: Various Expense Accounts $4,892.00
- Credit: Chase Operating Account $4,898.50 (includes ACH fees)

**10:48 AM - The Cash Flow Monitoring**

With payments processed, Kevin updates his daily cash flow dashboard. This Excel spreadsheet tracks:

- Beginning cash balance: $187,432.18
- Expected Stripe payouts: $46,443.72 (received)
- Vendor payments executed: $13,365.73
- Ending projected balance: $220,510.17

Kevin also updates his weekly cash flow forecast, adding expected payments for the rest of the week:

- Tuesday: $8,400 (payroll processing)
- Wednesday: $5,200 (quarterly insurance payment)
- Thursday: $3,100 (medium-priority vendor payments)
- Friday: $2,800 (marina partner revenue sharing)

The forecast shows healthy liquidity through the end of the month, assuming normal Stripe payout volumes.

**11:07 AM - The Exception Handling**

Kevin's payment processing is interrupted by an urgent Slack message from Maria in AP: "Kevin - got a weird situation. Marina del Rey sent a check for $2,400, but they're also set up for ACH autopay. Should I process the check or reverse their autopay to avoid double payment?"

Kevin opens Marina del Rey's payment history in Bill.com and sees:
- October 1: ACH payment scheduled for $2,400 (auto-renewal)
- October 1: Check received for $2,400 (manual payment)

This requires investigation. Kevin calls Marina del Rey's accounting department.

"Hi, this is Kevin from Dockwa. We received your check for $2,400, but you also have an ACH autopay scheduled for the same amount. Do you want to cancel the autopay going forward?"

The response: "Oh yes, we meant to cancel that autopay. We switched to check payments last month but forgot to update our Dockwa account. Please cancel the ACH and process the check."

Kevin updates their Bill.com payment preferences and cancels the pending ACH transaction. He messages Maria: "Process the check, I cancelled their autopay. Updated their preferences to prevent this in the future."

**11:23 AM - The Stripe Partner Revenue Distribution**

One of Dockwa's most complex payment processes involves distributing revenue to marina partners. When a boater pays for a slip reservation through Dockwa, the payment gets split:

- Dockwa's commission: 8-12% (varies by contract)
- Marina's revenue: 88-92%
- Payment processing fees: ~2.9%

Kevin navigates to Stripe's Connect dashboard to review pending partner payouts. For yesterday's reservations:

- Gross reservation payments: $28,472.15
- Dockwa commissions: $3,416.66
- Marina partner revenue: $24,198.91
- Processing fees: $856.58

Kevin needs to create individual ACH transfers to 23 different marina partners. Stripe Connect automates most of this process, but Kevin manually reviews each payout for accuracy:

**Harbor View Marina:** $1,847.23 (87% of $2,123.50 gross)
**Sunset Yacht Club:** $943.18 (91% of $1,036.48 gross)
**Pacific Coast Storage:** $2,156.92 (89% of $2,423.51 gross)

Kevin approves the batch payout, and Stripe schedules the transfers for Thursday morning.

**11:44 AM - The Monthly Vendor Review Process**

The third Thursday of each month, Kevin conducts a comprehensive vendor review. Today's focus is payment terms optimization and relationship management.

He exports vendor payment data from Bill.com for the past 90 days and creates an analysis spreadsheet:

**Payment Volume Analysis:**
- Total vendors: 147
- Active vendors (monthly payments): 89
- High-volume vendors (>$5K/month): 12
- Payment method preferences: 67% ACH, 21% Check, 12% Wire

**Payment Timing Analysis:**
- Average days to payment: 18.3
- Vendors paid early (discount eligible): 23
- Vendors paid late (interest charged): 7
- Autopay failures requiring manual intervention: 15

Kevin identifies opportunities for improvement:
- Negotiate early payment discounts with 8 high-volume vendors
- Convert 12 check-preferring vendors to ACH (reduce processing time)
- Fix autopay setup issues with 15 problematic vendors

**12:02 PM - The Integration Challenge Documentation**

Kevin opens his ongoing "Payment System Integration Issues" document and adds today's observations:

**Current Pain Points:**
1. **Stripe-to-Bank Timing:** Daily payouts create cash flow timing challenges for same-day vendor payments
2. **Card Expiration Management:** No automated alerts when corporate cards expire, causing autopay failures
3. **Vendor Payment Preferences:** No standardized system for collecting and maintaining payment preferences
4. **Multi-System Reconciliation:** Manual effort required to match Stripe, Bill.com, and NetSuite records

**Proposed Solutions:**
1. **Real-time Banking Integration:** Connect Stripe directly to Bill.com for instant payment capability
2. **Card Management Automation:** Automated card updates for recurring payments
3. **Vendor Onboarding Workflow:** Standardized process for collecting payment preferences
4. **Unified Reconciliation Dashboard:** Single view of all payment activity across systems

**12:18 PM - The Vendor Communication Project**

Kevin's afternoon project involves updating vendor payment communications. Too many vendors are confused about Dockwa's payment processes, leading to unnecessary emails and phone calls.

He drafts a standardized vendor payment FAQ document:

**Dockwa Vendor Payment Process - FAQ**

**Q: When will my invoice be paid?**
A: Standard payment terms are Net 30. High-priority vendors (critical services) are paid within 5 business days.

**Q: What payment methods do you accept?**
A: We prefer ACH transfers (faster, lower fees). We also process wire transfers for urgent payments and checks upon request.

**Q: How do I update my banking information?**
A: Email ap@dockwa.com with updated banking details. Changes take 1-2 business days to process.

**Q: Why did my autopay fail?**
A: Common causes include expired cards, insufficient funds, or banking changes. We'll always email you immediately when autopay fails.

**Q: Can I get early payment discounts?**
A: We offer 2% early payment discounts for payments within 10 days. Contact ap@dockwa.com to set up early payment terms.

Kevin plans to email this FAQ to all active vendors and post it on Dockwa's vendor portal.

**12:34 PM - The Daily Wrap-Up Process**

Kevin's final task each day is updating the AP status dashboard. This shared Google Sheet tracks:

- **Payments Processed Today:** 23 payments totaling $13,365.73
- **Average Processing Time:** 4.2 minutes per payment
- **Autopay Success Rate:** 87% (2 failures out of 15 scheduled)
- **Vendor Inquiries:** 3 (1 payment status, 1 banking update, 1 early payment request)
- **System Issues:** 1 (AWS card expiration)

**Outstanding Issues:**
- Marina del Rey autopay cancellation (resolved)
- AquaTech urgent payment (completed)
- AWS card update (completed)

**Tomorrow's Priorities:**
- Process remaining medium-priority vendor payments
- Follow up on early payment discount negotiations
- Update vendor FAQ document
- Review quarterly payment method preferences

**12:47 PM - The Process Improvement Reflection**

As Kevin saves his work and prepares for lunch, he reflects on the morning's payment orchestration. Dockwa's payment ecosystem has grown increasingly sophisticated, but it still requires significant manual coordination:

- **Multiple Systems:** Stripe, Bill.com, NetSuite, and various bank portals each serve specific functions but don't integrate seamlessly
- **Timing Dependencies:** Stripe payouts must clear before vendor payments can be processed, creating daily coordination challenges
- **Exception Handling:** Payment failures, vendor changes, and urgent requests require human judgment and quick decision-making
- **Relationship Management:** Vendor communication and payment preferences need ongoing attention

Kevin opens his Notes app and dictates a voice memo: "Payment processing insights - October 15. Successfully processed 23 vendor payments totaling $13.4K. Two key learnings: First, card expiration alerts need automation - the AWS failure could have been prevented. Second, vendor payment preferences need a centralized database - too much time spent on payment method coordination. The technology stack works well when everything goes according to plan, but human oversight remains critical for exceptions and relationship management."

He sends a quick message to his team: "AP processing complete for the day. All priority vendors paid, no service interruptions. Documentation updated for tomorrow's workflow."

Kevin closes his laptop and heads to lunch, knowing that tomorrow will bring another round of payment orchestration challenges across Dockwa's growing vendor ecosystem. The marina business may be seasonal, but vendor payments are a year-round ballet of timing, technology, and relationship management.
