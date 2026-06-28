from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ALERT_TIMEFRAME
from app.models import MarketAlertSetting, MarketIndicatorSnapshot, MarketPersonaSnapshot
from app.schemas import IndicatorSnapshotIn, PersonaSnapshotIn


INDICATOR_UPSERT_FIELDS = (
    "window_start",
    "window_end",
    "price_open",
    "price_high",
    "price_low",
    "price_close",
    "price_change_pct",
    "volatility_pct",
    "total_volume_krw",
    "volume_surge_ratio",
    "whale_buy_krw",
    "whale_sell_krw",
    "retail_buy_krw",
    "retail_sell_krw",
    "whale_net_krw",
    "retail_net_krw",
    "whale_net_ratio",
    "retail_net_ratio",
    "divergence_score",
    "trade_count",
    "whale_count",
    "retail_count",
    "metrics_json",
)

PERSONA_UPSERT_FIELDS = ("persona", "confidence", "reason_codes", "metrics_json")


async def upsert_indicator_snapshot(
    session: AsyncSession, snapshot: IndicatorSnapshotIn
) -> MarketIndicatorSnapshot:
    values = snapshot.model_dump()
    stmt = insert(MarketIndicatorSnapshot).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["market", "timeframe", "snapshot_at"],
        set_={field: getattr(stmt.excluded, field) for field in INDICATOR_UPSERT_FIELDS}
        | {"updated_at": datetime.utcnow()},
    )
    await session.execute(stmt)
    await session.commit()
    return await get_indicator_snapshot(session, snapshot.market, snapshot.timeframe, snapshot.snapshot_at)


async def upsert_persona_snapshot(
    session: AsyncSession, snapshot: PersonaSnapshotIn
) -> MarketPersonaSnapshot:
    values = snapshot.model_dump()
    stmt = insert(MarketPersonaSnapshot).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["market", "timeframe", "snapshot_at"],
        set_={field: getattr(stmt.excluded, field) for field in PERSONA_UPSERT_FIELDS}
        | {"updated_at": datetime.utcnow()},
    )
    await session.execute(stmt)
    await session.commit()
    return await get_persona_snapshot(session, snapshot.market, snapshot.timeframe, snapshot.snapshot_at)


async def get_indicator_snapshot(
    session: AsyncSession, market: str, timeframe: str, snapshot_at: datetime
) -> MarketIndicatorSnapshot:
    result = await session.execute(
        select(MarketIndicatorSnapshot).where(
            MarketIndicatorSnapshot.market == market,
            MarketIndicatorSnapshot.timeframe == timeframe,
            MarketIndicatorSnapshot.snapshot_at == snapshot_at,
        )
    )
    snapshot = result.scalar_one()
    return snapshot


async def get_persona_snapshot(
    session: AsyncSession, market: str, timeframe: str, snapshot_at: datetime
) -> MarketPersonaSnapshot:
    result = await session.execute(
        select(MarketPersonaSnapshot).where(
            MarketPersonaSnapshot.market == market,
            MarketPersonaSnapshot.timeframe == timeframe,
            MarketPersonaSnapshot.snapshot_at == snapshot_at,
        )
    )
    snapshot = result.scalar_one()
    return snapshot


async def list_indicator_snapshots(
    session: AsyncSession, market: str, timeframe: str, limit: int = 100
) -> list[MarketIndicatorSnapshot]:
    result = await session.execute(
        select(MarketIndicatorSnapshot)
        .where(
            MarketIndicatorSnapshot.market == market,
            MarketIndicatorSnapshot.timeframe == timeframe,
        )
        .order_by(MarketIndicatorSnapshot.snapshot_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_latest_persona_snapshot(
    session: AsyncSession, market: str, timeframe: str
) -> MarketPersonaSnapshot | None:
    result = await session.execute(
        select(MarketPersonaSnapshot)
        .where(
            MarketPersonaSnapshot.market == market,
            MarketPersonaSnapshot.timeframe == timeframe,
        )
        .order_by(MarketPersonaSnapshot.snapshot_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def set_alert_setting(
    session: AsyncSession, market: str, timeframe: str, enabled: bool
) -> MarketAlertSetting:
    stmt = insert(MarketAlertSetting).values(market=market, timeframe=timeframe, enabled=enabled)
    stmt = stmt.on_conflict_do_update(
        index_elements=["market", "timeframe"],
        set_={"enabled": stmt.excluded.enabled, "updated_at": datetime.utcnow()},
    )
    await session.execute(stmt)
    await session.commit()
    return await get_alert_setting(session, market)


async def get_alert_setting(session: AsyncSession, market: str) -> MarketAlertSetting:
    result = await session.execute(
        select(MarketAlertSetting).where(
            MarketAlertSetting.market == market,
            MarketAlertSetting.timeframe == ALERT_TIMEFRAME,
        )
    )
    setting = result.scalar_one_or_none()
    if setting is not None:
        return setting
    return MarketAlertSetting(market=market, timeframe=ALERT_TIMEFRAME, enabled=False)


async def is_alert_enabled(session: AsyncSession, market: str, timeframe: str) -> bool:
    if timeframe != ALERT_TIMEFRAME:
        return False
    setting = await get_alert_setting(session, market)
    return setting.enabled


async def count_rows(session: AsyncSession, statement: Select[Any]) -> int:
    result = await session.execute(select(func.count()).select_from(statement.subquery()))
    return result.scalar_one()

