from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class MarketIndicatorSnapshot(TimestampMixin, Base):
    __tablename__ = "market_indicator_snapshots"
    __table_args__ = (
        UniqueConstraint("market", "timeframe", "snapshot_at", name="uq_indicator_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price_open: Mapped[float] = mapped_column(Float, nullable=False)
    price_high: Mapped[float] = mapped_column(Float, nullable=False)
    price_low: Mapped[float] = mapped_column(Float, nullable=False)
    price_close: Mapped[float] = mapped_column(Float, nullable=False)
    price_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_pct: Mapped[float] = mapped_column(Float, nullable=False)
    total_volume_krw: Mapped[float] = mapped_column(Float, nullable=False)
    volume_surge_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    whale_buy_krw: Mapped[float] = mapped_column(Float, nullable=False)
    whale_sell_krw: Mapped[float] = mapped_column(Float, nullable=False)
    retail_buy_krw: Mapped[float] = mapped_column(Float, nullable=False)
    retail_sell_krw: Mapped[float] = mapped_column(Float, nullable=False)
    whale_net_krw: Mapped[float] = mapped_column(Float, nullable=False)
    retail_net_krw: Mapped[float] = mapped_column(Float, nullable=False)
    whale_net_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    retail_net_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    divergence_score: Mapped[float] = mapped_column(Float, nullable=False)
    trade_count: Mapped[int] = mapped_column(Integer, nullable=False)
    whale_count: Mapped[int] = mapped_column(Integer, nullable=False)
    retail_count: Mapped[int] = mapped_column(Integer, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class MarketPersonaSnapshot(TimestampMixin, Base):
    __tablename__ = "market_persona_snapshots"
    __table_args__ = (
        UniqueConstraint("market", "timeframe", "snapshot_at", name="uq_persona_snapshot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class MarketAlertSetting(TimestampMixin, Base):
    __tablename__ = "market_alert_settings"
    __table_args__ = (
        UniqueConstraint("market", "timeframe", name="uq_alert_setting"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

