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
from .holidays import UKCalendar, VALID_DIVISIONS


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


def _make_calendar(args) -> UKCalendar:
    """Create a UKCalendar from CLI args."""
    division = getattr(args, 'division', None)
    return UKCalendar(division)


def cmd_calendar_holidays(args):
    """Handle `invoicegen calendar holidays`"""
    from datetime import date as d
    cal = _make_calendar(args)

    if args.year:
        holidays = cal.get_holidays(args.year)
    else:
        start = d.fromisoformat(args.from_date)
        end = d.fromisoformat(args.to_date)
        holidays = cal.get_holidays_in_range(start, end)

    if not holidays:
        print("No public holidays found.")
        return

    for h in holidays:
        day_name = h.date.strftime("%A")
        notes = f" ({h.notes})" if h.notes else ""
        print(f"  {h.date}  {day_name:<10} {h.name}{notes}")


def cmd_calendar_check(args):
    """Handle `invoicegen calendar check`"""
    from datetime import date as d
    cal = _make_calendar(args)
    target = d.fromisoformat(args.date)

    day_name = target.strftime("%A")
    holiday = cal.is_public_holiday(target)
    working = cal.is_working_day(target)

    print(f"Date:          {target} ({day_name})")
    print(f"Working day:   {'Yes' if working else 'No'}")
    if holiday:
        print(f"Holiday:       {holiday.name}")
    elif cal.is_weekend(target):
        print(f"Weekend:       Yes")


def cmd_calendar_working_days(args):
    """Handle `invoicegen calendar working-days`"""
    from datetime import date as d
    cal = _make_calendar(args)
    start = d.fromisoformat(args.from_date)
    end = d.fromisoformat(args.to_date)

    count = cal.working_days_in_range(start, end)
    holidays = cal.get_holidays_in_range(start, end)
    holiday_weekdays = sum(
        1 for h in holidays
        if h.date.weekday() < 5
    )

    print(f"Period:           {start} to {end}")
    print(f"Working days:     {count}")
    print(f"Public holidays:  {len(holidays)} ({holiday_weekdays} on weekdays)")

    if args.list:
        print(f"\nWorking days:")
        for wd in cal.working_days_list(start, end):
            print(f"  {wd} ({wd.strftime('%A')})")


def cmd_calendar_month(args):
    """Handle `invoicegen calendar month`"""
    cal = _make_calendar(args)
    summary = cal.month_summary(args.year, args.month)

    from datetime import date as d
    month_name = d(args.year, args.month, 1).strftime("%B %Y")
    print(f"Month:            {month_name}")
    print(f"Total days:       {summary['total_days']}")
    print(f"Working days:     {summary['working_days']}")
    print(f"Weekend days:     {summary['weekends']}")
    print(f"Public holidays:  {summary['public_holidays']}"
          f" ({summary['holiday_weekday_count']} on weekdays)")

    if summary['holidays']:
        print(f"\nHolidays:")
        for h in summary['holidays']:
            print(f"  {h.date}  {h.name}")


def cmd_calendar_next(args):
    """Handle `invoicegen calendar next-working-day`"""
    from datetime import date as d
    cal = _make_calendar(args)
    target = d.fromisoformat(args.date)
    result = cal.next_working_day(target)
    print(f"Next working day after {target}: {result} ({result.strftime('%A')})")


def cmd_calendar_add(args):
    """Handle `invoicegen calendar add-working-days`"""
    from datetime import date as d
    cal = _make_calendar(args)
    start = d.fromisoformat(args.date)
    result = cal.add_working_days(start, args.days)
    direction = "after" if args.days >= 0 else "before"
    print(f"{abs(args.days)} working days {direction} {start}: {result} ({result.strftime('%A')})")


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

    # --- calendar ---
    p_cal = subparsers.add_parser('calendar', help='UK calendar and working day utilities')
    p_cal.add_argument('--division', choices=VALID_DIVISIONS,
                       help='UK division (default: england-and-wales)')
    cal_sub = p_cal.add_subparsers(dest='calendar_action', help='Calendar action')

    # calendar holidays
    p_ch = cal_sub.add_parser('holidays', help='List public holidays')
    p_ch_group = p_ch.add_mutually_exclusive_group(required=True)
    p_ch_group.add_argument('--year', type=int, help='Year to list holidays for')
    p_ch_group.add_argument('--from', dest='from_date', help='Start date (YYYY-MM-DD)')
    p_ch.add_argument('--to', dest='to_date', help='End date (YYYY-MM-DD, required with --from)')
    p_ch.set_defaults(func=cmd_calendar_holidays)

    # calendar check
    p_cc = cal_sub.add_parser('check', help='Check if a date is a working day')
    p_cc.add_argument('date', help='Date to check (YYYY-MM-DD)')
    p_cc.set_defaults(func=cmd_calendar_check)

    # calendar working-days
    p_cw = cal_sub.add_parser('working-days', help='Count working days in a range')
    p_cw.add_argument('from_date', metavar='from', help='Start date (YYYY-MM-DD)')
    p_cw.add_argument('to_date', metavar='to', help='End date (YYYY-MM-DD)')
    p_cw.add_argument('--list', action='store_true', help='List each working day')
    p_cw.set_defaults(func=cmd_calendar_working_days)

    # calendar month
    p_cm = cal_sub.add_parser('month', help='Monthly summary of working days')
    p_cm.add_argument('year', type=int, help='Year')
    p_cm.add_argument('month', type=int, choices=range(1, 13), help='Month (1-12)')
    p_cm.set_defaults(func=cmd_calendar_month)

    # calendar next-working-day
    p_cn = cal_sub.add_parser('next-working-day', help='Find next working day after a date')
    p_cn.add_argument('date', help='Date (YYYY-MM-DD)')
    p_cn.set_defaults(func=cmd_calendar_next)

    # calendar add-working-days
    p_ca = cal_sub.add_parser('add-working-days', help='Add N working days to a date')
    p_ca.add_argument('date', help='Start date (YYYY-MM-DD)')
    p_ca.add_argument('days', type=int, help='Working days to add (negative to subtract)')
    p_ca.set_defaults(func=cmd_calendar_add)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()
