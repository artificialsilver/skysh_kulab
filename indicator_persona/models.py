from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal

Timeframe = Literal["15m", "4h"]


class Persona(str, Enum):
    ACCUMULATION = "accumulation"
    BREAKOUT = "breakout"
    DISTRIBUTION_TRAP = "distribution_trap"
    PANIC_SELL = "panic_sell"
    RETAIL_CHOP = "retail_chop"
    SLEEP = "sleep"


@dataclass(frozen=True)
class MinuteBucket:
    market: str
    bucket_minute: datetime
    open: float
    high: float
    low: float
    close: float
    total_volume_krw: float
    whale_buy_krw: float
    whale_sell_krw: float
    retail_buy_krw: float
    retail_sell_krw: float
    trade_count: int
    whale_count: int
    retail_count: int


@dataclass(frozen=True)
class IndicatorSnapshot:
    market: str
    timeframe: Timeframe
    window_start: datetime
    window_end: datetime
    snapshot_at: datetime
    price_open: float
    price_high: float
    price_low: float
    price_close: float
    price_change_pct: float
    volatility_pct: float
    total_volume_krw: float
    volume_surge_ratio: float
    whale_buy_krw: float
    whale_sell_krw: float
    retail_buy_krw: float
    retail_sell_krw: float
    whale_net_krw: float
    retail_net_krw: float
    whale_net_ratio: float
    retail_net_ratio: float
    divergence_score: float
    trade_count: int
    whale_count: int
    retail_count: int
    metrics_json: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PersonaSnapshot:
    market: str
    timeframe: Timeframe
    snapshot_at: datetime
    persona: Persona
    confidence: float
    reason_codes: list[str]
    metrics_json: dict[str, Any]
