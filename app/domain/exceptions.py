class PortfolioXError(Exception):
    """Base exception for all domain logic errors in PortfolioX."""
    pass

class InvalidOrderError(PortfolioXError):
    """Raised when an order has invalid parameters (e.g., quantity <= 0)."""
    pass


class UnsupportedOrderTypeError(PortfolioXError):
    """Raised when an unrecognized order type is encountered."""
    pass