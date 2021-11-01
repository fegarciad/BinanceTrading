######################
# Trading Strategies #
######################

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd

from Models.Utils import ema, macd, rsi, sma


class TradingStrategy(ABC):

    @abstractmethod
    def signal(self, data: pd.DataFrame) -> str:
        """Returns trading signal (Buy/Sell/Do nothing)."""
    
    @abstractmethod
    def __str__(self) -> str:
        """Returns name of strategy."""


@dataclass
class MACDStrategy(TradingStrategy):
    """MACD strategy, if MACD line crosses signal line, buy or sell."""
    
    period_long: int = 26
    period_short: int = 12 
    period_signal: int = 9

    def __str__(self) -> str:
        return 'MACD Strategy (long={}, short={}, signal={})'.format(self.period_long,self.period_short,self.period_signal)

    def signal(self, data: pd.DataFrame) -> str:
        
        buy_orders = []
        sell_orders = []
        flag = False

        date_col = 'Close time'
        price_col = 'Close price'

        prices =  data[[date_col,price_col]].sort_values(by=date_col).reset_index(drop=True)
        macd_line, signal_line = macd(prices[price_col],period_long=self.period_long,period_short=self.period_short,period_signal=self.period_signal)
        prices['MACD'] = macd_line
        prices['Signal'] = signal_line

        for _, row in prices.iterrows():
            if row['MACD'] > row['Signal']:
                sell_orders.append('')
                if not flag:
                    buy_orders.append('BUY')
                    flag = True
                else:
                    buy_orders.append('')
            elif row['MACD'] < row['Signal']:
                buy_orders.append('')
                if flag:
                    sell_orders.append('SELL')
                    flag = False
                else:
                    sell_orders.append('')
            else:
                buy_orders.append('')
                sell_orders.append('')
        
        if (buy_orders[-1] and sell_orders[-1]) or (not buy_orders[-1] and not sell_orders[-1]):
            order = ''
        else:
            order = buy_orders[-1] if buy_orders[-1] else sell_orders[-1]
        print(buy_orders[-1], sell_orders[-1], order)
        return order


@dataclass
class RandomStrategy(TradingStrategy):
    """Random trading strategy for testing."""

    def __str__(self) -> str:
        return 'Random Strategy'
    
    def signal(self, data: pd.DataFrame) -> str:
        x = np.random.randint(100)
        print(data,'\n',x)
        if x < 25:
            return 'BUY'
        elif x > 75:
            return 'SELL'
        else:
            return ''

