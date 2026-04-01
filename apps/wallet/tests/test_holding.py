import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch

from apps.apis.services.base import PriceResult
from apps.wallet.models import Holding, Asset, AssetType
from apps.portfolio.models import Portfolio


class TestHolding:
    @pytest.fixture
    def asset(self):
        return Asset(symbol="BTC", name="Bitcoin", asset_type=AssetType.CRYPTO)

    @pytest.fixture
    def portfolio(self):
        return Portfolio(pk=1, name="TestPortfolio", user_id=1)

    def test_holding_str(self, asset, portfolio):
        holding = Holding(
            portfolio=portfolio,
            asset=asset,
            quantity=Decimal("1.5"),
            avg_buy_price=Decimal("50000.00"),
        )
        assert "BTC" in str(holding)

    def test_total_cost(self, asset, portfolio):
        holding = Holding(
            portfolio=portfolio,
            asset=asset,
            quantity=Decimal("2.0"),
            avg_buy_price=Decimal("50000.00"),
        )
        assert holding.total_cost == Decimal("100000.00")

    @patch("apps.wallet.models.get_price")
    def test_current_value(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = PriceResult(
            symbol="BTC",
            price=Decimal("67500.00"),
            currency="USD",
            provider="mock",
            timestamp=datetime.utcnow(),
        )
        holding = Holding(
            portfolio=portfolio,
            asset=asset,
            quantity=Decimal("1.0"),
            avg_buy_price=Decimal("50000.00"),
        )
        assert holding.current_value == Decimal("67500.00")

    @patch("apps.wallet.models.get_price")
    def test_current_value_no_price(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = None
        holding = Holding(
            portfolio=portfolio,
            asset=asset,
            quantity=Decimal("1.0"),
            avg_buy_price=Decimal("50000.00"),
        )
        assert holding.current_value is None

