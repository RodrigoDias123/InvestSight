import pytest
from decimal import Decimal
from unittest.mock import MagicMock, PropertyMock, patch

from apps.portfolio.models import Portfolio


class TestPortfolioPnL:
    @patch("apps.portfolio.models.Portfolio.current_value", new_callable=PropertyMock)
    @patch("apps.portfolio.models.Portfolio.total_invested", new_callable=PropertyMock)
    def test_total_pnl_gain(self, mock_invested, mock_current):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_invested.return_value = Decimal("100000.00")
        mock_current.return_value = Decimal("120000.00")

        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("20000.00")

    @patch("apps.portfolio.models.Portfolio.current_value", new_callable=PropertyMock)
    @patch("apps.portfolio.models.Portfolio.total_invested", new_callable=PropertyMock)
    def test_total_pnl_loss(self, mock_invested, mock_current):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_invested.return_value = Decimal("100000.00")
        mock_current.return_value = Decimal("80000.00")

        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("-20000.00")

    @patch("apps.portfolio.models.Portfolio.current_value", new_callable=PropertyMock)
    @patch("apps.portfolio.models.Portfolio.total_invested", new_callable=PropertyMock)
    def test_total_pnl_empty_returns_zero(self, mock_invested, mock_current):
        from django.contrib.auth.models import User

        user = User(username="test", email="test@test.com")
        portfolio = Portfolio(name="Test", user=user)

        mock_invested.return_value = Decimal("0")
        mock_current.return_value = Decimal("0")

        pnl = portfolio.total_pnl
        assert pnl["absolute"] == Decimal("0")
        assert pnl["percentage"] == Decimal("0")
