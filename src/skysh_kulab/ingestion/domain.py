from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


class Actor(StrEnum):
    WHALE = "whale"
    RETAIL = "retail"


@dataclass(frozen=True)
class TradeEvent:
    market: str
    trade_ts: datetime
    price: float
    volume: float
    amount_krw: float
    side: Side
    actor: Actor

    @property
    def bucket_minute(self) -> datetime:
        return self.trade_ts.astimezone(UTC).replace(second=0, microsecond=0)

    @property
    def redis_key(self) -> str:
        return f"bucket:{self.market}:{self.bucket_minute:%Y%m%d%H%M}"

    @classmethod
    def from_upbit_message(
        cls,
        message: dict[str, Any],
        whale_threshold_krw: float,
    ) -> "TradeEvent":
        market = str(message["code"])
        price = float(message["trade_price"])
        volume = float(message["trade_volume"])
        amount_krw = price * volume
        side = parse_upbit_side(str(message["ask_bid"]))
        actor = Actor.WHALE if amount_krw >= whale_threshold_krw else Actor.RETAIL
        return cls(
            market=market,
            trade_ts=parse_upbit_trade_ts(message),
            price=price,
            volume=volume,
            amount_krw=amount_krw,
            side=side,
            actor=actor,
        )


def parse_upbit_side(ask_bid: str) -> Side:
    if ask_bid == "BID":
        return Side.BUY
    if ask_bid == "ASK":
        return Side.SELL
    raise ValueError(f"Unsupported Upbit ask_bid value: {ask_bid}")


def parse_upbit_trade_ts(message: dict[str, Any]) -> datetime:
    trade_timestamp = message.get("trade_timestamp") or message.get("timestamp")
    if trade_timestamp is None:
        raise ValueError("Upbit message does not include trade_timestamp or timestamp")
    return datetime.fromtimestamp(float(trade_timestamp) / 1000, tz=UTC)

