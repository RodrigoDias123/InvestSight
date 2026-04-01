from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

#Model
@dataclass
class PriceResult:
    symbol: str
    price: Decimal
    currency: str
    provider: str
    timestamp: datetime

class PriceService(ABC):
    @abstractmethod
    def get_price(self, symbol: str) -> Optional[PriceResult]:
        pass

    @abstractmethod
    def get_all_prices(self) -> dict[str, PriceResult]:
        pass
