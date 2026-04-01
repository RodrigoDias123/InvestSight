import pytest
from decimal import Decimal

from apps.portfolio.models import Portfolio


@pytest.fixture
def portfolio_factory(db, django_user_model):
    def create(**kwargs):
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", "user_r1"),
            email=kwargs.pop("email", "user_r1@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R1"),
            user=user,
        )

    return create


@pytest.fixture
def holding_factory(db):
    from apps.wallet.models import Asset, Holding

    def create(**kwargs):
        portfolio = kwargs.pop("portfolio")
        total_cost = kwargs.pop("total_cost", None)
        quantity = kwargs.pop("quantity", Decimal("1"))

        if total_cost is not None:
            avg_buy_price = total_cost / quantity
        else:
            avg_buy_price = kwargs.pop("avg_buy_price", Decimal("100"))

        symbol = kwargs.pop("symbol", "BTC")
        asset, _ = Asset.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": kwargs.pop("asset_name", "Bitcoin"),
                "asset_type": kwargs.pop("asset_type", "crypto"),
            },
        )
        return Holding.objects.create(
            portfolio=portfolio,
            asset=asset,
            quantity=quantity,
            avg_buy_price=avg_buy_price,
        )

    def create_batch(size, **kwargs):
        return [create(**kwargs) for _ in range(size)]

    create.create_batch = create_batch
    return create


@pytest.mark.django_db
class TestTotalInvested:
    def test_total_invested_single_holding(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory()
        holding_factory(portfolio=portfolio, total_cost=Decimal("100.00"))
        assert portfolio.total_invested == Decimal("100.00")

    def test_total_invested_multiple_holdings(self, portfolio_factory, holding_factory):
        portfolio = portfolio_factory(
            username="user_r1_multi", email="user_r1_multi@example.com"
        )
        holding_factory(portfolio=portfolio, total_cost=Decimal("100.00"))
        holding_factory(portfolio=portfolio, total_cost=Decimal("250.50"))
        assert portfolio.total_invested == Decimal("350.50")

    def test_total_invested_empty_portfolio(self, portfolio_factory):
        portfolio = portfolio_factory(
            username="user_r1_empty", email="user_r1_empty@example.com"
        )
        assert portfolio.total_invested == Decimal("0")

    def test_total_invested_uses_aggregate(
        self, portfolio_factory, holding_factory, django_assert_num_queries
    ):
        portfolio = portfolio_factory(
            username="user_r1_agg", email="user_r1_agg@example.com"
        )
        holding_factory.create_batch(
            3, portfolio=portfolio, total_cost=Decimal("50.00")
        )
        with django_assert_num_queries(1):
            _ = portfolio.total_invested
