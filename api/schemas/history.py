from pydantic import BaseModel
from typing import List


class HistoryPoint(BaseModel):
    timestamp: int   # timestamp em milissegundos
    price: float     # preço em float (CoinGecko e Yahoo usam float)


class PriceHistoryResponse(BaseModel):
    symbol: str
    days: int
    history: List[HistoryPoint]
