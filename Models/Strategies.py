######################
# Trading Strategies #
######################

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd

from Models.Utils import ema, macd, rsi, sma


class TradingStrategy(ABC):
    """Trading strategy base class."""

    @abstractmethod
    def get_lookback(self) -> int:
        """Get minimum number of historic data points required to run strategy."""
    
    @abstractmethod
    def __str__(self) -> str:
        """Returns name of strategy."""

    @abstractmethod
    def signal(self, data: pd.DataFrame) -> str:
        """Returns trading signal (Buy/Sell/Do nothing)."""
    

@dataclass
class MACDStrategy(TradingStrategy):
    """MACD strategy, if MACD line crosses signal line, buy or sell."""
    
    period_long: int = 26
    period_short: int = 12 
    period_signal: int = 9

    assert period_long > period_short

    def get_lookback(self) -> int:
        return max([self.period_long,self.period_signal]) + 5

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
        
        return order


@dataclass
class TMAStrategy(TradingStrategy):
    """Three Moving Average Strategy, if MA's cross buy or sell"""

    period_long: int = 63
    period_mid: int = 21
    period_short: int = 5

    assert period_long > period_mid > period_short

    def get_lookback(self) -> int:
        return self.period_long + 5

    def __str__(self) -> str:
        return 'Three Moving Average Strategy (long={}, mid={}, short={})'.format(self.period_long,self.period_mid,self.period_short)

    def signal(self, data: pd.DataFrame) -> str:
        
        buy_orders = []
        sell_orders = []
        shortFlag = False
        longFlag = False

        date_col = 'Close time'
        price_col = 'Close price'

        prices =  data[[date_col,price_col]].sort_values(by=date_col).reset_index(drop=True)
        long_ma, mid_ma, short_ma = ema(prices[price_col],self.period_long), ema(prices[price_col],self.period_mid), ema(prices[price_col],self.period_short)
        prices['Long'], prices['Middle'], prices['Short'] = long_ma, mid_ma, short_ma

        for _, row in prices.iterrows():
            if row['Middle'] < row['Long'] and row['Short'] < row['Middle'] and not longFlag and not shortFlag:
                sell_orders.append('')
                buy_orders.append('BUY')
                shortFlag = True
            elif row['Short'] > row['Middle'] and shortFlag:
                sell_orders.append('SELL')
                buy_orders.append('')
                shortFlag = False
            
            elif row['Middle'] > row['Long'] and row['Short'] > row['Middle'] and not longFlag and not shortFlag:
                sell_orders.append('')
                buy_orders.append('BUY')
                longFlag = True
            elif row['Short'] < row['Middle'] and longFlag:
                sell_orders.append('SELL')
                buy_orders.append('')
                longFlag = False

            else:
                buy_orders.append('')
                sell_orders.append('')

        if (buy_orders[-1] and sell_orders[-1]) or (not buy_orders[-1] and not sell_orders[-1]):
            order = ''
        else:
            order = buy_orders[-1] if buy_orders[-1] else sell_orders[-1]
        
        return order


@dataclass
class RandomStrategy(TradingStrategy):
    """Random trading strategy for testing."""

    def get_lookback(self) -> int:
        return 5

    def __str__(self) -> str:
        return 'Random Strategy'
    
    def signal(self, data: pd.DataFrame) -> str:
        x = np.random.randint(100)
        if x < 25:
            return 'BUY'
        elif x > 75:
            return 'SELL'
        else:
            return ''

