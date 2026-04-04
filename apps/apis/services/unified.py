import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from apps.apis.services.base import PriceResult
from apps.apis.services.mock import MockPriceService
from apps.apis.services.coingecko import CoinGeckoService
from apps.apis.services.yahoo import YahooFinanceService
from apps.apis.services.retry import with_retry
from apps.apis.services.logging import get_logger
from apps.apis.settings import settings
import requests

DATA_FILE = Path("apps/apis/data/prices.json")
logger = get_logger("unified")
USE_MOCK_DATA = settings.USE_MOCK_DATA


def load_data_file() -> dict:
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        DATA_FILE.write_text(json.dumps({
            "coingecko_ids": {},
            "yahoo_ids": {},
            "prices": {},
            "timestamp": None
        }, indent=4))

    try:
        return json.loads(DATA_FILE.read_text())
    except json.JSONDecodeError:
        logger.error("json_file_corrupted")
        return {
            "coingecko_ids": {},
            "yahoo_ids": {},
            "prices": {},
            "timestamp": None
        }


def save_data_file(data: dict):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, indent=4))


class UnifiedPriceService:
    """
    Unified interface for:
      - price lookup
      - multi-currency conversion
      - historical data
      - fallback logic
    """

    def __init__(self):
        self.mock_service = MockPriceService()
        self.coingecko_service = CoinGeckoService()
        self.yahoo_service = YahooFinanceService()


    def convert_currency(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        if from_currency == to_currency:
            return amount

        try:
            url = f"https://api.frankfurter.app/latest?amount={amount}&from={from_currency}&to={to_currency}"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                logger.error("fx_api_error", status=response.status_code)
                return amount

            data = response.json()

            rate = list(data["rates"].values())[0]

            return Decimal(str(rate))

        except Exception as e:
            logger.error("fx_conversion_exception", error=str(e))
            return amount

    def get_all_currency(self):
        try:
            url = "https://api.frankfurter.app/currencies"
            response = requests.get(url, timeout=5)

            if response.status_code != 200:
                logger.error("fx_currencies_api_error", status=response.status_code)
                return {}

            return response.json()

        except Exception as e:
            logger.error("fx_currencies_exception", error=str(e))
            return {}


    @with_retry
    def get_price(self, symbol: str, target_currency: str = "USD") -> Optional[PriceResult]:
        symbol = symbol.upper()
        target_currency = target_currency.upper()

        logger.info("unified_price_request", symbol=symbol, target_currency=target_currency)

        # Mock override
        if USE_MOCK_DATA:
            logger.warning("mock_mode_enabled", symbol=symbol)
            result = self.mock_service.get_price(symbol)
            if result and result.currency != target_currency:
                result.price = self.convert_currency(result.price, result.currency, target_currency)
                result.currency = target_currency
            return result

        provider = settings.PROVIDER_REGISTRY.get(symbol)

        # Load last valid JSON value
        data = load_data_file()
        last_raw = data.get("prices", {}).get(symbol)
        last_valid = None

        if last_raw:
            try:
                last_valid = PriceResult(
                    symbol=last_raw["symbol"],
                    price=Decimal(last_raw["price"]),
                    currency=last_raw["currency"],
                    provider=last_raw["provider"],
                    timestamp=datetime.fromisoformat(last_raw["timestamp"]),
                )
                logger.info("json_last_valid_found", symbol=symbol)
            except Exception:
                logger.error("json_last_valid_parse_error", symbol=symbol)

        # Try provider
        try:
            if provider == "coingecko":
                result = self.coingecko_service.get_price(symbol)
            elif provider == "yahoo":
                result = self.yahoo_service.get_price(symbol)
            else:
                logger.warning("provider_not_found", symbol=symbol)
                result = None

            if result:
                # Convert currency if needed
                if result.currency != target_currency:
                    result.price = self.convert_currency(result.price, result.currency, target_currency)
                    result.currency = target_currency

                logger.info("provider_success", symbol=symbol, provider=result.provider)
                return result

        except Exception as e:
            logger.error("provider_error", symbol=symbol, provider=provider, error=str(e))
            if last_valid:
                logger.warning("fallback_last_valid", symbol=symbol)
                return last_valid

        # Fallback to last valid JSON
        if last_valid:
            logger.warning("fallback_last_valid_no_exception", symbol=symbol)
            return last_valid

        # Fallback to mock
        logger.warning("fallback_mock", symbol=symbol)
        result = self.mock_service.get_price(symbol)

        if result is None:
            result = PriceResult(
                symbol=symbol,
                price=Decimal("0"),
                currency="USD",
                provider="mock",
                timestamp=datetime.utcnow(),
            )

        if result.currency != target_currency:
            result.price = self.convert_currency(result.price, result.currency, target_currency)
            result.currency = target_currency

        return result


    @with_retry
    def get_all_prices(self, target_currency: str = "USD") -> Dict[str, PriceResult]:
        target_currency = target_currency.upper()

        if settings.USE_MOCK_DATA:
            logger.warning("mock_mode_enabled_all_prices")
            results = self.mock_service.get_all_prices()
        else:
            results = {}

            # CoinGecko
            try:
                cg = self.coingecko_service.get_all_prices()
                results.update(cg)
            except Exception as e:
                logger.error("coingecko_all_prices_error", error=str(e))

            # Yahoo
            try:
                yf = self.yahoo_service.get_all_prices()
                results.update(yf)
            except Exception as e:
                logger.error("yahoo_all_prices_error", error=str(e))

        # Convert all to target currency
        for pr in results.values():
            if pr.currency != target_currency:
                pr.price = self.convert_currency(pr.price, pr.currency, target_currency)
                pr.currency = target_currency

        return results

    
    def update_all(self):
        """
        Fetch all prices from providers and store them in the local JSON file.
        Used by the scheduler to keep fallback data fresh.
        """
        logger.info("scheduled_update_started")

        try:
            # Get all prices in USD (base currency)
            prices = self.get_all_prices(target_currency="USD")

            # Load existing JSON
            data = load_data_file()

            # Save updated prices
            data["prices"] = {
                symbol: {
                    "symbol": pr.symbol,
                    "price": str(pr.price),
                    "currency": pr.currency,
                    "provider": pr.provider,
                    "timestamp": pr.timestamp.isoformat(),
                }
                for symbol, pr in prices.items()
            }

            data["timestamp"] = datetime.utcnow().isoformat()

            save_data_file(data)

            logger.info("scheduled_update_success", count=len(prices))

        except Exception as e:
            logger.error("scheduled_update_failed", error=str(e))
            raise


    def get_history(self, symbol: str, days: int = 30):
        symbol = symbol.upper()
        provider = settings.PROVIDER_REGISTRY.get(symbol)

        if provider == "coingecko":
            return self.coingecko_service.get_history(symbol, days)

        if provider == "yahoo":
            return self.yahoo_service.get_history(symbol, days)

        raise ValueError(f"No provider for symbol {symbol}")


_unified_service = None


def _get_service() -> UnifiedPriceService:
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedPriceService()
    return _unified_service


def get_price(symbol: str, target_currency: str = "USD") -> Optional[PriceResult]:
    return _get_service().get_price(symbol, target_currency)


def get_all_prices(target_currency: str = "USD") -> Dict[str, PriceResult]:
    return _get_service().get_all_prices(target_currency)


unified_price_service = _get_service()