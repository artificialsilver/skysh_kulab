from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MarketIndicatorSnapshot, MarketPersonaSnapshot
from app.schemas import IndicatorSnapshotIn, PersonaSnapshotIn
from app.storage import (
    get_latest_persona_snapshot,
    is_alert_enabled,
    set_alert_setting,
    upsert_indicator_snapshot,
    upsert_persona_snapshot,
)


SNAPSHOT_AT = datetime(2026, 6, 28, 5, 30, tzinfo=timezone.utc)


def fake_indicator(**overrides) -> IndicatorSnapshotIn:
    data = {
        "market": "KRW-BTC",
        "timeframe": "15m",
        "snapshot_at": SNAPSHOT_AT,
        "window_start": datetime(2026, 6, 28, 5, 15, tzinfo=timezone.utc),
        "window_end": SNAPSHOT_AT,
        "price_open": 97000000.0,
        "price_high": 99000000.0,
        "price_low": 96900000.0,
        "price_close": 98500000.0,
        "price_change_pct": 1.55,
        "volatility_pct": 2.1,
        "total_volume_krw": 7200000000.0,
        "volume_surge_ratio": 1.8,
        "whale_buy_krw": 2600000000.0,
        "whale_sell_krw": 1200000000.0,
        "retail_buy_krw": 2100000000.0,
        "retail_sell_krw": 1300000000.0,
        "whale_net_krw": 1400000000.0,
        "retail_net_krw": 800000000.0,
        "whale_net_ratio": 0.1944,
        "retail_net_ratio": 0.1111,
        "divergence_score": 0.0,
        "trade_count": 18420,
        "whale_count": 211,
        "retail_count": 18209,
        "metrics_json": {"threshold_version": "v1-temp"},
    }
    data.update(overrides)
    return IndicatorSnapshotIn(**data)


def fake_persona(**overrides) -> PersonaSnapshotIn:
    data = {
        "market": "KRW-BTC",
        "timeframe": "15m",
        "snapshot_at": SNAPSHOT_AT,
        "persona": "breakout",
        "confidence": 0.82,
        "reason_codes": ["volume_surge", "price_breakout", "whale_buy"],
        "metrics_json": {
            "price_change_pct": 1.55,
            "volume_surge_ratio": 1.8,
            "whale_net_ratio": 0.1944,
        },
    }
    data.update(overrides)
    return PersonaSnapshotIn(**data)


async def test_indicator_upsert_updates_existing_row(session: AsyncSession) -> None:
    await upsert_indicator_snapshot(session, fake_indicator(price_close=98500000.0))
    row = await upsert_indicator_snapshot(session, fake_indicator(price_close=99000000.0))

    result = await session.execute(select(MarketIndicatorSnapshot))
    rows = result.scalars().all()

    assert len(rows) == 1
    assert row.price_close == 99000000.0


async def test_timeframes_are_stored_independently(session: AsyncSession) -> None:
    await upsert_indicator_snapshot(session, fake_indicator(timeframe="15m"))
    await upsert_indicator_snapshot(session, fake_indicator(timeframe="4h"))

    result = await session.execute(select(MarketIndicatorSnapshot))

    assert len(result.scalars().all()) == 2


async def test_persona_upsert_and_latest(session: AsyncSession) -> None:
    await upsert_persona_snapshot(session, fake_persona(persona="breakout"))
    await upsert_persona_snapshot(session, fake_persona(persona="accumulation", confidence=0.7))

    latest = await get_latest_persona_snapshot(session, "KRW-BTC", "15m")
    result = await session.execute(select(MarketPersonaSnapshot))

    assert len(result.scalars().all()) == 1
    assert latest is not None
    assert latest.persona == "accumulation"
    assert latest.confidence == 0.7


async def test_markets_endpoint(client) -> None:
    response = await client.get("/api/markets")

    assert response.status_code == 200
    assert response.json() == {"markets": ["KRW-BTC", "KRW-ETH", "KRW-XRP"]}


async def test_snapshots_response_shape(client, session: AsyncSession) -> None:
    await upsert_indicator_snapshot(session, fake_indicator())

    response = await client.get("/api/market/KRW-BTC/snapshots?timeframe=15m")
    body = response.json()

    assert response.status_code == 200
    assert body["market"] == "KRW-BTC"
    assert body["timeframe"] == "15m"
    assert body["snapshots"][0]["snapshot_at"] == "2026-06-28T05:30:00Z"
    assert "persona" not in body["snapshots"][0]
    assert body["snapshots"][0]["metrics_json"] == {"threshold_version": "v1-temp"}


async def test_persona_response_shape(client, session: AsyncSession) -> None:
    await upsert_persona_snapshot(session, fake_persona())

    response = await client.get("/api/market/KRW-BTC/persona?timeframe=15m")
    body = response.json()

    assert response.status_code == 200
    assert body["market"] == "KRW-BTC"
    assert body["timeframe"] == "15m"
    assert body["snapshot_at"] == "2026-06-28T05:30:00Z"
    assert body["persona"] == "breakout"
    assert body["reason_codes"] == ["volume_surge", "price_breakout", "whale_buy"]


async def test_market_and_timeframe_validation(client) -> None:
    bad_market = await client.get("/api/market/KRW-DOGE/snapshots?timeframe=15m")
    bad_timeframe = await client.get("/api/market/KRW-BTC/snapshots?timeframe=1h")

    assert bad_market.status_code == 404
    assert bad_timeframe.status_code == 422


async def test_alert_setting_on_off(client, session: AsyncSession) -> None:
    default_response = await client.get("/api/market/KRW-BTC/alerts/settings")
    enabled_response = await client.put(
        "/api/market/KRW-BTC/alerts/settings",
        json={"timeframe": "15m", "enabled": True},
    )
    disabled_response = await client.put(
        "/api/market/KRW-BTC/alerts/settings",
        json={"timeframe": "15m", "enabled": False},
    )

    assert default_response.json() == {"market": "KRW-BTC", "timeframe": "15m", "enabled": False}
    assert enabled_response.json() == {"market": "KRW-BTC", "timeframe": "15m", "enabled": True}
    assert await is_alert_enabled(session, "KRW-BTC", "15m") is False
    assert disabled_response.json() == {"market": "KRW-BTC", "timeframe": "15m", "enabled": False}


async def test_alert_setting_only_allows_15m(client, session: AsyncSession) -> None:
    response = await client.put(
        "/api/market/KRW-BTC/alerts/settings",
        json={"timeframe": "4h", "enabled": True},
    )
    await set_alert_setting(session, "KRW-BTC", "15m", True)

    assert response.status_code == 422
    assert await is_alert_enabled(session, "KRW-BTC", "4h") is False
