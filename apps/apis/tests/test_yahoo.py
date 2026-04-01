import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from apps.apis.services.yahoo import YahooFinanceService


@pytest.mark.L3
class TestYahooFinanceService:
    @patch("apps.apis.services.yahoo.YAHOO_FINANCE_ENABLED", True)
    @patch("apps.apis.services.yahoo.yfinance.Ticker")
    def test_get_price_aapl(self, mock_ticker):
        mock_info = {"currentPrice": 175.50}
        mock_ticker.return_value.info = mock_info

        service = YahooFinanceService()
        result = service.get_price("AAPL")

        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == Decimal("175.50")
        assert result.provider == "yahoo"

    @patch("apps.apis.services.yahoo.YAHOO_FINANCE_ENABLED", False)
    def test_get_price_disabled(self):
        service = YahooFinanceService()
        result = service.get_price("AAPL")
        assert result is None
