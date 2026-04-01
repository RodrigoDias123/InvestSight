import pytest
from decimal import Decimal

from apps.apis.services.mock import MockPriceService


@pytest.mark.L1
class TestMockPriceService:
    def test_get_price_btc(self):
        service = MockPriceService()
        result = service.get_price("BTC")
        assert result is not None
        assert result.symbol == "BTC"
        assert result.price == Decimal("67500.00")
        assert result.currency == "USD"
        assert result.provider == "mock"

    def test_get_price_eth(self):
        service = MockPriceService()
        result = service.get_price("ETH")
        assert result is not None
        assert result.symbol == "ETH"
        assert result.price == Decimal("3450.00")

    def test_get_price_aapl(self):
        service = MockPriceService()
        result = service.get_price("AAPL")
        assert result is not None
        assert result.symbol == "AAPL"
        assert result.price == Decimal("175.50")

    def test_get_price_tsla(self):
        service = MockPriceService()
        result = service.get_price("TSLA")
        assert result is not None
        assert result.symbol == "TSLA"
        assert result.price == Decimal("250.00")

    def test_get_price_unknown(self):
        service = MockPriceService()
        result = service.get_price("UNKNOWN")
        assert result is None

    def test_get_price_case_insensitive(self):
        service = MockPriceService()
        result = service.get_price("btc")
        assert result is not None
        assert result.symbol == "BTC"

    def test_get_all_prices(self):
        service = MockPriceService()
        result = service.get_all_prices()
        assert len(result) == 4
        assert "BTC" in result
        assert "ETH" in result
        assert "AAPL" in result
        assert "TSLA" in result
