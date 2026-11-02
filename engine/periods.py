"""Period calculation shared by the CLI and future desktop front ends."""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def calculate_period(start_date: str, period: int) -> tuple[datetime, datetime]:
    """Return the existing inclusive query boundaries without changing CLI semantics.

    period == 0: a month from start_date.
    period == -1: a ten-day period starting at start_date.
    Otherwise: period days from start_date.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    if period == 0:
        end = start + relativedelta(months=1)
    elif period == -1:
        if start.day >= 21:
            end = start + relativedelta(months=1) - timedelta(days=start.day)
        else:
            end = start + timedelta(days=10)
    else:
        end = start + timedelta(days=period)
    return start, end
