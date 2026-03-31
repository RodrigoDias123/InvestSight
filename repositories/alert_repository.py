from datetime import datetime
from decimal import Decimal
from typing import Optional

from django.db.models import QuerySet

from apps.portfolio.models import Alert


class AlertRepository:
    @staticmethod
    def get_active(portfolio_id: int) -> QuerySet[Alert]:
        return Alert.objects.filter(
            portfolio_id=portfolio_id, active=True, triggered=False
        ).select_related("asset")

    def get_by_portfolio(self, portfolio_id: int) -> QuerySet[Alert]:
        return Alert.objects.filter(portfolio_id=portfolio_id).select_related("asset")

    def create(
        self, portfolio_id: int, asset_id: int, target_price: Decimal, direction: str
    ) -> Alert:
        from apps.portfolio.models import Portfolio
        from apps.wallet.models import Asset

        portfolio = Portfolio.objects.get(id=portfolio_id)
        asset = Asset.objects.get(id=asset_id)

        return Alert.objects.create(
            portfolio=portfolio,
            asset=asset,
            target_price=target_price,
            direction=direction,
        )

    def mark_triggered(self, alert_id: int) -> Alert:
        alert = Alert.objects.get(id=alert_id)
        alert.triggered = True
        alert.triggered_at = datetime.utcnow()
        alert.save()
        return alert

    def deactivate(self, alert_id: int) -> Alert:
        alert = Alert.objects.get(id=alert_id)
        alert.active = False
        alert.save()
        return alert
