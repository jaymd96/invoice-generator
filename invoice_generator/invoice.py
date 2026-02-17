#!/usr/bin/env python3
"""
Professional Invoice Generator - Standard template
"""

import json
from pathlib import Path
from typing import Dict, List, Any

from .templates import TEMPLATE_STANDARD


class InvoiceGenerator:
    """Generate professional HTML invoices from JSON data"""

    def __init__(self):
        self.template_html = TEMPLATE_STANDARD

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format number as currency with commas"""
        return "{:,.2f}".format(amount)

    @staticmethod
    def format_address(address_lines: List[str]) -> str:
        """Convert address lines to HTML paragraphs"""
        return '\n'.join(f'<p>{line}</p>' for line in address_lines)

    @staticmethod
    def format_simple_address(address_lines: List[str]) -> str:
        """Convert address to simple comma-separated format"""
        if len(address_lines) >= 2:
            return f"{address_lines[0]}, {address_lines[-1]}"
        return address_lines[0] if address_lines else ""

    def format_items(self, items: List[Dict], currency_symbol: str) -> str:
        """Convert items list to HTML table rows"""
        rows = []
        for item in items:
            sub_desc = ''
            if 'sub_description' in item and item['sub_description']:
                sub_desc = f'<br><span style="font-size: 10px; color: #6b7280;">{item["sub_description"]}</span>'

            row = f"""<tr>
                    <td>{item['description']}{sub_desc}</td>
                    <td>{item['quantity']}</td>
                    <td>{currency_symbol} {self.format_currency(item['unit_price'])}</td>
                    <td>{item.get('tax', '')}</td>
                    <td>{item.get('discount', '')}</td>
                    <td>{currency_symbol} {self.format_currency(item['total'])}</td>
                </tr>"""
            rows.append(row)

        return '\n                '.join(rows)

    @staticmethod
    def format_payment_details(details: Dict[str, str]) -> str:
        """Convert payment details dict to HTML grid"""
        rows = []
        for key, value in details.items():
            row = f'<strong>{key}</strong><span>{value}</span>'
            rows.append(row)
        return '\n                    '.join(rows)

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate HTML invoice from JSON data"""
        # Calculate item totals if not provided
        for item in data['items']:
            if 'total' not in item:
                item['total'] = item.get('quantity', 1) * item.get('unit_price', 0)

        # Validate and calculate totals if not provided
        if 'subtotal' not in data:
            data['subtotal'] = sum(item['total'] for item in data['items'])

        if 'tax' not in data:
            data['tax'] = 0  # Default 0% tax for reverse charge

        if 'total' not in data:
            data['total'] = data['subtotal'] + data['tax']

        # Calculate total days
        total_days = sum(item.get('quantity', 1) for item in data['items'])

        # Determine tax rate display
        tax_rate = "0% VAT" if data['tax'] == 0 else "20% VAT"

        # Format customer contact and website if provided
        customer_contact_line = ''
        if 'customer_contact' in data:
            customer_contact_line = f'<p style="font-weight: 600;">Attn: {data["customer_contact"]}</p>'

        customer_website_line = ''
        if 'customer_website' in data:
            customer_website_line = f'<p style="margin-top: 3px;"><a href="{data["customer_website"]}" style="color: #0891b2; text-decoration: none;">{data["customer_website"]}</a></p>'

        currency_symbol = data.get('currency_symbol', '\u00a3')
        for item in data['items']:
            if 'currency_symbol' not in item:
                item['currency_symbol'] = currency_symbol
            if 'total' not in item:
                item['total'] = item['quantity'] * item['unit_price']

        # Format complex fields
        replacements = {
            'invoice_number': data['invoice_number'],
            'invoice_date': data['invoice_date'],
            'due_date': data.get('due_date', ''),
            'supply_date': data.get('supply_date', data['invoice_date']),
            'company_logo': data.get('company_logo', ''),
            'company_name': data['company_name'],
            'company_email': data['company_email'],
            'company_number': data.get('company_number', ''),
            'company_vat_label': data.get('company_vat_label', 'VAT'),
            'company_vat': data.get('company_vat', ''),
            'customer_name': data['customer_name'],
            'customer_contact_line': customer_contact_line,
            'customer_website_line': customer_website_line,
            'customer_email': data.get('customer_email', ''),
            'currency': data.get('currency', 'GBP'),
            'currency_symbol': currency_symbol,
            'customer_address': self.format_address(data.get('customer_address', [])),
            'company_address': self.format_address(data['company_address']),
            'company_simple_address': self.format_simple_address(data['company_address']),
            'items_rows': self.format_items(data['items'], currency_symbol),
            'payment_details': self.format_payment_details(data.get('payment_details', {})),
            'subtotal': self.format_currency(data['subtotal']),
            'tax': self.format_currency(data['tax']),
            'tax_rate': tax_rate,
            'total': self.format_currency(data['total']),
            'total_days': total_days,
            'notes': data.get('notes', '')
        }

        # Replace placeholders
        html = self.template_html
        for key, value in replacements.items():
            html = html.replace('{{' + key + '}}', str(value))

        return html

    def generate_from_file(self, json_file: str) -> str:
        """Generate invoice from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        return self.generate(data)

    def save(self, html: str, output_file: str):
        """Save generated HTML to file"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html)
