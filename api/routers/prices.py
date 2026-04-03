from fastapi import APIRouter, HTTPException
from api.schemas.price import PriceResponse, PriceListResponse
from api.schemas.history import PriceHistoryResponse
from apps.apis.services.cache import (
    get_price_with_cache,
    get_all_prices_with_cache,
)
from apps.apis.services.unified import unified_price_service
from apps.apis.services.logging import get_logger
from api.schemas.convert import ConvertResponse

router = APIRouter()
logger = get_logger("prices_router")


# Get Price, supports multi-currency
@router.get("/{symbol}", response_model=PriceResponse)
async def get_price_route(symbol: str, target_currency: str = "USD"):
    symbol = symbol.upper()
    target_currency = target_currency.upper()

    logger.info("price_request_received", symbol=symbol, target_currency=target_currency)

    result = get_price_with_cache(symbol, target_currency=target_currency)

    if result is None:
        logger.warning("price_not_found", symbol=symbol)
        raise HTTPException(status_code=404, detail="Price not found")

    logger.info(
        "price_request_success",
        symbol=symbol,
        provider=result.provider,
        currency=result.currency,
    )

    return PriceResponse(
        symbol=result.symbol,
        price=result.price,
        currency=result.currency,
        provider=result.provider,
        timestamp=result.timestamp,
    )

# Get all Prices, supports multi-currency
@router.get("/", response_model=PriceListResponse)
async def get_all_prices_route(target_currency: str = "USD"):
    target_currency = target_currency.upper()

    logger.info("all_prices_request_received", target_currency=target_currency)

    results = get_all_prices_with_cache(target_currency=target_currency)

    logger.info("all_prices_request_success", count=len(results))

    return PriceListResponse(
        prices={
            symbol: PriceResponse(
                symbol=pr.symbol,
                price=pr.price,
                currency=pr.currency,
                provider=pr.provider,
                timestamp=pr.timestamp,
            )
            for symbol, pr in results.items()
        }
    )

# Get price History
@router.get("/history/{symbol}", response_model=PriceHistoryResponse)
async def get_price_history_route(symbol: str, days: int = 30):
    symbol = symbol.upper()

    logger.info("history_request_received", symbol=symbol, days=days)

    try:
        history = unified_price_service.get_history(symbol, days)
    except Exception as e:
        logger.error("history_request_failed", symbol=symbol, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    logger.info("history_request_success", symbol=symbol, points=len(history))

    return PriceHistoryResponse(
        symbol=symbol,
        days=days,
        history=history,
    )


