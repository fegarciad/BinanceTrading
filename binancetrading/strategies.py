
"""Trading Strategies"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd

import binancetrading as bt


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
    """MACD Strategy: If MACD line crosses signal line, buy or sell."""

    period_long: int = 26
    period_short: int = 12
    period_signal: int = 9

    assert period_long > period_short

    def get_lookback(self) -> int:
        return max([self.period_long, self.period_signal]) + 5

    def __str__(self) -> str:
        return f'MACD Strategy (long={self.period_long}, short={self.period_short}, signal={self.period_signal})'

    def signal(self, data: pd.DataFrame) -> str:

        buy_orders = []
        sell_orders = []
        flag = False

        date_col = 'Close time'
        price_col = 'Close price'

        prices = data[[date_col, price_col]].sort_values(by=date_col).reset_index(drop=True)
        macd_line, signal_line = bt.utils.macd(prices[price_col], period_long=self.period_long, period_short=self.period_short, period_signal=self.period_signal)
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
    """Three Moving Average Strategy: If MA's cross, buy or sell"""

    period_long: int = 63
    period_mid: int = 21
    period_short: int = 5

    assert period_long > period_mid > period_short

    def get_lookback(self) -> int:
        return self.period_long + 5

    def __str__(self) -> str:
        return f'Three Moving Average Strategy (long={self.period_long}, mid={self.period_mid}, short={self.period_short})'

    def signal(self, data: pd.DataFrame) -> str:

        buy_orders = []
        sell_orders = []
        short_flag = False
        long_flag = False

        date_col = 'Close time'
        price_col = 'Close price'

        prices = data[[date_col, price_col]].sort_values(by=date_col).reset_index(drop=True)
        long_ma, mid_ma, short_ma = bt.utils.ema(prices[price_col], self.period_long), bt.utils.ema(prices[price_col], self.period_mid), bt.utils.ema(prices[price_col], self.period_short)
        prices['Long'], prices['Middle'], prices['Short'] = long_ma, mid_ma, short_ma

        for _, row in prices.iterrows():
            if row['Middle'] < row['Long'] and row['Short'] < row['Middle'] and not long_flag and not short_flag:
                sell_orders.append('')
                buy_orders.append('BUY')
                short_flag = True
            elif row['Short'] > row['Middle'] and short_flag:
                sell_orders.append('SELL')
                buy_orders.append('')
                short_flag = False

            elif row['Middle'] > row['Long'] and row['Short'] > row['Middle'] and not long_flag and not short_flag:
                sell_orders.append('')
                buy_orders.append('BUY')
                long_flag = True
            elif row['Short'] < row['Middle'] and long_flag:
                sell_orders.append('SELL')
                buy_orders.append('')
                long_flag = False

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
    """Random Strategy: For testing purposes."""

    upper: int = 75
    lower: int = 25

    def get_lookback(self) -> int:
        return 5

    def __str__(self) -> str:
        return f'Random Strategy (upper={self.upper}, lower={self.lower})'

    def signal(self, data: pd.DataFrame) -> str:
        signal = np.random.randint(100)
        if signal < self.lower:
            return 'BUY'
        elif signal > self.upper:
            return 'SELL'
        else:
            return ''
