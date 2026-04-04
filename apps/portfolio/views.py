from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import json

from apps.portfolio.models import Portfolio
from apps.wallet.models import (
    Asset,
    Holding,
    SeedPhrase,
    WalletTransaction,
    WalletTransactionType,
)
from apps.apis.services.unified import get_price as get_live_price


# This view handles user signup. It uses Django's built-in UserCreationForm to create a new user. If the form is valid, it saves the user, logs them in, and redirects to the homepage. If the request method is GET, it simply renders the signup form.
def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Portfolio.objects.create(name="My Portfolio", user=user)
            login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


#
@login_required
def index(request):
    portfolios = Portfolio.objects.filter(user=request.user)
    if not portfolios.exists():
        Portfolio.objects.create(name="My Portfolio", user=request.user)
        portfolios = Portfolio.objects.filter(user=request.user)
    return render(request, "portfolio/dashboard.html", {"portfolios": portfolios})


@login_required
def detail(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    holdings = portfolio.holdings.select_related("asset")
    allocation = portfolio.get_allocation()
    assets = Asset.objects.all().order_by("symbol")

    from apps.apis.settings import settings as api_settings

    registry = api_settings.PROVIDER_REGISTRY
    crypto_symbols = sorted(s for s, p in registry.items() if p == "coingecko")
    stock_symbols = sorted(s for s, p in registry.items() if p == "yahoo")

    from decimal import Decimal

    crypto_value = Decimal("0")
    stock_value = Decimal("0")
    for h in holdings:
        v = h.current_value
        if v is None:
            continue
        if h.asset.asset_type == "crypto":
            crypto_value += v
        else:
            stock_value += v

    return render(
        request,
        "portfolio/detail.html",
        {
            "portfolio": portfolio,
            "holdings": holdings,
            "allocation": allocation,
            "assets": assets,
            "crypto_symbols": crypto_symbols,
            "stock_symbols": stock_symbols,
            "crypto_value": crypto_value,
            "stock_value": stock_value,
        },
    )


@login_required
@require_POST
def add_holding(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)

    symbol = request.POST.get("symbol", "").strip().upper()
    name = request.POST.get("name", "").strip()
    asset_type = request.POST.get("asset_type", "crypto")
    quantity = request.POST.get("quantity", "").strip()
    avg_buy_price = request.POST.get("avg_buy_price", "").strip()

    errors = []
    if not symbol:
        errors.append("Symbol is required.")
    if not quantity:
        errors.append("Quantity is required.")
    if not avg_buy_price:
        errors.append("Average buy price is required.")

    if not errors:
        try:
            qty = Decimal(quantity)
            price = Decimal(avg_buy_price)
        except InvalidOperation:
            errors.append("Quantity and price must be valid numbers.")

    if errors:
        holdings = portfolio.holdings.select_related("asset")
        allocation = portfolio.get_allocation()
        assets = Asset.objects.all().order_by("symbol")
        return render(
            request,
            "portfolio/detail.html",
            {
                "portfolio": portfolio,
                "holdings": holdings,
                "allocation": allocation,
                "assets": assets,
                "errors": errors,
            },
        )

    asset, _ = Asset.objects.get_or_create(
        symbol=symbol,
        defaults={"name": name or symbol, "asset_type": asset_type},
    )
    Holding.objects.create(
        portfolio=portfolio,
        asset=asset,
        quantity=qty,
        avg_buy_price=price,
    )
    return redirect("portfolio:detail", portfolio_id=portfolio_id)


@login_required
# This view handles the wallet page for the user. It checks if the user has an associated seed phrase and creates one if it doesn't exist. If the request method is POST and the action is to mark the seed phrase as downloaded, it updates the seed phrase accordingly. Finally, it renders the wallet page with the seed phrase information.
def wallet(request):
    seed_phrase = getattr(request.user, "seed_phrase", None)
    if not seed_phrase:
        seed_phrase = SeedPhrase.objects.create(user=request.user)

    if request.method == "POST":
        data = json.loads(request.body)
        if data.get("action") == "mark_downloaded":
            seed_phrase.is_downloaded = True
            seed_phrase.save()
            return JsonResponse({"status": "ok"})

    transactions = WalletTransaction.objects.filter(user=request.user)[:25]
    return render(
        request,
        "portfolio/wallet.html",
        {
            "seed_phrase": seed_phrase,
            "transactions": transactions,
        },
    )


def import_wallet_step1(request):
    return render(request, "wallet/import/step1.html")


def import_wallet_step2(request):
    if request.method == "POST":
        request.session["import_seed_phrase"] = (
            request.POST.get("seed_phrase", "").strip().lower()
        )
        return redirect("portfolio:import_step3")
    return render(request, "wallet/import/step2.html")


# This view handles the third step of the wallet import process. It checks if the request method is POST and retrieves the password and confirm password from the form. It validates that the passwords match and meet a minimum length requirement. If there are any validation errors, it renders the step 3 template with an error message. If the passwords are valid, it saves the password in the session and redirects to step 4 for confirmation.
def import_wallet_step3(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if password != confirm_password:
            return render(
                request, "wallet/import/step3.html", {"error": "Passwords do not match"}
            )

        if len(password) < 8:
            return render(
                request,
                "wallet/import/step3.html",
                {"error": "Password must be at least 8 characters"},
            )

        request.session["import_password"] = password
        return redirect("portfolio:import_step4")

    return render(request, "wallet/import/step3.html")


# This view handles the fourth step of the wallet import process. It retrieves the seed phrase and password from the session, checks if they are valid, and counts the number of words in the seed phrase. If the word count is not 12 or 24, it clears the session data and redirects back to step 2. If everything is valid, it renders a template that displays the seed phrase and its word count for confirmation before completing the import process.
def import_wallet_step4(request):
    seed_phrase = request.session.get("import_seed_phrase", "")
    password = request.session.get("import_password", "")

    if not seed_phrase or not password:
        return redirect("portfolio:import_step1")

    words = seed_phrase.split()
    word_count = len(words)

    if word_count not in [12, 24]:
        del request.session["import_seed_phrase"]
        del request.session["import_password"]
        return redirect("portfolio:import_step2")

    return render(
        request,
        "wallet/import/step4.html",
        {"seed_phrase": seed_phrase, "word_count": word_count},
    )


# This view handles the completion of the wallet import process. It retrieves the seed phrase and password from the session, checks if they are valid, and if the user is authenticated, it updates or creates a SeedPhrase object for the user with the imported seed phrase. Finally, it redirects to the wallet page.
def import_wallet_complete(request):
    if request.method == "POST":
        seed_phrase = request.session.pop("import_seed_phrase", "")
        password = request.session.pop("import_password", "")

        if seed_phrase and password:
            if request.user.is_authenticated:
                seed_phrase_obj, created = SeedPhrase.objects.get_or_create(
                    user=request.user
                )
                seed_phrase_obj.save()
                WalletTransaction.objects.create(
                    user=request.user,
                    transaction_type=WalletTransactionType.IMPORT,
                    note="Wallet imported with seed phrase",
                    metadata={"word_count": len(seed_phrase.split())},
                )

        return redirect("portfolio:wallet")

    return redirect("portfolio:index")


# This view handles logging wallet transactions. It expects a POST request with JSON data containing the transaction details. It validates the transaction type, amount, and metadata, and if everything is valid, it creates a new WalletTransaction object linked to the user. Finally, it returns a JSON response indicating success or any validation errors that occurred.
@csrf_protect
@require_POST
@login_required
def wallet_transaction_log(request):
    try:
        data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    tx_type = data.get("transaction_type", "").strip().lower()
    valid_types = {choice[0] for choice in WalletTransactionType.choices}
    if tx_type not in valid_types:
        return JsonResponse(
            {"status": "error", "message": "Invalid transaction type"}, status=400
        )

    amount = data.get("amount")
    parsed_amount = None
    if amount not in (None, ""):
        try:
            parsed_amount = Decimal(str(amount))
        except InvalidOperation, ValueError, TypeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid amount"}, status=400
            )

    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    tx = WalletTransaction.objects.create(
        user=request.user,
        transaction_type=tx_type,
        asset_symbol=(data.get("asset_symbol", "") or "")[:12].upper(),
        amount=parsed_amount,
        from_address=(data.get("from_address", "") or "")[:255],
        to_address=(data.get("to_address", "") or "")[:255],
        reference=(data.get("reference", "") or "")[:128],
        note=(data.get("note", "") or "")[:255],
        metadata=metadata,
    )

    return JsonResponse({"status": "ok", "id": tx.id})


@login_required
def wallet_live_price(request, symbol: str):
    target_currency = request.GET.get("target_currency", "USD").upper()
    if len(target_currency) != 3 or not target_currency.isalpha():
        return JsonResponse(
            {"status": "error", "message": "Invalid target currency"}, status=400
        )

    result = get_live_price(symbol.upper(), target_currency=target_currency)
    if result is None:
        return JsonResponse(
            {"status": "error", "message": "Price not found"}, status=404
        )

    if result.timestamp < datetime.utcnow() - timedelta(minutes=15):
        return JsonResponse(
            {
                "status": "error",
                "message": "Live quote is stale",
                "symbol": result.symbol,
                "provider": result.provider,
                "timestamp": result.timestamp.isoformat(),
            },
            status=503,
        )

    return JsonResponse(
        {
            "status": "ok",
            "symbol": result.symbol,
            "price": str(result.price),
            "currency": result.currency,
            "provider": result.provider,
            "timestamp": result.timestamp.isoformat(),
        }
    )


# This view displays a list of supported cryptocurrencies for receiving funds. It retrieves the cryptocurrency information from the CRYPTO_REGISTRY and renders a template that lists all available cryptocurrencies along with their metadata, such as name, symbol, and icon.
@login_required
def receive_crypto_list(request):
    from apps.wallet.models import CRYPTO_REGISTRY

    return render(
        request, "wallet/crypto_list.html", {"cryptos": CRYPTO_REGISTRY.items()}
    )


# This view handles the page for receiving cryptocurrency. Address generation is fully client-side from the user's local seed phrase; the backend only provides crypto metadata and the BIP39 wordlist.
@login_required
def receive_crypto(request, crypto: str = "bitcoin"):
    from apps.wallet.models import CRYPTO_REGISTRY, WORDLIST

    crypto = crypto.lower()

    if crypto not in CRYPTO_REGISTRY:
        return redirect("portfolio:receive_crypto_list")

    crypto_info = CRYPTO_REGISTRY[crypto]

    return render(
        request,
        "wallet/receive.html",
        {
            "crypto": crypto,
            "crypto_info": crypto_info,
            "wordlist": json.dumps(WORDLIST),
        },
    )
