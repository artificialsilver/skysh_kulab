from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Iterable

from skysh_kulab.ingestion.domain import TradeEvent
from skysh_kulab.ingestion.minute_bucket import MinuteBucketRepository


UPBIT_WEBSOCKET_URL = "wss://api.upbit.com/websocket/v1"


@dataclass
class UpbitTradeIngestion:
    markets: tuple[str, ...]
    whale_threshold_krw: float
    bucket_repository: MinuteBucketRepository
    reconnect_delay_seconds: float = 3.0

    async def run_forever(self) -> None:
        while True:
            try:
                await self._run_once()
            except Exception:
                logging.exception("Upbit WebSocket ingestion failed; reconnecting")
                await asyncio.sleep(self.reconnect_delay_seconds)

    async def _run_once(self) -> None:
        import websockets

        async with websockets.connect(UPBIT_WEBSOCKET_URL, ping_interval=20) as websocket:
            await websocket.send(json.dumps(subscription_payload(self.markets)))
            async for raw_message in websocket:
                message = json.loads(raw_message.decode() if isinstance(raw_message, bytes) else raw_message)
                event = TradeEvent.from_upbit_message(message, self.whale_threshold_krw)
                key = self.bucket_repository.add_trade_event(event)
                logging.info(
                    "stored trade market=%s key=%s amount_krw=%.2f actor=%s side=%s",
                    event.market,
                    key,
                    event.amount_krw,
                    event.actor.value,
                    event.side.value,
                )


def subscription_payload(markets: Iterable[str]) -> list[dict[str, object]]:
    return [
        {"ticket": "skysh-kulab-ingestion"},
        {"type": "trade", "codes": list(markets)},
        {"format": "DEFAULT"},
    ]

