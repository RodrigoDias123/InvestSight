from datetime import date
from decimal import Decimal

from apps.portfolio.models import Portfolio, PortfolioSnapshot


def capture_portfolio_snapshots() -> int:
    """
    Snapshot the current_value of every Portfolio.
    Intended to run daily (e.g. via Django management command or Celery beat).
    Returns the number of portfolios processed.
    """
    count = 0
    for portfolio in Portfolio.objects.all():
        value = portfolio.current_value or Decimal("0")
        PortfolioSnapshot.objects.update_or_create(
            portfolio=portfolio,
            date=date.today(),
            defaults={"value": value},
        )
        count += 1
    return count
