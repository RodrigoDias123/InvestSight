import pytest
from apps.apis import config


@pytest.mark.L9
class TestConfig:
    def test_use_mock_data_default(self):
        assert config.USE_MOCK_DATA is not None

    def test_provider_registry(self):
        assert "BTC" in config.PROVIDER_REGISTRY
        assert "ETH" in config.PROVIDER_REGISTRY
        assert "AAPL" in config.PROVIDER_REGISTRY
        assert "TSLA" in config.PROVIDER_REGISTRY

    def test_cache_ttl_values(self):
        assert config.CACHE_TTL_CRYPTO > 0
        assert config.CACHE_TTL_STOCK > 0
