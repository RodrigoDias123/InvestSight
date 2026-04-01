import requests
from datetime import datetime
from decimal import Decimal
from typing import Optional
from apps.apis.config import COINGECKO_BASE_URL, COINGECKO_API_KEY
from apps.apis.exceptions import ProviderUnavailable
from apps.apis.services.base import PriceResult, PriceService


# Mapping between your internal symbols and CoinGecko's coin IDs
COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

class CoinGeckoService(PriceService):
    def __init__(self):
        # Base URL and API key for CoinGecko
        self.base_url = COINGECKO_BASE_URL
        self.api_key = COINGECKO_API_KEY

    def get_price(self, symbol: str) -> Optional[PriceResult]:
        # Normalize symbol to uppercase
        symbol = symbol.upper()
        # If the symbol is not supported, return None
        if symbol not in COINGECKO_IDS:
            return None
        # Convert symbol to CoinGecko's internal ID
        coin_id = COINGECKO_IDS[symbol]
        # API endpoint for simple price lookup
        url = f"{self.base_url}/simple/price"
        # Query parameters
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
        }
        # Add API key if available
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key

        try:
            # Make the HTTP request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            # Extract the USD price
            price = data.get(coin_id, {}).get("usd")
            if price is None:
                return None

            # Return a PriceResult object
            return PriceResult(
                symbol=symbol,
                price=Decimal(str(price)),
                currency="USD",
                provider="coingecko",
                timestamp=datetime.utcnow(),
            )

        except requests.RequestException as e:
            # Wrap any request error in a custom exception
            raise ProviderUnavailable(f"CoinGecko API failed: {e}")

    def get_all_prices(self) -> dict[str, PriceResult]:
        # If base URL is missing, return empty result
        if not self.base_url:
            return {}

        # API endpoint for multiple coins
        url = f"{self.base_url}/simple/price"

        # Query parameters for all supported coins
        params = {
            "ids": ",".join(COINGECKO_IDS.values()),
            "vs_currencies": "usd",
        }

        # Add API key if available
        if self.api_key:
            params["x_cg_demo_api_key"] = self.api_key

        try:
            # Make the HTTP request
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()
            result = {}

            # Loop through all supported symbols
            for symbol, coin_id in COINGECKO_IDS.items():
                if coin_id in data:
                    price = data[coin_id].get("usd")
                    if price:
                        # Build a PriceResult for each coin
                        result[symbol] = PriceResult(
                            symbol=symbol,
                            price=Decimal(str(price)),
                            currency="USD",
                            provider="coingecko",
                            timestamp=datetime.utcnow(),
                        )

            return result

        except requests.RequestException as e:
            # Wrap any request error in a custom exception
            raise ProviderUnavailable(f"CoinGecko API failed: {e}")
