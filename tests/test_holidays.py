"""Tests for the UK Calendar / holidays module."""

import pytest
from datetime import date
from unittest.mock import patch

from invoice_generator.holidays import UKCalendar, Holiday, DIVISIONS


# --- Sample GOV.UK API response ---

SAMPLE_API_RESPONSE = {
    "england-and-wales": {
        "division": "england-and-wales",
        "events": [
            {"title": "New Year\u2019s Day", "date": "2026-01-01", "notes": "", "bunting": True},
            {"title": "Good Friday", "date": "2026-04-03", "notes": "", "bunting": False},
            {"title": "Easter Monday", "date": "2026-04-06", "notes": "", "bunting": True},
            {"title": "Early May bank holiday", "date": "2026-05-04", "notes": "", "bunting": True},
            {"title": "Spring bank holiday", "date": "2026-05-25", "notes": "", "bunting": True},
            {"title": "Summer bank holiday", "date": "2026-08-31", "notes": "", "bunting": True},
            {"title": "Christmas Day", "date": "2026-12-25", "notes": "", "bunting": True},
            {"title": "Boxing Day", "date": "2026-12-28", "notes": "Substitute day", "bunting": True},
        ],
    },
    "scotland": {
        "division": "scotland",
        "events": [
            {"title": "New Year\u2019s Day", "date": "2026-01-01", "notes": "", "bunting": True},
            {"title": "2nd January", "date": "2026-01-02", "notes": "", "bunting": True},
            {"title": "St Andrew\u2019s Day", "date": "2026-11-30", "notes": "", "bunting": True},
        ],
    },
    "northern-ireland": {
        "division": "northern-ireland",
        "events": [
            {"title": "New Year\u2019s Day", "date": "2026-01-01", "notes": "", "bunting": True},
            {"title": "St Patrick\u2019s Day", "date": "2026-03-17", "notes": "", "bunting": True},
        ],
    },
}


@pytest.fixture
def mock_api():
    """Patch _fetch_bank_holidays to return sample data."""
    with patch("invoice_generator.holidays._fetch_bank_holidays", return_value=SAMPLE_API_RESPONSE) as m:
        yield m


@pytest.fixture
def cal(mock_api):
    """Calendar instance with mocked API (england-and-wales)."""
    return UKCalendar()


@pytest.fixture
def cal_scotland(mock_api):
    """Calendar instance for Scotland with mocked API."""
    return UKCalendar("scotland")


class TestHolidayParsing:
    def test_from_gov(self):
        h = Holiday.from_gov(SAMPLE_API_RESPONSE["england-and-wales"]["events"][0])
        assert h.name == "New Year\u2019s Day"
        assert h.date == date(2026, 1, 1)

    def test_notes(self):
        h = Holiday.from_gov(SAMPLE_API_RESPONSE["england-and-wales"]["events"][-1])
        assert h.notes == "Substitute day"


class TestUKCalendarInit:
    def test_default_division(self, mock_api):
        cal = UKCalendar()
        assert cal.division == "england-and-wales"

    def test_england_alias(self, mock_api):
        cal = UKCalendar("england")
        assert cal.division == "england-and-wales"

    def test_wales_alias(self, mock_api):
        cal = UKCalendar("wales")
        assert cal.division == "england-and-wales"

    def test_scotland(self, mock_api):
        cal = UKCalendar("scotland")
        assert cal.division == "scotland"

    def test_case_insensitive(self, mock_api):
        cal = UKCalendar("Scotland")
        assert cal.division == "scotland"

    def test_invalid_division(self, mock_api):
        with pytest.raises(ValueError, match="Unknown division"):
            UKCalendar("london")


class TestGetHolidays:
    def test_returns_holidays_for_year(self, cal):
        holidays = cal.get_holidays(2026)
        assert len(holidays) == 8
        assert holidays[0].name == "New Year\u2019s Day"

    def test_no_holidays_outside_data(self, cal):
        holidays = cal.get_holidays(2099)
        assert len(holidays) == 0

    def test_lazy_loads_once(self, cal, mock_api):
        cal.get_holidays(2026)
        cal.get_holidays(2026)
        assert mock_api.call_count == 1

    def test_scotland_holidays(self, cal_scotland):
        holidays = cal_scotland.get_holidays(2026)
        names = [h.name for h in holidays]
        assert "2nd January" in names
        assert "St Andrew\u2019s Day" in names


class TestGetHolidaysInRange:
    def test_range_filter(self, cal):
        holidays = cal.get_holidays_in_range(date(2026, 4, 1), date(2026, 4, 30))
        names = [h.name for h in holidays]
        assert "Good Friday" in names
        assert "Easter Monday" in names
        assert "Christmas Day" not in names


class TestIsPublicHoliday:
    def test_holiday_date(self, cal):
        h = cal.is_public_holiday(date(2026, 12, 25))
        assert h is not None
        assert h.name == "Christmas Day"

    def test_non_holiday_date(self, cal):
        assert cal.is_public_holiday(date(2026, 6, 15)) is None


