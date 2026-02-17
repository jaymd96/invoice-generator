#!/usr/bin/env python3
"""
Consolidated Timesheet Generator - day and period views with multiple header layouts
"""

import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Tuple

# ---------------------------------------------------------------------------
# Header CSS templates for different layouts
# ---------------------------------------------------------------------------
HEADER_TEMPLATES = {
    'default': """
        .timesheet-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 15px;
        }

        .timesheet-title h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .period-info {
            font-size: 13px;
            color: #6b7280;
        }

        .header-right {
            text-align: right;
        }

        .company-logo {
            max-width: 150px;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
            margin-bottom: 5px;
            display: block;
            margin-left: auto;
        }

        .employee-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .employee-details {
            font-size: 13px;
            color: #6b7280;
        }
    """,

    'three-column': """
        .timesheet-header {
            display: grid;
            grid-template-columns: 150px 1fr 200px;
            align-items: center;
            gap: 30px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 15px;
        }

        .header-left {
            display: flex;
            align-items: center;
        }

        .header-center {
            text-align: center;
        }

        .header-center h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .period-info {
            font-size: 13px;
            color: #6b7280;
        }

        .header-right {
            text-align: right;
        }

        .company-logo {
            max-width: 150px;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
        }

        .employee-name {
            font-size: 16px;
            font-weight: 600;
        }

        .employee-details {
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
        }
    """,

    'logo-left': """
        .timesheet-header {
            display: flex;
            gap: 25px;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 15px;
        }

        .company-logo {
            max-width: 150px;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
            flex-shrink: 0;
        }

        .header-content {
            flex: 1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header-left h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .period-info {
            font-size: 13px;
            color: #6b7280;
        }

        .header-right {
            text-align: right;
        }

        .employee-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 5px;
        }

        .employee-details {
            font-size: 13px;
            color: #6b7280;
        }
    """,

    'split': """
        .timesheet-header {
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0;
        }

        .header-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 10px;
            border-bottom: 1px solid #f3f4f6;
        }

        .header-bottom {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 10px;
            padding-bottom: 15px;
        }

        .company-logo {
            max-width: 150px;
            max-height: 60px;
            width: auto;
            height: auto;
            object-fit: contain;
        }

        .employee-info {
            text-align: right;
            font-size: 14px;
            color: #6b7280;
        }

        .header-bottom h1 {
            font-size: 24px;
            font-weight: 600;
        }

        .period-info {
            font-size: 13px;
            color: #6b7280;
        }
    """
}

# Header HTML templates
HEADER_HTML = {
    'default': """
        <div class="timesheet-header">
            <div>
                <h1>{{title}}</h1>
                <div class="period-info">
                    {{period_start}} - {{period_end}}
                </div>
            </div>
            <div class="header-right">
                {{company_logo_html}}
                <div class="employee-name">{{employee_name}}</div>
                <div class="employee-details">
                    {{employee_id}}<br>
                    {{employee_team}}
                </div>
            </div>
        </div>
    """,

    'three-column': """
        <div class="timesheet-header">
            <div class="header-left">
                {{company_logo_html}}
            </div>
            <div class="header-center">
                <h1>{{title}}</h1>
                <div class="period-info">
                    {{period_start}} - {{period_end}}
                </div>
            </div>
            <div class="header-right">
                <div class="employee-name">{{employee_name}}</div>
                <div class="employee-details">
                    {{employee_id}} · {{employee_team}}
                </div>
            </div>
        </div>
    """,

    'logo-left': """
        <div class="timesheet-header">
            {{company_logo_html}}
            <div class="header-content">
                <div class="header-left">
                    <h1>{{title}}</h1>
                    <div class="period-info">
                        {{period_start}} - {{period_end}}
                    </div>
                </div>
                <div class="header-right">
                    <div class="employee-name">{{employee_name}}</div>
                    <div class="employee-details">
                        {{employee_id}}<br>
                        {{employee_team}}
                    </div>
                </div>
            </div>
        </div>
    """,

    'split': """
        <div class="timesheet-header">
            <div class="header-top">
                {{company_logo_html}}
                <div class="employee-info">
                    {{employee_name}} · {{employee_id}} · {{employee_team}}
                </div>
            </div>
            <div class="header-bottom">
                <h1>{{title}}</h1>
                <div class="period-info">
                    {{period_start}} - {{period_end}}
                </div>
            </div>
        </div>
    """
}

