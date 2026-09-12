import json
import os
import threading
import time

import websocket
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from dotenv import load_dotenv


# =====================================================
# ENVIRONMENT
# =====================================================

load_dotenv()

FINNHUB_API_KEY = os.getenv(
    "FINNHUB_API_KEY"
)

FINNHUB_WS_URL = (
    f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"
)


# =====================================================
# SYMBOL MAPPING
# =====================================================

# Dashboard symbol -> Finnhub symbol

SYMBOL_MAP = {

    "XAUUSD": "OANDA:XAU_USD",

    "EURUSD": "OANDA:EUR_USD",

    "GBPUSD": "OANDA:GBP_USD",

    "BTCUSD": "BINANCE:BTCUSDT",

}


# =====================================================
# LIVE MARKET FEED
# =====================================================

class LiveMarketFeed:

    def __init__(self):

        self.ws = None

        self.thread = None

        self.running = False

        # Currently selected symbol
        self.current_symbol = "XAUUSD"

        # IMPORTANT:
        # Subscribe to ALL supported symbols.
        self.subscribed_symbols = set(
            SYMBOL_MAP.keys()
        )

        self.lock = threading.Lock()


    # =================================================
    # GET FINNHUB SYMBOL
    # =================================================

    def get_finnhub_symbol(
        self,
        symbol
    ):

        symbol = (
            symbol
            .upper()
            .strip()
        )

        return SYMBOL_MAP.get(
            symbol
        )


    # =================================================
    # GET BROWSER SYMBOL
    # =================================================

    def get_browser_symbol(
        self,
        finnhub_symbol
    ):

        if not finnhub_symbol:

            return None


        for (
            browser_symbol,
            provider_symbol
        ) in SYMBOL_MAP.items():

            if provider_symbol == finnhub_symbol:

                return browser_symbol


        return None


    # =================================================
    # WEBSOCKET OPEN
    # =================================================

    def on_open(
        self,
        ws
    ):

        print(
            "======================================"
        )

        print(
            "FINNHUB WEBSOCKET CONNECTED"
        )

        print(
            "======================================"
        )

        # Subscribe to all four markets
        self.subscribe_all_symbols()


    # =================================================
    # SUBSCRIBE ALL SYMBOLS
    # =================================================

    def subscribe_all_symbols(
        self
    ):

        if not self.ws:

            print(
                "[FINNHUB] WebSocket not available"
            )

            return


        for browser_symbol in self.subscribed_symbols:

            finnhub_symbol = (
                self.get_finnhub_symbol(
                    browser_symbol
                )
            )


            if not finnhub_symbol:

                print(
                    "[FINNHUB] Unsupported symbol:",
                    browser_symbol
                )

                continue


            message = {

                "type": "subscribe",

                "symbol":
                    finnhub_symbol

            }


            try:

                self.ws.send(
                    json.dumps(
                        message
                    )
                )


                print(
                    f"[FINNHUB] SUBSCRIBED: "
                    f"{browser_symbol} -> "
                    f"{finnhub_symbol}"
                )


            except Exception as error:

                print(
                    f"[FINNHUB] Subscribe error "
                    f"for {browser_symbol}:",
                    error
                )


    # =================================================
    # UNSUBSCRIBE
    # =================================================

    def unsubscribe_symbol(
        self,
        finnhub_symbol
    ):

        if not self.ws:

            return


        message = {

            "type": "unsubscribe",

            "symbol":
                finnhub_symbol

        }


        try:

            self.ws.send(
                json.dumps(
                    message
                )
            )


            print(
                f"[FINNHUB] UNSUBSCRIBED: "
                f"{finnhub_symbol}"
            )


        except Exception as error:

            print(
                "[FINNHUB] Unsubscribe error:",
                error
            )


    # =================================================
    # CHANGE SELECTED SYMBOL
    # =================================================

    def change_symbol(
        self,
        symbol
    ):

        symbol = (
            symbol
            .upper()
            .strip()
        )


        if symbol not in SYMBOL_MAP:

            print(
                f"[FINNHUB] Invalid symbol: "
                f"{symbol}"
            )

            return False


        with self.lock:

            old_symbol = (
                self.current_symbol
            )

            self.current_symbol = symbol


        print(
            f"[FINNHUB] Symbol change: "
            f"{old_symbol} -> {symbol}"
        )


        print(
            f"[FINNHUB] Provider symbol: "
            f"{self.get_finnhub_symbol(symbol)}"
        )


        # IMPORTANT:
        #
        # Do NOT unsubscribe the old symbol.
        #
        # All four symbols remain subscribed so
        # prices can be cached independently.

        return True


    # =================================================
    # FINNHUB MESSAGE
    # =================================================

    def on_message(
        self,
        ws,
        message
    ):

        try:

            data = json.loads(
                message
            )


            print(
                "[FINNHUB RAW]",
                data
            )


            message_type = data.get(
                "type"
            )


            # -----------------------------------------
            # STATUS MESSAGE
            # -----------------------------------------

            if message_type != "trade":

                print(
                    "[FINNHUB STATUS]",
                    data
                )


                self.send_status_to_browser(
                    data
                )


                return


            # -----------------------------------------
            # TRADE DATA
            # -----------------------------------------

            trades = data.get(
                "data",
                []
            )


            for trade in trades:

                self.process_tick(
                    trade
                )


        except Exception as error:

            print(
                "[FINNHUB] Message error:",
                error
            )


    # =================================================
    # PROCESS TICK
    # =================================================

    def process_tick(
        self,
        trade
    ):

        try:

            price = float(
                trade["p"]
            )

            timestamp = int(
                trade["t"]
            )


        except (
            KeyError,
            TypeError,
            ValueError
        ):

            return


        # Finnhub tells us which provider symbol
        # generated this tick.

        finnhub_symbol = trade.get(
            "s"
        )


        if not finnhub_symbol:

            print(
                "[FINNHUB] Trade symbol missing:",
                trade
            )

            return


        # Convert provider symbol back to
        # our dashboard symbol.

        browser_symbol = (
            self.get_browser_symbol(
                finnhub_symbol
            )
        )


        if not browser_symbol:

            print(
                "[FINNHUB] Unknown trade symbol:",
                finnhub_symbol
            )

            return


        # ---------------------------------------------
        # Create browser tick
        # ---------------------------------------------

        tick = {

            "type":
                "market_tick",

            "symbol":
                browser_symbol,

            "provider_symbol":
                finnhub_symbol,

            "price":
                price,

            "timestamp":
                timestamp

        }


        print(
            f"[LIVE] "
            f"{browser_symbol} "
            f"{price}"
        )


        # ---------------------------------------------
        # Send to Django Channels
        # ---------------------------------------------

        channel_layer = (
            get_channel_layer()
        )


        async_to_sync(
            channel_layer.group_send
        )(
            "market_data",
            {

                "type":
                    "market_tick",

                "data":
                    tick

            }
        )


    # =================================================
    # SEND STATUS TO BROWSER
    # =================================================

    def send_status_to_browser(
        self,
        data
    ):

        channel_layer = (
            get_channel_layer()
        )


        async_to_sync(
            channel_layer.group_send
        )(
            "market_data",
            {

                "type":
                    "feed_status",

                "data":
                    data

            }
        )


    # =================================================
    # FINNHUB ERROR
    # =================================================

    def on_error(
        self,
        ws,
        error
    ):

        print(
            "[FINNHUB ERROR]",
            error
        )


        self.send_status_to_browser(
            {

                "status":
                    "error",

                "message":
                    str(error)

            }
        )


    # =================================================
    # FINNHUB CLOSE
    # =================================================

    def on_close(
        self,
        ws,
        close_status_code,
        close_msg
    ):

        print(
            "[FINNHUB CLOSED]",
            close_status_code,
            close_msg
        )


        self.ws = None


        self.send_status_to_browser(
            {

                "status":
                    "closed",

                "message":
                    "Finnhub connection closed"

            }
        )


    # =================================================
    # START
    # =================================================

    def start(
        self
    ):

        if self.running:

            print(
                "[FINNHUB] Feed already running"
            )

            return


        if not FINNHUB_API_KEY:

            print(
                "[FINNHUB ERROR] "
                "FINNHUB_API_KEY not found"
            )

            return


        self.running = True


        self.thread = threading.Thread(

            target=self.run,

            daemon=True

        )


        self.thread.start()


        print(
            "[FINNHUB] Background feed started"
        )


    # =================================================
    # RUN
    # =================================================

    def run(
        self
    ):

        while self.running:

            try:

                print(
                    "[FINNHUB] Connecting..."
                )


                self.ws = websocket.WebSocketApp(

                    FINNHUB_WS_URL,

                    on_open=self.on_open,

                    on_message=self.on_message,

                    on_error=self.on_error,

                    on_close=self.on_close

                )


                self.ws.run_forever(

                    ping_interval=20,

                    ping_timeout=10

                )


            except Exception as error:

                print(
                    "[FINNHUB] Connection exception:",
                    error
                )


            self.ws = None


            if self.running:

                print(
                    "[FINNHUB] "
                    "Reconnecting in 5 seconds..."
                )

                time.sleep(
                    5
                )


# =====================================================
# GLOBAL FEED INSTANCE
# =====================================================

live_market_feed = LiveMarketFeed()