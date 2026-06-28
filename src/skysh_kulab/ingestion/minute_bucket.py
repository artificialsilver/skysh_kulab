from __future__ import annotations

from dataclasses import dataclass

from skysh_kulab.ingestion.domain import Actor, Side, TradeEvent
from skysh_kulab.ingestion.redis_resp import RedisClient


BUCKET_UPSERT_SCRIPT = """
local key = KEYS[1]
local price = tonumber(ARGV[1])
local amount = tonumber(ARGV[2])
local flow_field = ARGV[3]
local actor_count_field = ARGV[4]
local ttl = tonumber(ARGV[5])

if redis.call("EXISTS", key) == 0 then
  redis.call(
    "HSET",
    key,
    "open", price,
    "high", price,
    "low", price,
    "close", price,
    "total_volume_krw", 0,
    "whale_buy_krw", 0,
    "whale_sell_krw", 0,
    "retail_buy_krw", 0,
    "retail_sell_krw", 0,
    "trade_count", 0,
    "whale_count", 0,
    "retail_count", 0
  )
end

local high = tonumber(redis.call("HGET", key, "high"))
local low = tonumber(redis.call("HGET", key, "low"))

if price > high then
  redis.call("HSET", key, "high", price)
end

if price < low then
  redis.call("HSET", key, "low", price)
end

redis.call("HSET", key, "close", price)
redis.call("HINCRBYFLOAT", key, "total_volume_krw", amount)
redis.call("HINCRBYFLOAT", key, flow_field, amount)
redis.call("HINCRBY", key, "trade_count", 1)
redis.call("HINCRBY", key, actor_count_field, 1)
redis.call("EXPIRE", key, ttl)

return key
""".strip()


@dataclass
class MinuteBucketRepository:
    redis: RedisClient
    ttl_seconds: int

    def add_trade_event(self, event: TradeEvent) -> str:
        flow_field = flow_amount_field(event.actor, event.side)
        actor_count_field = actor_count_field_name(event.actor)
        return self.redis.execute(
            "EVAL",
            BUCKET_UPSERT_SCRIPT,
            1,
            event.redis_key,
            event.price,
            event.amount_krw,
            flow_field,
            actor_count_field,
            self.ttl_seconds,
        )

    def get_bucket(self, key: str) -> dict[str, str]:
        return self.redis.hgetall(key)


def flow_amount_field(actor: Actor, side: Side) -> str:
    return f"{actor.value}_{side.value}_krw"


def actor_count_field_name(actor: Actor) -> str:
    return f"{actor.value}_count"

