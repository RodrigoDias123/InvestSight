import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from apps.portfolio.models import Portfolio


class TestAllocation:
    @patch("apps.portfolio.models.Portfolio.holdings")
    def test_allocation_empty(self, mock_holdings):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_qs = MagicMock()
        mock_qs.select_related.return_value = []
        mock_holdings.return_value = mock_qs

        allocation = portfolio.get_allocation()
        assert allocation == []

    @patch("apps.portfolio.models.Portfolio.holdings")
    def test_allocation_single_holding(self, mock_holdings):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_holding = MagicMock()
        mock_holding.asset.symbol = "BTC"
        mock_holding.current_value = Decimal("100000.00")

        mock_holdings.select_related.return_value = [mock_holding]

        allocation = portfolio.get_allocation()
        assert len(allocation) == 1
        assert allocation[0]["asset"] == "BTC"
        assert allocation[0]["pct_of_portfolio"] == 100.0
