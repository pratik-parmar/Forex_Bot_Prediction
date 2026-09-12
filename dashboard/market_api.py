import pandas as pd
import yfinance as yf

from django.http import JsonResponse


# =========================================================
# SYMBOL MAPPING
# =========================================================

SYMBOL_MAP = {

    "XAUUSD": "GC=F",

    "EURUSD": "EURUSD=X",

    "GBPUSD": "GBPUSD=X",

    "BTCUSD": "BTC-USD",

}


# =========================================================
# TIMEFRAME MAPPING
# =========================================================

TIMEFRAME_MAP = {

    "1": {
        "interval": "1m",
        "period": "7d",
        "label": "1m",
    },

    "5": {
        "interval": "5m",
        "period": "60d",
        "label": "5m",
    },

    "15": {
        "interval": "15m",
        "period": "60d",
        "label": "15m",
    },

    "30": {
        "interval": "30m",
        "period": "60d",
        "label": "30m",
    },

    "60": {
        "interval": "60m",
        "period": "1y",
        "label": "1H",
    },

    "D": {
        "interval": "1d",
        "period": "5y",
        "label": "1D",
    },

}


# =========================================================
# CLEAN YAHOO DATA
# =========================================================

def clean_dataframe(
    data
):

    if data is None or data.empty:

        return pd.DataFrame()


    if isinstance(
        data.columns,
        pd.MultiIndex
    ):

        data.columns = [

            str(
                column[0]
            ).lower()

            for column in data.columns

        ]

    else:

        data.columns = [

            str(
                column
            ).lower()

            for column in data.columns

        ]


    required_columns = [

        "open",
        "high",
        "low",
        "close",

    ]


    for column in required_columns:

        if column not in data.columns:

            raise ValueError(
                f"Missing market column: {column}"
            )


    data = data[
        ~data.index.duplicated(
            keep="last"
        )
    ]


    data = data.sort_index()


    return data


# =========================================================
# FETCH MARKET DATA
# =========================================================

def fetch_market_data(
    display_symbol="XAUUSD",
    timeframe="15"
):

    yahoo_symbol = SYMBOL_MAP.get(
        display_symbol
    )


    timeframe_config = TIMEFRAME_MAP.get(
        timeframe
    )


    if yahoo_symbol is None:

        raise ValueError(
            f"Unsupported symbol: "
            f"{display_symbol}"
        )


    if timeframe_config is None:

        raise ValueError(
            f"Unsupported timeframe: "
            f"{timeframe}"
        )


    data = yf.download(

        tickers=yahoo_symbol,

        period=timeframe_config["period"],

        interval=timeframe_config["interval"],

        auto_adjust=False,

        progress=False,

        threads=False,

    )


    return clean_dataframe(
        data
    )


# =========================================================
# LIVE PRICE API
# =========================================================

