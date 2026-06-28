from __future__ import annotations

import unittest
from datetime import UTC, datetime

from skysh_kulab.ingestion.domain import Actor, Side, TradeEvent
from skysh_kulab.ingestion.minute_bucket import actor_count_field_name, flow_amount_field
from skysh_kulab.ingestion.upbit import subscription_payload


class IngestionContractTest(unittest.TestCase):
    def test_trade_event_redis_key_uses_utc_minute(self) -> None:
        event = TradeEvent(
            market="KRW-BTC",
            trade_ts=datetime(2026, 6, 28, 5, 30, 12, 123000, tzinfo=UTC),
            price=98500000.0,
            volume=0.12,
            amount_krw=11820000.0,
            side=Side.BUY,
            actor=Actor.WHALE,
        )

        self.assertEqual(event.redis_key, "bucket:KRW-BTC:202606280530")

    def test_bucket_field_names_match_docs(self) -> None:
        self.assertEqual(flow_amount_field(Actor.WHALE, Side.BUY), "whale_buy_krw")
        self.assertEqual(flow_amount_field(Actor.WHALE, Side.SELL), "whale_sell_krw")
        self.assertEqual(flow_amount_field(Actor.RETAIL, Side.BUY), "retail_buy_krw")
        self.assertEqual(flow_amount_field(Actor.RETAIL, Side.SELL), "retail_sell_krw")
        self.assertEqual(actor_count_field_name(Actor.WHALE), "whale_count")
        self.assertEqual(actor_count_field_name(Actor.RETAIL), "retail_count")

    def test_upbit_subscription_uses_three_markets(self) -> None:
        payload = subscription_payload(("KRW-BTC", "KRW-ETH", "KRW-XRP"))

        self.assertEqual(
            payload[1],
            {
                "type": "trade",
                "codes": ["KRW-BTC", "KRW-ETH", "KRW-XRP"],
            },
        )

    def test_upbit_message_maps_to_trade_event(self) -> None:
        event = TradeEvent.from_upbit_message(
            {
                "code": "KRW-BTC",
                "trade_timestamp": 1782624612123,
                "trade_price": 98500000.0,
                "trade_volume": 0.12,
                "ask_bid": "BID",
            },
            whale_threshold_krw=10000000,
        )

        self.assertEqual(event.market, "KRW-BTC")
        self.assertEqual(event.trade_ts, datetime(2026, 6, 28, 5, 30, 12, 123000, tzinfo=UTC))
        self.assertEqual(event.amount_krw, 11820000.0)
        self.assertEqual(event.side, Side.BUY)
        self.assertEqual(event.actor, Actor.WHALE)


if __name__ == "__main__":
    unittest.main()
