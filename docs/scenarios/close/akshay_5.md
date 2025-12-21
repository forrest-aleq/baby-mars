# Akshay's "Finance Day" at Hyperbrowser

## A Co-Founder's Scrappy Approach to Startup Finance

Akshay Shekhawat opens his laptop at 10:47 AM in the Hyperbrowser office in San Francisco, coffee already half-finished. The 28-year-old co-founder and CTO has been putting off "finance stuff" for three days, and Shri just pinged him on Slack: "Dude, can you check if we paid AWS? Getting warnings about our account."

His desk is a controlled chaos: one laptop (no dual monitors—he codes on this same machine), three empty La Croix cans, and a stack of papers that are definitely invoices but also might be old takeout menus. His coffee mug reads "I void warranties"—a gift from his college roommate.

**10:52 AM - The Stripe Dashboard Reality Check**

Akshay opens Chrome and navigates to stripe.com. Login, password (saved in browser), two-factor via his phone. He lands on the Stripe dashboard and immediately feels a mix of excitement and stress.

Revenue graph is trending up—nice. They processed $47K last week. But then he scrolls down and sees the balance: $23,847.22 in the Stripe account.

He has no idea if this is good or bad. Is that before or after fees? Are there pending payouts? He genuinely doesn't know. There's probably a way to see this, but he's never taken the time to figure it out.

**10:57 AM - The AWS Situation**

Right, AWS. Akshay navigates to his Gmail and searches "AWS invoice." He finds approximately 800 emails from AWS. He refines his search: "AWS invoice September 2025."

Three emails pop up:

* "Your AWS Invoice is Ready - September 2025" (opened, marked as unread)
* "AWS Payment Failed - Action Required" (unopened)
* "URGENT: AWS Service Interruption Warning" (unopened, from yesterday)

"Oh shit," Akshay mutters. He opens the urgent email. Their primary credit card on file was declined, and they have 48 hours before service suspension. The amount due: $8,347.50 for September usage.

He immediately opens Brex (their corporate card) in a new tab. Logs in. Checks the available credit: $47,000. Plenty of room. Why didn't the card work?

He clicks through to the cards section and sees their AWS card has a $5,000 monthly limit that he set six months ago when they were spending way less on infrastructure. The card hit its limit on September 22nd, which means they've been running up an unpaid balance for 8 days.

**11:03 AM - Emergency AWS Payment**

Akshay navigates back to AWS, finds the billing section (after clicking through three wrong menus), and updates the payment method to their main Brex card with the higher limit. He processes the $8,347.50 payment manually.

Confirmation email arrives. Crisis averted. He sends Shri a Slack: "AWS paid. We're good. Also we're spending way more on infra than I thought lol"

Shri responds: "How much?"

Akshay: "Like $8K last month"

Shri: "Is that normal?"

Akshay: "No idea. Probably? We're scaling pretty fast. I'll check if we have budget somewhere."

They do not have a budget.

**11:09 AM - The Invoice Email Dive**

Akshay figures he's in "finance mode" now, so he might as well tackle the other emails. He has a dedicated folder called "Bills/Invoices" where he drags things he'll "deal with later." The folder has 73 unread items.

He sorts by sender and starts scanning:

* GitHub Enterprise: $450/month (autopay on Brex)
* OpenAI API: $1,847.92 (autopay on Brex)
* Anthropic API: $2,934.18 (autopay on Brex)
* Linear: $89/month (autopay on Brex)
* Vercel: $250/month (autopay on Brex)
* Some contractor named Sarah: "Invoice #003 - Design Work" for $3,500

Wait, who's Sarah? Akshay clicks on the email from 11 days ago. It's from a designer Shri hired to redo their landing page. Akshay vaguely remembers approving this. The invoice says "Net 15" and it's now day 11.

He doesn't have a systematic way to pay contractors. He opens a new email:

"Hey Sarah! Thanks for the great work on the landing page. Can you send me your Zelle or Venmo? Want to get you paid today."

