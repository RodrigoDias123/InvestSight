import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.portfolio.models import Portfolio


class TestPortfolioTotals:
    @patch("apps.portfolio.models.Portfolio.holdings")
    def test_total_invested(self, mock_holdings):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_holdings.aggregate.return_value = {"total": Decimal("100000.00")}

        assert portfolio.total_invested == Decimal("100000.00")

    @patch("apps.portfolio.models.Portfolio.holdings")
    def test_total_invested_none(self, mock_holdings):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_holdings.aggregate.return_value = {"total": None}

        assert portfolio.total_invested == Decimal("0")

    @patch("apps.portfolio.models.Portfolio.holdings")
    def test_current_value_empty(self, mock_holdings):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_holdings.select_related.return_value = []

        assert portfolio.current_value == Decimal("0")
