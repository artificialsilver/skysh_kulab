from __future__ import annotations

from dataclasses import dataclass

from indicator_persona.models import Timeframe


@dataclass(frozen=True)
class ThresholdConfig:
    whale_threshold_krw: float
    price_flat: float
    price_up: float
    price_up_strong: float
    price_down_strong: float
    volatility_low: float
    volatility_mid: float
    volatility_high: float
    volume_surge: float
    volume_quiet: float
    whale_net_strong: float
    whale_net_positive: float
    whale_net_negative: float
    whale_net_weak: float
    retail_net_positive: float
    retail_net_active: float
    retail_net_weak: float
    divergence: float


DEFAULT_THRESHOLDS: dict[str, dict[Timeframe, ThresholdConfig]] = {
    "KRW-BTC": {
        "15m": ThresholdConfig(
            whale_threshold_krw=10_000_000,
            price_flat=0.30,
            price_up=0.50,
            price_up_strong=1.00,
            price_down_strong=1.00,
            volatility_low=0.50,
            volatility_mid=1.00,
            volatility_high=1.80,
            volume_surge=1.80,
            volume_quiet=0.70,
            whale_net_strong=0.15,
            whale_net_positive=0.08,
            whale_net_negative=0.08,
            whale_net_weak=0.04,
            retail_net_positive=0.08,
            retail_net_active=0.08,
            retail_net_weak=0.04,
            divergence=0.08,
        ),
        "4h": ThresholdConfig(
            whale_threshold_krw=10_000_000,
            price_flat=0.80,
            price_up=1.50,
            price_up_strong=3.00,
            price_down_strong=3.00,
            volatility_low=1.20,
            volatility_mid=2.50,
            volatility_high=5.00,
            volume_surge=1.40,
            volume_quiet=0.80,
            whale_net_strong=0.12,
            whale_net_positive=0.06,
            whale_net_negative=0.06,
            whale_net_weak=0.03,
            retail_net_positive=0.06,
            retail_net_active=0.06,
            retail_net_weak=0.03,
            divergence=0.06,
        ),
    },
    "KRW-ETH": {
        "15m": ThresholdConfig(
            whale_threshold_krw=7_000_000,
            price_flat=0.35,
            price_up=0.60,
            price_up_strong=1.20,
            price_down_strong=1.20,
            volatility_low=0.60,
            volatility_mid=1.20,
            volatility_high=2.00,
            volume_surge=1.80,
            volume_quiet=0.70,
            whale_net_strong=0.15,
            whale_net_positive=0.08,
            whale_net_negative=0.08,
            whale_net_weak=0.04,
            retail_net_positive=0.08,
            retail_net_active=0.08,
            retail_net_weak=0.04,
            divergence=0.08,
        ),
        "4h": ThresholdConfig(
            whale_threshold_krw=7_000_000,
            price_flat=1.00,
            price_up=1.80,
            price_up_strong=3.50,
            price_down_strong=3.50,
            volatility_low=1.50,
            volatility_mid=3.00,
            volatility_high=5.50,
            volume_surge=1.40,
            volume_quiet=0.80,
            whale_net_strong=0.12,
            whale_net_positive=0.06,
            whale_net_negative=0.06,
            whale_net_weak=0.03,
            retail_net_positive=0.06,
            retail_net_active=0.06,
            retail_net_weak=0.03,
            divergence=0.06,
        ),
    },
    "KRW-XRP": {
        "15m": ThresholdConfig(
            whale_threshold_krw=5_000_000,
            price_flat=0.50,
            price_up=0.90,
            price_up_strong=1.80,
            price_down_strong=1.80,
            volatility_low=0.90,
            volatility_mid=1.80,
            volatility_high=3.00,
            volume_surge=2.00,
            volume_quiet=0.70,
            whale_net_strong=0.16,
            whale_net_positive=0.09,
            whale_net_negative=0.09,
            whale_net_weak=0.05,
            retail_net_positive=0.09,
            retail_net_active=0.09,
            retail_net_weak=0.05,
            divergence=0.09,
        ),
        "4h": ThresholdConfig(
            whale_threshold_krw=5_000_000,
            price_flat=1.50,
            price_up=2.50,
            price_up_strong=5.00,
            price_down_strong=5.00,
            volatility_low=2.00,
            volatility_mid=4.00,
            volatility_high=7.00,
            volume_surge=1.50,
            volume_quiet=0.80,
            whale_net_strong=0.13,
            whale_net_positive=0.07,
            whale_net_negative=0.07,
            whale_net_weak=0.04,
            retail_net_positive=0.07,
            retail_net_active=0.07,
            retail_net_weak=0.04,
            divergence=0.07,
        ),
    },
}


def get_threshold(market: str, timeframe: Timeframe) -> ThresholdConfig:
    try:
        return DEFAULT_THRESHOLDS[market][timeframe]
    except KeyError as exc:
        raise ValueError(f"unsupported market/timeframe: {market}/{timeframe}") from exc
