from datetime import UTC, datetime, timedelta

from app.pipeline import bucket_from_redis_hash, calculate_snapshots, redis_key_for_bucket


def test_redis_hash_bucket_calculates_indicator_and_persona_schema() -> None:
    start = datetime(2026, 6, 28, 5, 15, tzinfo=UTC)
    redis_bucket = {
        "open": "97000000.0",
        "high": "99000000.0",
        "low": "96900000.0",
        "close": "98500000.0",
        "total_volume_krw": "530000000.0",
        "whale_buy_krw": "210000000.0",
        "whale_sell_krw": "90000000.0",
        "retail_buy_krw": "150000000.0",
        "retail_sell_krw": "80000000.0",
        "trade_count": "1520",
        "whale_count": "18",
        "retail_count": "1502",
    }
    buckets = [
        bucket_from_redis_hash("KRW-BTC", start + timedelta(minutes=minute), redis_bucket)
        for minute in range(15)
    ]

    indicator, persona = calculate_snapshots("KRW-BTC", "15m", buckets, [3_000_000_000.0])

    assert redis_key_for_bucket("KRW-BTC", start) == "bucket:KRW-BTC:202606280515"
    assert indicator.market == "KRW-BTC"
    assert indicator.timeframe == "15m"
    assert indicator.total_volume_krw == 7_950_000_000.0
    assert persona.market == "KRW-BTC"
    assert persona.timeframe == "15m"
