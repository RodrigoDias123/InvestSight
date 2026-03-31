import json
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
            username=kwargs.pop("username", "user_r8"),
            email=kwargs.pop("email", "user_r8@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R8"),
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

        _counter[0] += 1
        symbol = kwargs.pop("symbol", f"R8ASSET{_counter[0]:04d}")

        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", symbol),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )

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
class TestAllocationBreakdown:
    def test_percentages_sum_to_100(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(portfolio=portfolio, current_value=Decimal("300.00"))
        holding_factory(portfolio=portfolio, current_value=Decimal("700.00"))
        breakdown = portfolio.allocation_breakdown
        total_pct = sum(item["pct_of_portfolio"] for item in breakdown)
        assert round(total_pct, 2) == Decimal("100.00")

    def test_sorted_by_percentage_desc(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r8_sort", email="user_r8_sort@example.com"
        )
        holding_factory(portfolio=portfolio, current_value=Decimal("200.00"))
        holding_factory(portfolio=portfolio, current_value=Decimal("800.00"))
        breakdown = portfolio.allocation_breakdown
        pcts = [item["pct_of_portfolio"] for item in breakdown]
        assert pcts == sorted(pcts, reverse=True)

    def test_is_json_serializable(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r8_json", email="user_r8_json@example.com"
        )
        holding_factory(portfolio=portfolio, current_value=Decimal("500.00"))
        breakdown = portfolio.allocation_breakdown
        assert json.dumps(
            [
                {
                    k: float(v) if isinstance(v, Decimal) else v
                    for k, v in item.items()
                }
                for item in breakdown
            ]
        )

    def test_rounded_to_2_decimal_places(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r8_round", email="user_r8_round@example.com"
        )
        holding_factory(portfolio=portfolio, current_value=Decimal("333.33"))
        holding_factory(portfolio=portfolio, current_value=Decimal("333.33"))
        holding_factory(portfolio=portfolio, current_value=Decimal("333.34"))
        breakdown = portfolio.allocation_breakdown
        for item in breakdown:
            assert item["pct_of_portfolio"] == round(item["pct_of_portfolio"], 2)
