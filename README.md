# Invoice Generator

Professional CLI tool for generating HTML invoices and timesheets from JSON data, with per-client YAML configuration.

## Installation

```bash
pip install -e .          # Core (HTML generation)
pip install -e ".[pdf]"   # With PDF support (requires Playwright)
pip install -e ".[dev]"   # With test dependencies
```

For PDF generation, also install the Chromium browser:

```bash
playwright install chromium
```

## CLI Usage

```bash
# Generate an invoice
invoicegen invoice data.json -o invoice.html
invoicegen invoice data.json -o invoice.html --pdf
invoicegen invoice data.json --client example

# Generate a timesheet
invoicegen timesheet data.json -o timesheet.html
invoicegen timesheet data.json --view period --header-layout three-column

# Convert HTML to PDF
invoicegen pdf invoice.html -o invoice.pdf

# Manage clients
invoicegen client list
invoicegen client show example
invoicegen client init new_client
```

You can also run via `python -m invoice_generator`.

## Client Configuration

Clients are stored as YAML files in `clients/<name>/client.yaml`:

```yaml
name: Acme Corp
company: Acme
contact: Jane Smith
email: jane@acme.com
address:
  - "123 Business St"
  - "Dublin, Ireland"
currency: EUR
currency_symbol: "\u20AC"
daily_rate: 815.00
payment_terms_days: 30
payment_details:
  Bank: Example Bank
  IBAN: IE00XXXX
  BIC: XXXX
  Reference: Please use invoice number
```

When `--client NAME` is passed, values from the client config are used as defaults for fields not present in the input JSON.

## Invoice JSON Format

```json
{
  "invoice_number": "INV-001",
  "invoice_date": "2025-01-15",
  "due_date": "2025-02-14",
  "company_name": "Your Company",
  "company_email": "billing@company.com",
  "company_address": ["123 Street", "City, Country"],
  "customer_name": "Client Name",
  "customer_address": ["456 Avenue", "City, Country"],
  "currency": "EUR",
  "currency_symbol": "\u20ac",
  "items": [
    {
      "description": "Development work",
      "quantity": 5,
      "unit_price": 815.00
    }
  ],
  "payment_details": {
    "Bank": "Bank Name",
    "IBAN": "IE00XXXX"
  },
  "notes": "Payment terms: 30 days"
}
```

## Timesheet JSON Format

```json
{
  "employee_name": "Jane Developer",
  "period_start": "2025-01-06",
  "period_end": "2025-01-17",
  "entries": [
    {
      "date": "2025-01-06",
      "description": "API implementation",
      "project": "Project Alpha",
      "hours": 8.0
    }
  ]
}
```

### View modes

- `day` (default) - Entries grouped by day with task details
- `period` - Flat table with project breakdown summary

### Header layouts

`default`, `three-column`, `logo-left`, `split`

## Running Tests

```bash
pytest tests/ -v
```
