from typing import Optional
from apps.apis.config import PROVIDER_REGISTRY, USE_MOCK_DATA
from apps.apis.services.base import PriceResult
from apps.apis.services.mock import MockPriceService
from apps.apis.services.coingecko import CoinGeckoService
from apps.apis.services.yahoo import YahooFinanceService


class UnifiedPriceService:
    """
    A unified interface that decides which provider to use (CoinGecko, Yahoo, or Mock).
    It acts as a router and fallback mechanism for price lookups.
    """

    def __init__(self):
        # Initialize all provider services
        self.mock_service = MockPriceService()
        self.coingecko_service = CoinGeckoService()
        self.yahoo_service = YahooFinanceService()

    def get_price(self, symbol: str) -> Optional[PriceResult]:
        """
        Returns the price for a single symbol.
        Provider selection is based on PROVIDER_REGISTRY.
        Falls back to mock data if:
        - USE_MOCK_DATA is True
        - The provider fails
        - The symbol is unknown
        """
        # If mock mode is enabled, always return mock data
        if USE_MOCK_DATA:
            return self.mock_service.get_price(symbol)

        symbol = symbol.upper()
        provider = PROVIDER_REGISTRY.get(symbol)

        # Route to CoinGecko
        if provider == "coingecko":
            try:
                return self.coingecko_service.get_price(symbol)
            except Exception:
                # Fallback to mock if provider fails
                return self.mock_service.get_price(symbol)

        # Route to Yahoo Finance
        elif provider == "yahoo":
            try:
                return self.yahoo_service.get_price(symbol)
            except Exception:
                return self.mock_service.get_price(symbol)

        # Unknown provider → fallback to mock
        return self.mock_service.get_price(symbol)

    def get_all_prices(self) -> dict[str, PriceResult]:
        """
        Returns prices for all symbols defined in PROVIDER_REGISTRY.
        - Uses real providers unless USE_MOCK_DATA is True
        - Merges results from CoinGecko and Yahoo
        - Missing symbols fall back to mock data
        """
        # If mock mode is enabled, return all mock prices
        if USE_MOCK_DATA:
            return self.mock_service.get_all_prices()

        result = {}

        # Try to fetch all CoinGecko prices
        try:
            result.update(self.coingecko_service.get_all_prices())
        except Exception:
            pass  # Ignore provider failure

        # Try to fetch all Yahoo prices
        try:
            result.update(self.yahoo_service.get_all_prices())
        except Exception:
            pass

        # Ensure all symbols have a price (fallback to mock)
        for symbol in PROVIDER_REGISTRY:
            if symbol not in result:
                mock_result = self.mock_service.get_price(symbol)
                if mock_result:
                    result[symbol] = mock_result

        return result


# Singleton instance for global access
_unified_service = None

def get_price(symbol: str) -> Optional[PriceResult]:
    """
    Module-level helper that lazily initializes UnifiedPriceService.
    """
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedPriceService()
    return _unified_service.get_price(symbol)


def get_all_prices() -> dict[str, PriceResult]:
    """
    Module-level helper for fetching all prices.
    """
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedPriceService()
    return _unified_service.get_all_prices()
