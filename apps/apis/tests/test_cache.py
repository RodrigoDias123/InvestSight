import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from decimal import Decimal


@pytest.mark.L5
class TestCache:
    @patch("apps.apis.services.cache.cache")
    def test_get_cached_price_hit(self, mock_cache):
        from apps.apis.services.cache import get_cached_price
        from apps.apis.services.base import PriceResult

        mock_result = PriceResult(
            symbol="BTC",
            price=Decimal("67500.00"),
            currency="USD",
            provider="mock",
            timestamp=datetime.utcnow(),
        )
        mock_cache.get.return_value = mock_result

        result = get_cached_price("BTC")
        assert result is not None

    @patch("apps.apis.services.cache.cache")
    def test_get_cached_price_miss(self, mock_cache):
        from apps.apis.services.cache import get_cached_price

        mock_cache.get.return_value = None

        result = get_cached_price("BTC")
        assert result is None
