from django.urls import path
from . import views

app_name = "portfolio"

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
    path("", views.index, name="index"),
    path("<int:portfolio_id>/", views.detail, name="detail"),
]
