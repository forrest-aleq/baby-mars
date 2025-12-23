"""
Stargate Capability Mapping
============================

Maps Baby MARS work units to Stargate capability keys.
Per Stargate Integration Contract v1.1, Section 9.3.
"""

# Maps Baby MARS work unit (tool, verb) to Stargate capability_key
CAPABILITY_MAP = {
    # === QuickBooks (qb.*) ===
    ("erp", "process_invoice"): "qb.bill.create",
    ("erp", "create_record"): "qb.vendor.create",
    ("erp", "query_records"): "qb.query",
    ("erp", "post_journal_entry"): "qb.journal.create",
    ("erp", "create_vendor"): "qb.vendor.create",
    ("erp", "get_vendor"): "qb.vendor.get",
    ("erp", "list_vendors"): "qb.vendor.list",
    ("erp", "create_bill"): "qb.bill.create",
    ("erp", "get_bill"): "qb.bill.get",
    ("erp", "create_invoice"): "qb.invoice.create",
    ("erp", "get_invoice"): "qb.invoice.get",
    ("erp", "list_invoices"): "qb.invoice.list",
    ("erp", "create_payment"): "qb.payment.create",
    ("erp", "get_account"): "qb.account.get",
    ("erp", "list_accounts"): "qb.account.list",
    ("erp", "get_report"): "qb.report.profit_loss",
    ("erp", "create_customer"): "qb.customer.create",
    ("erp", "get_customer"): "qb.customer.get",
    ("erp", "list_customers"): "qb.customer.list",
    # === Stripe (stripe.*) ===
    ("stripe", "create_payment"): "stripe.payment.create",
    ("stripe", "create_customer"): "stripe.customer.create",
    ("stripe", "get_customer"): "stripe.customer.get",
    ("stripe", "refund"): "stripe.refund.create",
    ("stripe", "get_balance"): "stripe.balance.get",
    ("stripe", "create_invoice"): "stripe.invoice.create",
    ("stripe", "create_subscription"): "stripe.subscription.create",
    ("stripe", "list_payouts"): "stripe.payout.list",
    # === Bill.com (billcom.*) ===
    ("billcom", "create_bill"): "billcom.bill.create",
    ("billcom", "send_payment"): "billcom.payment.send",
    ("billcom", "approve_bill"): "billcom.bill.approve",
    ("billcom", "create_vendor"): "billcom.vendor.create",
    # === NetSuite (netsuite.*) ===
    ("netsuite", "query"): "netsuite.query",
    ("netsuite", "create_journal"): "netsuite.journal.create",
    ("netsuite", "create_vendor"): "netsuite.vendor.create",
    ("netsuite", "create_bill"): "netsuite.bill.create",
    # === Banking ===
    ("bank", "process_payment"): "qb.payment.create",
    ("bank", "reconcile_account"): "qb.query",
    ("bank", "get_balance"): "plaid.balance.get",
    ("bank", "list_transactions"): "plaid.transaction.list",
    ("bank", "initiate_transfer"): "mercury.transfer.create",
    # === Documents / OCR ===
    ("documents", "extract_data"): "ocr.extract",
    ("documents", "validate_document"): "ocr.validate",
    ("documents", "upload"): "gdrive.file.upload",
    ("documents", "download"): "gdrive.file.download",
    ("documents", "list"): "gdrive.file.list",
    # === Email (Gmail) ===
    ("email", "send_notification"): "gmail.send",
    ("email", "send"): "gmail.send",
    ("email", "read"): "gmail.read",
    ("email", "draft"): "gmail.draft",
    # === Slack ===
    ("slack", "send_message"): "slack.message.send",
    ("slack", "send_dm"): "slack.message.direct",
    ("slack", "upload_file"): "slack.file.upload",
    ("slack", "create_channel"): "slack.channel.create",
    # === CRM (HubSpot) ===
    ("crm", "create_contact"): "hubspot.contact.create",
    ("crm", "get_contact"): "hubspot.contact.get",
    ("crm", "update_contact"): "hubspot.contact.update",
    ("crm", "create_deal"): "hubspot.deal.create",
    ("crm", "create_company"): "hubspot.company.create",
    # === Project Management ===
    ("linear", "create_issue"): "linear.issue.create",
    ("asana", "create_task"): "asana.task.create",
    ("clickup", "create_task"): "clickup.task.create",
    ("notion", "create_page"): "notion.page.create",
    # === Workflow (internal) ===
    ("workflow", "approve_transaction"): "qb.payment.create",
    ("workflow", "escalate_issue"): "slack.message.send",
    ("workflow", "query_records"): "qb.query",
    # === Browser Automation ===
    ("browser", "navigate"): "browser.navigate",
    ("browser", "click"): "browser.click",
    ("browser", "fill_form"): "browser.fill_form",
    ("browser", "extract_data"): "browser.extract_data",
    ("browser", "extract_table"): "browser.extract_table",
    ("browser", "login"): "browser.login_with_credentials",
}


def map_work_unit_to_capability(tool: str, verb: str) -> str:
    """
    Map a Baby MARS work unit to a Stargate capability key.

    Args:
        tool: The tool category (erp, bank, email, etc.)
        verb: The action verb (create_record, send, etc.)

    Returns:
        Stargate capability key (always returns something)
    """
    key = (tool.lower(), verb.lower())

    if key in CAPABILITY_MAP:
        return CAPABILITY_MAP[key]

    # Construct capability from tool.verb pattern
    return f"{tool.lower()}.{verb.lower()}"
