from datetime import UTC, datetime, timedelta

from app.pipeline import bucket_from_redis_hash, calculate_snapshots, redis_key_for_bucket
from app.snapshot_worker import recent_bucket_keys


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


class FakeRedis:
    def __init__(self, keys: list[str]) -> None:
        self._keys = keys

    def keys(self, pattern: str) -> list[str]:
        market = pattern.removeprefix("bucket:").removesuffix(":*")
        return [key for key in self._keys if key.startswith(f"bucket:{market}:")]


def test_recent_bucket_keys_use_existing_latest_keys_not_wall_clock_range() -> None:
    keys = [
        "bucket:KRW-BTC:202606280500",
        "bucket:KRW-BTC:202606280501",
        "bucket:KRW-BTC:202606280510",
        "bucket:KRW-BTC:202606280530",
        "bucket:KRW-BTC:202606280545",
        "bucket:KRW-ETH:202606280600",
    ]

    recent = recent_bucket_keys(FakeRedis(keys), "KRW-BTC", 3)  # type: ignore[arg-type]

    assert [key for key, _ in recent] == [
        "bucket:KRW-BTC:202606280510",
        "bucket:KRW-BTC:202606280530",
        "bucket:KRW-BTC:202606280545",
    ]
