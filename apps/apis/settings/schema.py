from pydantic import BaseModel, Field
from typing import Dict


DEFAULT_PROVIDER_REGISTRY: Dict[str, str] = {
    # --- CoinGecko ---
    "BTC": "coingecko",
    "ETH": "coingecko",
    "USDT": "coingecko",
    "USDC": "coingecko",
    "BNB": "coingecko",
    "XRP": "coingecko",
    "ADA": "coingecko",
    "DOGE": "coingecko",
    "SOL": "coingecko",
    "DOT": "coingecko",
    "TRX": "coingecko",
    "MATIC": "coingecko",
    "LTC": "coingecko",
    "BCH": "coingecko",
    "LINK": "coingecko",
    "XLM": "coingecko",
    "ATOM": "coingecko",
    "ETC": "coingecko",
    "XMR": "coingecko",
    "ALGO": "coingecko",
    "ICP": "coingecko",
    "FIL": "coingecko",
    "APT": "coingecko",
    "ARB": "coingecko",
    "OP": "coingecko",
    "AVAX": "coingecko",
    "NEAR": "coingecko",
    "HBAR": "coingecko",
    "VET": "coingecko",
    "AAVE": "coingecko",
    "SAND": "coingecko",
    "MANA": "coingecko",
    "EGLD": "coingecko",
    "XTZ": "coingecko",
    "FTM": "coingecko",
    "GRT": "coingecko",
    "RUNE": "coingecko",
    "KSM": "coingecko",
    "CAKE": "coingecko",
    "QNT": "coingecko",
    "FLOW": "coingecko",
    "CHZ": "coingecko",
    "CRV": "coingecko",
    "DYDX": "coingecko",

    # --- Yahoo Finance ---
    "AAPL": "yahoo",
    "TSLA": "yahoo",
    "MSFT": "yahoo",
    "AMZN": "yahoo",
    "NVDA": "yahoo",
    "META": "yahoo",
    "GOOGL": "yahoo",
    "NFLX": "yahoo",
    "JPM": "yahoo",
    "V": "yahoo",
    "MA": "yahoo",
    "BAC": "yahoo",
    "KO": "yahoo",
    "PEP": "yahoo",
    "DIS": "yahoo",
}



class Settings(BaseModel):
    # Feature flags
    USE_MOCK_DATA: bool = False
    YAHOO_FINANCE_ENABLED: bool = True

    # Providers
    COINGECKO_BASE_URL: str = Field(..., min_length=10)
    COINGECKO_API_KEY: str = Field(..., min_length=10)

    # Cache
    CACHE_TTL_CRYPTO: int = 300
    CACHE_TTL_STOCK: int = 600
    CACHE_TTL_SECONDS: int = 300

    # Retry
    RETRY_MAX_ATTEMPTS: int = 3

    # Logging
    LOG_LEVEL: str = "DEBUG"

    # Provider registry (default + override)
    PROVIDER_REGISTRY: Dict[str, str] = Field(
        default_factory=lambda: DEFAULT_PROVIDER_REGISTRY.copy()
    )
