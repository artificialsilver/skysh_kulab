from __future__ import annotations

import os
from dataclasses import dataclass


MARKETS = ("KRW-BTC", "KRW-ETH", "KRW-XRP")


@dataclass(frozen=True)
class RedisConfig:
    host: str = os.getenv("REDIS_HOST", "127.0.0.1")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    bucket_ttl_seconds: int = int(os.getenv("REDIS_BUCKET_TTL_SECONDS", "18000"))


@dataclass(frozen=True)
class IngestionConfig:
    markets: tuple[str, ...] = MARKETS
    whale_threshold_krw: float = float(os.getenv("WHALE_THRESHOLD_KRW", "10000000"))
    redis: RedisConfig = RedisConfig()

