from django.urls import path
from . import views

app_name = "portfolio"
# This URL configuration defines the routes for the portfolio app, including user signup, wallet management, and portfolio details. Each route is linked to a corresponding view function that handles the logic for that endpoint. The routes include:
urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("wallet/", views.wallet, name="wallet"),
    path("wallet/receive/", views.receive_crypto_list, name="receive_crypto_list"),
    path("wallet/receive/<str:crypto>/", views.receive_crypto, name="receive_crypto"),
    path("wallet/import/", views.import_wallet_step1, name="import_step1"),
    path("wallet/import/seed-phrase/", views.import_wallet_step2, name="import_step2"),
    path("wallet/import/password/", views.import_wallet_step3, name="import_step3"),
    path("wallet/import/complete/", views.import_wallet_step4, name="import_step4"),
    path("wallet/import/done/", views.import_wallet_complete, name="import_complete"),
    path(
        "wallet/transactions/log/", views.wallet_transaction_log, name="wallet_tx_log"
    ),
    path(
        "wallet/prices/<str:symbol>/", views.wallet_live_price, name="wallet_live_price"
    ),
    path("", views.index, name="index"),
    path("<int:portfolio_id>/", views.detail, name="detail"),
]
