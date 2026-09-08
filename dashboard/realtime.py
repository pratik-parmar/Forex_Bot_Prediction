import os
import json
import asyncio
import websockets
from channels.layers import get_channel_layer
from dotenv import load_dotenv

# Load .env variables
load_dotenv()
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

async def stream_polygon_live_data(symbol="XAUUSD"):
    """
    Connects to Polygon.io Forex WebSocket stream, listens for live tick updates,
    and forwards prices to the Django Channels WebSocket group.
    """
    if not POLYGON_API_KEY:
        print("[-] ERROR: POLYGON_API_KEY is not defined in .env")
        return

    # Polygon Forex WebSocket cluster
    uri = "wss://socket.polygon.io/forex"
    channel_layer = get_channel_layer()

    # Format ticker for Polygon Forex (e.g. C.C:XAUUSD or C.C:EURUSD)
    polygon_ticker = f"C.C:{symbol}"

    async with websockets.connect(uri) as ws:
        # 1. Authenticate with Polygon
        auth_payload = {"action": "auth", "params": POLYGON_API_KEY}
        await ws.send(json.dumps(auth_payload))
        
        # 2. Subscribe to currency quotes
        sub_payload = {"action": "subscribe", "params": polygon_ticker}
        await ws.send(json.dumps(sub_payload))

        print(f"[+] Subscribed to Polygon feed for: {symbol}")

        # 3. Stream incoming data ticks
        while True:
            response = await ws.recv()
            messages = json.loads(response)

            for msg in messages:
                event_type = msg.get("ev")

                # 'C' represents Forex/Gold Quote updates
                if event_type == "C":
                    bid = msg.get("b", 0)
                    ask = msg.get("a", 0)
                    price = (bid + ask) / 2 if (bid and ask) else (bid or ask)

                    if price > 0:
                        # Broadcast live price directly to consumer channel group
                        await channel_layer.group_send(
                            "forex_live",
                            {
                                "type": "market_tick",  # Function in consumers.py
                                "price": price,
                                "symbol": symbol
                            }
                        )