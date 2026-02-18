"""
HTML Template for Invoice Generation - Standard layout only
Adapted for browser use via PyScript.
"""

TEMPLATE_STANDARD = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice - {{invoice_number}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            color: #333;
            line-height: 1.4;
            background-color: #f5f5f5;
        }

        .invoice-container {
            max-width: 800px;
            margin: 10px auto;
            background: white;
            padding: 25px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }

        .invoice-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }

        .invoice-title h1 {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .invoice-details {
            font-size: 12px;
        }

        .invoice-details div {
            margin-bottom: 2px;
        }

        .invoice-details strong {
            display: inline-block;
            width: 100px;
        }

        .company-info {
            text-align: right;
        }

        .company-logo {
            max-width: 150px;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
            margin-bottom: 5px;
            display: block;
            margin-left: auto;
        }

        .company-name {
            font-size: 16px;
            color: #6b7280;
            margin-bottom: 2px;
        }

        .billing-section {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 20px;
        }

        .billing-section h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .billing-section p {
            font-size: 12px;
            margin-bottom: 2px;
        }

        .payment-summary-section {
            display: grid;
            grid-template-columns: 1fr 280px;
            gap: 30px;
            align-items: start;
            margin-bottom: 25px;
        }

        .payment-details {
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 6px;
        }

        .payment-details h3 {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
        }

        .payment-grid {
            display: grid;
            grid-template-columns: 100px 1fr;
            gap: 6px;
            font-size: 12px;
        }

        .payment-grid strong {
            font-weight: 500;
        }

        .summary-box {
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 6px;
        }

        .summary-row {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 12px;
        }

        .summary-row.total {
            font-size: 14px;
            font-weight: 600;
            border-top: 2px solid #e5e7eb;
            margin-top: 8px;
            padding-top: 10px;
        }

        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        .items-table th {
            text-align: left;
            padding: 8px;
            border-bottom: 2px solid #e5e7eb;
            font-weight: 600;
            font-size: 12px;
        }

        .items-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 12px;
        }

        .items-table th:nth-child(2),
        .items-table td:nth-child(2) {
            text-align: center;
            width: 50px;
        }

        .items-table th:nth-child(3),
        .items-table td:nth-child(3),
        .items-table th:nth-child(4),
        .items-table td:nth-child(4),
        .items-table th:nth-child(5),
        .items-table td:nth-child(5),
        .items-table th:nth-child(6),
        .items-table td:nth-child(6) {
            text-align: right;
        }

        .due-section {
            text-align: center;
            padding: 15px;
            background-color: #f9fafb;
            border-radius: 6px;
            margin-top: 15px;
        }

        .due-amount {
            font-size: 18px;
            font-weight: 600;
            display: inline-block;
            margin-right: 20px;
        }

        .pay-button {
            background-color: #0891b2;
            color: white;
            padding: 8px 20px;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: background-color 0.2s;
            display: inline-block;
        }

        .pay-button:hover {
            background-color: #0e7490;
        }

        .notes-section {
            margin-top: 15px;
            padding-top: 10px;
            border-top: 1px solid #e5e7eb;
        }

        .notes-section h3 {
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 5px;
            color: #6b7280;
        }

        @media print {
            body {
                background-color: white;
            }

            .invoice-container {
                box-shadow: none;
                margin: 0;
                padding: 15px;
            }

            .pay-button {
                display: none;
            }

            .due-section {
                background-color: transparent;
                border: 1px solid #e5e7eb;
            }
        }
    </style>
</head>
<body>
    <div class="invoice-container">
        <div class="invoice-header">
            <div class="invoice-title">
                <h1>Invoice</h1>
                <div class="invoice-details">
                    <div><strong>Invoice number</strong> {{invoice_number}}</div>
                    <div><strong>Invoice date</strong> {{invoice_date}}</div>
                    <div><strong>Due date</strong> {{due_date}}</div>
                    <div><strong>Supply date</strong> {{supply_date}}</div>
                </div>
            </div>
            <div class="company-info">
                <img src="{{company_logo}}" alt="Company Logo" class="company-logo">
                <div class="company-name">{{company_name}}</div>
            </div>
        </div>

        <div class="billing-section">
            <div>
                <h3>Billed to</h3>
                <p><strong>{{customer_name}}</strong></p>
                {{customer_contact_line}}
                {{customer_address}}
                <p>{{customer_email}}</p>
                {{customer_website_line}}
            </div>
            <div>
                <h3>{{company_name}}</h3>
                {{company_address}}
                <p style="margin-top: 8px;">{{company_email}}</p>
                <p>Company no: {{company_number}}</p>
                <p>{{company_vat_label}}: {{company_vat}}</p>
            </div>
        </div>

        <div class="payment-summary-section">
            <div class="payment-details">
                <h3>Payment details</h3>
                <div class="payment-grid">
                    {{payment_details}}
                </div>
            </div>

            <div class="summary-box">
                <div class="summary-row">
                    <span>Subtotal</span>
                    <span>{{currency_symbol}} {{subtotal}}</span>
                </div>
                <div class="summary-row" style="font-size: 10px; color: #6b7280;">
                    <span>including discount</span>
                    <span></span>
                </div>
                <div class="summary-row">
                    <span>Tax</span>
                    <span>{{currency_symbol}} {{tax}}</span>
                </div>
                <div class="summary-row total">
                    <span>Total</span>
                    <span>{{currency_symbol}} {{total}}</span>
                </div>
            </div>
        </div>

        <table class="items-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Qty</th>
                    <th>Unit price ({{currency}})</th>
                    <th>Tax</th>
                    <th>Discount</th>
                    <th>Total ({{currency}})</th>
                </tr>
            </thead>
            <tbody>
                {{items_rows}}
            </tbody>
            <tfoot style="border-top: 2px solid #333;">
                <tr>
                    <td style="font-weight: 700; padding-top: 12px;">TOTAL DAYS</td>
                    <td style="font-weight: 700; text-align: center; padding-top: 12px;">{{total_days}}</td>
                    <td style="padding-top: 12px;"></td>
                    <td style="padding-top: 12px;"></td>
                    <td style="padding-top: 12px;"></td>
                    <td style="font-weight: 700; padding-top: 12px;">{{currency_symbol}} {{subtotal}}</td>
                </tr>
            </tfoot>
        </table>

        <div class="due-section">
            <div class="due-amount">{{currency_symbol}} {{total}} due {{due_date}}</div>
            <button class="pay-button">Pay invoice online</button>
        </div>

        <div class="notes-section">
            <h3>Notes</h3>
            {{notes}}
        </div>
    </div>
</body>
</html>"""
