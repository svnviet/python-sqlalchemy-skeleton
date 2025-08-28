# db_models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, BigInteger, Integer, Float, Index, UniqueConstraint, TIMESTAMP, text


class Base(DeclarativeBase): pass


@dataclass
class OrderRow(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    broker_order: Mapped[Optional[int]] = mapped_column(BigInteger, unique=True)
    broker_deal: Mapped[Optional[int]] = mapped_column(BigInteger)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    requested_price: Mapped[Optional[float]] = mapped_column(Float)
    filled_price: Mapped[Optional[float]] = mapped_column(Float)
    sl: Mapped[Optional[float]] = mapped_column(Float)
    tp: Mapped[Optional[float]] = mapped_column(Float)
    retcode: Mapped[Optional[int]] = mapped_column(Integer)
    retcode_label: Mapped[Optional[str]] = mapped_column(String)
    ret_comment: Mapped[Optional[str]] = mapped_column(String)
    request_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))


Index("ix_orders_symbol_created_at", OrderRow.symbol, OrderRow.created_at)


@dataclass
class DealRow(Base):
    __tablename__ = "deals"
    id: Mapped[int] = mapped_column(primary_key=True)
    deal_ticket: Mapped[int] = mapped_column(BigInteger, unique=True)
    order_ticket: Mapped[Optional[int]] = mapped_column(BigInteger)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    profit: Mapped[Optional[float]] = mapped_column(Float)
    commission: Mapped[Optional[float]] = mapped_column(Float)
    swap: Mapped[Optional[float]] = mapped_column(Float)
    time: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)


@dataclass
class PositionSnapRow(Base):
    __tablename__ = "positions_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    ticket: Mapped[int] = mapped_column(BigInteger, nullable=False)
    side: Mapped[str] = mapped_column(String, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    price_open: Mapped[float] = mapped_column(Float, nullable=False)
    sl: Mapped[Optional[float]] = mapped_column(Float)
    tp: Mapped[Optional[float]] = mapped_column(Float)
    profit: Mapped[Optional[float]] = mapped_column(Float)
    snapped_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=text("now()"))


Index("ix_possnaps_symbol_time", PositionSnapRow.symbol, PositionSnapRow.snapped_at)
