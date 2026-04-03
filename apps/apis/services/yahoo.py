import yfinance
from datetime import datetime
from decimal import Decimal
from typing import Optional

from apps.apis.config import YAHOO_FINANCE_ENABLED
from apps.apis.exceptions import ProviderUnavailable
from apps.apis.services.base import PriceResult, PriceService


# List of stock symbols supported by this provider
STOCK_SYMBOLS = ["AAPL", "TSLA"]


class YahooFinanceService(PriceService):
    """
    Price provider that fetches stock prices using the yfinance library.
    Only works if YAHOO_FINANCE_ENABLED is True.
    """

    def get_price(self, symbol: str) -> Optional[PriceResult]:
        # If Yahoo Finance integration is disabled, skip provider
        if not YAHOO_FINANCE_ENABLED:
            return None

        # Normalize symbol
        symbol = symbol.upper()

        # If the symbol is not supported, return None
        if symbol not in STOCK_SYMBOLS:
            return None

        try:
            # Fetch ticker data from Yahoo Finance
            ticker = yfinance.Ticker(symbol)
            info = ticker.info

            # Try to get the current price; fallback to previous close
            price = info.get("currentPrice") or info.get("regularMarketPreviousClose")
            if price is None:
                return None

            # Build and return a PriceResult object
            return PriceResult(
                symbol=symbol,
                price=Decimal(str(price)),
                currency="USD",
                provider="yahoo",
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            # Wrap any error in a ProviderUnavailable exception
            raise ProviderUnavailable(f"Yahoo Finance API failed: {e}")

    def get_all_prices(self) -> dict[str, PriceResult]:
        """
        Returns prices for all supported stock symbols.
        Skips provider entirely if disabled.
        """
        if not YAHOO_FINANCE_ENABLED:
            return {}

        result = {}

        # Loop through supported symbols and fetch each price
        for symbol in STOCK_SYMBOLS:
            price_result = self.get_price(symbol)
            if price_result:
                result[symbol] = price_result

        return result
