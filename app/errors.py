class TradingError(RuntimeError):
    """Generic trading exception."""


class SymbolNotAvailable(TradingError):
    pass


class OrderRejected(TradingError):
    pass
