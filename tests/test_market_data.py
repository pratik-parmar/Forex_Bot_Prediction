import pandas as pd
import pytest

from data import market_data


def sample_yahoo_frame():
    idx = pd.date_range("2025-01-01", periods=3, freq="D")
    return pd.DataFrame(
        {
            "Open": [1.0, 1.1, 1.2],
            "High": [1.2, 1.3, 1.4],
            "Low": [0.9, 1.0, 1.1],
            "Close": [1.1, 1.2, 1.3],
            "Volume": [100, 110, 120],
        },
        index=idx,
    )


@pytest.mark.parametrize("symbol", ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"])
def test_get_market_candles_maps_supported_symbols(monkeypatch, symbol):
    captured = {}
    monkeypatch.setattr(
        market_data.yf,
        "download",
        lambda **kwargs: captured.update(kwargs) or sample_yahoo_frame(),
    )

    result = market_data.get_market_candles(symbol, "15")

    assert not result.empty
    assert {"Open", "High", "Low", "Close", "Timestamp"}.issubset(result.columns)
    assert captured["tickers"] == market_data.YAHOO_SYMBOLS[symbol]
    assert captured["interval"] == "15m"


def test_get_market_candles_rejects_unknown_symbol():
    with pytest.raises(ValueError, match="Unsupported market symbol"):
        market_data.get_market_candles("FAKE", "15")


def test_get_market_candles_rejects_unknown_timeframe():
    with pytest.raises(ValueError, match="Unsupported timeframe"):
        market_data.get_market_candles("EURUSD", "999")


def test_get_market_candles_raises_for_empty_yahoo_response(monkeypatch):
    monkeypatch.setattr(market_data.yf, "download", lambda **kwargs: pd.DataFrame())
    with pytest.raises(ValueError, match="No market candle data"):
        market_data.get_market_candles("EURUSD", "15")


def test_get_market_candles_handles_multiindex_columns(monkeypatch):
    frame = sample_yahoo_frame()
    frame.columns = pd.MultiIndex.from_product([frame.columns, ["EURUSD=X"]])
    monkeypatch.setattr(market_data.yf, "download", lambda **kwargs: frame.copy())

    result = market_data.get_market_candles("EURUSD", "15")
    assert {"Open", "High", "Low", "Close", "Timestamp"}.issubset(result.columns)
