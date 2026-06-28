from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.constants import MARKETS, TIMEFRAMES
from app.db import SessionLocal, init_db
from app.pipeline import bucket_from_redis_hash, calculate_snapshots, redis_key_for_bucket
from app.storage import upsert_indicator_snapshot, upsert_persona_snapshot
from indicator_persona import MinuteBucket, Timeframe
from skysh_kulab.ingestion.config import IngestionConfig
from skysh_kulab.ingestion.redis_resp import RedisClient


WINDOW_MINUTES: dict[Timeframe, int] = {"15m": 15, "4h": 240}


async def run_snapshot_worker(interval_seconds: float = 30.0) -> None:
    await init_db()
    while True:
        try:
            saved = await calculate_and_store_once()
            logging.info("snapshot worker saved %s snapshot pairs", saved)
        except Exception:
            logging.exception("snapshot worker iteration failed")
        await asyncio.sleep(interval_seconds)


async def calculate_and_store_once() -> int:
    config = IngestionConfig()
    redis = RedisClient(config.redis.host, config.redis.port, config.redis.db)
    saved = 0
    try:
        async with SessionLocal() as session:
            for market in MARKETS:
                for timeframe in TIMEFRAMES:
                    typed_timeframe: Timeframe = timeframe  # type: ignore[assignment]
                    buckets = read_recent_buckets(redis, market, typed_timeframe)
                    if not buckets:
                        continue
                    indicator, persona = calculate_snapshots(market, typed_timeframe, buckets)
                    await upsert_indicator_snapshot(session, indicator)
                    await upsert_persona_snapshot(session, persona)
                    saved += 1
    finally:
        redis.close()
    return saved


def read_recent_buckets(redis: RedisClient, market: str, timeframe: Timeframe) -> list[MinuteBucket]:
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    buckets: list[MinuteBucket] = []
    for offset in range(WINDOW_MINUTES[timeframe], 0, -1):
        bucket_minute = now - timedelta(minutes=offset)
        key = redis_key_for_bucket(market, bucket_minute)
        values = redis.hgetall(key)
        if not values:
            continue
        buckets.append(bucket_from_redis_hash(market, bucket_minute, values))
    return buckets


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate Indicator/Persona snapshots from Redis buckets")
    parser.add_argument("command", choices=("once", "run"))
    parser.add_argument("--interval", type=float, default=30.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if args.command == "once":
        saved = asyncio.run(calculate_and_store_once())
        print(f"saved={saved}")
        return
    asyncio.run(run_snapshot_worker(args.interval))


if __name__ == "__main__":
    main()
