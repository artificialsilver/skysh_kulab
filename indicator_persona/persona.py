from __future__ import annotations

from indicator_persona.models import IndicatorSnapshot, Persona, PersonaSnapshot
from indicator_persona.thresholds import ThresholdConfig, get_threshold


def classify_persona(
    indicator: IndicatorSnapshot,
    threshold: ThresholdConfig | None = None,
) -> PersonaSnapshot:
    active_threshold = threshold or get_threshold(indicator.market, indicator.timeframe)

    checks = [
        _panic_sell,
        _distribution_trap,
        _breakout,
        _accumulation,
        _retail_chop,
        _sleep,
    ]
    for check in checks:
        result = check(indicator, active_threshold)
        if result is not None:
            persona, reason_codes = result
            return _snapshot(indicator, persona, reason_codes)

    return _snapshot(indicator, Persona.SLEEP, ["fallback_sleep"])


def _snapshot(
    indicator: IndicatorSnapshot, persona: Persona, reason_codes: list[str]
) -> PersonaSnapshot:
    return PersonaSnapshot(
        market=indicator.market,
        timeframe=indicator.timeframe,
        snapshot_at=indicator.snapshot_at,
        persona=persona,
        confidence=_confidence(reason_codes),
        reason_codes=reason_codes,
        metrics_json={
            "price_change_pct": indicator.price_change_pct,
            "volatility_pct": indicator.volatility_pct,
            "volume_surge_ratio": indicator.volume_surge_ratio,
            "whale_net_ratio": indicator.whale_net_ratio,
            "retail_net_ratio": indicator.retail_net_ratio,
            "divergence_score": indicator.divergence_score,
        },
    )


def _confidence(reason_codes: list[str]) -> float:
    return min(0.55 + (0.09 * len(reason_codes)), 0.91)


def _panic_sell(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        indicator.price_change_pct <= -threshold.price_down_strong
        and indicator.volatility_pct >= threshold.volatility_high
        and indicator.whale_net_ratio <= -threshold.whale_net_negative
    ):
        reason_codes = ["price_down_strong", "volatility_high", "whale_sell"]
        if indicator.volume_surge_ratio >= threshold.volume_surge:
            reason_codes.append("volume_surge")
        return Persona.PANIC_SELL, reason_codes
    return None


def _distribution_trap(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        indicator.price_change_pct >= threshold.price_up
        and indicator.whale_net_ratio <= -threshold.whale_net_negative
        and indicator.retail_net_ratio >= threshold.retail_net_positive
        and indicator.divergence_score >= threshold.divergence
    ):
        return Persona.DISTRIBUTION_TRAP, [
            "price_up",
            "whale_distribution",
            "retail_buy",
            "divergence",
        ]
    return None


def _breakout(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        indicator.price_change_pct >= threshold.price_up_strong
        and indicator.volume_surge_ratio >= threshold.volume_surge
        and indicator.whale_net_ratio >= threshold.whale_net_positive
    ):
        reason_codes = ["price_breakout", "volume_surge", "whale_buy"]
        if indicator.volatility_pct >= threshold.volatility_mid:
            reason_codes.append("volatility_mid")
        return Persona.BREAKOUT, reason_codes
    return None


def _accumulation(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        indicator.whale_net_ratio >= threshold.whale_net_strong
        and abs(indicator.price_change_pct) <= threshold.price_flat
        and indicator.volatility_pct <= threshold.volatility_low
    ):
        reason_codes = ["whale_accumulation", "price_flat", "volatility_low"]
        if indicator.retail_net_ratio <= threshold.retail_net_weak:
            reason_codes.append("retail_weak")
        return Persona.ACCUMULATION, reason_codes
    return None


def _retail_chop(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        abs(indicator.price_change_pct) <= threshold.price_flat
        and indicator.volatility_pct >= threshold.volatility_mid
        and abs(indicator.whale_net_ratio) <= threshold.whale_net_weak
        and abs(indicator.retail_net_ratio) >= threshold.retail_net_active
    ):
        return Persona.RETAIL_CHOP, [
            "price_flat",
            "volatility_mid",
            "whale_weak",
            "retail_active",
        ]
    return None


def _sleep(
    indicator: IndicatorSnapshot, threshold: ThresholdConfig
) -> tuple[Persona, list[str]] | None:
    if (
        abs(indicator.price_change_pct) <= threshold.price_flat
        and indicator.volatility_pct <= threshold.volatility_low
        and indicator.volume_surge_ratio <= threshold.volume_quiet
        and abs(indicator.whale_net_ratio) <= threshold.whale_net_weak
        and abs(indicator.retail_net_ratio) <= threshold.retail_net_weak
    ):
        return Persona.SLEEP, [
            "price_flat",
            "volatility_low",
            "volume_quiet",
            "flows_weak",
        ]
    return None
