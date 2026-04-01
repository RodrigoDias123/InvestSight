import pytest

from apps.portfolio.models import Portfolio
from repositories import PortfolioRepository


@pytest.fixture
def portfolio_factory(db, django_user_model):
    def create(**kwargs):
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", "user_r4"),
            email=kwargs.pop("email", "user_r4@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R4"),
            user=user,
        )

    return create


@pytest.fixture
def holding_factory(db):
    from apps.wallet.models import Asset, Holding

    def create(**kwargs):
        portfolio = kwargs.pop("portfolio")
        asset = kwargs.pop("asset", None)
        if asset is None:
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
            quantity=kwargs.pop("quantity", "1"),
            avg_buy_price=kwargs.pop("avg_buy_price", "100"),
        )

    def create_batch(size, **kwargs):
        return [create(**kwargs) for _ in range(size)]

    create.create_batch = create_batch
    return create


@pytest.mark.django_db
class TestHoldingsSelector:
    def test_get_holdings_returns_queryset_for_portfolio(
        self, portfolio_factory, holding_factory
    ):
        portfolio = portfolio_factory()
        holding_factory(portfolio=portfolio)
        qs = PortfolioRepository.get_holdings(portfolio.id)
        assert qs.count() == 1

    def test_get_holdings_excludes_other_portfolios(
        self, portfolio_factory, holding_factory
    ):
        p1 = portfolio_factory(username="user_r4_p1", email="user_r4_p1@example.com")
        p2 = portfolio_factory(username="user_r4_p2", email="user_r4_p2@example.com")
        holding_factory(portfolio=p1, symbol="ETH", asset_name="Ethereum")
        holding_factory(portfolio=p2, symbol="AAPL", asset_name="Apple", asset_type="stock")

        qs = PortfolioRepository.get_holdings(p1.id)
        assert qs.count() == 1

    def test_get_holdings_no_n1_queries(
        self, portfolio_factory, holding_factory, django_assert_num_queries
    ):
        portfolio = portfolio_factory(username="user_r4_n1", email="user_r4_n1@example.com")
        holding_factory.create_batch(5, portfolio=portfolio, symbol="SOL", asset_name="Solana")

        with django_assert_num_queries(1):
            list(PortfolioRepository.get_holdings(portfolio.id))

    def test_get_holdings_empty_portfolio(self, portfolio_factory):
        portfolio = portfolio_factory(username="user_r4_empty", email="user_r4_empty@example.com")
        qs = PortfolioRepository.get_holdings(portfolio.id)
        assert qs.count() == 0
