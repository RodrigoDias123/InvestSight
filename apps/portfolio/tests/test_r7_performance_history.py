import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from apps.portfolio.models import PortfolioSnapshot
from apps.portfolio.tasks import capture_portfolio_snapshots


@pytest.fixture
def portfolio_factory(db, django_user_model):
    _counter = [0]

    def create(**kwargs):
        _counter[0] += 1
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", f"user_r7_{_counter[0]}"),
            email=kwargs.pop("email", f"user_r7_{_counter[0]}@example.com"),
            password="testpass123",
        )
        from apps.portfolio.models import Portfolio

        return Portfolio.objects.create(
            name=kwargs.pop("name", f"Portfolio R7 {_counter[0]}"),
            user=user,
        )

    return create


@pytest.mark.django_db
class TestPerformanceHistory:
    def test_snapshot_created_with_correct_value(self, portfolio_factory):
        portfolio = portfolio_factory()
        PortfolioSnapshot.objects.create(
            portfolio=portfolio, date=date.today(), value=Decimal("500.00")
        )
        snapshot = PortfolioSnapshot.objects.get(portfolio=portfolio)
        assert snapshot.value == Decimal("500.00")

    def test_snapshot_persists_across_days(self, portfolio_factory):
        portfolio = portfolio_factory()
        today = date.today()
        yesterday = today - timedelta(days=1)
        PortfolioSnapshot.objects.create(
            portfolio=portfolio, date=yesterday, value=Decimal("400.00")
        )
        PortfolioSnapshot.objects.create(
            portfolio=portfolio, date=today, value=Decimal("420.00")
        )
        assert PortfolioSnapshot.objects.filter(portfolio=portfolio).count() == 2

    def test_query_by_date_range(self, portfolio_factory):
        portfolio = portfolio_factory()
        today = date.today()
        for i in range(5):
            PortfolioSnapshot.objects.create(
                portfolio=portfolio,
                date=today - timedelta(days=i),
                value=Decimal("100.00"),
            )
        start = today - timedelta(days=2)
        results = PortfolioSnapshot.objects.filter(
            portfolio=portfolio, date__gte=start
        )
        assert results.count() == 3

    def test_celery_task_creates_snapshot(self, portfolio_factory):
        portfolio = portfolio_factory()
        with patch("apps.wallet.models.get_price", return_value=None):
            capture_portfolio_snapshots()
        assert PortfolioSnapshot.objects.filter(portfolio=portfolio).exists()
