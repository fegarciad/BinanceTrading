##################
# Backtest Class #
##################

import sys
import time
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from Models.Account import Account
from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy
from Models.TradingBot import TradingBot


class Backtest:

    def __init__(self, account: Account, exchange: Exchange, tradingbot: TradingBot, strategy: TradingStrategy, periods: int) -> None:
        self.account = account
        self.exchange = exchange
        self.strategy = strategy
        self.tradingbot = tradingbot
        self.backtest_periods = periods
        self.init_wealth: float = 0.0
        self.final_wealth: float = 0.0
        self.backtest_df: pd.DataFrame = pd.DataFrame()

        if not self.account.paper_trade:
            print('\nBacktest can only run in paper trading mode.')
            sys.exit(1)

        if self.backtest_periods < self.strategy.get_lookback():
            print(f'\nMore than {self.strategy.get_lookback()} periods are required to run {str(self.strategy)}.')
            sys.exit(1)

    def get_hist_data(self) -> pd.DataFrame:
        """Get historic price data to backtest strategies."""
        data_list = self.exchange.init_candles(self.tradingbot.symbol, self.tradingbot.interval, self.backtest_periods)
        data = self.exchange.candle_list_to_df(data_list)
        return data

    def run_backtest(self, log_candles: bool = False) -> float:
        """Execute backtest on strategy."""
        self.account.log_to_file('############\n# BACKTEST #\n############', init=True)
        msg = f'\nRunning Backest on {str(self.strategy)}, {self.backtest_periods} Data Points'
        print(msg)
        self.account.log_to_file(msg)
        self.account.log_to_file(f'\nStarted at: {time.strftime("%Y-%m-%d %H:%M", time.localtime())}')
        self.account.log_to_file(f'\nSymbol: {self.tradingbot.symbol}\nInterval: {self.tradingbot.interval}\nOrdersize: {self.tradingbot.order_size}')
        self.account.log_to_file(f'\nTake profit: {self.tradingbot.profit}%\nStop Loss: {self.tradingbot.profit}%')
        data = self.get_hist_data()
        self.init_wealth = self.value_portfolio(data.iloc[0]['Open price'])

        for i in range(self.strategy.get_lookback() + 1, data.shape[0]):
            live_data = data.iloc[:i]
            if log_candles:
                self.account.log_to_file('\n' + live_data.to_string(index=False))
            sig = self.tradingbot.exec_strategy(live_data)
            if sig:
                self.account.trades[-1]['Time'] = live_data.iloc[-1]['Close time']

        msg = f'\nNumber of trades: {len(self.account.trades)}'
        print(msg)
        self.account.log_to_file(msg)
        print(pd.DataFrame(self.account.trades))
        self.account.log_to_file(pd.DataFrame(self.account.trades).to_string(index=False))
        self.final_wealth = self.value_portfolio(data.iloc[-1]['Close price'])
        self.backtest_df = self.backtest_dataframe(live_data)
        self.account.value_positions(self.tradingbot.symbol)
        msg = f'\nReturn of {str(self.strategy)}: {self.final_wealth - self.init_wealth:.2f} ({(self.final_wealth / self.init_wealth - 1) * 100:.2f}%)'
        print(msg)
        self.account.log_to_file(msg)
        return self.final_wealth - self.init_wealth

    def value_portfolio(self, price: float) -> float:
        """Value current portfolio."""
        cash = self.account.cash_position
        coin = self.account.position
        commissions = self.account.commissions
        wealth = cash + coin * price - commissions
        return wealth

    def backtest_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create dataframe with price and trade data from backtest."""
        trade_df = pd.DataFrame(self.account.trades)
        trade_df.rename(columns={'Time': 'Close time'}, inplace=True)
        backtest_df = pd.merge(data, trade_df[['Side', 'Close time']], on='Close time', how='left')
        backtest_df['BUY'] = backtest_df.loc[backtest_df['Side'] == 'BUY', 'Close price']
        backtest_df['SELL'] = backtest_df.loc[backtest_df['Side'] == 'SELL', 'Close price']
        return backtest_df

    def plot_backtest(self) -> None:
        """Plot price chart, entry and exit signals."""
        _, axis = plt.subplots(1, 1, figsize=(12, 10))
        axis.plot(self.backtest_df['Close time'], self.backtest_df['Close price'], zorder=1)
        axis.scatter(self.backtest_df['Close time'], self.backtest_df['BUY'], color='green', label='Buy', marker='^', s=75, zorder=2)
        axis.scatter(self.backtest_df['Close time'], self.backtest_df['SELL'], color='red', label='Sell', marker='v', s=75, zorder=2)
        axis.set_xlabel('Dates', fontsize=20)
        title = f'Backtest {str(self.strategy)} {self.backtest_periods} periods {self.tradingbot.interval} ticks'
        axis.set_title(title, fontsize=30, y=1.03, loc='center', wrap=True)
        axis.legend(fontsize=15)
        axis.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: format(int(x), ',')))
        plt.savefig('Images//' + title + '.png')
        plt.show()
