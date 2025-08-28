from app.db_models import DealRow, OrderRow, PositionSnapRow
from app.dtos import (OrderKind, OrderRequestDTO, OrderResultDTO,
                      PendingOrderDTO, PositionDTO, TradeSide)
from app.interfaces import TradingGateway
from config.db import session_scope


class TradingService:
    """High-level use-cases built on the TradingGateway with DB persistence."""

    def __init__(self, gw: TradingGateway) -> None:
        self.gw = gw

    # --- Basic buy/sell ---
    def buy(
        self,
        symbol: str,
        volume: float,
        *,
        sl_dist: float | None = None,
        tp_dist: float | None = None,
        deviation: int = 120,
        comment: str = "py-buy",
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
        res = self.gw.market_order(req)
        self._record_order(req, res)
        return res

    def sell(
        self,
        symbol: str,
        volume: float,
        *,
        sl_dist: float | None = None,
        tp_dist: float | None = None,
        deviation: int = 120,
        comment: str = "py-sell",
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
        res = self.gw.market_order(req)
        self._record_order(req, res)
        return res

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
        comment: str = "py-pending",
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
        res = self.gw.pending_order(req)
        self._record_order(req, res)
        return res

    # --- SL/TP updates & closing ---
    def modify_sltp(
        self, position_ticket: int, *, sl: float, tp: float
    ) -> OrderResultDTO:
        res = self.gw.modify_position_sltp(position_ticket, sl=sl, tp=tp)
        self._record_order_change(position_ticket, res)
        return res

    def close(self, position_ticket: int, *, deviation: int = 120) -> OrderResultDTO:
        res = self.gw.close_position(position_ticket, deviation=deviation)
        self._record_order_change(position_ticket, res)
        return res

    def close_all(self, symbol: str, *, deviation: int = 120) -> list[OrderResultDTO]:
        out: list[OrderResultDTO] = []
        for p in self.gw.positions(symbol):
            res = self.gw.close_position(p.ticket, deviation=deviation)
            self._record_order_change(p.ticket, res)
            out.append(res)
        return out

    # --- Queries ---
    def status(self) -> dict:
        return {"account": self.gw.account_info()}

    def positions(self, symbol: str | None = None) -> list[PositionDTO]:
        ps = self.gw.positions(symbol)
        self._record_positions(ps)
        return ps

    def orders(self, symbol: str | None = None) -> list[PendingOrderDTO]:
        return self.gw.orders(symbol)

    # --- Persistence helpers ---
    def _record_order(self, req: OrderRequestDTO, res: OrderResultDTO) -> None:
        """Persist an order request & result into orders table."""
        with session_scope() as session:
            row = OrderRow(
                broker_order=res.order,
                broker_deal=res.deal,
                symbol=req.symbol,
                side=req.side.value,
                kind=req.kind.value,
                volume=req.volume,
                requested_price=req.price,
                filled_price=res.price,
                sl=req.sl,
                tp=req.tp,
                retcode=res.retcode,
                retcode_label=res.label,
                ret_comment=res.comment,
                request_id=res.request_id,
            )
            session.add(row)

            # Optional: if deal exists, record into deals table
            if res.deal:
                deal_row = DealRow(
                    deal_ticket=res.deal,
                    order_ticket=res.order,
                    symbol=req.symbol,
                    side=req.side.value,
                    volume=req.volume,
                    price=res.price or 0.0,
                    profit=None,  # can update later via history_deals_get
                    commission=None,
                    swap=None,
                    time=row.created_at,
                )
                session.add(deal_row)

    def _record_order_change(self, ticket: int, res: OrderResultDTO) -> None:
        """Log order modifications (close/modify SLTP)."""
        with session_scope() as session:
            # Just append as an OrderRow with same ticket reference
            row = OrderRow(
                broker_order=res.order or ticket,
                broker_deal=res.deal,
                symbol="",
                side="",  # unknown unless fetched from MT5
                kind="MODIFY",
                volume=0.0,
                requested_price=None,
                filled_price=res.price,
                sl=None,
                tp=None,
                retcode=res.retcode,
                retcode_label=res.label,
                ret_comment=res.comment,
                request_id=res.request_id,
            )
            session.add(row)

    def _record_positions(self, positions: list[PositionDTO]) -> None:
        """Snapshot open positions into positions_snapshots table."""
        with session_scope() as session:
            for p in positions:
                snap = PositionSnapRow(
                    symbol=p.symbol,
                    ticket=p.ticket,
                    side=p.side.value,
                    volume=p.volume,
                    price_open=p.price_open,
                    sl=p.sl,
                    tp=p.tp,
                    profit=p.profit,
                )
                session.add(snap)
