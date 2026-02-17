#!/usr/bin/env python3
"""
PDF Converter using Playwright for high-quality PDF generation
"""

import os
from pathlib import Path
from typing import Optional, Dict, List


class PDFConverter:
    """Convert HTML invoices and timesheets to PDF using Playwright"""

    def __init__(self, margins: Optional[Dict[str, str]] = None):
        self.margins = margins or {
            'top': '10mm',
            'right': '10mm',
            'bottom': '50mm',
            'left': '10mm'
        }

    def convert(self, html_file: str, output_pdf: Optional[str] = None) -> str:
        """Convert HTML file to PDF. Returns path to generated PDF."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright is required for PDF conversion. "
                "Install it with: pip install playwright && playwright install chromium"
            )

        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()

        if output_pdf is None:
            output_pdf = str(Path(html_file).with_suffix('.pdf'))

        Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content, wait_until='networkidle')
            page.pdf(
                path=output_pdf,
                format='A4',
                print_background=True,
                margin=self.margins,
                display_header_footer=False,
                prefer_css_page_size=False
            )
            browser.close()

        return output_pdf

    def convert_from_html(self, html_content: str, output_pdf: str) -> str:
        """Convert HTML string directly to PDF. Returns path to generated PDF."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright is required for PDF conversion. "
                "Install it with: pip install playwright && playwright install chromium"
            )

        Path(output_pdf).parent.mkdir(parents=True, exist_ok=True)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html_content, wait_until='networkidle')
            page.pdf(
                path=output_pdf,
                format='A4',
                print_background=True,
                margin=self.margins,
                display_header_footer=False,
                prefer_css_page_size=False
            )
            browser.close()

        return output_pdf

    def batch_convert(self, pattern: str = "*.html",
                      output_dir: Optional[str] = None) -> List[str]:
        """Convert multiple HTML files matching a pattern"""
        from glob import glob

        html_files = glob(pattern)
        pdf_files = []

        if not html_files:
            print(f"No HTML files found matching pattern: {pattern}")
            return pdf_files

        print(f"Found {len(html_files)} HTML file(s) to convert:")

        for html_file in html_files:
            print(f"  Converting: {html_file}")
            try:
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    output_pdf = os.path.join(
                        output_dir,
                        Path(html_file).with_suffix('.pdf').name
                    )
                else:
                    output_pdf = None

                pdf_path = self.convert(html_file, output_pdf)
                pdf_files.append(pdf_path)
                print(f"  PDF created: {pdf_path}")
            except Exception as e:
                print(f"  Error converting {html_file}: {e}")

        return pdf_files
