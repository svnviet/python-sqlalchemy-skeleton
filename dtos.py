from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any


class TradeSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderKind(str, Enum):
    MARKET = "market"
    BUY_LIMIT = "buy_limit"
    SELL_LIMIT = "sell_limit"
    BUY_STOP = "buy_stop"
    SELL_STOP = "sell_stop"
    BUY_STOP_LIMIT = "buy_stop_limit"
    SELL_STOP_LIMIT = "sell_stop_limit"


@dataclass(frozen=True)
class AccountDTO:
    login: int
    name: str
    server: str
    currency: str
    equity: float
    balance: float
    margin_free: float
    leverage: int
    trade_allowed: bool


@dataclass(frozen=True)
class SymbolInfoDTO:
    name: str
    digits: int
    point: float
    volume_min: float
    volume_step: float
    volume_max: float
    trade_mode: int
    filling_mode: int
    stops_level: int


@dataclass(frozen=True)
class TickDTO:
    time: int
    bid: float
    ask: float
    last: float


@dataclass(frozen=True)
class OrderRequestDTO:
    symbol: str
    side: TradeSide
    volume: float
    kind: OrderKind = OrderKind.MARKET
    price: Optional[float] = None  # required for pending orders
    stoplimit_price: Optional[float] = None  # for stop-limit
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: int = 120
    comment: str = "py-trade"
    # As distances (price units) for convenience in services
    sl_dist: Optional[float] = None
    tp_dist: Optional[float] = None


@dataclass(frozen=True)
class OrderResultDTO:
    retcode: int
    label: str
    comment: str
    order: Optional[int]
    deal: Optional[int]
    price: Optional[float]
    request_id: Optional[int]
    last_error: Any = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PositionDTO:
    ticket: int
    symbol: str
    side: TradeSide
    volume: float
    price_open: float
    sl: float
    tp: float
    profit: float


@dataclass(frozen=True)
class PendingOrderDTO:
    ticket: int
    symbol: str
    kind: OrderKind
    volume: float
    price: float
    sl: float
    tp: float
