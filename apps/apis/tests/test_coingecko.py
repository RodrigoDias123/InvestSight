import pytest
from unittest.mock import patch, MagicMock

from apps.apis.services.coingecko import CoinGeckoService
from apps.apis.exceptions import ProviderUnavailable


@pytest.mark.L2
class TestCoinGeckoService:
    @patch("apps.apis.services.coingecko.requests.get")
    def test_get_price_btc(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"bitcoin": {"usd": 67500.00}}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        service = CoinGeckoService()
        result = service.get_price("BTC")

        assert result is not None
        assert result.symbol == "BTC"
        assert result.price == 67500.00
        assert result.provider == "coingecko"

    def test_get_price_unknown_symbol(self):
        service = CoinGeckoService()
        result = service.get_price("UNKNOWN")
        assert result is None
