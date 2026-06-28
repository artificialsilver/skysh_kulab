from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants import ALERT_TIMEFRAME, MARKETS, TIMEFRAMES
from app.db import SessionLocal, get_session, init_db
from app.demo_data import seed_demo_data
from app.market_data import fetch_upbit_tickers
from app.models import MarketIndicatorSnapshot, MarketPersonaSnapshot
from app.schemas import AlertSettingIn, iso_z
from app.storage import (
    get_alert_setting,
    get_latest_persona_snapshot,
    list_indicator_snapshots,
    set_alert_setting,
)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    async with SessionLocal() as session:
        await seed_demo_data(session)
    yield


app = FastAPI(title="skysh storage API", lifespan=lifespan)


def require_market(market: str) -> str:
    if market not in MARKETS:
        raise HTTPException(status_code=404, detail="unsupported market")
    return market


def require_timeframe(timeframe: str) -> str:
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=422, detail="unsupported timeframe")
    return timeframe


def require_alert_timeframe(timeframe: str) -> str:
    if timeframe != ALERT_TIMEFRAME:
        raise HTTPException(status_code=422, detail="alert setting timeframe must be 15m")
    return timeframe


def indicator_to_response(snapshot: MarketIndicatorSnapshot) -> dict:
    return {
        "snapshot_at": iso_z(snapshot.snapshot_at),
        "window_start": iso_z(snapshot.window_start),
        "window_end": iso_z(snapshot.window_end),
        "price_open": snapshot.price_open,
        "price_high": snapshot.price_high,
        "price_low": snapshot.price_low,
        "price_close": snapshot.price_close,
        "price_change_pct": snapshot.price_change_pct,
        "volatility_pct": snapshot.volatility_pct,
        "total_volume_krw": snapshot.total_volume_krw,
        "volume_surge_ratio": snapshot.volume_surge_ratio,
        "whale_buy_krw": snapshot.whale_buy_krw,
        "whale_sell_krw": snapshot.whale_sell_krw,
        "retail_buy_krw": snapshot.retail_buy_krw,
        "retail_sell_krw": snapshot.retail_sell_krw,
        "whale_net_krw": snapshot.whale_net_krw,
        "retail_net_krw": snapshot.retail_net_krw,
        "whale_net_ratio": snapshot.whale_net_ratio,
        "retail_net_ratio": snapshot.retail_net_ratio,
        "divergence_score": snapshot.divergence_score,
        "trade_count": snapshot.trade_count,
        "whale_count": snapshot.whale_count,
        "retail_count": snapshot.retail_count,
        "metrics_json": snapshot.metrics_json,
    }


def persona_to_response(snapshot: MarketPersonaSnapshot) -> dict:
    return {
        "market": snapshot.market,
        "timeframe": snapshot.timeframe,
        "snapshot_at": iso_z(snapshot.snapshot_at),
        "persona": snapshot.persona,
        "confidence": snapshot.confidence,
        "reason_codes": snapshot.reason_codes,
        "metrics_json": snapshot.metrics_json,
    }


@app.get("/api/markets")
async def markets() -> dict[str, list[str]]:
    return {"markets": list(MARKETS)}


@app.get("/api/tickers")
async def tickers() -> dict:
    try:
        prices = fetch_upbit_tickers()
    except Exception as exc:
        raise HTTPException(status_code=503, detail="ticker source unavailable") from exc
    return {"tickers": {market: {"price": price} for market, price in prices.items()}}


@app.get("/api/market/{market}/snapshots")
async def snapshots(
    market: str,
    timeframe: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    market = require_market(market)
    timeframe = require_timeframe(timeframe)
    rows = await list_indicator_snapshots(session, market, timeframe)
    return {
        "market": market,
        "timeframe": timeframe,
        "snapshots": [indicator_to_response(row) for row in rows],
    }


@app.get("/api/market/{market}/persona")
async def persona(
    market: str,
    timeframe: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    market = require_market(market)
    timeframe = require_timeframe(timeframe)
    snapshot = await get_latest_persona_snapshot(session, market, timeframe)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="persona snapshot not found")
    return persona_to_response(snapshot)


@app.get("/api/market/{market}/alerts/settings")
async def read_alert_setting(
    market: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    market = require_market(market)
    setting = await get_alert_setting(session, market)
    return {"market": market, "timeframe": ALERT_TIMEFRAME, "enabled": setting.enabled}


@app.put("/api/market/{market}/alerts/settings")
async def write_alert_setting(
    market: str,
    payload: AlertSettingIn,
    session: AsyncSession = Depends(get_session),
) -> dict:
    market = require_market(market)
    timeframe = require_alert_timeframe(payload.timeframe)
    setting = await set_alert_setting(session, market, timeframe, payload.enabled)
    return {"market": market, "timeframe": setting.timeframe, "enabled": setting.enabled}
