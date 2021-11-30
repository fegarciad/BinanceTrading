#################
# Order Classes #
#################

import time
from dataclasses import dataclass


@dataclass
class MarketOrder:
    """Market order class."""

    confirmation: dict[str, str]
    commission: float

    def __post_init__(self) -> None:
        self.symbol = self.confirmation['symbol']
        self.side = self.confirmation['side']
        self.qty = float(self.confirmation['executedQty'])
        self.order_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(float(self.confirmation['transactTime']) / 1000))
        self.price = float(self.confirmation['cummulativeQuoteQty']) / float(self.confirmation['executedQty'])

    def __str__(self) -> str:
        return f'Order: {self.side} {self.qty:,.4f} {self.symbol} for ${self.price:,.2f} (${self.price*self.qty:,.2f} total) at {self.order_time}'

    @property
    def order_dict(self) -> dict:
        """Order details."""
        return {'Symbol': self.symbol, 'Side': self.side, 'Price': self.price, 'Quantity': self.qty, 'Time': self.order_time}


@dataclass
class PaperOrder:
    """Paper market order class."""

    confirmation: dict[str, str]
    commission: float

    def __post_init__(self) -> None:
        self.symbol = self.confirmation['symbol']
        self.side = self.confirmation['side']
        self.qty = float(self.confirmation['quantity'])
        self.order_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.price: float = 0.0

    def __str__(self) -> str:
        return f'Order: {self.side} {self.qty:,.4f} {self.symbol} for ${self.price:,.2f} (${self.price*self.qty:,.2f} total) at {self.order_time}'

    def set_price(self, price: float) -> None:
        """Set price of order."""
        self.price = price

    @property
    def order_dict(self) -> dict:
        """Order details."""
        return {'Symbol': self.symbol, 'Side': self.side, 'Price': self.price, 'Quantity': self.qty, 'Time': self.order_time}