VALID_HEADER_LAYOUTS = list(HEADER_TEMPLATES.keys())
VALID_VIEWS = ['day', 'period']


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: str) -> datetime:
    """Parse various date formats"""
    formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d %b %Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")


def _get_day_view_template(header_layout: str = 'default') -> str:
    """Get day view template with specified header layout"""
    header_css = HEADER_TEMPLATES.get(header_layout, HEADER_TEMPLATES['default'])
    header_html = HEADER_HTML.get(header_layout, HEADER_HTML['default'])

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timesheet - {{employee_name}} - {{period_end}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            color: #333;
            line-height: 1.4;
            background-color: #f5f5f5;
        }

        .timesheet-container {
            max-width: 1000px;
            margin: 10px auto;
            background: white;
            padding: 25px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        """ + header_css + """

        .day-entry {
            margin-bottom: 25px;
            border: 1px solid #e5e7eb;
            border-radius: 6px;
            overflow: hidden;
        }

        .day-header {
            background-color: #f9fafb;
            padding: 12px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #e5e7eb;
        }

        .day-date {
            font-weight: 600;
            font-size: 14px;
        }

        .day-total {
            font-size: 13px;
            font-weight: 500;
            color: #6b7280;
        }

        .task-list {
            padding: 0;
        }

        .task-entry {
            padding: 12px 15px;
            border-bottom: 1px solid #f3f4f6;
            display: flex;
            gap: 15px;
        }

        .task-entry:last-child {
            border-bottom: none;
        }

        .task-hours {
            min-width: 50px;
            font-weight: 600;
            color: #111827;
            font-size: 14px;
        }

        .task-details {
            flex: 1;
        }

        .task-project {
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 2px;
        }

        .task-description {
            font-size: 13px;
            color: #374151;
            line-height: 1.5;
        }

        .summary-section {
            margin-top: 30px;
            padding: 20px;
            background-color: #f9fafb;
            border-radius: 6px;
        }

        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }

        .summary-item {
            text-align: center;
        }

        .summary-value {
            font-size: 24px;
            font-weight: 600;
            color: #111827;
        }

        .summary-label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
        }

        .weekend {
            background-color: #fef3c7;
        }

        @media print {
            body {
                background-color: white;
            }

            .timesheet-container {
                box-shadow: none;
                margin: 0;
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="timesheet-container">
        """ + header_html + """

        {{day_entries}}

        <div class="summary-section">
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-value">{{total_hours}}</div>
                    <div class="summary-label">Total Hours</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{{total_days}}</div>
                    <div class="summary-label">Days Worked</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{{avg_hours}}</div>
                    <div class="summary-label">Avg Hours/Day</div>
                </div>
                <div class="summary-item">
                    <div class="summary-value">{{total_tasks}}</div>
                    <div class="summary-label">Tasks Completed</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""


def _get_period_view_template(header_layout: str = 'default') -> str:
    """Get period view template with specified header layout"""
    header_css = HEADER_TEMPLATES.get(header_layout, HEADER_TEMPLATES['default'])
    header_html = HEADER_HTML.get(header_layout, HEADER_HTML['default'])

    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timesheet - {{employee_name}} - {{period_end}}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            color: #333;
            line-height: 1.4;
            background-color: #f5f5f5;
        }

        .timesheet-container {
            max-width: 1000px;
            margin: 10px auto;
            background: white;
            padding: 25px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        """ + header_css + """

        .time-entries-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }

        .time-entries-table th {
            text-align: left;
            padding: 10px;
            border-bottom: 2px solid #e5e7eb;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6b7280;
        }

        .time-entries-table td {
            padding: 12px 10px;
            border-bottom: 1px solid #f3f4f6;
            font-size: 13px;
        }

        .time-entries-table th:nth-child(3),
        .time-entries-table td:nth-child(3) {
            text-align: center;
            width: 80px;
        }

        .project-name {
            font-size: 11px;
            color: #6b7280;
        }

        .weekend {
            background-color: #fffbeb;
        }

        .summary-section {
            margin-top: 30px;
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }

        .project-breakdown {
            background-color: #f9fafb;
            padding: 20px;
            border-radius: 6px;
        }

        .project-breakdown h3 {
            font-size: 16px;
            margin-bottom: 15px;
        }

        .project-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
            font-size: 13px;
        }

        .project-item:last-child {
            border-bottom: none;
        }

        .totals-box {
            background-color: #f9fafb;
            padding: 20px;
            border-radius: 6px;
            height: fit-content;
        }

        .totals-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 13px;
        }

        .totals-row.total {
            font-size: 16px;
            font-weight: 600;
            border-top: 2px solid #e5e7eb;
            margin-top: 10px;
            padding-top: 12px;
        }

        @media print {
            body {
                background-color: white;
            }

            .timesheet-container {
                box-shadow: none;
                margin: 0;
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="timesheet-container">
        """ + header_html + """

        <table class="time-entries-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Task Description</th>
                    <th>Hours</th>
                </tr>
            </thead>
            <tbody>
                {{time_entries}}
            </tbody>
        </table>

        <div class="summary-section">
            <div class="project-breakdown">
                <h3>Project Breakdown</h3>
                {{project_breakdown}}
            </div>

            <div class="totals-box">
                <div class="totals-row">
                    <span>Days Worked</span>
                    <span>{{total_days}}</span>
                </div>
                <div class="totals-row">
                    <span>Average Hours/Day</span>
                    <span>{{avg_hours}}</span>
                </div>
                <div class="totals-row total">
                    <span>Total Hours</span>
                    <span>{{total_hours}}</span>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""


def _format_day_entries(entries: List[Dict], hide_task_hours: bool = False) -> str:
    """Format entries grouped by day for day view"""
    days = defaultdict(list)
    for entry in entries:
        date = entry.get('date', entry.get('day'))
        days[date].append(entry)

    html_parts = []
    for date in sorted(days.keys()):
        date_obj = _parse_date(date)
        day_name = date_obj.strftime('%A')
        formatted_date = date_obj.strftime('%d %B %Y')

        day_entries = days[date]
        day_total = sum(float(e.get('hours', 0)) for e in day_entries)

        day_class = 'weekend' if day_name in ['Saturday', 'Sunday'] else ''

        task_html = []
        for entry in day_entries:
            hours = float(entry.get('hours', 0))
            project = entry.get('project', '')
            description = entry.get('description', entry.get('task', 'No description'))

            if hide_task_hours:
                task_html.append(f"""
                <div class="task-entry">
                    <div class="task-details" style="margin-left: 0;">
                        {f'<div class="task-project">{project}</div>' if project else ''}
                        <div class="task-description">{description}</div>
                    </div>
                </div>""")
            else:
                task_html.append(f"""
                <div class="task-entry">
                    <div class="task-hours">{hours:.1f}h</div>
                    <div class="task-details">
                        {f'<div class="task-project">{project}</div>' if project else ''}
                        <div class="task-description">{description}</div>
                    </div>
                </div>""")

        html_parts.append(f"""
        <div class="day-entry">
            <div class="day-header {day_class}">
                <div class="day-date">{day_name}, {formatted_date}</div>
                <div class="day-total">{day_total:.1f} hours</div>
            </div>
            <div class="task-list">
                {''.join(task_html)}
            </div>
        </div>""")

    return '\n'.join(html_parts)


def _format_period_entries(entries: List[Dict]) -> str:
    """Format entries as a flat table for period view"""
    rows = []

    for entry in sorted(entries, key=lambda x: x.get('date', x.get('day'))):
        date = entry.get('date', entry.get('day'))
        date_obj = _parse_date(date)
        day_name = date_obj.strftime('%a')
        formatted_date = date_obj.strftime('%d %b')

        hours = float(entry.get('hours', 0))
        project = entry.get('project', '')
        description = entry.get('description', entry.get('task', 'No description'))

        row_class = 'weekend' if day_name in ['Sat', 'Sun'] else ''

        row = f"""<tr class="{row_class}">
                    <td>{formatted_date} ({day_name})</td>
                    <td>
                        {description}
                        {f'<br><span class="project-name">{project}</span>' if project else ''}
                    </td>
                    <td>{hours:.1f}</td>
                </tr>"""
        rows.append(row)

    return '\n                '.join(rows)


def _calculate_project_breakdown(entries: List[Dict]) -> str:
    """Calculate hours per project and return HTML"""
    projects = defaultdict(float)

    for entry in entries:
        project = entry.get('project', 'Unassigned')
        hours = float(entry.get('hours', 0))
        projects[project] += hours

    sorted_projects = sorted(projects.items(), key=lambda x: x[1], reverse=True)

    html_parts = []
    for project, hours in sorted_projects:
        html_parts.append(f"""
                <div class="project-item">
                    <span>{project}</span>
                    <span>{hours:.1f}h</span>
                </div>""")

    return ''.join(html_parts)


def calculate_stats(entries: List[Dict]) -> Dict[str, str]:
    """Calculate summary statistics from timesheet entries"""
    total_hours = sum(float(e.get('hours', 0)) for e in entries)
    days_worked = len(set(e.get('date', e.get('day')) for e in entries))
    avg_hours = total_hours / days_worked if days_worked > 0 else 0
    total_tasks = len(entries)

    return {
        'total_hours': f"{total_hours:.1f}",
        'total_days': str(days_worked),
        'avg_hours': f"{avg_hours:.1f}",
        'total_tasks': str(total_tasks)
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_timesheet(data: Dict[str, Any], view: str = 'day',
                       header_layout: str = 'default',
                       hide_task_hours: bool = False) -> str:
    """Generate HTML timesheet from data dict"""
    stats = calculate_stats(data['entries'])

    title = data.get('title', 'Engineering Timesheet')

    logo = data.get('company_logo', '')
    logo_html = ''
    if logo:
        logo_html = f'<img src="{logo}" alt="Company Logo" class="company-logo">'

    base_replacements = {
        'title': title,
        'company_logo_html': logo_html,
        'employee_name': data.get('employee_name', 'Unknown'),
        'employee_id': data.get('employee_id', ''),
        'employee_team': data.get('employee_team', data.get('team', '')),
        'period_start': data.get('period_start', ''),
        'period_end': data.get('period_end', ''),
        **stats
    }

    if view == 'day':
        template = _get_day_view_template(header_layout)
        replacements = {
            **base_replacements,
            'day_entries': _format_day_entries(data['entries'], hide_task_hours)
        }

        if not data.get('show_summary', True):
            template = template.replace(
                '<div class="summary-section">',
                '<!-- summary hidden --><div class="summary-section" style="display:none;">')
    else:  # period view
        template = _get_period_view_template(header_layout)
        replacements = {
            **base_replacements,
            'time_entries': _format_period_entries(data['entries']),
            'project_breakdown': _calculate_project_breakdown(data['entries'])
        }

        if not data.get('show_summary', True):
            template = template.replace(
                '<div class="summary-section">',
                '<!-- summary hidden --><div class="summary-section" style="display:none;">')

    html = template
    for key, value in replacements.items():
        html = html.replace('{{' + key + '}}', str(value))

    return html


def validate_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate timesheet data. Returns (is_valid, errors)."""
    errors = []
    required_fields = ['employee_name', 'period_start', 'period_end', 'entries']

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if 'entries' in data:
        if not isinstance(data['entries'], list):
            errors.append("'entries' must be a list")
        else:
            for i, entry in enumerate(data['entries']):
                if 'date' not in entry and 'day' not in entry:
                    errors.append(f"Entry {i}: missing field 'date'")
                if 'description' not in entry:
                    errors.append(f"Entry {i}: missing field 'description'")
                if 'hours' not in entry:
                    errors.append(f"Entry {i}: missing field 'hours'")

    return (len(errors) == 0, errors)


class TimesheetGenerator:
    """Class-based interface for timesheet generation"""

    def __init__(self, view: str = "day", header_layout: str = "default"):
        self.view = view
        self.header_layout = header_layout

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate HTML timesheet from data dict"""
        return generate_timesheet(
            data,
            view=self.view,
            header_layout=self.header_layout
        )

    def generate_from_file(self, json_file: str) -> str:
        """Generate timesheet from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        return self.generate(data)

    def save(self, html: str, output_file: str):
        """Save generated HTML to file"""
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(html)

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        return validate_data(data)
