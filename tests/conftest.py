import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_invoice_data():
    with open(FIXTURES_DIR / "sample_invoice.json") as f:
        return json.load(f)


@pytest.fixture
def sample_timesheet_data():
    with open(FIXTURES_DIR / "sample_timesheet.json") as f:
        return json.load(f)