def live_price(
    request
):

    symbol = request.GET.get(

        "symbol",

        "XAUUSD"

    ).upper().strip()


    # -----------------------------------------------------
    # Validate symbol
    # -----------------------------------------------------

    if symbol not in SYMBOL_MAP:

        return JsonResponse(

            {

                "success":
                    False,

                "symbol":
                    symbol,

                "error":
                    f"Unsupported symbol: {symbol}"

            },

            status=400

        )


    try:

        yahoo_symbol = (
            SYMBOL_MAP[symbol]
        )


        # =================================================
        # 1. GET RECENT INTRADAY DATA
        # =================================================

        intraday = yf.download(

            tickers=yahoo_symbol,

            period="5d",

            interval="1m",

            auto_adjust=False,

            progress=False,

            threads=False,

        )


        intraday = clean_dataframe(
            intraday
        )


        # =================================================
        # 2. GET DAILY DATA
        #
        # This is our important weekend/holiday fallback.
        #
        # Example:
        #
        # Saturday
        #     ↓
        # no new FX tick
        #     ↓
        # latest daily candle
        #     ↓
        # Friday closing price
        # =================================================

        daily = yf.download(

            tickers=yahoo_symbol,

            period="10d",

            interval="1d",

            auto_adjust=False,

            progress=False,

            threads=False,

        )


        daily = clean_dataframe(
            daily
        )


        last_close = None


        if not daily.empty:

            last_close = float(

                daily.iloc[-1]["close"]

            )


        # =================================================
        # 3. GET LATEST INTRADAY PRICE
        # =================================================

        latest_intraday_price = None

        latest_intraday_timestamp = None


        if not intraday.empty:

            latest_intraday_price = float(

                intraday.iloc[-1]["close"]

            )


            latest_intraday_timestamp = (

                intraday.index[-1]

            )


        # =================================================
        # 4. DETERMINE IF INTRADAY DATA IS RECENT
        # =================================================

        intraday_is_recent = False


        if (
            latest_intraday_timestamp
            is not None
        ):

            now = pd.Timestamp.now(
                tz="UTC"
            )


            candle_time = pd.Timestamp(

                latest_intraday_timestamp

            )


            if candle_time.tzinfo is None:

                candle_time = (
                    candle_time
                    .tz_localize("UTC")
                )

            else:

                candle_time = (
                    candle_time
                    .tz_convert("UTC")
                )


            age_minutes = (

                now - candle_time

            ).total_seconds() / 60


            # If Yahoo's latest 1m candle is
            # within 30 minutes, treat it as
            # current market data.
            #
            # If it is much older, use the
            # last daily close.

            intraday_is_recent = (

                age_minutes <= 30

            )


        # =================================================
        # 5. SELECT PRICE
        # =================================================

        if (

            intraday_is_recent

            and

            latest_intraday_price
            is not None

        ):

            price = (
                latest_intraday_price
            )

            price_source = (
                "latest_market_price"
            )

            market_open = True

            market_state = (
                "REGULAR"
            )


        elif last_close is not None:

            price = last_close

            price_source = (
                "last_close"
            )

            market_open = False

            market_state = (
                "CLOSED"
            )


        elif (
            latest_intraday_price
            is not None
        ):

            # Last fallback
            price = (
                latest_intraday_price
            )

            price_source = (
                "latest_available"
            )

            market_open = False

            market_state = (
                "CLOSED"
            )


        else:

            return JsonResponse(

                {

                    "success":
                        False,

                    "symbol":
                        symbol,

                    "error":
                        "No market price available."

                },

                status=503

            )


        # =================================================
        # 6. RETURN RESPONSE
        # =================================================

        return JsonResponse(

            {

                "success":
                    True,

                "symbol":
                    symbol,

                "source_symbol":
                    yahoo_symbol,

                "price":
                    price,

                "last_close":
                    last_close,

                "previous_close":
                    last_close,

                "market_open":
                    market_open,

                "market_state":
                    market_state,

                "price_source":
                    price_source,

                "timestamp":
                    (
                        latest_intraday_timestamp.isoformat()
                        if latest_intraday_timestamp
                        is not None
                        else None
                    ),

                "source":
                    "Yahoo Finance",

            }

        )


    except Exception as error:

        print(
            "Live price error:",
            error
        )


        return JsonResponse(

            {

                "success":
                    False,

                "symbol":
                    symbol,

                "error":
                    str(error),

            },

            status=500

        )


# =========================================================
# MARKET CANDLES API
# =========================================================

def market_candles(
    request
):

    symbol = request.GET.get(

        "symbol",

        "XAUUSD"

    ).upper()


    timeframe = request.GET.get(

        "timeframe",

        "15"

    )


    try:

        data = fetch_market_data(

            symbol,

            timeframe

        )


        if data.empty:

            return JsonResponse(

                {

                    "success":
                        False,

                    "error":
                        "No market data available."

                },

                status=503

            )


        candles = []


        for index, row in data.iterrows():

            candles.append(

                {

                    "time":
                        int(
                            index.timestamp()
                        ),

                    "open":
                        float(
                            row["open"]
                        ),

                    "high":
                        float(
                            row["high"]
                        ),

                    "low":
                        float(
                            row["low"]
                        ),

                    "close":
                        float(
                            row["close"]
                        ),

                }

            )


        return JsonResponse(

            {

                "success":
                    True,

                "symbol":
                    symbol,

                "timeframe":
                    timeframe,

                "candles":
                    candles,

            }

        )


    except Exception as error:

        print(
            "Market candles error:",
            error
        )


        return JsonResponse(

            {

                "success":
                    False,

                "error":
                    str(error),

            },

            status=500

        )