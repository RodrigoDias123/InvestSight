import json
import environ
from .schema import Settings, DEFAULT_PROVIDER_REGISTRY

env = environ.Env()
environ.Env.read_env()  # Load .env automatically

# Load override registry from .env (string → dict)
raw_registry = env("PROVIDER_REGISTRY", default="{}")
override_registry = json.loads(raw_registry)

# Merge defaults + overrides
merged_registry = {**DEFAULT_PROVIDER_REGISTRY, **override_registry}

settings = Settings(
    USE_MOCK_DATA=env.bool("USE_MOCK_DATA", False),
    YAHOO_FINANCE_ENABLED=env.bool("YAHOO_FINANCE_ENABLED", True),

    COINGECKO_BASE_URL=env("COINGECKO_BASE_URL", default="https://api.coingecko.com/api/v3"),
    COINGECKO_API_KEY=env("COINGECKO_API_KEY", default="CG-Zg73FQsCZpyFVJp8Mx2y4Zq8"),

    CACHE_TTL_CRYPTO=env.int("CACHE_TTL_CRYPTO", 300),
    CACHE_TTL_STOCK=env.int("CACHE_TTL_STOCK", 600),
    CACHE_TTL_SECONDS=env.int("CACHE_TTL_SECONDS", 300),

    RETRY_MAX_ATTEMPTS=env.int("RETRY_MAX_ATTEMPTS", 3),

    LOG_LEVEL=env("LOG_LEVEL", default="DEBUG"),

    PROVIDER_REGISTRY=merged_registry,
)
