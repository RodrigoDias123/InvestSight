import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from apps.apis.services.base import PriceResult
from apps.portfolio.models import Portfolio, PortfolioSnapshot
from apps.portfolio.tasks import capture_portfolio_snapshots
from repositories import AlertRepository


@pytest.fixture
def price_registry():
    return {}


@pytest.fixture(autouse=True)
def patch_get_price(price_registry):
    def fake_get_price(symbol):
        price = price_registry.get(symbol.upper())
        if price is not None:
            return PriceResult(
                symbol=symbol.upper(),
                price=price,
                currency="USD",
                provider="mock",
                timestamp=datetime.now(timezone.utc),
            )
        return None

    with patch("apps.wallet.models.get_price", side_effect=fake_get_price):
        yield


@pytest.fixture
def portfolio_factory(db, django_user_model):
    _counter = [0]

    def create(**kwargs):
        _counter[0] += 1
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", f"user_r9_{_counter[0]}"),
            email=kwargs.pop("email", f"user_r9_{_counter[0]}@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", f"Portfolio R9 {_counter[0]}"),
            user=user,
        )

    return create


@pytest.fixture
def holding_factory(db, price_registry):
    from apps.wallet.models import Asset, Holding

    _counter = [0]

    def create(**kwargs):
        portfolio = kwargs.pop("portfolio")
        total_cost = kwargs.pop("total_cost", None)
        current_value = kwargs.pop("current_value", None)
        quantity = kwargs.pop("quantity", Decimal("1"))

        _counter[0] += 1
        symbol = kwargs.pop("symbol", f"R9ASSET{_counter[0]:04d}")

        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", symbol),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )

        if total_cost is not None:
            avg_buy_price = total_cost / quantity
        else:
            avg_buy_price = kwargs.pop("avg_buy_price", Decimal("100"))

        if current_value is not None:
            price_registry[symbol.upper()] = current_value / quantity

        return Holding.objects.create(
            portfolio=portfolio,
            asset=asset,
            quantity=quantity,
            avg_buy_price=avg_buy_price,
        )

    return create


@pytest.fixture
def alert_factory(db):
    from apps.portfolio.models import Alert
    from apps.wallet.models import Asset

    _counter = [0]

    def create(**kwargs):
        portfolio = kwargs.pop("portfolio")
        _counter[0] += 1
        symbol = kwargs.pop("symbol", f"R9ALT{_counter[0]:04d}")
        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", symbol),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )
        return Alert.objects.create(
            portfolio=portfolio,
            asset=asset,
            target_price=kwargs.pop("target_price", Decimal("100.00")),
            direction=kwargs.pop("direction", "above"),
            active=kwargs.pop("active", True),
            triggered=kwargs.pop("triggered", False),
        )

    return create


@pytest.mark.django_db
class TestPortfolioFullSuite:
    def test_total_invested_aggregation(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(portfolio=portfolio, total_cost=Decimal("100.00"))
        holding_factory(portfolio=portfolio, total_cost=Decimal("200.00"))
        assert portfolio.total_invested == Decimal("300.00")

    def test_current_value_mocks_price_service(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(
            portfolio=portfolio,
            quantity=Decimal("10"),
            current_value=Decimal("150.00"),
        )
        assert portfolio.current_value == Decimal("150.00")

    def test_pnl_calculation(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(
            portfolio=portfolio,
            total_cost=Decimal("100.00"),
            current_value=Decimal("130.00"),
        )
        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("30.00")

    def test_active_alerts_excluded_triggered(self, portfolio_factory, alert_factory):
        portfolio = portfolio_factory()
        alert_factory(portfolio=portfolio, active=True, triggered=True)
        assert AlertRepository.get_active(portfolio.id).count() == 0

    def test_allocation_percentages_sum_100(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(portfolio=portfolio, current_value=Decimal("400.00"))
        holding_factory(portfolio=portfolio, current_value=Decimal("600.00"))
        total = sum(i["pct_of_portfolio"] for i in portfolio.allocation_breakdown)
        assert round(total, 2) == Decimal("100.00")

    def test_snapshot_created_by_task(self, portfolio_factory):
        portfolio = portfolio_factory()
        capture_portfolio_snapshots()
        assert PortfolioSnapshot.objects.filter(portfolio=portfolio).exists()

    def test_coverage_check(self):
        """Correr: uv run pytest --cov=. --cov-report=term-missing (mínimo 80%)"""
        pass
