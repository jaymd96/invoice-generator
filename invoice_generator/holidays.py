"""
UK Calendar and working day utilities using the GOV.UK Bank Holidays API.

Provides holiday lookups, working day checks, and date arithmetic
for the United Kingdom (with optional division filtering).

API: https://www.gov.uk/bank-holidays.json
"""

import json
import ssl
import urllib.request
import urllib.error
from datetime import date, timedelta
from dataclasses import dataclass


API_URL = "https://www.gov.uk/bank-holidays.json"

DIVISIONS = {
    "england": "england-and-wales",
    "wales": "england-and-wales",
    "england-and-wales": "england-and-wales",
    "scotland": "scotland",
    "northern-ireland": "northern-ireland",
}

VALID_DIVISIONS = ["england-and-wales", "scotland", "northern-ireland"]


@dataclass
class Holiday:
    """A UK bank holiday."""
    name: str
    date: date
    notes: str = ""

    @classmethod
    def from_gov(cls, data: dict) -> "Holiday":
        return cls(
            name=data["title"],
            date=date.fromisoformat(data["date"]),
            notes=data.get("notes", ""),
        )


def _ssl_context() -> ssl.SSLContext:
    """Create an SSL context, using certifi certs if available."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def _fetch_bank_holidays() -> dict:
    """Fetch all bank holidays from the GOV.UK API."""
    req = urllib.request.Request(API_URL, headers={"Accept": "application/json"})
    try:
        ctx = _ssl_context()
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GOV.UK API error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach GOV.UK API: {e.reason}") from e


class UKCalendar:
    """
    UK bank holiday calendar with working day arithmetic.

    Usage:
        cal = UKCalendar()                       # England & Wales (default)
        cal = UKCalendar("scotland")             # Scotland
        cal = UKCalendar("northern-ireland")     # Northern Ireland

        cal.is_working_day(date(2026, 12, 25))   # False
        cal.working_days_in_range(start, end)     # int
        cal.add_working_days(start, 10)           # date
    """

    def __init__(self, division: str | None = None):
        if division and division.lower() not in DIVISIONS:
            valid = ", ".join(sorted(set(DIVISIONS.keys())))
            raise ValueError(
                f"Unknown division '{division}'. Valid: {valid}"
            )
        self.division = DIVISIONS.get(
            division.lower() if division else "england-and-wales",
            "england-and-wales",
        )
        self._holidays: list[Holiday] | None = None
        self._holiday_set: set[date] | None = None

    def _ensure_loaded(self):
        """Lazy-load holidays from the API on first access."""
        if self._holidays is not None:
            return
        data = _fetch_bank_holidays()
        division_data = data.get(self.division, {})
        events = division_data.get("events", [])
        self._holidays = [Holiday.from_gov(e) for e in events]
        self._holiday_set = {h.date for h in self._holidays}

    def get_holidays(self, year: int) -> list[Holiday]:
        """Get bank holidays for a given year."""
        self._ensure_loaded()
        return [h for h in self._holidays if h.date.year == year]

    def get_holidays_in_range(self, start: date, end: date) -> list[Holiday]:
        """Get all bank holidays within a date range (inclusive)."""
        self._ensure_loaded()
        return sorted(
            [h for h in self._holidays if start <= h.date <= end],
            key=lambda h: h.date,
        )

    def is_public_holiday(self, d: date) -> Holiday | None:
        """Return the Holiday if the date is a bank holiday, else None."""
        self._ensure_loaded()
        if d in self._holiday_set:
            for h in self._holidays:
                if h.date == d:
                    return h
        return None

    def is_weekend(self, d: date) -> bool:
        """Check if a date falls on a weekend (Saturday=5, Sunday=6)."""
        return d.weekday() >= 5

    def is_working_day(self, d: date) -> bool:
        """Check if a date is a working day (not weekend, not bank holiday)."""
        return not self.is_weekend(d) and self.is_public_holiday(d) is None

    def working_days_in_range(self, start: date, end: date) -> int:
        """Count working days in a date range (inclusive of both ends)."""
        if start > end:
            raise ValueError("start date must be before or equal to end date")
        self._ensure_loaded()
        count = 0
        d = start
        while d <= end:
            if d.weekday() < 5 and d not in self._holiday_set:
                count += 1
            d += timedelta(days=1)
        return count

    def working_days_list(self, start: date, end: date) -> list[date]:
        """List all working days in a date range (inclusive)."""
        if start > end:
            raise ValueError("start date must be before or equal to end date")
        self._ensure_loaded()
        days = []
        d = start
        while d <= end:
            if d.weekday() < 5 and d not in self._holiday_set:
                days.append(d)
            d += timedelta(days=1)
        return days

    def next_working_day(self, d: date) -> date:
        """Find the next working day after the given date."""
        d = d + timedelta(days=1)
        while not self.is_working_day(d):
            d += timedelta(days=1)
        return d

    def previous_working_day(self, d: date) -> date:
        """Find the previous working day before the given date."""
        d = d - timedelta(days=1)
        while not self.is_working_day(d):
            d -= timedelta(days=1)
        return d

    def add_working_days(self, start: date, days: int) -> date:
        """
        Add N working days to a date. Negative values subtract.
        Returns the resulting date.
        """
        if days == 0:
            return start
        step = 1 if days > 0 else -1
        remaining = abs(days)
        d = start
        while remaining > 0:
            d += timedelta(days=step)
            if self.is_working_day(d):
                remaining -= 1
        return d

    def month_summary(self, year: int, month: int) -> dict:
        """
        Get a summary of a month: total days, working days, weekends, holidays.
        """
        first = date(year, month, 1)
        if month == 12:
            last = date(year, 12, 31)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)

        self._ensure_loaded()
        holidays_in_month = [
            h for h in self._holidays
            if first <= h.date <= last
        ]
        holiday_dates_in_month = {h.date for h in holidays_in_month}

        total = (last - first).days + 1
        weekends = sum(
            1 for i in range(total)
            if (first + timedelta(days=i)).weekday() >= 5
        )
        holiday_weekdays = sum(
            1 for d in holiday_dates_in_month if d.weekday() < 5
        )
        working = total - weekends - holiday_weekdays

        return {
            "year": year,
            "month": month,
            "total_days": total,
            "working_days": working,
            "weekends": weekends,
            "public_holidays": len(holidays_in_month),
            "holiday_weekday_count": holiday_weekdays,
            "holidays": holidays_in_month,
        }
