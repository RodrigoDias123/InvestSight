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
            username=kwargs.pop("username", "user_r2"),
            email=kwargs.pop("email", "user_r2@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R2"),
            user=user,
        )

    return create


@pytest.fixture
def holding_factory(db, price_registry):
    from apps.wallet.models import Asset, Holding

    _counter = [0]

    def create(**kwargs):
        portfolio = kwargs.pop("portfolio")
        current_value = kwargs.pop("current_value", None)
        quantity = kwargs.pop("quantity", Decimal("1"))

        symbol = kwargs.pop("symbol", None)
        if symbol is None:
            _counter[0] += 1
            symbol = f"ASSET{_counter[0]:04d}"

        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", symbol),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )

        avg_buy_price = kwargs.pop("avg_buy_price", Decimal("100"))
        if current_value is not None:
            avg_buy_price = current_value / quantity
            price_registry[symbol.upper()] = avg_buy_price

        return Holding.objects.create(
            portfolio=portfolio,
            asset=asset,
            quantity=quantity,
            avg_buy_price=avg_buy_price,
        )

    def create_batch(size, **kwargs):
        return [create(**kwargs) for _ in range(size)]

    create.create_batch = create_batch
    return create


@pytest.mark.django_db
class TestCurrentPortfolioValue:
    def test_current_value_single_holding(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(
            portfolio=portfolio, quantity=Decimal("2"), current_value=Decimal("200.00")
        )
        assert portfolio.current_value == Decimal("200.00")

    def test_current_value_multiple_holdings(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r2_multi", email="user_r2_multi@example.com"
        )
        holding_factory(portfolio=portfolio, current_value=Decimal("100.00"))
        holding_factory(portfolio=portfolio, current_value=Decimal("300.00"))
        assert portfolio.current_value == Decimal("400.00")

    def test_current_value_empty_portfolio(self, portfolio_factory):
        portfolio = portfolio_factory(
            username="user_r2_empty", email="user_r2_empty@example.com"
        )
        assert portfolio.current_value == Decimal("0")

    def test_current_value_bulk_price_fetch(
        self, portfolio_factory, holding_factory, django_assert_num_queries
    ):
        portfolio = portfolio_factory(
            username="user_r2_bulk", email="user_r2_bulk@example.com"
        )
        holding_factory.create_batch(5, portfolio=portfolio)
        with django_assert_num_queries(1):
            _ = portfolio.current_value
