import pytest
from apps.apis.exceptions import PriceAPIError, ProviderUnavailable


@pytest.mark.L6
class TestErrorHandling:
    def test_price_api_error(self):
        with pytest.raises(PriceAPIError):
            raise PriceAPIError("Test error")

    def test_provider_unavailable(self):
        with pytest.raises(ProviderUnavailable):
            raise ProviderUnavailable("Provider down")
