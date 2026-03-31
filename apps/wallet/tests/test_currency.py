import pytest
from decimal import Decimal


class TestCurrency:
    def test_decimal_from_float(self):
        value = Decimal("0.1") + Decimal("0.2")
        assert value == Decimal("0.3")

    def test_decimal_precision(self):
        value = Decimal("12345.67890123")
        assert value.as_tuple().exponent == -8
