################
# Orders Class #
################

import time
from dataclasses import dataclass


@dataclass
class MarketOrder:

    confirmation: dict[str,str]
    commission: float

    def __post_init__(self) -> None:
        self.symbol = self.confirmation['symbol']
        self.side = self.confirmation['side']
        self.qty = float(self.confirmation['executedQty'])
        self.order_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(self.confirmation['transactTime']/1000))
        self.price = float(self.confirmation['cummulativeQuoteQty'])/float(self.confirmation['executedQty'])

    def __str__(self) -> str:
        return 'Order: {} {:,.4f} {} for ${:,.2f} (${:,.2f} total) at {}'.format(self.side,self.qty,self.symbol,self.price,self.price*self.qty,self.order_time)
    
    @property
    def order_dict(self) -> dict:
        return {'Symbol': self.symbol, 'Side': self.side, 'Price': self.price, 'Quantity': self.qty, 'Time': self.order_time}


@dataclass
class PaperOrder:
    
    confirmation: dict[str,str]
    commission: float

    def __post_init__(self) -> None:
        self.symbol = self.confirmation['symbol']
        self.side = self.confirmation['side']
        self.qty = self.confirmation['quantity']
        self.order_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        self.price = None

    def __str__(self) -> str:
        return 'Order: {} {:,.4f} {} for ${:,.2f} (${:,.2f} total) at {}'.format(self.side,self.qty,self.symbol,self.price,self.price*self.qty,self.order_time)

    def set_price(self, price: float) -> None:
        self.price = price

    @property
    def order_dict(self) -> dict:
        return {'Symbol': self.symbol, 'Side': self.side, 'Price': self.price, 'Quantity': self.qty, 'Time': self.order_time}
