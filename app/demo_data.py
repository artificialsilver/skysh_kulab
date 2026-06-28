from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import MARKETS, TIMEFRAMES
from app.pipeline import calculate_snapshots
from app.storage import set_alert_setting, upsert_indicator_snapshot, upsert_persona_snapshot
from indicator_persona import MinuteBucket, Timeframe


SNAPSHOT_END = datetime(2026, 6, 28, 5, 30, tzinfo=UTC)


async def seed_demo_data(session: AsyncSession) -> None:
    if os.getenv("SKYSH_SEED_DEMO", "1") == "0":
        return

    for market in MARKETS:
        for timeframe in TIMEFRAMES:
            typed_timeframe: Timeframe = timeframe  # type: ignore[assignment]
            buckets = demo_buckets(market, typed_timeframe)
            baseline = [sum(bucket.total_volume_krw for bucket in buckets) * 0.62]
            indicator, persona = calculate_snapshots(market, typed_timeframe, buckets, baseline)
            await upsert_indicator_snapshot(session, indicator)
            await upsert_persona_snapshot(session, persona)

    for market in MARKETS:
        await set_alert_setting(session, market, "15m", market != "KRW-ETH")


def demo_buckets(market: str, timeframe: Timeframe) -> list[MinuteBucket]:
    count = 15 if timeframe == "15m" else 240
    start = SNAPSHOT_END - timedelta(minutes=count)
    profile = _profile(market)
    buckets: list[MinuteBucket] = []

    for index in range(count):
        progress = index / max(count - 1, 1)
        wave = ((index % 7) - 3) * profile["wave"]
        open_price = profile["base"] * (1 + profile["drift"] * progress) + wave
        close_price = open_price * (1 + profile["close_bias"])
        high = max(open_price, close_price) * (1 + profile["range"])
        low = min(open_price, close_price) * (1 - profile["range"])
        volume = profile["volume"] * (1 + progress * 0.35)
        whale_buy = volume * profile["whale_buy"]
        whale_sell = volume * profile["whale_sell"]
        retail_buy = volume * profile["retail_buy"]
        retail_sell = volume * profile["retail_sell"]

        buckets.append(
            MinuteBucket(
                market=market,
                bucket_minute=start + timedelta(minutes=index),
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                total_volume_krw=volume,
                whale_buy_krw=whale_buy,
                whale_sell_krw=whale_sell,
                retail_buy_krw=retail_buy,
                retail_sell_krw=retail_sell,
                trade_count=int(profile["trades"] * (1 + progress * 0.2)),
                whale_count=int(profile["whales"] * (1 + progress * 0.2)),
                retail_count=int(profile["trades"] * (1 + progress * 0.2)) - int(profile["whales"]),
            )
        )

    return buckets


def _profile(market: str) -> dict[str, float]:
    profiles = {
        "KRW-BTC": {
            "base": 97_000_000,
            "drift": 0.018,
            "wave": 65_000,
            "close_bias": 0.0015,
            "range": 0.004,
            "volume": 455_000_000,
            "whale_buy": 0.36,
            "whale_sell": 0.17,
            "retail_buy": 0.29,
            "retail_sell": 0.18,
            "trades": 1120,
            "whales": 14,
        },
        "KRW-ETH": {
            "base": 5_430_000,
            "drift": -0.004,
            "wave": 7_500,
            "close_bias": -0.0004,
            "range": 0.003,
            "volume": 180_000_000,
            "whale_buy": 0.22,
            "whale_sell": 0.29,
            "retail_buy": 0.27,
            "retail_sell": 0.22,
            "trades": 620,
            "whales": 7,
        },
        "KRW-XRP": {
            "base": 742,
            "drift": -0.022,
            "wave": 1.8,
            "close_bias": -0.002,
            "range": 0.007,
            "volume": 265_000_000,
            "whale_buy": 0.15,
            "whale_sell": 0.39,
            "retail_buy": 0.2,
            "retail_sell": 0.26,
            "trades": 2100,
            "whales": 10,
        },
    }
    return profiles[market]

