from app.db_models import DealRow, OrderRow, PositionSnapRow
from app.dtos import (OrderKind, OrderRequestDTO, OrderResultDTO,
                      PendingOrderDTO, PositionDTO, TradeSide)
from app.interfaces import TradingGateway
from typing import Optional, List

from app.services.base import BaseService


class TradingService:
    """High-level use-cases built on the TradingGateway with DB persistence."""

    def __init__(self, gw: TradingGateway) -> None:
        self.gw = gw
        # Repos
        self.orders_repo = BaseService(OrderRow)
        self.deals_repo = BaseService(DealRow)
        self.positions_repo = BaseService(PositionSnapRow)

    # --- Basic buy/sell ---
    def buy(self, symbol: str, volume: float, *,
            sl_dist: float | None = None,
            tp_dist: float | None = None,
            deviation: int = 120,
            comment: str = "py-buy") -> OrderResultDTO:
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

    def sell(self, symbol: str, volume: float, *,
             sl_dist: float | None = None,
             tp_dist: float | None = None,
             deviation: int = 120,
             comment: str = "py-sell") -> OrderResultDTO:
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
    def place_pending(self, symbol: str, side: TradeSide, kind: OrderKind,
                      price: float, volume: float, *,
                      sl: float = 0.0, tp: float = 0.0,
                      stoplimit_price: float | None = None,
                      deviation: int = 120,
                      comment: str = "py-pending") -> OrderResultDTO:
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
    def modify_sltp(self, position_ticket: int, *, sl: float, tp: float) -> OrderResultDTO:
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

    # --- Live Queries ---
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
        """Persist an order request & result into orders/deals table."""
        order_data = dict(
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
        self.orders_repo.create(**order_data)

        if res.deal:
            deal_data = dict(
                deal_ticket=res.deal,
                order_ticket=res.order,
                symbol=req.symbol,
                side=req.side.value,
                volume=req.volume,
                price=res.price or 0.0,
                profit=None,
                commission=None,
                swap=None,
                time=None,  # DB default "now()"
            )
            self.deals_repo.create(**deal_data)

    def _record_order_change(self, ticket: int, res: OrderResultDTO) -> None:
        order_data = dict(
            broker_order=res.order or ticket,
            broker_deal=res.deal,
            symbol="",
            side="",
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
        self.orders_repo.create(**order_data)

    def _record_positions(self, positions: list[PositionDTO]) -> None:
        for p in positions:
            snap_data = dict(
                symbol=p.symbol,
                ticket=p.ticket,
                side=p.side.value,
                volume=p.volume,
                price_open=p.price_open,
                sl=p.sl,
                tp=p.tp,
                profit=p.profit,
            )
            self.positions_repo.create(**snap_data)

    # --- Query Helpers (DB history) ---
    def list_orders(self, limit: int = 100) -> List[OrderRow]:
        return self.orders_repo.list(limit)

    def get_order(self, order_id: int) -> Optional[OrderRow]:
        return self.orders_repo.get(order_id)

    def list_deals(self, limit: int = 100) -> List[DealRow]:
        return self.deals_repo.list(limit)

    def get_deal(self, deal_id: int) -> Optional[DealRow]:
        return self.deals_repo.get(deal_id)

    def list_positions_snap(self, limit: int = 100) -> List[PositionSnapRow]:
        return self.positions_repo.list(limit)

    def get_position_snap(self, snap_id: int) -> Optional[PositionSnapRow]:
        return self.positions_repo.get(snap_id)
