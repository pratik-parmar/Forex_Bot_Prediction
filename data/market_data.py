import json
import asyncio
import websockets
from channels.layers import get_channel_layer

async def stream_live_forex_ticks(symbol="EUR_USD", api_key="FINNHUB_API_KEY"):
    """
    Connects to live Forex feed WebSocket and broadcasts true real-time ticks
    directly to the Django Channel group.
    """
    channel_layer = get_channel_layer()
    uri = f"wss://ws.finnhub.io?token={api_key}"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to currency pair
        subscribe_msg = json.dumps({"type": "subscribe", "symbol": f"OANDA:{symbol}"})
        await websocket.send(subscribe_msg)

        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            # Filter real-time trade/tick updates
            if data.get("type") == "trade":
                for tick in data["data"]:
                    live_payload = {
                        "type": "market_tick",  # Function name in consumers.py
                        "symbol": tick["s"],
                        "price": tick["p"],
                        "timestamp": tick["t"]
                    }
                    
                    # Broadcast immediately to all connected UI clients
                    await channel_layer.group_send("forex_live", live_payload)