import json
import os
import threading
import time

import websocket
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

FINNHUB_WS_URL = (
    f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"
)


# Browser symbol -> Finnhub symbol
SYMBOL_MAP = {
    "XAUUSD": "OANDA:XAU_USD",
    "EURUSD": "OANDA:EUR_USD",
    "GBPUSD": "OANDA:GBP_USD",
    "BTCUSD": "BINANCE:BTCUSDT",
}


class LiveMarketFeed:

    def __init__(self):

        self.ws = None
        self.thread = None
        self.running = False

        self.current_symbol = "XAUUSD"

        self.lock = threading.Lock()

    # -------------------------------------------------
    # Get Finnhub symbol
    # -------------------------------------------------

    def get_finnhub_symbol(self, symbol):

        symbol = symbol.upper().strip()

        return SYMBOL_MAP.get(symbol)

    # -------------------------------------------------
    # WebSocket OPEN
    # -------------------------------------------------

    def on_open(self, ws):

        print("======================================")
        print("FINNHUB WEBSOCKET CONNECTED")
        print("======================================")

        self.subscribe_current_symbol()

    # -------------------------------------------------
    # Subscribe
    # -------------------------------------------------

    def subscribe_current_symbol(self):

        if not self.ws:
            return

        browser_symbol = self.current_symbol

        finnhub_symbol = self.get_finnhub_symbol(
            browser_symbol
        )

        if not finnhub_symbol:

            print(
                f"[FINNHUB] Unsupported symbol: "
                f"{browser_symbol}"
            )

            return

        message = {
            "type": "subscribe",
            "symbol": finnhub_symbol
        }

        try:

            self.ws.send(
                json.dumps(message)
            )

            print(
                f"[FINNHUB] SUBSCRIBED: "
                f"{browser_symbol} -> "
                f"{finnhub_symbol}"
            )

        except Exception as e:

            print(
                "[FINNHUB] Subscribe error:",
                e
            )

    # -------------------------------------------------
    # Unsubscribe
    # -------------------------------------------------

    def unsubscribe_symbol(self, finnhub_symbol):

        if not self.ws:
            return

        message = {
            "type": "unsubscribe",
            "symbol": finnhub_symbol
        }

        try:

            self.ws.send(
                json.dumps(message)
            )

            print(
                f"[FINNHUB] UNSUBSCRIBED: "
                f"{finnhub_symbol}"
            )

        except Exception as e:

            print(
                "[FINNHUB] Unsubscribe error:",
                e
            )

    # -------------------------------------------------
    # Change symbol
    # -------------------------------------------------

    def change_symbol(self, symbol):

        symbol = symbol.upper().strip()

        if symbol not in SYMBOL_MAP:

            print(
                f"[FINNHUB] Invalid symbol: {symbol}"
            )

            return False

        with self.lock:

            old_symbol = self.current_symbol

            old_finnhub_symbol = (
                self.get_finnhub_symbol(
                    old_symbol
                )
            )

            new_finnhub_symbol = (
                self.get_finnhub_symbol(
                    symbol
                )
            )

            self.current_symbol = symbol

        print(
            f"[FINNHUB] Symbol change: "
            f"{old_symbol} -> {symbol}"
        )

        print(
            f"[FINNHUB] Provider symbol: "
            f"{new_finnhub_symbol}"
        )

        if self.ws:

            # Remove old subscription
            if old_finnhub_symbol:
                self.unsubscribe_symbol(
                    old_finnhub_symbol
                )

            # Subscribe new symbol
            self.subscribe_current_symbol()

        return True

    # -------------------------------------------------
    # FINNHUB MESSAGE
    # -------------------------------------------------

    def on_message(self, ws, message):

        try:

            data = json.loads(message)

            print(
                "[FINNHUB RAW]",
                data
            )

            message_type = data.get("type")

            # -----------------------------------------
            # Finnhub status messages
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
            # Trade data
            # -----------------------------------------

            trades = data.get(
                "data",
                []
            )

            for trade in trades:

                self.process_tick(
                    trade
                )

        except Exception as e:

            print(
                "[FINNHUB] Message error:",
                e
            )

    # -------------------------------------------------
    # Process tick
    # -------------------------------------------------

    def process_tick(self, trade):

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

        browser_symbol = (
            self.current_symbol
        )

        tick = {

            "type": "market_tick",

            "symbol": browser_symbol,

            "provider_symbol":
                self.get_finnhub_symbol(
                    browser_symbol
                ),

            "price": price,

            "timestamp": timestamp

        }

        print(
            f"[LIVE] "
            f"{browser_symbol} "
            f"{price}"
        )

        channel_layer = (
            get_channel_layer()
        )

        async_to_sync(
            channel_layer.group_send
        )(
            "market_data",
            {
                "type": "market_tick",
                "data": tick
            }
        )

    # -------------------------------------------------
    # Send status to browser
    # -------------------------------------------------

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
                "type": "feed_status",
                "data": data
            }
        )

    # -------------------------------------------------
    # FINNHUB ERROR
    # -------------------------------------------------

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
                "status": "error",
                "message": str(error)
            }
        )

    # -------------------------------------------------
    # FINNHUB CLOSE
    # -------------------------------------------------

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
                "status": "closed",
                "message": "Finnhub connection closed"
            }
        )

    # -------------------------------------------------
    # START
    # -------------------------------------------------

    def start(self):

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

    # -------------------------------------------------
    # RUN
    # -------------------------------------------------

    def run(self):

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

            except Exception as e:

                print(
                    "[FINNHUB] Connection exception:",
                    e
                )

            self.ws = None

            if self.running:

                print(
                    "[FINNHUB] "
                    "Reconnecting in 5 seconds..."
                )

                time.sleep(5)


live_market_feed = LiveMarketFeed()