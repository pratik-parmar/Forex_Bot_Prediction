import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import MutualFund, NAVHistory, UserPortfolio


def fund_list(request):
    funds = MutualFund.objects.all()
    return render(request, "mutual_funds/fund_list.html", {"funds": funds})


@login_required
def portfolio_view(request):
    # Using select_related optimizes database hits if 'mutual_fund' is a ForeignKey on UserPortfolio
    portfolios = UserPortfolio.objects.filter(user=request.user).select_related(
        "mutual_fund"
    )
    return render(request, "mutual_funds/portfolio.html", {"portfolios": portfolios})


def fund_detail(request, scheme_code):
    fund = get_object_or_404(MutualFund, scheme_code=scheme_code)
    return render(request, "mutual_funds/chart.html", {"fund": fund})


def fund_chart_api(request, scheme_code):
    fund = get_object_or_404(MutualFund, scheme_code=scheme_code)
    
    # Fetching only required fields minimizes memory usage for large datasets
    navs = NAVHistory.objects.filter(mutual_fund=fund).order_by("date").values("date", "nav")

    chart_data = [
        {
            "time": nav["date"].strftime("%Y-%m-%d") if hasattr(nav["date"], "strftime") else str(nav["date"]),
            "value": float(nav["nav"]),
        }
        for nav in navs
    ]

    predictions = []
    if chart_data:
        last_nav_item = navs.last()
        last_date = last_nav_item["date"]
        last_val = float(last_nav_item["nav"])
        
        for i in range(1, 8):
            next_date = last_date + datetime.timedelta(days=i)
            last_val *= 1.002
            predictions.append({
                "time": next_date.strftime("%Y-%m-%d"),
                "value": round(last_val, 4),
            })

    return JsonResponse({
        "historical": chart_data,
        "forecast": predictions,
    })