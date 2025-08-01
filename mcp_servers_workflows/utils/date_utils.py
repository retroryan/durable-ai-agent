"""Date utilities for Open-Meteo API data retrieval."""

from datetime import datetime, timedelta, timezone


def get_current_date():
    """
    Get the current date for API queries.

    Returns:
        datetime: Current date and time
    """
    return datetime.now(timezone.utc)


def get_forecast_range(days_ahead=7, past_days=0):
    """
    Get date range for forecast queries.

    Args:
        days_ahead: Number of days to forecast (max 16)
        past_days: Number of past days to include (max 92)

    Returns:
        tuple: (start_date, end_date)
    """
    current = get_current_date()
    start_date = current - timedelta(days=past_days)
    end_date = current + timedelta(days=days_ahead)
    return start_date.date(), end_date.date()


def get_historical_range(days_back=30):
    """
    Get date range for historical queries.

    Note: Open-Meteo archive data has a 5-day delay.

    Args:
        days_back: Number of days to go back from 5 days ago

    Returns:
        tuple: (start_date, end_date)
    """
    current = get_current_date()
    # Account for 5-day delay in archive data
    end_date = current - timedelta(days=5)
    start_date = end_date - timedelta(days=days_back)
    return start_date.date(), end_date.date()


def format_date_for_api(date):
    """
    Format a date for Open-Meteo API.

    Args:
        date: datetime or date object

    Returns:
        str: Date in YYYY-MM-DD format
    """
    if hasattr(date, "date"):
        date = date.date()
    return date.strftime("%Y-%m-%d")
