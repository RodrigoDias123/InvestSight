from pydantic import BaseModel
from decimal import Decimal

class ConvertResponse(BaseModel):
    from_currency: str
    to_currency: str
    amount: Decimal
    converted_amount: Decimal
