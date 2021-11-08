##################
# Backtest Class #
##################

import pandas as pd
from scipy.optimize import brute

from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy
from Models.TradingBot import TradingBot


class Backtest():
    
    def __init__(self, exchange: Exchange, tradingbot: TradingBot, strategy: TradingStrategy, periods: int) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.tradingbot = tradingbot
        self.backtest_periods = periods
        self.lookback = strategy.get_lookback()

        if self.tradingbot.paper_trade != True:
            print('Backtest can only run in paper trading mode.')
            self.exchange.close_connection()

    def get_hist_data(self) -> pd.DataFrame:
        """Get historic price data to backtest strategies."""
        data_list = self.exchange.init_candles(self.tradingbot.symbol,self.tradingbot.interval,self.backtest_periods)
        data = self.exchange.candlelist_to_df(data_list)
        return data

    def run_backtest(self) -> int:
        """Execute backtest on strategy."""
        self.exchange.log_to_file('############\n# BACKTEST #\n############\n',init=True)
        data = self.get_hist_data()
        print('\nRunning Backest on {}, {} Data Points\n'.format(str(self.strategy),self.backtest_periods))
        self.exchange.value_positions()
        self.init_wealth = self.exchange.Wealth
        self.exchange.log_to_file('Init\n' + data.iloc[:self.lookback].to_string(index=False))

        for i in range(self.lookback + 1,data.shape[0]):
            live_data = data.iloc[:i]
            self.exchange.log_to_file(live_data.to_string(index=False))
            self.tradingbot.exec_strategy(live_data)
        
        self.exchange.value_positions()
        print('Number of trades: {}'.format(len(self.exchange.Trades)))
        self.final_wealth = self.exchange.Wealth
        print('Return of {}: {:.2f} ({:.2f}%)'.format(str(self.strategy),self.final_wealth-self.init_wealth,(self.final_wealth/self.init_wealth - 1)*100))
        return self.final_wealth - self.init_wealth

    def set_params(self, params: tuple) -> None:
        """Set strategy parameters."""
        pass

    def update_and_run(self, params: tuple) -> int:
        """Update parameters and run strategy."""
        return -self.backtest()

    def optimize_params(self,param_ranges: tuple) -> None:
        """Optimize strategy parameters."""
        opt = brute(self.update_and_run, param_ranges, finish=None)
        return opt, -self.update_and_run(opt)
