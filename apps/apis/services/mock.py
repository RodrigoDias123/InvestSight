from datetime import datetime
from decimal import Decimal
from typing import Optional

from apps.apis.services.base import PriceResult, PriceService


# Hard‑coded mock prices used for testing or fallback scenarios
MOCK_PRICES = {
    "BTC": Decimal("67500.00"),
    "ETH": Decimal("3450.00"),
    "AAPL": Decimal("175.50"),
    "TSLA": Decimal("250.00"),
}


class MockPriceService(PriceService):
    """
    A mock implementation of PriceService.
    Useful for development, testing, or when external providers are unavailable.
    """

    def get_price(self, symbol: str) -> Optional[PriceResult]:
        # Normalize symbol to uppercase
        symbol = symbol.upper()

        # If the symbol is not in the mock price list, return None
        if symbol not in MOCK_PRICES:
            return None

        # Return a PriceResult with the mock price
        return PriceResult(
            symbol=symbol,
            price=MOCK_PRICES[symbol],
            currency="USD",
            provider="mock",
            timestamp=datetime.utcnow(),
        )

    def get_all_prices(self) -> dict[str, PriceResult]:
        """
        Returns a dictionary of PriceResult objects for all mock symbols.
        """
        # Build a dict by calling get_price() for each symbol
        return {symbol: self.get_price(symbol) for symbol in MOCK_PRICES}
