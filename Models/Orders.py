################
# Orders Class #
################

import time
from dataclasses import dataclass, field


@dataclass
class MarketOrder:

    confirmation: dict[str,str] = field(default_factory=dict)

    def __post_init__(self):
        self.symbol = self.confirmation["symbol"]
        self.side = self.confirmation["side"]
        self.qty = self.confirmation["executedQty"]
        self.order_time = time.strftime('%Y-%m-%d %H:%M',time.localtime(self.confirmation['transactTime']/1000))
        self.price = float(self.confirmation['cummulativeQuoteQty'])/float(self.confirmation['executedQty'])
        self.order_dict = {"symbol": self.symbol, "side": self.side, "type": "MARKET", "quantity": self.qty}

    def __str__(self) -> str:
        return 'Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}'.format(self.side,self.qty,self.symbol,self.price,self.price*self.qty,self.order_time)


@dataclass
class PaperOrder:
    
    confirmation: dict[str,str] = field(default_factory=dict)

    def __post_init__(self):
        self.symbol = self.confirmation["symbol"]
        self.side = self.confirmation["side"]
        self.qty = self.confirmation["quantity"]
        self.order_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))
        self.price = 0
        self.order_dict = {"symbol": self.symbol, "side": self.side, "type": "MARKET", "quantity": self.qty}

    def __str__(self) -> str:
        return 'Order: {} {} {} for ${:,.2f} (${:,.2f} total) at {}'.format(self.side,self.qty,self.symbol,self.price,self.price*self.qty,self.order_time)

