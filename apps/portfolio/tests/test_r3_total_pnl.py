import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from apps.apis.services.base import PriceResult
from apps.portfolio.models import Portfolio


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
    def create(**kwargs):
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", "user_r3"),
            email=kwargs.pop("email", "user_r3@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R3"),
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
        symbol = kwargs.pop("symbol", f"ASSET{_counter[0]:04d}")

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


@pytest.mark.django_db
class TestTotalPnl:
    def test_pnl_positive(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(
            portfolio=portfolio,
            total_cost=Decimal("100.00"),
            current_value=Decimal("150.00"),
        )
        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("50.00")
        assert pnl["percentage"] == Decimal("50.00")

    def test_pnl_negative(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r3_neg", email="user_r3_neg@example.com"
        )
        holding_factory(
            portfolio=portfolio,
            total_cost=Decimal("200.00"),
            current_value=Decimal("150.00"),
        )
        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("-50.00")
        assert pnl["percentage"] == Decimal("-25.00")

    def test_pnl_zero(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r3_zero", email="user_r3_zero@example.com"
        )
        holding_factory(
            portfolio=portfolio,
            total_cost=Decimal("100.00"),
            current_value=Decimal("100.00"),
        )
        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("0")
        assert pnl["percentage"] == Decimal("0")

    def test_pnl_empty_portfolio_returns_zero(self, portfolio_factory):
        portfolio = portfolio_factory(
            username="user_r3_empty", email="user_r3_empty@example.com"
        )
        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("0")
        assert pnl["percentage"] == Decimal("0")
