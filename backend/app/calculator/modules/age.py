import calendar
import re
from datetime import date, datetime


MONTHS = {name.lower(): index for index, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): index for index, name in enumerate(calendar.month_abbr) if name})


def _extract_dates(text: str) -> list[date]:
    matches: list[tuple[int, date]] = []

    for match in re.finditer(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", text):
        matches.append((match.start(), date(int(match.group(1)), int(match.group(2)), int(match.group(3)))))

    for match in re.finditer(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b", text):
        matches.append((match.start(), date(int(match.group(3)), int(match.group(2)), int(match.group(1)))))

    month_pattern = "|".join(sorted(MONTHS, key=len, reverse=True))
    for match in re.finditer(rf"\b(\d{{1,2}})\s+({month_pattern})\s+(\d{{4}})\b", text, re.IGNORECASE):
        matches.append((match.start(), date(int(match.group(3)), MONTHS[match.group(2).lower()], int(match.group(1)))))

    unique: list[date] = []
    for _, parsed in sorted(matches, key=lambda item: item[0]):
        if parsed not in unique:
            unique.append(parsed)
    return unique


def _difference(start: date, end: date) -> tuple[int, int, int]:
    years = end.year - start.year
    months = end.month - start.month
    days = end.day - start.day

    if days < 0:
        months -= 1
        previous_month = end.month - 1 or 12
        previous_year = end.year if end.month > 1 else end.year - 1
        days += calendar.monthrange(previous_year, previous_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def calculate(query: str) -> dict:
    dates = _extract_dates(query)
    if not dates:
        raise ValueError("Include a date such as 2003-08-15 or 15 August 2003.")

    start = dates[0]
    end = dates[1] if len(dates) > 1 else date.today()
    if start > end:
        raise ValueError("The starting date cannot be after the comparison date.")

    years, months, days = _difference(start, end)
    total_days = (end - start).days
    return {
        "title": "Exact age",
        "answer": f"{years} years, {months} months, and {days} days",
        "value": total_days,
        "unit": "total days",
        "formula": "comparison date − date of birth",
        "steps": [
            f"Use {start.isoformat()} as the starting date.",
            f"Use {end.isoformat()} as the comparison date.",
            f"Borrow calendar days and months where required: {years}y {months}m {days}d.",
        ],
        "assumptions": ["The first date is the date of birth.", "If no second date is supplied, today's server date is used."],
        "confidence": 0.99,
        "metadata": {"start_date": start.isoformat(), "end_date": end.isoformat(), "total_days": total_days},
    }

