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
    _counter = [0]

    def create(**kwargs):
        _counter[0] += 1
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", f"user_r6_{_counter[0]}"),
            email=kwargs.pop("email", f"user_r6_{_counter[0]}@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", f"Portfolio R6 {_counter[0]}"),
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
        symbol = kwargs.pop("symbol", f"R6ASSET{_counter[0]:04d}")

        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", symbol),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )

        if total_cost is not None:
            avg_buy_price = total_cost / quantity if quantity != 0 else Decimal("0")
        else:
            avg_buy_price = kwargs.pop("avg_buy_price", Decimal("100"))

        if current_value is not None:
            price_registry[symbol.upper()] = current_value / quantity if quantity != 0 else Decimal("0")

        return Holding.objects.create(
            portfolio=portfolio,
            asset=asset,
            quantity=quantity,
            avg_buy_price=avg_buy_price,
        )

    return create


@pytest.mark.django_db
@pytest.mark.parametrize("holdings_data,expected_total", [
    ([], Decimal("0")),                                           # vazio
    ([Decimal("100.00")], Decimal("100.00")),                    # 1 holding
    ([Decimal("100.00"), Decimal("200.00")], Decimal("300.00")), # multi-holding
    ([Decimal("0.00")], Decimal("0")),                           # preço zero
])
def test_portfolio_total_invested(holdings_data, expected_total, portfolio_factory, holding_factory):
    portfolio = portfolio_factory()
    for cost in holdings_data:
        holding_factory(portfolio=portfolio, total_cost=cost)
    result = portfolio.total_invested
    assert abs(result - expected_total) < Decimal("0.01")


@pytest.mark.django_db
@pytest.mark.parametrize("holdings_data,expected_value", [
    ([], Decimal("0")),
    ([Decimal("150.00")], Decimal("150.00")),
    ([Decimal("150.00"), Decimal("250.00")], Decimal("400.00")),
    ([Decimal("0.00")], Decimal("0")),
])
def test_portfolio_current_value(holdings_data, expected_value, portfolio_factory, holding_factory):
    portfolio = portfolio_factory()
    for val in holdings_data:
        holding_factory(portfolio=portfolio, current_value=val)
    result = portfolio.current_value
    assert abs(result - expected_value) < Decimal("0.01")
