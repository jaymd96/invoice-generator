"""
PyScript <-> JS bridge.
Exposes Python invoice/timesheet generation functions to JavaScript.
"""

import json
from pyscript import window

from invoice import InvoiceGenerator
from timesheet import generate_timesheet as _generate_timesheet, validate_data


_invoice_gen = InvoiceGenerator()


def generate_invoice(json_str):
    """Called from JS with a JSON string. Returns HTML string."""
    data = json.loads(json_str)
    return _invoice_gen.generate(data)


def generate_ts(json_str, view="day", header_layout="default"):
    """Called from JS with a JSON string. Returns HTML string."""
    data = json.loads(json_str)
    return _generate_timesheet(data, view=view, header_layout=header_layout)


def validate_timesheet(json_str):
    """Called from JS. Returns JSON string with {valid, errors}."""
    data = json.loads(json_str)
    is_valid, errors = validate_data(data)
    return json.dumps({"valid": is_valid, "errors": errors})


# Expose functions on the window object so JS can call them
window.pyGenerateInvoice = generate_invoice
window.pyGenerateTimesheet = generate_ts
window.pyValidateTimesheet = validate_timesheet

# Signal to JS that Python is ready
window.pyReady = True
if hasattr(window, '_onPyReady') and window._onPyReady:
    window._onPyReady()
