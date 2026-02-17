#!/usr/bin/env python3
"""
Unified CLI for invoice generation with subcommands
"""

import sys
import json
import argparse
from pathlib import Path

from .invoice import InvoiceGenerator
from .timesheet import TimesheetGenerator, VALID_VIEWS, VALID_HEADER_LAYOUTS, validate_data
from .pdf import PDFConverter
from .client import load_client, init_client, list_clients


def _read_json(path: str) -> dict:
    """Read JSON from file path"""
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON - {e}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write(f"Error: File not found - {path}\n")
        sys.exit(1)


def _resolve_output(args, default_name: str, client_name: str = None,
                    clients_dir: str = "clients") -> str | None:
    """Resolve output path from args, client config, or None for stdout"""
    if hasattr(args, 'output') and args.output:
        return args.output
    if hasattr(args, 'output_dir') and args.output_dir:
        return str(Path(args.output_dir) / default_name)
    if client_name:
        return str(Path(clients_dir) / client_name / "invoices" / default_name)
    return None


def cmd_invoice(args):
    """Handle `invoicegen invoice` subcommand"""
    data = _read_json(args.input)

    clients_dir = getattr(args, 'clients_dir', 'clients')
    if args.client:
        client = load_client(args.client, clients_dir)
        # Populate defaults from client config that aren't in the JSON
        if 'currency' not in data:
            data['currency'] = client.currency
        if 'currency_symbol' not in data:
            data['currency_symbol'] = client.currency_symbol
        if 'payment_details' not in data:
            data['payment_details'] = client.payment_details

    generator = InvoiceGenerator()
    html = generator.generate(data)

    output = _resolve_output(
        args,
        Path(args.input).stem + '.html',
        args.client,
        clients_dir,
    )

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        generator.save(html, output)
        print(f"Invoice generated: {output}")

        if args.pdf:
            converter = PDFConverter()
            pdf_path = converter.convert(output)
            print(f"PDF generated: {pdf_path}")
    else:
        sys.stdout.write(html)


def cmd_timesheet(args):
    """Handle `invoicegen timesheet` subcommand"""
    data = _read_json(args.input)

    clients_dir = getattr(args, 'clients_dir', 'clients')
    if args.client:
        client = load_client(args.client, clients_dir)
        if 'currency' not in data:
            data['currency'] = client.currency
        if 'currency_symbol' not in data:
            data['currency_symbol'] = client.currency_symbol

    generator = TimesheetGenerator(view=args.view, header_layout=args.header_layout)
    html = generator.generate(data)

    output = _resolve_output(
        args,
        Path(args.input).stem + '.html',
        args.client,
        clients_dir,
    )

    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        generator.save(html, output)
        print(f"Timesheet generated: {output}")

        if args.pdf:
            converter = PDFConverter()
            pdf_path = converter.convert(output)
            print(f"PDF generated: {pdf_path}")
    else:
        sys.stdout.write(html)


def cmd_pdf(args):
    """Handle `invoicegen pdf` subcommand"""
    margins = {
        'top': args.margin_top,
        'right': args.margin_right,
        'bottom': args.margin_bottom,
        'left': args.margin_left,
    }
    converter = PDFConverter(margins=margins)

    if args.output:
        pdf_path = converter.convert(args.input, args.output)
        print(f"PDF created: {pdf_path}")
    else:
        pdf_path = converter.convert(args.input)
        print(f"PDF created: {pdf_path}")


def cmd_client(args):
    """Handle `invoicegen client` subcommand"""
    clients_dir = getattr(args, 'clients_dir', 'clients')

    if args.client_action == 'init':
        try:
            config_path = init_client(args.name, clients_dir)
            print(f"Client initialized: {config_path}")
        except FileExistsError as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)

    elif args.client_action == 'list':
        clients = list_clients(clients_dir)
        if clients:
            for name in clients:
                print(name)
        else:
            print("No clients configured.")

    elif args.client_action == 'show':
        try:
            client = load_client(args.name, clients_dir)
            print(f"Name:           {client.name}")
            print(f"Company:        {client.company}")
            print(f"Contact:        {client.contact}")
            print(f"Email:          {client.email}")
            print(f"Address:        {', '.join(client.address)}")
            print(f"Currency:       {client.currency} ({client.currency_symbol})")
            print(f"Daily rate:     {client.currency_symbol}{client.daily_rate:.2f}")
            print(f"Payment terms:  {client.payment_terms_days} days")
            if client.payment_details:
                print("Payment details:")
                for key, value in client.payment_details.items():
                    print(f"  {key}: {value}")
        except FileNotFoundError as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog='invoicegen',
        description='Professional invoice and timesheet generator',
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # --- invoice ---
    p_inv = subparsers.add_parser('invoice', help='Generate an invoice from JSON')
    p_inv.add_argument('input', help='JSON input file')
    p_inv.add_argument('-o', '--output', help='Output HTML file')
    p_inv.add_argument('--pdf', action='store_true', help='Also generate PDF')
    p_inv.add_argument('--client', help='Client name (loads defaults from YAML)')
    p_inv.add_argument('--output-dir', help='Output directory')
    p_inv.add_argument('--clients-dir', default='clients', help='Clients directory')
    p_inv.set_defaults(func=cmd_invoice)

    # --- timesheet ---
    p_ts = subparsers.add_parser('timesheet', help='Generate a timesheet from JSON')
    p_ts.add_argument('input', help='JSON input file')
    p_ts.add_argument('-o', '--output', help='Output HTML file')
    p_ts.add_argument('--pdf', action='store_true', help='Also generate PDF')
    p_ts.add_argument('--view', choices=VALID_VIEWS, default='day',
                      help='View type (default: day)')
    p_ts.add_argument('--header-layout', choices=VALID_HEADER_LAYOUTS, default='default',
                      help='Header layout style')
    p_ts.add_argument('--client', help='Client name (loads defaults from YAML)')
    p_ts.add_argument('--output-dir', help='Output directory')
    p_ts.add_argument('--clients-dir', default='clients', help='Clients directory')
    p_ts.set_defaults(func=cmd_timesheet)

    # --- pdf ---
    p_pdf = subparsers.add_parser('pdf', help='Convert HTML to PDF')
    p_pdf.add_argument('input', help='HTML file to convert')
    p_pdf.add_argument('-o', '--output', help='Output PDF file')
    p_pdf.add_argument('--margin-top', default='10mm', help='Top margin')
    p_pdf.add_argument('--margin-right', default='10mm', help='Right margin')
    p_pdf.add_argument('--margin-bottom', default='50mm', help='Bottom margin')
    p_pdf.add_argument('--margin-left', default='10mm', help='Left margin')
    p_pdf.set_defaults(func=cmd_pdf)

    # --- client ---
    p_client = subparsers.add_parser('client', help='Manage client configurations')
    p_client.add_argument('--clients-dir', default='clients', help='Clients directory')
    client_sub = p_client.add_subparsers(dest='client_action', help='Client action')

    p_ci = client_sub.add_parser('init', help='Initialize a new client')
    p_ci.add_argument('name', help='Client identifier (e.g. acme_corp)')

    p_cl = client_sub.add_parser('list', help='List configured clients')

    p_cs = client_sub.add_parser('show', help='Show client details')
    p_cs.add_argument('name', help='Client identifier')

    p_client.set_defaults(func=cmd_client)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()
