from mt5_adapter import MT5Gateway
from services import TradingService

if __name__ == "__main__":
    # Minimal demo usage
    gw = MT5Gateway()
    gw.initialize(  # attach to running MT5, or set MT5_PATH env / pass path=...
        # login=..., password=..., server=..., path=r"C:\Program Files\MetaTrader 5\terminal64.exe"
    )
    svc = TradingService(gw)

    # 1) Simple BUY 0.01 lots XAUUSD with $2 SL/TP distance
    print("BUY:", svc.buy("XAUUSD", 0.01, sl_dist=2.0, tp_dist=2.0))

    # 2) Place a BuyLimit
    # tick = gw.tick("XAUUSD")
    # print("PENDING:", svc.place_pending("XAUUSD", TradeSide.BUY, OrderKind.BUY_LIMIT, price=tick.bid-2.0, volume=0.02, sl=0.0, tp=0.0))

    # 3) List positions & close first
    pos = svc.positions("XAUUSD")
    if pos:
        first = pos[0].ticket
        print("CLOSE:", svc.close(first))

    gw.shutdown()
