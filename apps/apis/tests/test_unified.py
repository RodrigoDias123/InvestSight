import pytest
from unittest.mock import patch

from apps.apis.services.unified import UnifiedPriceService, get_price


@pytest.mark.L4
class TestUnifiedPriceService:
    @patch("apps.apis.services.unified.USE_MOCK_DATA", True)
    def test_get_price_uses_mock(self):
        service = UnifiedPriceService()
        result = service.get_price("BTC")
        assert result is not None
        assert result.provider == "mock"

    @patch("apps.apis.services.unified.USE_MOCK_DATA", False)
    def test_get_price_fallback_to_mock(self):
        service = UnifiedPriceService()
        result = service.get_price("UNKNOWN")
        assert result is not None
        assert result.provider == "mock"
