from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

from apps.portfolio.models import Portfolio
from apps.wallet.models import SeedPhrase


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def index(request):
    portfolios = Portfolio.objects.filter(user=request.user)
    return render(request, "portfolio/dashboard.html", {"portfolios": portfolios})


@login_required
def detail(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=request.user)
    holdings = portfolio.holdings.select_related("asset")
    allocation = portfolio.get_allocation()
    return render(
        request,
        "portfolio/detail.html",
        {
            "portfolio": portfolio,
            "holdings": holdings,
            "allocation": allocation,
        },
    )


@login_required
def wallet(request):
    seed_phrase = getattr(request.user, "seed_phrase", None)
    if not seed_phrase:
        seed_phrase = SeedPhrase.objects.create(user=request.user)

    if request.method == "POST":
        import json

        data = json.loads(request.body)
        if data.get("action") == "mark_downloaded":
            seed_phrase.is_downloaded = True
            seed_phrase.save()
            return JsonResponse({"status": "ok"})

    return render(request, "portfolio/wallet.html", {"seed_phrase": seed_phrase})
