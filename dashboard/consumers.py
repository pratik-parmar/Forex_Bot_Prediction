import os
import json
import asyncio
import numpy as np
import websockets
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from dotenv import load_dotenv

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

class ForexLiveConsumer(AsyncWebsocketConsumer):
    stream_task = None
    price_histories = {
        "XAUUSD": [],
        "EURUSD": [],
        "GBPUSD": [],
        "BTCUSD": []
    }

    async def connect(self):
        self.group_name = "forex_live"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if ForexLiveConsumer.stream_task is None or ForexLiveConsumer.stream_task.done():
            ForexLiveConsumer.stream_task = asyncio.create_task(self.start_live_stream_safely())

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def market_tick(self, event):
        await self.send(text_data=json.dumps({
            "symbol": event.get("symbol"),
            "price": event.get("price"),
            "ema_20": event.get("ema_20"),
            "ema_50": event.get("ema_50"),
            "rsi_14": event.get("rsi_14"),
            "atr_14": event.get("atr_14"),
            "signal": event.get("signal"),
            "reason": event.get("reason")
        }))

    async def start_live_stream_safely(self):
        """Outer wrapper with auto-reconnect loop so the stream never dies permanently."""
        while True:
            try:
                await self.start_live_stream()
            except Exception as e:
                print(f"[-] Finnhub Stream Error: {e}. Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def start_live_stream(self):
        channel_layer = get_channel_layer()
        
        if not FINNHUB_API_KEY:
            print("[!] WARNING: FINNHUB_API_KEY is missing from environment variables!")
            
        api_key = FINNHUB_API_KEY if FINNHUB_API_KEY else "c0123456789"
        uri = f"wss://ws.finnhub.io?token={api_key}"

        async with websockets.connect(uri) as ws:
            symbols_to_subscribe = [
                "OANDA:XAU_USD",
                "OANDA:EUR_USD",
                "OANDA:GBP_USD",
                "BINANCE:BTCUSDT",
                "BITSTAMP:BTCUSD"
            ]
            
            for sym in symbols_to_subscribe:
                await ws.send(json.dumps({"type": "subscribe", "symbol": sym}))

            while True:
                response = await ws.recv()
                payload = json.loads(response)

                if payload.get("type") == "trade":
                    for tick in payload.get("data", []):
                        raw_sym = tick.get("s", "")
                        price = float(tick.get("p", 0))
                        
                        clean_symbol = None
                        if "XAU" in raw_sym:
                            clean_symbol = "XAUUSD"
                        elif "EUR" in raw_sym:
                            clean_symbol = "EURUSD"
                        elif "GBP" in raw_sym:
                            clean_symbol = "GBPUSD"
                        elif "BTC" in raw_sym or "BITSTAMP" in raw_sym or "BINANCE" in raw_sym:
                            clean_symbol = "BTCUSD"

                        if clean_symbol and price > 0:
                            history = ForexLiveConsumer.price_histories[clean_symbol]
                            history.append(price)
                            if len(history) > 100:
                                history.pop(0)

                            ema20, ema50, rsi14, atr14, signal, reason = self.calculate_indicators(history)

                            await channel_layer.group_send(
                                "forex_live",
                                {
                                    "type": "market_tick",
                                    "symbol": clean_symbol,
                                    "price": price,
                                    "ema_20": ema20,
                                    "ema_50": ema50,
                                    "rsi_14": rsi14,
                                    "atr_14": atr14,
                                    "signal": signal,
                                    "reason": reason
                                }
                            )

    def calculate_indicators(self, history):
        if len(history) < 5:
            return "-", "-", "-", "-", "HOLD", "Gathering initial price data..."

        arr = np.array(history)

        ema_20 = round(float(pd_ema(arr, 20)), 2) if len(arr) >= 20 else round(arr[-1], 2)
        ema_50 = round(float(pd_ema(arr, 50)), 2) if len(arr) >= 50 else round(arr[-1], 2)
        rsi_14 = round(float(compute_rsi(arr, 14)), 2) if len(arr) >= 15 else 50.0
        atr_14 = round(float(np.mean(np.abs(np.diff(arr[-15:])))) if len(arr) >= 15 else 0.1, 4)

        signal = "HOLD"
        reason = "Market consolidating between EMAs."
        if ema_20 > ema_50:
            signal = "BUY"
            reason = "EMA 20 crossed above EMA 50 (Bullish Momentum)."
        elif ema_20 < ema_50:
            signal = "SELL"
            reason = "EMA 20 dropped below EMA 50 (Bearish Pressure)."

        return ema_20, ema_50, rsi_14, atr_14, signal, reason

def pd_ema(data, window):
    alpha = 2 / (window + 1)
    ema = data[0]
    for val in data[1:]:
        ema = (val * alpha) + (ema * (1 - alpha))
    return ema

def compute_rsi(data, window=14):
    deltas = np.diff(data)
    seed = deltas[:window]
    up = seed[seed >= 0].sum() / window
    down = -seed[seed < 0].sum() / window
    if down == 0:
        return 100.0
    rs = up / down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

RealtimeConsumer = ForexLiveConsumer