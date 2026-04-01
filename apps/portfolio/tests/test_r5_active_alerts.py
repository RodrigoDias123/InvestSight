import pytest
from decimal import Decimal

from repositories import AlertRepository


@pytest.fixture
def portfolio_factory(db, django_user_model):
    from apps.portfolio.models import Portfolio

    def create(**kwargs):
        user = kwargs.pop("user", None) or django_user_model.objects.create_user(
            username=kwargs.pop("username", "user_r5"),
            email=kwargs.pop("email", "user_r5@example.com"),
            password="testpass123",
        )
        return Portfolio.objects.create(
            name=kwargs.pop("name", "Portfolio R5"),
            user=user,
        )

    return create


@pytest.fixture
def alert_factory(db):
    from apps.portfolio.models import Alert
    from apps.wallet.models import Asset

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
        return Alert.objects.create(
            portfolio=portfolio,
            asset=asset,
            target_price=kwargs.pop("target_price", Decimal("100.00")),
            direction=kwargs.pop("direction", "above"),
            active=kwargs.pop("active", True),
            triggered=kwargs.pop("triggered", False),
        )

    return create


@pytest.mark.django_db
class TestActiveAlerts:
    def test_returns_only_active_alerts(self, portfolio_factory, alert_factory):
        portfolio = portfolio_factory()
        alert_factory(portfolio=portfolio, active=True, triggered=False)
        alert_factory(portfolio=portfolio, active=False, triggered=False)

        alerts = AlertRepository.get_active(portfolio.id)
        assert alerts.count() == 1

    def test_excludes_triggered_alerts(self, portfolio_factory, alert_factory):
        portfolio = portfolio_factory(username="user_r5_tr", email="user_r5_tr@example.com")
        alert_factory(portfolio=portfolio, active=True, triggered=True)

        alerts = AlertRepository.get_active(portfolio.id)
        assert alerts.count() == 0

    def test_excludes_other_portfolio_alerts(self, portfolio_factory, alert_factory):
        p1 = portfolio_factory(username="user_r5_p1", email="user_r5_p1@example.com")
        p2 = portfolio_factory(username="user_r5_p2", email="user_r5_p2@example.com")
        alert_factory(portfolio=p1, active=True, triggered=False)

        alerts = AlertRepository.get_active(p2.id)
        assert alerts.count() == 0

    def test_empty_when_no_alerts(self, portfolio_factory):
        portfolio = portfolio_factory(username="user_r5_empty", email="user_r5_empty@example.com")

        alerts = AlertRepository.get_active(portfolio.id)
        assert alerts.count() == 0
