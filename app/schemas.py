from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.constants import ALERT_TIMEFRAME, MARKETS, PERSONAS, TIMEFRAMES


def iso_z(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_market(value: str) -> str:
    if value not in MARKETS:
        raise ValueError(f"market must be one of: {', '.join(MARKETS)}")
    return value


def validate_timeframe(value: str) -> str:
    if value not in TIMEFRAMES:
        raise ValueError(f"timeframe must be one of: {', '.join(TIMEFRAMES)}")
    return value


class IndicatorSnapshotIn(BaseModel):
    market: str
    timeframe: str
    snapshot_at: datetime
    window_start: datetime
    window_end: datetime
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
    metrics_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("market")
    @classmethod
    def _market(cls, value: str) -> str:
        return validate_market(value)

    @field_validator("timeframe")
    @classmethod
    def _timeframe(cls, value: str) -> str:
        return validate_timeframe(value)


class PersonaSnapshotIn(BaseModel):
    market: str
    timeframe: str
    snapshot_at: datetime
    persona: str
    confidence: float
    reason_codes: list[str] = Field(default_factory=list)
    metrics_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("market")
    @classmethod
    def _market(cls, value: str) -> str:
        return validate_market(value)

    @field_validator("timeframe")
    @classmethod
    def _timeframe(cls, value: str) -> str:
        return validate_timeframe(value)

    @field_validator("persona")
    @classmethod
    def _persona(cls, value: str) -> str:
        if value not in PERSONAS:
            raise ValueError(f"persona must be one of: {', '.join(PERSONAS)}")
        return value


class AlertSettingIn(BaseModel):
    timeframe: str = ALERT_TIMEFRAME
    enabled: bool

    @field_validator("timeframe")
    @classmethod
    def _alert_timeframe(cls, value: str) -> str:
        if value != ALERT_TIMEFRAME:
            raise ValueError("alert setting timeframe must be 15m")
        return value

