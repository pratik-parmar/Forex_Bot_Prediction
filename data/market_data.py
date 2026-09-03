import yfinance as yf


def get_forex_data(symbol="EURUSD=X", period="7d", interval="1m"):
    """
    Download Forex market data.

    symbol:
        EURUSD=X = EUR/USD
        GBPUSD=X = GBP/USD
        USDJPY=X = USD/JPY

    period:
        Amount of historical data.

    interval:
        Candle timeframe.
    """

    data = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False
    )

    if data.empty:
        raise ValueError("No market data received.")

    return data