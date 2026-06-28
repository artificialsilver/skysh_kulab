from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest import TestCase, main

from indicator_persona import MinuteBucket, Persona, calculate_indicator, classify_persona


def _bucket(
    minute: int,
    *,
    open_price: float = 100.0,
    close_price: float = 100.0,
    high: float | None = None,
    low: float | None = None,
    total_volume: float = 100.0,
    whale_buy: float = 0.0,
    whale_sell: float = 0.0,
    retail_buy: float = 0.0,
    retail_sell: float = 0.0,
    market: str = "KRW-BTC",
) -> MinuteBucket:
    start = datetime(2026, 6, 28, 5, 0, tzinfo=timezone.utc)
    return MinuteBucket(
        market=market,
        bucket_minute=start + timedelta(minutes=minute),
        open=open_price,
        high=high if high is not None else max(open_price, close_price),
        low=low if low is not None else min(open_price, close_price),
        close=close_price,
        total_volume_krw=total_volume,
        whale_buy_krw=whale_buy,
        whale_sell_krw=whale_sell,
        retail_buy_krw=retail_buy,
        retail_sell_krw=retail_sell,
        trade_count=10,
        whale_count=1 if whale_buy or whale_sell else 0,
        retail_count=9,
    )


class IndicatorCalculationTest(TestCase):
    def test_calculates_15m_indicator_from_latest_15_minute_buckets(self) -> None:
        buckets = [
            _bucket(
                minute,
                open_price=100 + minute,
                close_price=101 + minute,
                high=102 + minute,
                low=99 + minute,
                total_volume=100,
                whale_buy=20,
                whale_sell=5,
                retail_buy=10,
                retail_sell=3,
            )
            for minute in range(20)
        ]

        indicator = calculate_indicator(
            "KRW-BTC", "15m", buckets, baseline_window_volumes=[1000]
        )

        self.assertEqual(indicator.timeframe, "15m")
        self.assertEqual(indicator.window_start, buckets[5].bucket_minute)
        self.assertEqual(indicator.snapshot_at, buckets[19].bucket_minute + timedelta(minutes=1))
        self.assertEqual(indicator.price_open, 105)
        self.assertEqual(indicator.price_close, 120)
        self.assertEqual(indicator.price_high, 121)
        self.assertEqual(indicator.price_low, 104)
        self.assertEqual(indicator.total_volume_krw, 1500)
        self.assertAlmostEqual(indicator.volume_surge_ratio, 1.5)
        self.assertEqual(indicator.trade_count, 150)
        self.assertAlmostEqual(indicator.whale_net_ratio, 225 / 1500)

    def test_calculates_4h_persistence_metrics(self) -> None:
        buckets = [
            _bucket(
                minute,
                open_price=100,
                close_price=101 if minute % 2 == 0 else 99,
                total_volume=100,
                whale_buy=20 if minute % 3 == 0 else 0,
                whale_sell=20 if minute % 3 != 0 else 0,
            )
            for minute in range(240)
        ]

        indicator = calculate_indicator("KRW-BTC", "4h", buckets)

        self.assertEqual(indicator.timeframe, "4h")
        self.assertIn("positive_bucket_ratio", indicator.metrics_json)
        self.assertAlmostEqual(indicator.metrics_json["positive_bucket_ratio"], 0.5)
        self.assertGreater(indicator.metrics_json["whale_sell_bucket_ratio"], 0.6)


class PersonaClassificationTest(TestCase):
    def test_classifies_breakout(self) -> None:
        buckets = [
            _bucket(
                minute,
                open_price=100,
                close_price=102,
                high=102,
                low=99,
                total_volume=200,
                whale_buy=60,
                whale_sell=10,
                retail_buy=20,
                retail_sell=10,
            )
            for minute in range(15)
        ]

        indicator = calculate_indicator(
            "KRW-BTC", "15m", buckets, baseline_window_volumes=[1000]
        )
        persona = classify_persona(indicator)

        self.assertEqual(persona.persona, Persona.BREAKOUT)
        self.assertIn("price_breakout", persona.reason_codes)

    def test_classifies_distribution_trap_before_breakout(self) -> None:
        buckets = [
            _bucket(
                minute,
                open_price=100,
                close_price=101,
                high=102,
                low=99,
                total_volume=200,
                whale_buy=5,
                whale_sell=50,
                retail_buy=60,
                retail_sell=5,
            )
            for minute in range(15)
        ]

        indicator = calculate_indicator("KRW-BTC", "15m", buckets)
        persona = classify_persona(indicator)

        self.assertEqual(persona.persona, Persona.DISTRIBUTION_TRAP)
        self.assertIn("divergence", persona.reason_codes)


if __name__ == "__main__":
    main()
