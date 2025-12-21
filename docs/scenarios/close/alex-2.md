# Story 7: Dockwa Marina SaaS - Monthly Subscription Churn Analysis
## **Difficulty Level: 2 (Hard)**

### Alex's Data Detective Work

Alex Thompson sits in the Dockwa office at 9:31 AM, staring at two monitors displaying completely different customer counts for September. The Recurly dashboard shows 2,847 active subscriptions, while the internal analytics dashboard shows 3,104 active customers. As the 25-year-old revenue operations analyst, Alex knows these numbers should match—and when they don't, it usually means hours of cross-system detective work to find the discrepancies.

The monthly board report is due Thursday, and the investor relations team needs accurate subscription metrics. CEO Sarah Martinez has been asking pointed questions about churn rates after a competitor raised Series C funding, and Alex can't afford to present conflicting data.

**9:38 AM - The Recurly Deep Dive**

Alex opens Recurly in Chrome and navigates to the Analytics dashboard. The September summary shows:
- Active Subscriptions (September 30): 2,847
- New Subscriptions: 342
- Cancelled Subscriptions: 189
- Net Growth: +153

But these numbers don't tell the full story. Alex needs to understand the different subscription states that might explain the discrepancy with the internal dashboard.

She clicks on "Subscription Details" and exports the full subscriber list. The CSV download takes 47 seconds and contains 4,193 rows—far more than the 2,847 "active" subscriptions shown in the summary.

**9:46 AM - The Status Code Mystery**

Opening the CSV in Excel, Alex sees subscription statuses she's never encountered:
- Active: 2,847 (matches dashboard)
- Cancelled: 1,024
- Expired: 189
- Past_due: 94
- Paused: 39

The "Past_due" subscriptions are particularly puzzling. Are these counted as active customers in the internal system but not in Recurly? Alex needs to understand Dockwa's business logic for handling failed payments.

She opens Slack and messages Kevin from Engineering: "Quick question about subscription status - how does our internal system handle 'past_due' Recurly subscriptions? Are they counted as active customers?"

Kevin responds: "Past_due subscriptions stay active for 7 days while we retry payment. After that they move to cancelled. But our internal dashboard might be caching old status data."

**10:02 AM - The Internal Dashboard Investigation**

Alex opens Dockwa's internal analytics dashboard (built on Looker) and navigates to the customer metrics page. The September 30 count shows 3,104 "active customers," but Alex realizes the definition might be different from Recurly's "active subscriptions."

She clicks on the data definition and finds: "Active Customers = All customers with marina reservations in the last 90 days OR active subscription status, excluding customers marked as 'test accounts.'"

This explains part of the discrepancy—the internal system counts customers who made reservations but might not have ongoing subscriptions.

**10:14 AM - The Database Query Attempt**

Alex needs to build a bridge between the Recurly data and internal customer data. She opens the company's database query tool (Mode Analytics) and attempts to write a SQL query to reconcile the numbers.

```sql
SELECT
    COUNT(DISTINCT c.customer_id) as active_customers,
    COUNT(DISTINCT s.subscription_id) as active_subscriptions
FROM customers c
LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
WHERE c.status = 'active'
AND c.test_account = false
AND (s.status = 'active' OR c.last_booking_date >= '2025-07-01')
```

The query returns an error: "Permission denied for table 'subscriptions'." Alex doesn't have direct database access to the subscription table.

She messages the data team: "Need help with customer/subscription reconciliation query. Getting permission error on subscriptions table. Can someone help run this analysis?"

**10:28 AM - The Export and Match Process**

While waiting for database help, Alex decides to manually reconcile the data using exports from both systems. She exports the customer list from the internal dashboard and the subscription list from Recurly, both as CSV files.

From the internal dashboard: "Active_Customers_Sep30_2025.csv" (3,104 rows)
From Recurly: "Active_Subscriptions_Sep30_2025.csv" (2,847 rows)

Alex opens both files and realizes the immediate challenge—they use different customer identifiers. The internal system uses incremental customer IDs (1001, 1002, 1003...) while Recurly uses email addresses as the primary identifier.

**10:41 AM - The Email Matching Challenge**

Alex needs to match customers between systems using email addresses. She creates a new Excel workbook with two sheets: "Internal_Data" and "Recurly_Data."

She copies the internal customer data to sheet 1 and Recurly subscription data to sheet 2. Both datasets include email addresses, but Alex quickly discovers data quality issues:

Internal system emails:
- john.smith@marina.com
- SARAH.JONES@YACHTCLUB.ORG
- mike_torres@gmail.com

Recurly emails:
- john.smith@marina.com
- sarah.jones@yachtclub.org
- mike.torres@gmail.com

The case sensitivity and formatting differences mean a simple VLOOKUP won't work. Alex needs to normalize the email addresses first.

**10:53 AM - Excel Formula Engineering**

Alex creates a helper column in both sheets to standardize email addresses:
`=LOWER(TRIM(B2))` where B2 contains the email address.

She then uses a more complex VLOOKUP to match customers:
`=IF(ISERROR(VLOOKUP(C2,Recurly_Data!C:E,3,FALSE)),"NO MATCH",VLOOKUP(C2,Recurly_Data!C:E,3,FALSE))`

The formula reveals the scope of the discrepancy:
- 2,731 customers appear in both systems
- 116 Recurly subscriptions have no matching internal customer record
- 373 internal customers have no active Recurly subscription

