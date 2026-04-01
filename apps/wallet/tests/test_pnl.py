import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import patch, MagicMock

from apps.apis.services.base import PriceResult
from apps.wallet.models import Holding, Asset, AssetType
from apps.portfolio.models import Portfolio


class TestPnL:
    @pytest.fixture
    def asset(self):
        return Asset(symbol="BTC", name="Bitcoin", asset_type=AssetType.CRYPTO)

    @pytest.fixture
    def portfolio(self):
        return Portfolio(pk=1, name="TestPortfolio", user_id=1)

    @patch("apps.wallet.models.get_price")
    def test_profit_loss_gain(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = PriceResult(
            symbol="BTC", price=Decimal("67500.00"), currency="USD",
            provider="mock", timestamp=datetime.utcnow(),
        )
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("1.0"), avg_buy_price=Decimal("50000.00"),
        )
        assert holding.profit_loss == Decimal("17500.00")

    @patch("apps.wallet.models.get_price")
    def test_profit_loss_loss(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = PriceResult(
            symbol="BTC", price=Decimal("40000.00"), currency="USD",
            provider="mock", timestamp=datetime.utcnow(),
        )
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("1.0"), avg_buy_price=Decimal("50000.00"),
        )
        assert holding.profit_loss == Decimal("-10000.00")

    @patch("apps.wallet.models.get_price")
    def test_profit_loss_breakeven(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = PriceResult(
            symbol="BTC", price=Decimal("50000.00"), currency="USD",
            provider="mock", timestamp=datetime.utcnow(),
        )
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("1.0"), avg_buy_price=Decimal("50000.00"),
        )
        assert holding.profit_loss == Decimal("0")

    @patch("apps.wallet.models.get_price")
    def test_pnl_pct_gain(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = PriceResult(
            symbol="BTC", price=Decimal("67500.00"), currency="USD",
            provider="mock", timestamp=datetime.utcnow(),
        )
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("1.0"), avg_buy_price=Decimal("50000.00"),
        )
        assert holding.pnl_pct == Decimal("35")

    def test_pnl_pct_zero_cost(self, asset, portfolio):
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("0"), avg_buy_price=Decimal("0"),
        )
        assert holding.pnl_pct is None

    @patch("apps.wallet.models.get_price")
    def test_pnl_pct_none_when_current_value_none(self, mock_get_price, asset, portfolio):
        mock_get_price.return_value = None
        holding = Holding(
            portfolio=portfolio, asset=asset,
            quantity=Decimal("1.0"), avg_buy_price=Decimal("50000.00"),
        )
        assert holding.pnl_pct is None