class TestIsWorkingDay:
    def test_regular_weekday(self, cal):
        # 2026-02-24 is a Tuesday
        assert cal.is_working_day(date(2026, 2, 24)) is True

    def test_weekend(self, cal):
        # 2026-02-28 is a Saturday
        assert cal.is_working_day(date(2026, 2, 28)) is False

    def test_bank_holiday(self, cal):
        assert cal.is_working_day(date(2026, 12, 25)) is False


class TestWorkingDaysInRange:
    def test_full_week_no_holidays(self, cal):
        # Mon 2026-02-02 to Fri 2026-02-06 (no holidays)
        count = cal.working_days_in_range(date(2026, 2, 2), date(2026, 2, 6))
        assert count == 5

    def test_includes_weekend(self, cal):
        # Mon to Sun (7 days, 5 working)
        count = cal.working_days_in_range(date(2026, 2, 2), date(2026, 2, 8))
        assert count == 5

    def test_week_with_holiday(self, cal):
        # Dec 22 (Mon) to Dec 28 (Mon, Boxing Day substitute)
        # Working: Mon 22, Tue 23, Wed 24 = 3 days
        # Not working: Thu 25 (Xmas), Fri 26 (weekend? no, Fri), Sat 27, Sun 28? No, 28 is Mon (Boxing)
        # Actually: Mon 22, Tue 23, Wed 24 are working. Thu 25 = Xmas. Fri 26 = regular day (26th is Sat? no)
        # Let me check: Dec 25 2026 is Friday. Dec 26 is Saturday. Dec 28 is Monday (Boxing Day sub).
        # So Dec 22 Mon, 23 Tue, 24 Wed, 25 Fri=holiday, 26 Sat, 27 Sun, 28 Mon=holiday
        # Working: 22, 23, 24 = 3
        count = cal.working_days_in_range(date(2026, 12, 22), date(2026, 12, 28))
        assert count == 3

    def test_start_after_end_raises(self, cal):
        with pytest.raises(ValueError, match="start date"):
            cal.working_days_in_range(date(2026, 2, 10), date(2026, 2, 1))


class TestWorkingDaysList:
    def test_lists_dates(self, cal):
        days = cal.working_days_list(date(2026, 2, 2), date(2026, 2, 6))
        assert len(days) == 5
        assert all(isinstance(d, date) for d in days)


class TestNextWorkingDay:
    def test_from_friday(self, cal):
        # Fri 2026-02-06 -> Mon 2026-02-09
        assert cal.next_working_day(date(2026, 2, 6)) == date(2026, 2, 9)

    def test_from_saturday(self, cal):
        assert cal.next_working_day(date(2026, 2, 7)) == date(2026, 2, 9)

    def test_before_xmas(self, cal):
        # Wed Dec 24 -> next working day: Dec 25 is Fri (Xmas), Dec 26 Sat, Dec 27 Sun,
        # Dec 28 Mon (Boxing Day sub) -> Dec 29 Tue
        result = cal.next_working_day(date(2026, 12, 24))
        assert result == date(2026, 12, 29)


class TestAddWorkingDays:
    def test_add_positive(self, cal):
        # Mon Feb 2 + 5 working days = Mon Feb 9
        result = cal.add_working_days(date(2026, 2, 2), 5)
        assert result == date(2026, 2, 9)

    def test_add_zero(self, cal):
        result = cal.add_working_days(date(2026, 2, 2), 0)
        assert result == date(2026, 2, 2)

    def test_add_negative(self, cal):
        # Fri Feb 6 - 5 working days = Fri Jan 30
        result = cal.add_working_days(date(2026, 2, 6), -5)
        assert result == date(2026, 1, 30)


class TestMonthSummary:
    def test_february_2026(self, cal):
        summary = cal.month_summary(2026, 2)
        assert summary["year"] == 2026
        assert summary["month"] == 2
        assert summary["total_days"] == 28
        assert summary["working_days"] == 20
        assert summary["weekends"] == 8
        assert summary["public_holidays"] == 0

    def test_december_2026(self, cal):
        summary = cal.month_summary(2026, 12)
        assert summary["total_days"] == 31
        assert summary["public_holidays"] == 2  # Xmas + Boxing Day sub
        # Dec 25 is Friday (weekday), Dec 28 is Monday (weekday) = 2 holiday weekdays
        assert summary["holiday_weekday_count"] == 2

    def test_january_2026(self, cal):
        summary = cal.month_summary(2026, 1)
        # Jan 1 is Thursday = 1 holiday weekday
        assert summary["public_holidays"] == 1
        assert summary["holiday_weekday_count"] == 1
        # 31 days, 9 weekend days (5 Sat + 4 Sun), 1 holiday weekday = 21 working days
        assert summary["working_days"] == 21
