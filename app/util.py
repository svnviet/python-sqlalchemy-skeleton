from typing import Dict

import MetaTrader5 as mt5


def build_retcode_map() -> Dict[int, str]:
    pairs = [
        ("TRADE_RETCODE_DONE", "DONE"),
        ("TRADE_RETCODE_DONE_PARTIAL", "DONE_PARTIAL"),
        ("TRADE_RETCODE_PLACED", "PLACED"),
        ("TRADE_RETCODE_REJECT", "REJECT"),
        ("TRADE_RETCODE_CANCEL", "CANCEL"),
        ("TRADE_RETCODE_INVALID", "INVALID"),
        ("TRADE_RETCODE_INVALID_VOLUME", "INVALID_VOLUME"),
        ("TRADE_RETCODE_INVALID_PRICE", "INVALID_PRICE"),
        ("TRADE_RETCODE_INVALID_STOPS", "INVALID_STOPS"),
        ("TRADE_RETCODE_MARKET_CLOSED", "MARKET_CLOSED"),
        ("TRADE_RETCODE_NO_MONEY", "NO_MONEY"),
        ("TRADE_RETCODE_PRICE_CHANGED", "PRICE_CHANGED"),
        ("TRADE_RETCODE_PRICE_OFF", "OFF_QUOTES"),
        ("TRADE_RETCODE_TRADE_DISABLED", "TRADE_DISABLED"),
        ("TRADE_RETCODE_TIMEOUT", "TIMEOUT"),
        ("TRADE_RETCODE_ORDER_CHANGED", "ORDER_CHANGED"),
        ("TRADE_RETCODE_TOO_MANY_REQUESTS", "TOO_MANY_REQUESTS"),
        ("TRADE_RETCODE_CLIENT_DISABLES_AT", "CLIENT_AT_DISABLED"),
        ("TRADE_RETCODE_LOCKED", "SYMBOL_TRADE_DISABLED"),
        ("TRADE_RETCODE_FROZEN", "SYMBOL_FROZEN"),
    ]
    m: Dict[int, str] = {}
    for const, label in pairs:
        v = getattr(mt5, const, None)
        if isinstance(v, int):
            m[v] = label
    return m


RETCODES = build_retcode_map()


def label_retcode(code: int) -> str:
    return RETCODES.get(code, f"UNKNOWN({code})")
