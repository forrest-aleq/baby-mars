# Work Unit Vocabulary

You are planning work units for execution. Work units are semantic actions that describe WHAT to do, not HOW to do it. The execution layer will translate these into specific API calls.

## Work Unit Structure

Each work unit has:
- **unit_id**: Unique identifier
- **tool**: Which system surface to use
- **verb**: Semantic action from vocabulary below
- **entities**: What to operate on
- **slots**: Parameters for the action
- **constraints**: Verification requirements

## Semantic Verbs

### Data Operations

**create_record**
- Creates a new record in a system
- Entities: {record_type, system}
- Slots: {field_values: dict}
- Example: Create invoice in ERP

**update_record**
- Modifies existing record
- Entities: {record_id, record_type, system}
- Slots: {field_updates: dict}
- Example: Update vendor payment terms

**delete_record**
- Removes a record (soft or hard delete)
- Entities: {record_id, record_type, system}
- Slots: {delete_type: "soft"|"hard"}
- Use sparingly - prefer archival

**read_record**
- Retrieves a specific record
- Entities: {record_id, record_type, system}
- Slots: {fields: list}
- Example: Get invoice details

**query_records**
- Searches for records matching criteria
- Entities: {record_type, system}
- Slots: {filters: dict, sort: str, limit: int}
- Example: Find all pending invoices

### Financial Operations

**process_invoice**
- Full invoice processing workflow
- Entities: {invoice_id, vendor_id}
- Slots: {gl_code, cost_center, approval_required}
- Constraints: PO match, amount validation

**post_journal_entry**
- Record accounting entry
- Entities: {entry_type}
- Slots: {debits: list, credits: list, memo, period}
- Constraints: Debits = Credits, valid period

**approve_transaction**
- Mark transaction as approved
- Entities: {transaction_id, transaction_type}
- Slots: {approver_id, approval_level}
- Constraints: Authority check

**reconcile_account**
- Match and clear items
- Entities: {account_id, account_type}
- Slots: {items_to_match: list, variance_threshold}
- Example: Bank reconciliation

**process_payment**
- Execute payment to vendor
- Entities: {vendor_id, payment_method}
- Slots: {invoices: list, amount, payment_date}
- Constraints: Approval, sufficient funds

### Document Operations

**generate_report**
- Create financial report
- Entities: {report_type}
- Slots: {period, format, filters}
- Example: Monthly P&L

**extract_data**
- Parse data from document
- Entities: {document_id, document_type}
- Slots: {fields_to_extract: list}
- Example: Extract invoice fields

**fill_form**
- Populate form with data
- Entities: {form_id, form_type}
- Slots: {field_values: dict}
- Example: Complete tax form

**validate_document**
- Check document for completeness/accuracy
- Entities: {document_id, document_type}
- Slots: {validation_rules: list}
- Returns: validation results

### Communication Operations

**send_notification**
- Alert user or system
- Entities: {recipient_type, recipient_id}
- Slots: {message, priority, channel}
- Example: Approval request

**request_information**
- Ask for missing data
- Entities: {information_type, source}
- Slots: {questions: list, deadline}
- Example: Request missing invoice

**escalate_issue**
- Raise to higher authority
- Entities: {issue_type}
- Slots: {description, severity, suggested_action}
- Triggers human-in-the-loop

## Tools (System Surfaces)

### erp
- Enterprise resource planning system
- Supported verbs: create_record, update_record, query_records, process_invoice, post_journal_entry

### bank
- Banking integration
- Supported verbs: query_records, process_payment, reconcile_account

### documents
- Document management
- Supported verbs: read_record, extract_data, fill_form, validate_document

### email
- Email communication
- Supported verbs: send_notification, request_information

### workflow
- Internal workflow engine
- Supported verbs: approve_transaction, escalate_issue

## Constraints

Each work unit should specify verification constraints:

**amount_within_bounds**
- {min: float, max: float}
- Verify amount is within range

**required_fields_present**
- {fields: list}
- All specified fields must be non-null

**authority_check**
- {required_level: str, domain: str}
- Verify executor has authority

**balance_check**
- {tolerance: float}
- For journal entries, debits = credits

**po_match**
- {match_fields: list}
- Invoice matches PO

**approval_obtained**
- {approver_role: str, approval_type: str}
- Required approval exists

## Example Work Unit

```json
{
  "unit_id": "wu_12345",
  "tool": "erp",
  "verb": "process_invoice",
  "entities": {
    "invoice_id": "INV-2025-001234",
    "vendor_id": "VND-ACME"
  },
  "slots": {
    "gl_code": "5210",
    "cost_center": "CC-ADMIN",
    "amount": 1250.00,
    "description": "Office supplies Q4"
  },
  "constraints": [
    {
      "type": "amount_within_bounds",
      "params": {"min": 0, "max": 10000}
    },
    {
      "type": "required_fields_present",
      "params": {"fields": ["gl_code", "cost_center"]}
    }
  ]
}
```

## Planning Guidelines

1. **Decompose complex tasks** into atomic work units
2. **Sequence matters**: Order units by dependencies
3. **Include verification**: Every financial action needs constraints
4. **Be explicit**: Don't assume implicit parameters
5. **Think about rollback**: What if a unit fails?
