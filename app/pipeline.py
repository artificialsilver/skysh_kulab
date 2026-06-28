from __future__ import annotations

from datetime import UTC, datetime
from typing import Mapping

from indicator_persona import (
    IndicatorSnapshot,
    MinuteBucket,
    PersonaSnapshot,
    Timeframe,
    calculate_indicator,
    classify_persona,
)

from app.schemas import IndicatorSnapshotIn, PersonaSnapshotIn


REQUIRED_BUCKET_FIELDS = (
    "open",
    "high",
    "low",
    "close",
    "total_volume_krw",
    "whale_buy_krw",
    "whale_sell_krw",
    "retail_buy_krw",
    "retail_sell_krw",
    "trade_count",
    "whale_count",
    "retail_count",
)


def redis_key_for_bucket(market: str, bucket_minute: datetime) -> str:
    minute = bucket_minute.astimezone(UTC).replace(second=0, microsecond=0)
    return f"bucket:{market}:{minute:%Y%m%d%H%M}"


def bucket_from_redis_hash(
    market: str,
    bucket_minute: datetime,
    values: Mapping[str, str | int | float],
) -> MinuteBucket:
    missing = [field for field in REQUIRED_BUCKET_FIELDS if field not in values]
    if missing:
        raise ValueError(f"Redis bucket is missing fields: {', '.join(missing)}")

    return MinuteBucket(
        market=market,
        bucket_minute=bucket_minute.astimezone(UTC).replace(second=0, microsecond=0),
        open=float(values["open"]),
        high=float(values["high"]),
        low=float(values["low"]),
        close=float(values["close"]),
        total_volume_krw=float(values["total_volume_krw"]),
        whale_buy_krw=float(values["whale_buy_krw"]),
        whale_sell_krw=float(values["whale_sell_krw"]),
        retail_buy_krw=float(values["retail_buy_krw"]),
        retail_sell_krw=float(values["retail_sell_krw"]),
        trade_count=int(values["trade_count"]),
        whale_count=int(values["whale_count"]),
        retail_count=int(values["retail_count"]),
    )


def calculate_snapshots(
    market: str,
    timeframe: Timeframe,
    buckets: list[MinuteBucket],
    baseline_window_volumes: list[float] | None = None,
) -> tuple[IndicatorSnapshotIn, PersonaSnapshotIn]:
    indicator = calculate_indicator(market, timeframe, buckets, baseline_window_volumes)
    persona = classify_persona(indicator)
    return indicator_schema(indicator), persona_schema(persona)


def indicator_schema(snapshot: IndicatorSnapshot) -> IndicatorSnapshotIn:
    return IndicatorSnapshotIn(
        market=snapshot.market,
        timeframe=snapshot.timeframe,
        snapshot_at=snapshot.snapshot_at,
        window_start=snapshot.window_start,
        window_end=snapshot.window_end,
        price_open=snapshot.price_open,
        price_high=snapshot.price_high,
        price_low=snapshot.price_low,
        price_close=snapshot.price_close,
        price_change_pct=snapshot.price_change_pct,
        volatility_pct=snapshot.volatility_pct,
        total_volume_krw=snapshot.total_volume_krw,
        volume_surge_ratio=snapshot.volume_surge_ratio,
        whale_buy_krw=snapshot.whale_buy_krw,
        whale_sell_krw=snapshot.whale_sell_krw,
        retail_buy_krw=snapshot.retail_buy_krw,
        retail_sell_krw=snapshot.retail_sell_krw,
        whale_net_krw=snapshot.whale_net_krw,
        retail_net_krw=snapshot.retail_net_krw,
        whale_net_ratio=snapshot.whale_net_ratio,
        retail_net_ratio=snapshot.retail_net_ratio,
        divergence_score=snapshot.divergence_score,
        trade_count=snapshot.trade_count,
        whale_count=snapshot.whale_count,
        retail_count=snapshot.retail_count,
        metrics_json=snapshot.metrics_json,
    )


def persona_schema(snapshot: PersonaSnapshot) -> PersonaSnapshotIn:
    return PersonaSnapshotIn(
        market=snapshot.market,
        timeframe=snapshot.timeframe,
        snapshot_at=snapshot.snapshot_at,
        persona=snapshot.persona.value,
        confidence=snapshot.confidence,
        reason_codes=snapshot.reason_codes,
        metrics_json=snapshot.metrics_json,
    )

