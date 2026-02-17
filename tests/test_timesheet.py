import copy

from invoice_generator.timesheet import (
    TimesheetGenerator,
    generate_timesheet,
    validate_data,
    calculate_stats,
)


class TestTimesheetGenerator:
    def test_day_view(self, sample_timesheet_data):
        gen = TimesheetGenerator(view='day')
        html = gen.generate(sample_timesheet_data)
        assert "<!DOCTYPE html>" in html
        assert "Jane Developer" in html
        assert "API endpoint implementation" in html

    def test_period_view(self, sample_timesheet_data):
        gen = TimesheetGenerator(view='period')
        html = gen.generate(sample_timesheet_data)
        assert "<!DOCTYPE html>" in html
        assert "Jane Developer" in html
        assert "Project Breakdown" in html

    def test_header_layouts(self, sample_timesheet_data):
        for layout in ['default', 'three-column', 'logo-left', 'split']:
            gen = TimesheetGenerator(header_layout=layout)
            html = gen.generate(sample_timesheet_data)
            assert "Jane Developer" in html

    def test_save_creates_file(self, sample_timesheet_data, tmp_path):
        gen = TimesheetGenerator()
        html = gen.generate(sample_timesheet_data)
        out = tmp_path / "sub" / "ts.html"
        gen.save(html, str(out))
        assert out.exists()


class TestValidateData:
    def test_valid_data(self, sample_timesheet_data):
        is_valid, errors = validate_data(sample_timesheet_data)
        assert is_valid
        assert errors == []

    def test_missing_employee_name(self, sample_timesheet_data):
        data = copy.deepcopy(sample_timesheet_data)
        del data['employee_name']
        is_valid, errors = validate_data(data)
        assert not is_valid
        assert any("employee_name" in e for e in errors)

    def test_missing_entry_fields(self):
        data = {
            'employee_name': 'Test',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'entries': [{'hours': 8}],
        }
        is_valid, errors = validate_data(data)
        assert not is_valid
        assert any("date" in e for e in errors)
        assert any("description" in e for e in errors)

    def test_entries_not_list(self):
        data = {
            'employee_name': 'Test',
            'period_start': '2025-01-01',
            'period_end': '2025-01-31',
            'entries': "bad",
        }
        is_valid, errors = validate_data(data)
        assert not is_valid


class TestCalculateStats:
    def test_stats(self, sample_timesheet_data):
        stats = calculate_stats(sample_timesheet_data['entries'])
        assert stats['total_hours'] == "33.5"
        assert stats['total_days'] == "5"
        assert stats['total_tasks'] == "5"
        assert float(stats['avg_hours']) > 0
