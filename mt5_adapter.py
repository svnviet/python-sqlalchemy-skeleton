import os, sys, platform
from pathlib import Path
from typing import Optional, List, Dict, Any
import MetaTrader5 as mt5
from util import label_retcode  # if split; here we already imported above

from dtos import AccountDTO, SymbolInfoDTO, TickDTO, OrderRequestDTO, OrderResultDTO, TradeSide, OrderKind, PositionDTO, \
    PendingOrderDTO
from errors import TradingError, SymbolNotAvailable


# Reuse DTOs & utils from the faux modules above (same file here)
# from trading.dtos import *
# from trading.util import label_retcode, RETCODES
# from trading.errors import SymbolNotAvailable

def _clean_path(p: str | None) -> Optional[Path]:
    if not p:
        return None
    p = p.strip().strip('"').strip("'")
    path = Path(p).expanduser()
    if path.is_dir():
        path = path / "terminal64.exe"
    return path


class MT5Gateway:
    """Concrete TradingGateway implementation for MetaTrader 5."""

    def __init__(self) -> None:
        self._initialized = False

    # --- lifecycle ---
    def initialize(self, *, login: int | None = None, password: str | None = None,
                   server: str | None = None, path: str | None = None) -> None:
        if platform.architecture()[0] != "64bit":
            raise TradingError("Use 64-bit Python with MT5.")

        # Try attach first
        if not mt5.initialize():
            # try explicit path
            exe = _clean_path(path or os.getenv("MT5_PATH"))
            if not exe or not exe.exists():
                err = mt5.last_error()
                raise TradingError(f"MT5 initialize failed and no valid path provided. last_error={err}")
            try:
                os.add_dll_directory(str(exe.parent))
            except Exception:
                pass
            if not mt5.initialize(path=str(exe)):
                raise TradingError(f"MT5 initialize(path=...) failed: {mt5.last_error()}")
        # optional login
        if login and password and server:
            if not mt5.login(int(login), password=password, server=server):
                raise TradingError(f"MT5 login failed: {mt5.last_error()}")
        self._initialized = True

    def shutdown(self) -> None:
        if self._initialized:
            mt5.shutdown()
            self._initialized = False

    # --- info ---
    def account_info(self) -> AccountDTO:
        ai = mt5.account_info()
        if not ai:
            raise TradingError("No MT5 account connected.")
        return AccountDTO(
            login=ai.login, name=ai.name, server=ai.server, currency=ai.currency,
            equity=ai.equity, balance=ai.balance, margin_free=ai.margin_free,
            leverage=ai.leverage, trade_allowed=ai.trade_allowed,
        )

    def ensure_symbol(self, symbol: str) -> SymbolInfoDTO:
        mt5.symbol_select(symbol, True)
        si = mt5.symbol_info(symbol)
        if si is None:
            raise SymbolNotAvailable(f"{symbol} not enabled on this account/server")
        return SymbolInfoDTO(
            name=si.name, digits=si.digits, point=si.point,
            volume_min=si.volume_min, volume_step=si.volume_step, volume_max=si.volume_max,
            trade_mode=si.trade_mode, filling_mode=si.filling_mode, stops_level=si.trade_stops_level
        )

    def tick(self, symbol: str) -> TickDTO:
        self.ensure_symbol(symbol)
        t = mt5.symbol_info_tick(symbol)
        if not t:
            raise TradingError(f"No tick for {symbol}")
        return TickDTO(time=t.time, bid=t.bid, ask=t.ask, last=t.last)

    # --- trading core ---
    def market_order(self, req: OrderRequestDTO) -> OrderResultDTO:
        si = self.ensure_symbol(req.symbol)
        t = mt5.symbol_info_tick(req.symbol)
        if not t:
            raise TradingError(f"No tick for {req.symbol}")
        price = t.ask if req.side == TradeSide.BUY else t.bid

        # support sl_dist/tp_dist convenience
        sl, tp = req.sl, req.tp
        if req.sl_dist is not None:
            sl = round(price - req.sl_dist if req.side == TradeSide.BUY else price + req.sl_dist, si.digits)
        if req.tp_dist is not None:
            tp = round(price + req.tp_dist if req.side == TradeSide.BUY else price - req.tp_dist, si.digits)

        fill = si.filling_mode if si.filling_mode in (
            getattr(mt5, "ORDER_FILLING_FOK", 0), getattr(mt5, "ORDER_FILLING_IOC", 1),
            getattr(mt5, "ORDER_FILLING_RETURN", 2)
        ) else getattr(mt5, "ORDER_FILLING_IOC", 1)

        request = dict(
            action=mt5.TRADE_ACTION_DEAL,
            symbol=req.symbol,
            type=mt5.ORDER_TYPE_BUY if req.side == TradeSide.BUY else mt5.ORDER_TYPE_SELL,
            volume=float(req.volume),
            price=price,
            sl=sl or 0.0,
            tp=tp or 0.0,
            deviation=req.deviation,
            type_time=mt5.ORDER_TIME_GTC,
            type_filling=fill,
            comment=req.comment,
        )
        res = mt5.order_send(request)
        return self._fmt_res(res)

    def pending_order(self, req: OrderRequestDTO) -> OrderResultDTO:
        si = self.ensure_symbol(req.symbol)
        kind_map = {
            OrderKind.BUY_LIMIT: mt5.ORDER_TYPE_BUY_LIMIT,
            OrderKind.SELL_LIMIT: mt5.ORDER_TYPE_SELL_LIMIT,
            OrderKind.BUY_STOP: mt5.ORDER_TYPE_BUY_STOP,
            OrderKind.SELL_STOP: mt5.ORDER_TYPE_SELL_STOP,
            OrderKind.BUY_STOP_LIMIT: mt5.ORDER_TYPE_BUY_STOP_LIMIT,
            OrderKind.SELL_STOP_LIMIT: mt5.ORDER_TYPE_SELL_STOP_LIMIT,
        }
        if req.kind == OrderKind.MARKET:
            raise TradingError("Use market_order() for OrderKind.MARKET")
        if req.price is None:
            raise TradingError("Pending order requires 'price'")

        fill = getattr(mt5, "ORDER_FILLING_RETURN", 2)
        request = dict(
            action=mt5.TRADE_ACTION_PENDING,
            symbol=req.symbol,
            type=kind_map[req.kind],
            volume=float(req.volume),
            price=req.price,
            stoplimit=req.stoplimit_price or 0.0,
            sl=req.sl or 0.0,
            tp=req.tp or 0.0,
            deviation=req.deviation,
            type_time=mt5.ORDER_TIME_GTC,
            type_filling=fill,
            expiration=0,
            comment=req.comment,
        )
        res = mt5.order_send(request)
        return self._fmt_res(res)

    def positions(self, symbol: str | None = None) -> list[PositionDTO]:
        ps = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
        out: list[PositionDTO] = []
        for p in ps or []:
            side = TradeSide.BUY if p.type == mt5.POSITION_TYPE_BUY else TradeSide.SELL
            out.append(PositionDTO(
                ticket=p.ticket, symbol=p.symbol, side=side,
                volume=p.volume, price_open=p.price_open, sl=p.sl, tp=p.tp, profit=p.profit
            ))
        return out

    def orders(self, symbol: str | None = None) -> list[PendingOrderDTO]:
        os_ = mt5.orders_get(symbol=symbol) if symbol else mt5.orders_get()
        kind_rev = {
            mt5.ORDER_TYPE_BUY_LIMIT: OrderKind.BUY_LIMIT,
            mt5.ORDER_TYPE_SELL_LIMIT: OrderKind.SELL_LIMIT,
            mt5.ORDER_TYPE_BUY_STOP: OrderKind.BUY_STOP,
            mt5.ORDER_TYPE_SELL_STOP: OrderKind.SELL_STOP,
            mt5.ORDER_TYPE_BUY_STOP_LIMIT: OrderKind.BUY_STOP_LIMIT,
            mt5.ORDER_TYPE_SELL_STOP_LIMIT: OrderKind.SELL_STOP_LIMIT,
        }
        out: list[PendingOrderDTO] = []
        for o in os_ or []:
            out.append(PendingOrderDTO(
                ticket=o.ticket, symbol=o.symbol, kind=kind_rev.get(o.type, OrderKind.MARKET),
                volume=o.volume_current, price=o.price_open, sl=o.sl, tp=o.tp
            ))
        return out

    def modify_position_sltp(self, position_ticket: int, *, sl: float, tp: float) -> OrderResultDTO:
        # Need the symbol to send SLTP
        pos = next((p for p in mt5.positions_get() or [] if p.ticket == position_ticket), None)
        if not pos:
            raise TradingError(f"Position {position_ticket} not found")
        req = dict(action=mt5.TRADE_ACTION_SLTP, position=position_ticket, symbol=pos.symbol, sl=sl, tp=tp,
                   comment="py-modify")
        res = mt5.order_send(req)
        return self._fmt_res(res)

    def close_position(self, position_ticket: int, deviation: int = 120) -> OrderResultDTO:
        pos = next((p for p in mt5.positions_get() or [] if p.ticket == position_ticket), None)
        if not pos:
            raise TradingError(f"Position {position_ticket} not found")
        is_buy = pos.type == mt5.POSITION_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if is_buy else tick.ask
        req = dict(
            action=mt5.TRADE_ACTION_DEAL, symbol=pos.symbol,
            volume=pos.volume, type=mt5.ORDER_TYPE_SELL if is_buy else mt5.ORDER_TYPE_BUY,
            position=position_ticket, price=price, deviation=deviation,
            type_time=mt5.ORDER_TIME_GTC, type_filling=getattr(mt5, "ORDER_FILLING_IOC", 1),
            comment="py-close",
        )
        res = mt5.order_send(req)
        return self._fmt_res(res)

    def cancel_order(self, order_ticket: int) -> OrderResultDTO:
        o = next((o for o in mt5.orders_get() or [] if o.ticket == order_ticket), None)
        if not o:
            raise TradingError(f"Order {order_ticket} not found")
        req = dict(action=mt5.TRADE_ACTION_REMOVE, order=order_ticket, symbol=o.symbol, comment="py-cancel")
        res = mt5.order_send(req)
        return self._fmt_res(res)

    # --- internal ---
    def _fmt_res(self, res) -> OrderResultDTO:
        if res is None:
            return OrderResultDTO(
                retcode=-1, label="NO_RESULT", comment="", order=None, deal=None, price=None,
                request_id=None, last_error=mt5.last_error(), raw={}
            )
        return OrderResultDTO(
            retcode=res.retcode,
            label=label_retcode(res.retcode),
            comment=getattr(res, "comment", ""),
            order=getattr(res, "order", None),
            deal=getattr(res, "deal", None),
            price=getattr(res, "price", None),
            request_id=getattr(res, "request_id", None),
            last_error=mt5.last_error(),
            raw=getattr(res, "_asdict", lambda: {})(),
        )
