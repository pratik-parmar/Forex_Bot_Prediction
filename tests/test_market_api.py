import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


def json_body(response):
    import json
    return json.loads(response.content.decode("utf-8"))


@pytest.mark.parametrize(
    "url_name",
    ["live_price", "markets_overview", "market_candles", "technical_analysis"],
)
def test_market_apis_require_authentication(client, url_name):
    response = client.get(reverse(url_name))
    assert response.status_code == 401
    assert json_body(response)["success"] is False


def test_live_price_returns_snapshot_for_authenticated_user(client, user, monkeypatch):
    from dashboard import market_api

    monkeypatch.setattr(
        market_api,
        "get_market_snapshot",
        lambda symbol: {
            "price": 2345.5,
            "last_close": 2340.0,
            "previous_close": 2340.0,
            "market_open": True,
            "market_state": "REGULAR",
            "price_source": "latest_market_price",
            "timestamp": None,
        },
    )
    client.force_login(user)
    response = client.get(reverse("live_price"), {"symbol": "XAUUSD"})
    payload = json_body(response)

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["symbol"] == "XAUUSD"
    assert payload["price"] == 2345.5


def test_live_price_rejects_unsupported_symbol(client, user):
    client.force_login(user)
    response = client.get(reverse("live_price"), {"symbol": "FAKE"})
    assert response.status_code == 400
    assert json_body(response)["success"] is False


def test_markets_overview_returns_each_supported_market(client, user, monkeypatch):
    from dashboard import market_api

    monkeypatch.setattr(
        market_api,
        "get_market_snapshot",
        lambda symbol: {
            "price": 1.25,
            "last_close": 1.20,
            "previous_close": 1.20,
            "market_open": False,
            "market_state": "CLOSED",
            "price_source": "last_close",
            "timestamp": None,
        },
    )
    client.force_login(user)
    response = client.get(reverse("markets_overview"))
    payload = json_body(response)

    assert response.status_code == 200
    assert payload["success"] is True
    assert {item["symbol"] for item in payload["markets"]} == {
        "XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"
    }


def test_technical_analysis_rejects_unsupported_symbol(client, user):
    client.force_login(user)
    response = client.get(
        reverse("technical_analysis"),
        {"symbol": "FAKE", "timeframe": "15"},
    )
    assert response.status_code == 400
    assert json_body(response)["success"] is False


def test_technical_analysis_returns_analysis_when_dependencies_succeed(
    client, user, monkeypatch
):
    from dashboard import views

    monkeypatch.setattr(views, "get_market_candles", lambda **kwargs: object())
    monkeypatch.setattr(
        views,
        "calculate_technical_analysis",
        lambda *args, **kwargs: {"signal": "HOLD", "reason": "Test result"},
    )
    client.force_login(user)
    response = client.get(
        reverse("technical_analysis"),
        {"symbol": "EURUSD", "timeframe": "15"},
    )
    payload = json_body(response)

    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["symbol"] == "EURUSD"
    assert payload["timeframe_label"] == "15m"
    assert payload["signal"] == "HOLD"


def test_market_candles_returns_503_when_no_data(client, user, monkeypatch):
    import pandas as pd
    from dashboard import market_api

    monkeypatch.setattr(
        market_api,
        "fetch_market_data",
        lambda *args, **kwargs: pd.DataFrame(),
    )
    client.force_login(user)
    response = client.get(reverse("market_candles"))
    assert response.status_code == 503
    assert json_body(response)["success"] is False
