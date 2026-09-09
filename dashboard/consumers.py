import json

from channels.generic.websocket import AsyncWebsocketConsumer

from dashboard.realtime import live_market_feed


class MarketConsumer(
    AsyncWebsocketConsumer
):

    async def connect(self):

        await self.channel_layer.group_add(
            "market_data",
            self.channel_name
        )

        await self.accept()

        print(
            "[DASHBOARD] Browser connected"
        )

        await self.send(
            text_data=json.dumps({
                "type": "status",
                "message":
                    "Django WebSocket connected"
            })
        )

    async def disconnect(
        self,
        close_code
    ):

        await self.channel_layer.group_discard(
            "market_data",
            self.channel_name
        )

        print(
            "[DASHBOARD] Browser disconnected"
        )

    async def receive(
        self,
        text_data
    ):

        try:

            data = json.loads(
                text_data
            )

            action = data.get(
                "action"
            )

            # -------------------------------------
            # CHANGE SYMBOL
            # -------------------------------------

            if action == "change_symbol":

                symbol = data.get(
                    "symbol"
                )

                if not symbol:

                    await self.send(
                        text_data=json.dumps({
                            "type": "feed_status",
                            "status": "error",
                            "message":
                                "Symbol missing"
                        })
                    )

                    return

                print(
                    f"[DASHBOARD] "
                    f"Symbol requested: {symbol}"
                )

                success = (
                    live_market_feed.change_symbol(
                        symbol
                    )
                )

                if success:

                    await self.send(
                        text_data=json.dumps({
                            "type":
                                "feed_status",
                            "status":
                                "subscribed",
                            "symbol":
                                symbol.upper(),
                            "message":
                                f"Subscribed to {symbol.upper()}"
                        })
                    )

                else:

                    await self.send(
                        text_data=json.dumps({
                            "type":
                                "feed_status",
                            "status":
                                "error",
                            "message":
                                f"Unsupported symbol: {symbol}"
                        })
                    )

        except Exception as e:

            print(
                "[DASHBOARD] Receive error:",
                e
            )

            await self.send(
                text_data=json.dumps({
                    "type": "feed_status",
                    "status": "error",
                    "message": str(e)
                })
            )

    async def market_tick(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps(
                event["data"]
            )
        )

    async def feed_status(
        self,
        event
    ):

        await self.send(
            text_data=json.dumps({
                "type": "feed_status",
                "data": event["data"]
            })
        )