Sarah responds in 4 minutes: "Hi Akshay! I actually sent my bank info in the original invoice email for ACH transfer. Here it is again: [bank details]. Thanks!"

Akshay realizes he's never sent an ACH transfer before. He googles "how to send ACH payment" and discovers he needs to do this through his bank. He logs into Mercury (their business bank account) for the first time in... two months? Three?

**11:24 AM - Mercury Deep Dive**

The Mercury dashboard loads. Balance: $127,483.91.

Akshay stares at this number. Is this good? It seems good. But he has no idea what their burn rate is, what payroll is, or what's going out vs. coming in.

He clicks around and finds the "Send Money" button. Selects "Wire or ACH." Enters Sarah's banking details from her email. Amount: $3,500. Description: "Landing page design - Invoice 003."

He hits submit and gets a confirmation screen: "Payment will be processed in 2-3 business days." He forwards the confirmation to Sarah: "Sent! Should hit your account by early next week. Thanks again!"

**11:31 AM - The Brex Statement Situation**

Akshay figures he should probably look at the full Brex statement since he's already in finance mode. He opens Brex and navigates to statements. September's statement shows total spending of $31,847.22.

He downloads the CSV because... he's not sure why, but it feels like something he should do. The CSV has 247 line items. He scans through:

* AWS charges (multiple small ones)
* OpenAI API (daily charges)
* Anthropic API (also daily)
* DoorDash (Shri orders lunch for the team)
* More DoorDash
* A LOT of DoorDash
* "ANTHROPIC" for $50 (what is this? Different from the API?)
* "THE CREAMERY SF" $73.42 (team dinner?)
* "AIRPORT PARKING" $45 (someone's trip)
* "FIGMA PRO" $135/month

Akshay makes a mental note that they're spending $2,800/month on food delivery. Is that a lot? He has no context.

**11:43 AM - The "Do We Have Accounting Software?" Realization**

Akshay's phone buzzes with a text from his college friend who works in finance at a Series B startup: "Yo when's your next board meeting? Need any help prepping financials?"

Board meeting. Right. They have one in... Akshay checks his calendar... 18 days. And they'll need to present financials. Which they don't really have.

He messages Shri on Slack: "Do we have actual financial statements?"

Shri: "Like what?"

Akshay: "Idk, P&L, balance sheet, that stuff investors want"

Shri: "I thought you were handling that"

Akshay: "I literally just look at Stripe and Brex"

Shri: "Is that not enough?"

Akshay: "Pretty sure we need actual accounting"

Shri: "Can't you just export some CSVs?"

**11:51 AM - The Contractor Payments List**

Akshay suddenly remembers they have other contractors. He searches his email for "invoice" and finds:

* Marcus (backend engineer, part-time): Invoice from August 27 for $6,000. Marked as "Due September 10." It is now September 28.
* Jenny (content writer): Invoice from September 1 for $2,500. Due September 15.
* Some company called "Legal Zoom": $2,847 for trademark filing. Due: unclear.

He starts to panic. Are all of these unpaid? He checks his Mercury transaction history and searches for "Marcus." He finds a $6,000 payment from September 12th. Okay, Marcus is paid, just late.

He searches for "Jenny." No payment. Crap.

He immediately sends Jenny an email: "Hey Jenny! Sorry for the delay on payment. Sending your $2,500 today. Can you reply with your bank details?"

Jenny responds: "Hi Akshay, no worries! I actually sent my details in my original invoice email, but here they are again: [bank info]. Also, I sent another invoice on Sept 15 for the additional blog posts. Just FYI!"

Another invoice. Of course there's another invoice.

**12:04 PM - The "We Need Systems" Moment**

Akshay opens a new note in his Notes app and starts typing:

"Finance stuff we're bad at:

* Don't know our burn rate
* Pay contractors late
* No real financial statements
* Not tracking MRR properly
* Brex has like 10 different cards with random limits
* No idea when bills are due
* AWS almost got shut off
* Food spending is insane?
* Need accounting software
* Board meeting in 18 days wtf"

He sends this list to Shri: "We need to fix this"

Shri responds: "Yeah. Want me to ask other YC founders what they use?"

Akshay: "Yes please. Also can you handle the contractor stuff? I just paid Sarah and Jenny but there might be more"

Shri: "I'll go through my emails"

**12:17 PM - Back to Actual Work**

Akshay gets a Slack notification from their Discord community: "Hey @akshay, the MCP server is throwing errors when connecting to Claude. Can you look at this?"

This. This is what he should be doing. Not finance. He's a CTO. He builds product. But someone has to make sure vendors get paid and AWS stays on.

He responds in Discord: "On it. Give me 20 min to finish something and I'll dig in."

But first, he navigates back to Brex and looks at the transaction list one more time. There's a charge for $1,847.50 labeled "ANTHROPIC CLAUDE" from three days ago. He has no idea what this is. Their Anthropic API usage is tracked separately. He makes a note to ask the team.

**12:23 PM - The Quickbooks Suggestion**

Akshay does a quick Google search: "best accounting software for startups." Every result mentions QuickBooks, Xero, or something called "Pilot" that's like outsourced accounting.

He texts a founder friend: "Yo do you use accounting software?"

Friend: "Yeah we use QuickBooks + Fondo for bookkeeping. Game changer. You don't have that yet?"

Akshay: "We use Stripe and vibes"

Friend: "Lmao you're gonna die at your next board meeting. Get a bookkeeper ASAP"

**12:31 PM - The Reality of Hyperbrowser's Finances**

Akshay leans back and tries to piece together what he actually knows about their finances:

**What he knows:**

* They have $127K in Mercury
* They made ~$47K last week in revenue (on Stripe)
* They spend ~$32K/month on Brex
* AWS is like $8K/month
* Payroll is... he literally doesn't know. Gusto handles it automatically.

**What he doesn't know:**

* Actual monthly burn rate
* Net profit/loss
* How long their runway is
* Whether they're GAAP-compliant (probably not)
* If they're collecting sales tax correctly (definitely not)
* What their gross margin is
* Pretty much everything a CFO would know

He makes a decision: After the board meeting, they're hiring someone to handle this. Or at least getting a bookkeeper. This is not a good use of co-founder time.

**12:39 PM - One More Payment Before Lunch**

Akshay remembers the LegalZoom invoice. He finds the email: "Trademark Registration Services - Invoice #LZ-9837422." Amount: $2,847. Due: Net 30 from August 15.

He calculates: That's... 44 days ago. They're two weeks overdue.

He logs back into Mercury, navigates to payments, enters LegalZoom's information from the invoice, and processes the payment. $2,847 sent.

He forwards the confirmation to Shri: "Paid LegalZoom. We were 2 weeks late. Need better system."

Shri: "100%. After board meeting let's actually fix this."

**12:47 PM - Lunch Break (Finally)**

Akshay closes all the finance tabs. His brain hurts. He's an engineer who wants to build browser infrastructure for AI agents, not track invoices and reconcile bank accounts.

He heads out to grab lunch at the spot around the corner, texting the team: "Getting tacos, anyone want?"

Three responses come in immediately with orders. He'll expense it on Brex under... actually, does it matter? Nobody's tracking this anyway.

As he walks to the taco place, he thinks about how wild it is that they're processing nearly $200K/month in revenue but can't tell you their profit margin without spending an hour with spreadsheets.

This is the reality of a fast-growing YC startup: building incredible technology, serving customers at scale, and running finance like a college student managing their checking account.

**1:23 PM - The Afternoon Surprise**

Akshay returns with tacos and opens his laptop. New email from their bank: "Mercury Review: Additional Documentation Required."

He clicks through. Mercury is doing a routine review of their business account and needs:

* Updated articles of incorporation
* Current board resolution authorizing bank signers
* Proof of business address
* Tax return or financial statements

"Tax return or financial statements." Akshay laughs. They filed a tax extension and their accountant has been asking for their books for weeks. Their books are a bunch of CSVs and the Stripe dashboard.

He forwards the email to Shri: "Mercury needs docs. Do we have any of this?"

Shri: "I think our lawyer has the incorporation stuff? No idea about the rest."

Akshay: "Cool cool cool cool cool" (The "this is fine" message)

**1:34 PM - The "Brex Has Questions Too" Email**

Another email arrives, this time from Brex: "Action Required: Update Your Business Information."

Brex wants:

* Updated annual revenue figures
* Current business bank account information
* Verification of business address
* Copy of most recent financial statements

Akshay responds to the email: "Hi, we're in the process of finalizing our 2024 financial statements. Can we provide this in 2-3 weeks after our next board meeting?"

He has no idea if they'll have statements in 2-3 weeks, but it buys time.

**1:41 PM - The Team Slack**

A message pops up in their #general channel from Pranav (their growth hire): "Hey team, I need to expense my laptop. Where do I submit expense reports?"

Valid question. They don't have an expense report system. Everyone just uses Brex directly.

Akshay responds: "We don't have a formal process yet. Did you use your Brex card?"

Pranav: "I used my personal card. It was $2,400."

Akshay: "Oh. Uh. Can you send me a receipt and your Venmo?"

Pranav: "Don't we have an expense reimbursement process?"

Akshay: "We're uh... building one. Venmo works for now?"

He immediately makes a note: "Add expense reimbursement to list of finance things we need to fix."

**1:49 PM - The Actual Work Distraction**

Akshay's phone buzzes with a customer issue. Their largest customer (paying $1,200/month) is having authentication issues with the API. He drops everything finance-related and switches to debugging mode.

Twenty minutes later, he's deep in logs and has completely forgotten about all the finance stuff. This is where he thrives—fixing technical problems, not tracking invoices.

**2:11 PM - The Investor Check-In**

Email notification: "Quick check-in?" from Sarah Chen, one of their angel investors.

Akshay opens the email: "Hey Akshay & Shri! Hope you're crushing it. Quick Q: Can you send over your latest metrics deck? Want to intro you to a potential Series A lead but would love to have current numbers. LMK!"

Metrics deck. They don't have an updated metrics deck. The last one they made was for their YC batch presentation six months ago.

Akshay forwards to Shri: "We need to make a new deck. Think you can handle metrics side? I'll do product updates."

Shri: "Yeah but what's our actual MRR? I can see Stripe but is that gross or net?"

Akshay: "It's... whatever number Stripe shows minus like 3% for fees?"

Shri: "That's not how you calculate MRR"

Akshay: "It's not?"

Shri: "I don't think so. Let me Google it."

**2:23 PM - The Technical Debt Parallel**

As Akshay debugs the API authentication issue, he realizes the irony: They've been meticulous about avoiding technical debt in their codebase—clean code, comprehensive tests, proper documentation. But their financial "codebase" is held together with duct tape and hope.

They track every API response time but have no idea what their customer acquisition cost is.

They monitor server uptime obsessively but couldn't tell you their cash position without logging into three different platforms.

They built automated testing for code but manually track (or forget to track) vendor invoices.

**2:37 PM - The Decision Point**

Akshay sends a message to their YC group chat: "Real talk: when did you all get proper accounting set up? We're doing like $200K/month revenue and still tracking everything in Stripe and Brex lol"

Responses come in:

"Dude get a bookkeeper NOW"

"We hired Fondo at like $50K/month revenue. Best decision ever."

"You're at $200K/month and don't have accounting? Your investors are gonna be pissed"

"Try Pilot or Fondo. They handle everything. Worth every penny."

"We use QuickBooks + a part-time contractor. Works well."

**2:44 PM - The Plan**

Akshay creates a new Google Doc titled "Finance Cleanup - Action Items" and shares it with Shri:

**Immediate (This Week):**

* [ ] Pay Jenny's second invoice ($2,500)
* [ ] Verify all contractor payments are current
* [ ] Get Pranav his $2,400 laptop reimbursement
* [ ] List all recurring subscriptions with amounts
* [ ] Respond to Mercury with docs they need

**Short-term (Next 2 Weeks - Before Board Meeting):**

* [ ] Interview bookkeeping services (Fondo, Pilot, etc.)
* [ ] Get actual P&L for last 3 months somehow
* [ ] Calculate real MRR, burn rate, runway
* [ ] Clean up Brex card limits and categories
* [ ] Create simple expense reimbursement process
* [ ] Update investor deck with real numbers

**Long-term (Next Quarter):**

* [ ] Hire bookkeeper or outsource to Fondo
* [ ] Implement proper accounting software
* [ ] Set up sales tax collection (probably overdue)
* [ ] Get 2024 taxes filed (extension deadline coming)
* [ ] Create monthly financial review process
* [ ] Stop being embarrassingly bad at basic finance stuff

**2:51 PM - Back to Building**

Akshay fixes the authentication bug, pushes the code, and watches the customer's issue resolve in real-time. This is what he loves. This is what he's good at.

The finance stuff will get handled. They'll hire someone. They'll implement systems. But for now, they're a scrappy YC startup building infrastructure for AI agents, growing revenue 40% month-over-month, and occasionally forgetting to pay AWS.

He closes all the finance tabs and opens VS Code. There's a feature for their HyperAgent framework that customers have been requesting, and he wants to ship it before the weekend.

**3:17 PM - The Slack from Shri**

"Dude I just looked at our actual numbers. We're burning like $85K/month and making like $180K/month in revenue. That's actually pretty sick?"

Akshay responds: "Wait really? How'd you calculate that?"

Shri: "Pulled all the data from Stripe, Brex, Mercury, and Gusto. Made a spreadsheet. We're profitable."

Akshay: "Holy shit we're profitable?"

Shri: "Yeah by like $95K/month. After paying ourselves and everything."

Akshay: "Why do I feel like we're constantly broke then?"

Shri: "Because we have no visibility into our finances lol. But yeah, we're doing well. Still need a bookkeeper though."

Akshay: "100%. But this is good news. Let's use some of that profit to hire someone to handle all this."

**3:24 PM - The Reflection**

Akshay leans back and thinks about the day. He spent three hours on finance stuff—paying overdue invoices, fixing card limits, responding to bank requests, and discovering they're actually profitable.

Three hours that could have been spent building features, talking to customers, or improving their infrastructure. Three hours that, in a properly organized company, would be handled by a finance person or a good bookkeeping service.

But they're not a properly organized company yet. They're two technical co-founders who went from Y Combinator to $200K/month revenue in less than a year, and systems like "proper accounting" haven't caught up to their growth.

The good news: They're profitable and growing fast.

The bad news: They're two weeks away from a board meeting and don't have real financial statements.

The solution: Stop being cheap, hire proper help, and focus on what they're actually good at—building browser infrastructure for AI agents.

**3:31 PM - The Final Message**

Akshay sends one last Slack to Shri: "Let's get quotes from Fondo and Pilot tomorrow. I want this handled by end of next week."

Shri: "Agreed. I'll reach out to both. Should have saved us so much time months ago."

Akshay: "Yeah but we were scrappy YC founders"

Shri: "We're still scrappy. Just scrappy with bookkeepers now."

Akshay smiles and gets back to code. Tomorrow they'll deal with proper accounting. Today, they shipped features and somehow didn't let AWS shut off their infrastructure.

In the world of early-stage startups, that counts as a win.

---

**4:47 PM - The Final Tally**

Before shutting down for the day, Akshay makes a list of what he actually paid/processed today:

* AWS: $8,347.50 (crisis averted)
* Sarah (designer): $3,500
* Jenny (writer): $2,500 + need to pay second invoice
* LegalZoom: $2,847 (two weeks late)
* Pranav laptop: $2,400 (pending)

Total: ~$19,600 in payments, most of which were late or almost-disasters.

Revenue today per Stripe: $7,234

As he closes his laptop, Akshay makes a promise to himself: Next month, they'll have someone else doing this. He's a builder, not a bookkeeper. And Hyperbrowser deserves both.
