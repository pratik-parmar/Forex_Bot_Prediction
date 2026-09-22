from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from mutual_funds.models import MutualFund, NAVHistory
from mutual_funds.views import portfolio_view


pytestmark = pytest.mark.django_db


@pytest.fixture
def fund(db):
    return MutualFund.objects.create(
        scheme_code="123456",
        scheme_name="Pytest Equity Fund",
        fund_house="Test AMC",
        category="Equity",
    )


def test_fund_list_page_loads(client, fund):
    response = client.get(reverse("mutual_funds:fund_list"))
    assert response.status_code == 200


def test_fund_detail_page_loads(client, fund):
    response = client.get(
        reverse(
            "mutual_funds:fund_detail",
            kwargs={"scheme_code": fund.scheme_code},
        )
    )
    assert response.status_code == 200


def test_fund_chart_api_returns_historical_nav_and_forecast(client, fund):
    NAVHistory.objects.create(
        mutual_fund=fund, date=date(2025, 1, 1), nav=Decimal("100.0000")
    )
    NAVHistory.objects.create(
        mutual_fund=fund, date=date(2025, 1, 2), nav=Decimal("101.0000")
    )

    response = client.get(
        reverse(
            "mutual_funds:fund_chart_api",
            kwargs={"scheme_code": fund.scheme_code},
        )
    )
    payload = response.json()

    assert response.status_code == 200
    assert len(payload["historical"]) == 2
    assert len(payload["forecast"]) == 7
    assert payload["historical"][0]["value"] == 100.0


def test_nav_history_duplicate_fund_date_is_rejected(fund):
    NAVHistory.objects.create(
        mutual_fund=fund, date=date(2025, 2, 1), nav=Decimal("99.0000")
    )
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        NAVHistory.objects.create(
            mutual_fund=fund, date=date(2025, 2, 1), nav=Decimal("100.0000")
        )


def test_portfolio_view_redirects_anonymous_user():
    request = RequestFactory().get("/mutual-funds/portfolio/")
    request.user = AnonymousUser()

    response = portfolio_view(request)

    assert response.status_code == 302
    assert "/login/" in response.url
