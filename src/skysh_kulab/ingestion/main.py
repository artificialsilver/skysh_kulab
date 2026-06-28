from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import UTC, datetime

from skysh_kulab.ingestion.config import IngestionConfig
from skysh_kulab.ingestion.domain import Actor, Side, TradeEvent
from skysh_kulab.ingestion.minute_bucket import MinuteBucketRepository
from skysh_kulab.ingestion.redis_resp import RedisClient
from skysh_kulab.ingestion.upbit import UpbitTradeIngestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Skysh Kulab Upbit ingestion worker")
    parser.add_argument(
        "command",
        choices=("run", "fake-once", "ping-redis"),
        help="run: Upbit WebSocket, fake-once: write one test event, ping-redis: Redis health check",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = IngestionConfig()
    redis = RedisClient(config.redis.host, config.redis.port, config.redis.db)

    try:
        if args.command == "ping-redis":
            print("PONG" if redis.ping() else "NO PONG")
            return

        repository = MinuteBucketRepository(redis, config.redis.bucket_ttl_seconds)

        if args.command == "fake-once":
            event = TradeEvent(
                market="KRW-BTC",
                trade_ts=datetime.now(UTC),
                price=98500000.0,
                volume=0.12,
                amount_krw=11820000.0,
                side=Side.BUY,
                actor=Actor.WHALE,
            )
            key = repository.add_trade_event(event)
            print(key)
            print(repository.get_bucket(key))
            return

        worker = UpbitTradeIngestion(
            markets=config.markets,
            whale_threshold_krw=config.whale_threshold_krw,
            bucket_repository=repository,
        )
        asyncio.run(worker.run_forever())
    finally:
        redis.close()


if __name__ == "__main__":
    main()

