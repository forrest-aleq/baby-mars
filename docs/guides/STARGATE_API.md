# Stargate API Reference

**Version:** 2.0
**Last Updated:** December 2025
**Status:** Production Ready

---

## Overview

Stargate is the execution layer for Aleq. It provides a unified capability-based API for executing actions across multiple services.

**Base URL:** `http://localhost:8001`
**Auth:** `X-API-Key` header required on all endpoints (except `/health`)

---

## Core Endpoints

### Health Check

```
GET /health
```

No auth required.

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-26T12:00:00"
}
```

### List Capabilities

```
GET /api/v1/capabilities
```

Returns all registered capabilities grouped by service.

```json
{
  "capabilities": {
    "recurly.payment.apply": {
      "tool_name": "recurly.apply_payment",
      "description": "Apply external payment to invoice",
      "service": "recurly",
      "requires_oauth": false
    }
  },
  "count": 366
}
```

### Check Credential Status

```
POST /api/v1/credentials/status
```

Check if credentials exist before executing.

**Request:**
```json
{
  "org_id": "dockwa",
  "user_id": "maria",
  "capability_key": "recurly.payment.apply"
}
```

**Response:**
```json
{
  "credential_available": true,
  "credential_type": "customer",
  "requires_setup": false
}
```

### Execute Capability

```
POST /api/v1/execute
```

Execute any capability.

**Request:**
```json
{
  "capability_key": "recurly.payment.apply",
  "org_id": "dockwa",
  "user_id": "maria",
  "args": {
    "invoice_id": "inv_abc123",
    "amount": 875.00,
    "payment_method": "check"
  }
}
```

**Success Response:**
```json
{
  "status": "success",
  "capability_key": "recurly.payment.apply",
  "tool_used": "recurly.apply_payment",
  "outputs": {
    "invoice_id": "inv_abc123",
    "state": "paid",
    "amount_applied": 875.00
  },
  "timestamp": "2025-12-26T12:00:00"
}
```

**Error Response:**
```json
{
  "status": "error",
  "error_code": "CREDENTIAL_MISSING",
  "error_message": "No credentials found for recurly",
  "retry_strategy": "human_intervention"
}
```

---

## Error Codes

| Code | Retry Strategy | Meaning |
|------|---------------|---------|
| `CREDENTIAL_MISSING` | `human_intervention` | User needs to connect service |
| `CREDENTIAL_INVALID` | `human_intervention` | Token expired/revoked |
| `RATE_LIMIT` | `backoff` | API rate limit hit |
| `VALIDATION_ERROR` | `none` | Invalid input |
| `NOT_FOUND` | `none` | Resource doesn't exist |
| `EXTERNAL_API_ERROR` | `backoff` | External service error |

---

## Production Ready Services

### Utilities (No Credentials)

| Service | Capabilities | Required |
|---------|-------------|----------|
| **Financial Calculator** | 6 | Nothing |
| **Summarizer** | 5 | `ANTHROPIC_API_KEY` |
| **Web Search** | 4 | `TAVILY_API_KEY` |
| **OCR (Gemini)** | 2 | `GOOGLE_AI_API_KEY` |

### API Key Services

| Service | Capabilities | Required |
|---------|-------------|----------|
| **Stripe** | 61 | `STRIPE_SECRET_KEY` |
| **Recurly** | 12 | `RECURLY_API_KEY` |
| **Plaid** | 11 | `PLAID_CLIENT_ID`, `PLAID_SECRET` |

### OAuth Services

| Service | Capabilities | OAuth Flow |
|---------|-------------|------------|
| **QuickBooks** | 45 | `/oauth/quickbooks/callback` |
| **NetSuite** | 15 | Token-based auth |
| **Gmail** | 25 | `/oauth/google/callback` |
| **Slack** | 6 | `/oauth/slack/callback` |
| **HubSpot** | 4 | `/oauth/hubspot/callback` |
| **Bill.com** | 9 | `/oauth/billcom/callback` |

**Total Production Ready: 200 capabilities**

---

## Capability Reference

### Financial Calculator

Pure Python. No credentials needed.

| Capability | Description |
|------------|-------------|
| `financial.npv` | Net Present Value calculation |
| `financial.irr` | Internal Rate of Return |
| `financial.loan.amortization` | Loan amortization schedule |
| `financial.depreciation` | Asset depreciation (straight-line, declining) |
| `financial.currency.convert` | Currency conversion |
| `financial.ratios` | Financial ratios (current, quick, debt-to-equity) |

**Example:**
```json
{
  "capability_key": "financial.npv",
  "org_id": "any",
  "user_id": "any",
  "args": {
    "rate": 0.10,
    "cash_flows": [-1000, 300, 400, 500, 600]
  }
}
```

### OCR (Gemini Flash)

Requires `GOOGLE_AI_API_KEY`.

| Capability | Description |
|------------|-------------|
| `ocr.gemini.extract` | Extract structured data from any document |
| `ocr.gemini.tables` | Extract tables from documents |

**Example:**
```json
{
  "capability_key": "ocr.gemini.extract",
  "org_id": "dockwa",
  "user_id": "maria",
  "args": {
    "file_content": "<base64-encoded-pdf>",
    "file_type": "pdf",
    "extraction_prompt": "Extract all check payments with amount, payer, and invoice references"
  }
}
```

### Recurly (Subscription Billing)

Requires `RECURLY_API_KEY`.

| Capability | Description |
|------------|-------------|
| `recurly.account.create` | Create customer account |
| `recurly.subscription.create` | Create subscription |
| `recurly.subscription.cancel` | Cancel subscription |
| `recurly.subscription.pause` | Pause subscription |
| `recurly.subscription.resume` | Resume subscription |
| `recurly.subscription.list` | List subscriptions |
| `recurly.invoice.list` | List invoices |
| `recurly.invoice.get` | Get invoice details |
| `recurly.invoice.search` | Search invoices by account/number |
| `recurly.invoice.collect` | Force collect payment |
| `recurly.payment.apply` | Apply external payment (check/wire) |
| `recurly.plan.create` | Create subscription plan |

**Lockbox Example:**
```json
{
  "capability_key": "recurly.payment.apply",
  "org_id": "dockwa",
  "user_id": "system",
  "args": {
    "invoice_id": "inv_abc123",
    "amount": 2850.00,
    "payment_method": "check",
    "description": "Check #4521"
  }
}
```

### Stripe (Payments)

Requires `STRIPE_SECRET_KEY`. 61 capabilities covering:

- Payment intents, charges, refunds
- Customers, subscriptions, invoices
- Payouts, transfers, balance
- Connect accounts
- Payment methods, sources

### QuickBooks (Accounting)

OAuth required. 45 capabilities covering:

- Vendors, customers, employees
- Invoices, bills, payments
- Journal entries, accounts
- Reports (P&L, Balance Sheet, AR Aging)

### NetSuite (ERP)

Token auth required. 15 capabilities covering:

- Vendors, customers
- Journal entries
- Vendor bills
- SuiteQL queries

### Plaid (Banking)

Requires `PLAID_CLIENT_ID` + `PLAID_SECRET`. 11 capabilities:

| Capability | Description |
|------------|-------------|
| `plaid.link.create` | Create link token for UI |
| `plaid.token.exchange` | Exchange public token |
| `plaid.accounts.get` | Get linked accounts |
| `plaid.balance.get` | Get account balances |
| `plaid.transactions.get` | Get transactions |
| `plaid.transactions.sync` | Sync new transactions |
| `plaid.identity.get` | Get account holder identity |
| `plaid.institution.get` | Get institution details |

### Gmail

OAuth required. Key capabilities:

| Capability | Description |
|------------|-------------|
| `email.send` | Send email |
| `email.read` | Read emails (with query) |
| `email.search` | Search emails |
| `email.attachment.get` | Get attachment content |

### Slack

OAuth required.

| Capability | Description |
|------------|-------------|
| `slack.message.send` | Send to channel |
| `slack.message.direct` | Send DM |
| `slack.channel.list` | List channels |
| `slack.user.list` | List users |

---

## Multi-Tenant Credentials

Credentials are stored per org/user/service:

```
Composite Key: {org_id}:{user_id}:{service}
```

### Credential Types

- **customer**: Per-user OAuth (QuickBooks, Gmail)
- **agent**: System-wide credential (Aleq's Gmail for sending)
- **null**: No credential needed (Financial Calculator)

### Storing Credentials

```python
from app.database import CredentialManager

