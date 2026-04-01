from datetime import date
from typing import Optional
from django.core.cache import cache
from apps.apis.config import CACHE_TTL_CRYPTO, CACHE_TTL_STOCK, PROVIDER_REGISTRY
from apps.apis.services.base import PriceResult
from apps.apis.services.unified import UnifiedPriceService


_unified_service = None

# If is not created, will create the service, otherwise will reuse
def _get_unified_service():
    global _unified_service
    if _unified_service is None:
        _unified_service = UnifiedPriceService()
    return _unified_service

# Store the cache for 5 min
def _get_cache_ttl(symbol: str) -> int:
    #Check for the provider, if not found, default to mock
    provider = PROVIDER_REGISTRY.get(symbol.upper(), "mock")
    if provider == "coingecko":
        return CACHE_TTL_CRYPTO
    elif provider == "yahoo":
        return CACHE_TTL_STOCK
    return 300  #300s = 5min

# Create a unique key for the symbol
def _make_cache_key(symbol: str) -> str:
    # Gets today date
    today = date.today().isoformat()
    return f"price:{symbol.upper()}:{today}"

# Try to read the price from cache
def get_cached_price(symbol: str) -> Optional[PriceResult]:
    # Create cache key
    cache_key = _make_cache_key(symbol)
    # Try to fetch the cache value
    cached = cache.get(cache_key)
    # If found return it
    if cached:
        return cached
    # Else return None
    return None

# Save prices into the cache
def set_cached_price(symbol: str, price_result: PriceResult) -> None:
    # Create cache key
    cache_key = _make_cache_key(symbol)
    # Determinate how long will store it
    ttl = _get_cache_ttl(symbol)
    # Store it in django cache
    cache.set(cache_key, price_result, ttl)

# Fecth prices with cache
def get_price_with_cache(symbol: str) -> Optional[PriceResult]:
    # Check if the cache have price
    cached = get_cached_price(symbol)
    # If have, return it
    if cached:
       return cached
    # Otherwise, call the unified service to fetch the price
    price_result = _get_unified_service().get_price(symbol)
    if price_result:
        set_cached_price(symbol, price_result)

    return price_result