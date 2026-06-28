from __future__ import annotations

from datetime import timedelta
from math import copysign
from statistics import mean

from indicator_persona.models import IndicatorSnapshot, MinuteBucket, Timeframe
from indicator_persona.thresholds import ThresholdConfig, get_threshold

WINDOW_BUCKET_COUNTS: dict[Timeframe, int] = {"15m": 15, "4h": 240}


def calculate_indicator(
    market: str,
    timeframe: Timeframe,
    buckets: list[MinuteBucket],
    baseline_window_volumes: list[float] | None = None,
    threshold: ThresholdConfig | None = None,
) -> IndicatorSnapshot:
    """Calculate an indicator snapshot from latest 1-minute buckets."""
    if timeframe not in WINDOW_BUCKET_COUNTS:
        raise ValueError(f"unsupported timeframe: {timeframe}")

    valid_buckets = sorted(
        (bucket for bucket in buckets if bucket.market == market),
        key=lambda bucket: bucket.bucket_minute,
    )
    window_buckets = valid_buckets[-WINDOW_BUCKET_COUNTS[timeframe] :]
    if not window_buckets:
        raise ValueError("cannot calculate indicator without valid buckets")

    active_threshold = threshold or get_threshold(market, timeframe)
    price_open = window_buckets[0].open
    price_high = max(bucket.high for bucket in window_buckets)
    price_low = min(bucket.low for bucket in window_buckets)
    price_close = window_buckets[-1].close

    price_change_pct = (
        ((price_close - price_open) / price_open) * 100 if price_open > 0 else 0.0
    )
    volatility_pct = (
        ((price_high - price_low) / price_open) * 100 if price_open > 0 else 0.0
    )

    total_volume_krw = sum(bucket.total_volume_krw for bucket in window_buckets)
    whale_buy_krw = sum(bucket.whale_buy_krw for bucket in window_buckets)
    whale_sell_krw = sum(bucket.whale_sell_krw for bucket in window_buckets)
    retail_buy_krw = sum(bucket.retail_buy_krw for bucket in window_buckets)
    retail_sell_krw = sum(bucket.retail_sell_krw for bucket in window_buckets)

    whale_net_krw = whale_buy_krw - whale_sell_krw
    retail_net_krw = retail_buy_krw - retail_sell_krw

    if total_volume_krw > 0:
        whale_net_ratio = whale_net_krw / total_volume_krw
        retail_net_ratio = retail_net_krw / total_volume_krw
    else:
        whale_net_ratio = 0.0
        retail_net_ratio = 0.0

    divergence_score = _divergence_score(price_change_pct, whale_net_krw, whale_net_ratio)
    volume_surge_ratio = _volume_surge_ratio(total_volume_krw, baseline_window_volumes)
    metrics_json = {"threshold_version": "v1-temp"}

    if timeframe == "4h":
        metrics_json.update(_calculate_4h_metrics(window_buckets, active_threshold))

    window_start = window_buckets[0].bucket_minute
    window_end = window_buckets[-1].bucket_minute + timedelta(minutes=1)

    return IndicatorSnapshot(
        market=market,
        timeframe=timeframe,
        window_start=window_start,
        window_end=window_end,
        snapshot_at=window_end,
        price_open=price_open,
        price_high=price_high,
        price_low=price_low,
        price_close=price_close,
        price_change_pct=price_change_pct,
        volatility_pct=volatility_pct,
        total_volume_krw=total_volume_krw,
        volume_surge_ratio=volume_surge_ratio,
        whale_buy_krw=whale_buy_krw,
        whale_sell_krw=whale_sell_krw,
        retail_buy_krw=retail_buy_krw,
        retail_sell_krw=retail_sell_krw,
        whale_net_krw=whale_net_krw,
        retail_net_krw=retail_net_krw,
        whale_net_ratio=whale_net_ratio,
        retail_net_ratio=retail_net_ratio,
        divergence_score=divergence_score,
        trade_count=sum(bucket.trade_count for bucket in window_buckets),
        whale_count=sum(bucket.whale_count for bucket in window_buckets),
        retail_count=sum(bucket.retail_count for bucket in window_buckets),
        metrics_json=metrics_json,
    )


def _sign(value: float) -> int:
    if value == 0:
        return 0
    return int(copysign(1, value))


def _divergence_score(
    price_change_pct: float, whale_net_krw: float, whale_net_ratio: float
) -> float:
    price_direction = _sign(price_change_pct)
    whale_direction = _sign(whale_net_krw)
    if price_direction and whale_direction and price_direction != whale_direction:
        return min(abs(whale_net_ratio), 1.0)
    return 0.0


def _volume_surge_ratio(
    current_window_total_volume_krw: float, baseline_window_volumes: list[float] | None
) -> float:
    if not baseline_window_volumes:
        return 1.0
    positive_baselines = [volume for volume in baseline_window_volumes if volume > 0]
    if not positive_baselines:
        return 1.0
    return current_window_total_volume_krw / mean(positive_baselines)


def _calculate_4h_metrics(
    buckets: list[MinuteBucket], threshold: ThresholdConfig
) -> dict[str, float | int]:
    valid_bucket_count = len(buckets)
    if valid_bucket_count == 0:
        return {
            "positive_bucket_ratio": 0.0,
            "negative_bucket_ratio": 0.0,
            "whale_buy_bucket_ratio": 0.0,
            "whale_sell_bucket_ratio": 0.0,
            "divergence_bucket_count": 0,
            "strong_move_bucket_count": 0,
        }

    average_bucket_volume = mean(
        bucket.total_volume_krw for bucket in buckets if bucket.total_volume_krw > 0
    ) if any(bucket.total_volume_krw > 0 for bucket in buckets) else 0.0

    return {
        "positive_bucket_ratio": sum(bucket.close > bucket.open for bucket in buckets)
        / valid_bucket_count,
        "negative_bucket_ratio": sum(bucket.close < bucket.open for bucket in buckets)
        / valid_bucket_count,
        "whale_buy_bucket_ratio": sum(
            bucket.whale_buy_krw > bucket.whale_sell_krw for bucket in buckets
        )
        / valid_bucket_count,
        "whale_sell_bucket_ratio": sum(
            bucket.whale_sell_krw > bucket.whale_buy_krw for bucket in buckets
        )
        / valid_bucket_count,
        "divergence_bucket_count": sum(_bucket_diverged(bucket) for bucket in buckets),
        "strong_move_bucket_count": sum(
            _bucket_is_strong_move(bucket, threshold, average_bucket_volume)
            for bucket in buckets
        ),
    }


def _bucket_diverged(bucket: MinuteBucket) -> bool:
    bucket_price_change = bucket.close - bucket.open
    bucket_whale_net = bucket.whale_buy_krw - bucket.whale_sell_krw
    price_direction = _sign(bucket_price_change)
    whale_direction = _sign(bucket_whale_net)
    return bool(price_direction and whale_direction and price_direction != whale_direction)


def _bucket_is_strong_move(
    bucket: MinuteBucket, threshold: ThresholdConfig, average_bucket_volume: float
) -> bool:
    bucket_volatility_pct = (
        ((bucket.high - bucket.low) / bucket.open) * 100 if bucket.open > 0 else 0.0
    )
    volume_is_strong = (
        average_bucket_volume > 0
        and bucket.total_volume_krw >= average_bucket_volume * threshold.volume_surge
    )
    return bucket_volatility_pct >= threshold.volatility_mid or volume_is_strong
