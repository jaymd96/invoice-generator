import copy

from invoice_generator.invoice import InvoiceGenerator


class TestInvoiceGenerator:
    def test_generate_returns_html(self, sample_invoice_data):
        gen = InvoiceGenerator()
        html = gen.generate(sample_invoice_data)
        assert "<!DOCTYPE html>" in html
        assert "TEST-001" in html

    def test_currency_formatting(self):
        assert InvoiceGenerator.format_currency(7335.00) == "7,335.00"
        assert InvoiceGenerator.format_currency(0) == "0.00"
        assert InvoiceGenerator.format_currency(1234567.89) == "1,234,567.89"

    def test_address_formatting(self):
        lines = ["123 Test St", "Dublin, Ireland"]
        html = InvoiceGenerator.format_address(lines)
        assert "<p>123 Test St</p>" in html
        assert "<p>Dublin, Ireland</p>" in html

    def test_simple_address(self):
        lines = ["123 Test St", "Suite 4", "Dublin, Ireland"]
        result = InvoiceGenerator.format_simple_address(lines)
        assert result == "123 Test St, Dublin, Ireland"

    def test_auto_calculates_totals(self, sample_invoice_data):
        data = copy.deepcopy(sample_invoice_data)
        del data['subtotal']
        del data['tax']
        del data['total']
        for item in data['items']:
            del item['total']

        gen = InvoiceGenerator()
        html = gen.generate(data)
        assert "7,335.00" in html

    def test_default_currency_symbol(self):
        data = {
            'invoice_number': 'X-001',
            'invoice_date': '2025-01-01',
            'company_name': 'Co',
            'company_email': 'a@b.com',
            'company_address': ['Addr'],
            'customer_name': 'Client',
            'items': [{'description': 'Work', 'quantity': 1, 'unit_price': 100}],
        }
        gen = InvoiceGenerator()
        html = gen.generate(data)
        # Default currency symbol is pound sign
        assert '\u00a3' in html

    def test_payment_details_in_html(self, sample_invoice_data):
        gen = InvoiceGenerator()
        html = gen.generate(sample_invoice_data)
        assert "Test Bank" in html
        assert "IE00TEST000000000000" in html

    def test_notes_in_html(self, sample_invoice_data):
        gen = InvoiceGenerator()
        html = gen.generate(sample_invoice_data)
        assert "Reverse charge" in html

    def test_save_creates_file(self, sample_invoice_data, tmp_path):
        gen = InvoiceGenerator()
        html = gen.generate(sample_invoice_data)
        out = tmp_path / "sub" / "test.html"
        gen.save(html, str(out))
        assert out.exists()
        assert "TEST-001" in out.read_text()
