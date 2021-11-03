##################
# Backtest Class #
##################

import pandas as pd
from Models.Strategies import TradingStrategy
from Models.Exchange import Exchange


class BackTest():
    """Class to backtest strategies."""
    
    def __init__(self, exchange: Exchange, strategy: TradingStrategy, periods: int, init_portfolio: tuple[float,float]) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.backtest_periods = periods
        self.Position = init_portfolio[0]
        self.CashPosition = init_portfolio[1]

    def get_hist_data(self) -> pd.DataFrame:
        """Get historic price data to backtest strategies."""
        pass

    def backtest(self) -> None:
        """Execute backtest on strategy."""
        pass