**11:17 AM - The Missing Customer Investigation**

Alex focuses on the 116 Recurly subscriptions with no internal customer match. She sorts this subset and notices a pattern—many of these email addresses look like test accounts:

- test@dockwa.com
- demo_user@marina-example.com
- billing-test@recurly.com
- integration_test_user@dockwa.com

These are likely test subscriptions that should be excluded from revenue reporting but are showing up in Recurly's active subscription count.

**11:31 AM - The Recurly Cleanup Process**

Alex logs into Recurly's admin panel and searches for subscriptions containing "test" in the email address. She finds 47 active test subscriptions that are inflating the metrics.

But canceling these subscriptions individually would be time-intensive. Alex checks if Recurly has a bulk management feature. Under "Account Management" → "Bulk Operations," she finds an option to bulk update subscriptions based on email patterns.

She creates a filter: Email contains "test" OR Email contains "demo" OR Email contains "@dockwa.com" (internal company emails used for testing).

The filter returns 73 subscriptions. Alex exports this list to verify each one is actually a test account before making bulk changes.

**11:47 AM - The Internal Customer Analysis**

Now Alex investigates the 373 internal customers who don't have active Recurly subscriptions. Are these customers who cancelled their subscriptions but are still counted as "active" in the internal system?

She creates a pivot table from the internal customer data, grouping by "last_booking_date." The results show:
- 89 customers with bookings in the last 30 days (no subscription)
- 127 customers with bookings in the last 60 days
- 157 customers with bookings 60-90 days ago

This suggests these customers made recent reservations without maintaining ongoing subscriptions—they're transactional customers rather than subscription customers.

**12:08 PM - The Revenue Impact Analysis**

Alex realizes she needs to understand the financial impact of these discrepancies. She opens Recurly's revenue reporting and exports September's subscription revenue: $347,293.

Then she checks the internal revenue dashboard, which shows September total revenue of $428,847. The difference ($81,554) likely represents transactional booking fees from customers without subscriptions.

But Alex notices another issue—the internal revenue dashboard includes refunds as negative revenue, while Recurly shows net revenue. She needs to account for this methodological difference.

**12:24 PM - The Data Team Response**

Kevin from the data team responds to Alex's earlier message: "I ran your reconciliation query. Here are the results:

- Total unique customers in system: 3,104
- Customers with active subscriptions: 2,847
- Customers with recent bookings only: 257
- Test accounts: 73

The internal dashboard is double-counting some customers. I'll fix the query logic."

This confirms Alex's manual analysis but reveals an additional issue—the internal dashboard has been overcounting by including test accounts.

**12:37 PM - The Correction Process**

Alex now has enough information to prepare corrected metrics for the board report:

**Corrected September Subscription Metrics:**
- Active Subscriptions (excluding tests): 2,774
- Active Transactional Customers: 257
- Total Active Customers: 3,031
- Monthly Subscription Revenue: $347,293
- Transactional Revenue: $81,554
- Total Revenue: $428,847

But she needs to ensure these corrections are reflected in the ongoing reporting systems.

**12:51 PM - The Process Documentation**

Alex creates a new document: "Customer_Subscription_Reconciliation_Process.docx" to document her findings and establish a monthly routine:

1. **Monthly Reconciliation Steps:**
   - Export active customers from internal dashboard
   - Export active subscriptions from Recurly
   - Remove test accounts using standardized email filters
   - Match customers using normalized email addresses
   - Categorize discrepancies as subscription vs. transactional customers

2. **Identified Issues to Resolve:**
   - Standardize email formatting between systems
   - Implement automatic test account filtering
   - Align revenue recognition methodologies
   - Fix internal dashboard query to exclude test accounts

**1:15 PM - The Stakeholder Communication**

Alex composes an email to the investor relations team and CFO:

"Subject: September Customer Metrics - Corrected Analysis

Hi team,

I've completed the reconciliation of our customer and subscription metrics for September. Key findings:

**Corrected Numbers:**
- Active Subscriptions: 2,774 (not 2,847 - excluded test accounts)
- Total Active Customers: 3,031 (not 3,104 - removed duplicates)
- Net Customer Growth: +127 (adjusted for data quality issues)

**Process Improvements Needed:**
1. Monthly reconciliation between Recurly and internal systems
2. Automated test account filtering
3. Standardized customer definitions across platforms

Detailed analysis attached. These corrected numbers should be used for the board report.

Best,
Alex"

**1:28 PM - The System Integration Discussion**

Alex schedules a meeting with Kevin, the CFO, and the VP of Revenue Operations for tomorrow to discuss longer-term solutions. The manual reconciliation process took nearly 4 hours and identified systemic data quality issues that will recur monthly without process improvements.

She creates a meeting agenda:
1. Implement automated data quality checks
2. Standardize customer identification across systems
3. Create real-time dashboard connecting Recurly and internal data
4. Establish monthly reconciliation SLA and ownership

Alex saves all her analysis files to the shared drive under "Monthly_Reporting/Customer_Metrics/September_2025" and updates her task list. The corrected metrics are ready for the board report, but the underlying process improvements will require cross-functional collaboration and potentially months of system integration work.

As she closes her laptop for lunch, Alex reflects that data detective work like this is simultaneously frustrating and satisfying—every discrepancy tells a story about how the business actually operates versus how the systems think it operates.
