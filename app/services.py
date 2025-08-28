from dtos import (
    OrderKind,
    OrderRequestDTO,
    OrderResultDTO,
    PendingOrderDTO,
    PositionDTO,
    TradeSide,
)
from interfaces import TradingGateway


class TradingService:
    """High-level use-cases built on the TradingGateway."""

    def __init__(self, gw: TradingGateway) -> None:
        self.gw = gw

    # --- Basic buy/sell with SL/TP *distance* in price units ---
    def buy(
        self,
        symbol: str,
        volume: float,
        *,
        sl_dist: float | None = None,
        tp_dist: float | None = None,
        deviation: int = 120,
        comment: str = "py-buy"
    ) -> OrderResultDTO:
        req = OrderRequestDTO(
            symbol=symbol,
            side=TradeSide.BUY,
            volume=volume,
            kind=OrderKind.MARKET,
            sl_dist=sl_dist,
            tp_dist=tp_dist,
            deviation=deviation,
            comment=comment,
        )
        return self.gw.market_order(req)

    def sell(
        self,
        symbol: str,
        volume: float,
        *,
        sl_dist: float | None = None,
        tp_dist: float | None = None,
        deviation: int = 120,
        comment: str = "py-sell"
    ) -> OrderResultDTO:
        req = OrderRequestDTO(
            symbol=symbol,
            side=TradeSide.SELL,
            volume=volume,
            kind=OrderKind.MARKET,
            sl_dist=sl_dist,
            tp_dist=tp_dist,
            deviation=deviation,
            comment=comment,
        )
        return self.gw.market_order(req)

    # --- Pending orders ---
    def place_pending(
        self,
        symbol: str,
        side: TradeSide,
        kind: OrderKind,
        price: float,
        volume: float,
        *,
        sl: float = 0.0,
        tp: float = 0.0,
        stoplimit_price: float | None = None,
        deviation: int = 120,
        comment: str = "py-pending"
    ) -> OrderResultDTO:
        req = OrderRequestDTO(
            symbol=symbol,
            side=side,
            volume=volume,
            kind=kind,
            price=price,
            stoplimit_price=stoplimit_price,
            sl=sl,
            tp=tp,
            deviation=deviation,
            comment=comment,
        )
        return self.gw.pending_order(req)

    # --- SL/TP updates & closing ---
    def modify_sltp(
        self, position_ticket: int, *, sl: float, tp: float
    ) -> OrderResultDTO:
        return self.gw.modify_position_sltp(position_ticket, sl=sl, tp=tp)

    def close(self, position_ticket: int, *, deviation: int = 120) -> OrderResultDTO:
        return self.gw.close_position(position_ticket, deviation=deviation)

    def close_all(self, symbol: str, *, deviation: int = 120) -> list[OrderResultDTO]:
        out: list[OrderResultDTO] = []
        for p in self.gw.positions(symbol):
            out.append(self.gw.close_position(p.ticket, deviation=deviation))
        return out

    # --- Queries ---
    def status(self) -> dict:
        return {"account": self.gw.account_info()}

    def positions(self, symbol: str | None = None) -> list[PositionDTO]:
        return self.gw.positions(symbol)

    def orders(self, symbol: str | None = None) -> list[PendingOrderDTO]:
        return self.gw.orders(symbol)