CredentialManager.store_credential(
    org_id="dockwa",
    user_id="maria",
    service="quickbooks",
    access_token="eyJ...",
    refresh_token="1//...",
    token_expiry=datetime(2025, 12, 27),
    realm_id="9130123456789"
)
```

---

## Integration Pattern

### From MARS (The Brain)

```python
# 1. Check if credentials exist
status = stargate.post("/api/v1/credentials/status", {
    "org_id": org_id,
    "user_id": user_id,
    "capability_key": "recurly.payment.apply"
})

if not status["credential_available"]:
    # Surface to user: "Please connect Recurly"
    return checkpoint_for_human()

# 2. Execute
result = stargate.post("/api/v1/execute", {
    "capability_key": "recurly.payment.apply",
    "org_id": org_id,
    "user_id": user_id,
    "args": {
        "invoice_id": invoice_id,
        "amount": amount,
        "payment_method": "check"
    }
})

# 3. Handle result
if result["status"] == "success":
    return result["outputs"]
else:
    if result["retry_strategy"] == "backoff":
        return retry_with_backoff()
    else:
        return surface_error_to_user(result["error_message"])
```

---

## NOT Production Ready

These are registered but incomplete:

| Service | Issue |
|---------|-------|
| Hyperbrowser | All methods raise `NotImplementedError` |
| OCR (deepdoctection) | Table extraction incomplete |
| Power BI | Requires browser automation |
| Chase | Enterprise OAuth complexity |
| IBKR/Schwab | Complex broker APIs |

---

## Quick Start

```bash
# 1. Start server
source venv/bin/activate
python -m uvicorn app.main:app --reload --port 8001

# 2. Check health
curl http://localhost:8001/health

# 3. List capabilities
curl -H "X-API-Key: your-key" http://localhost:8001/api/v1/capabilities

# 4. Execute (example: NPV calculation)
curl -X POST http://localhost:8001/api/v1/execute \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "capability_key": "financial.npv",
    "org_id": "test",
    "user_id": "test",
    "args": {
      "rate": 0.10,
      "cash_flows": [-1000, 300, 400, 500, 600]
    }
  }'
```
