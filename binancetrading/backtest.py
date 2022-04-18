
"""Backtest Class"""

import sys
import time

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from binancetrading.account import log_msg
from binancetrading.exchange import _candle_list_to_df
from binancetrading.trading_bot import TradingBot


class Backtest:
    """Backtest class."""

    def __init__(self, tradingbot: TradingBot, periods: int) -> None:
        self.tradingbot = tradingbot
        self.backtest_periods = periods
        self.init_wealth: float = 0.0
        self.final_wealth: float = 0.0
        self.backtest_df: pd.DataFrame = pd.DataFrame()

        self.tradingbot.account._set_positions(self.tradingbot.coin, self.tradingbot.account.paper_position, self.tradingbot.account.paper_cash_position)
        self.tradingbot.account._value_positions(self.tradingbot.symbol, init=True)

        if not self.tradingbot.account.paper_trade:
            log_msg('Backtest can only run in paper trading mode.', verb=True)
            sys.exit(1)

        if self.backtest_periods < self.tradingbot.strategy.get_lookback():
            log_msg(f'More than {self.tradingbot.strategy.get_lookback()} periods are required to run {str(self.tradingbot.strategy)}.', verb=True)
            sys.exit(1)

    def get_hist_data(self, symbol: str, interval: str, backtest_periods: int) -> pd.DataFrame:
        """Get historic price data to backtest strategies."""
        data_list = self.tradingbot.exchange._init_candles(symbol, interval, backtest_periods)
        return _candle_list_to_df(data_list)

    def run_backtest(self, log_candles: bool = False, plot: bool = False) -> float:
        """Execute backtest on strategy."""
        log_msg(f'############\n# BACKTEST #\n############\n\nRunning Backest on {str(self.tradingbot.strategy)}, {self.backtest_periods} Data Points')
        log_msg(f'Started at: {time.strftime("%Y-%m-%d %H:%M", time.localtime())}')
        log_msg(f'Symbol: {self.tradingbot.symbol}\nInterval: {self.tradingbot.interval}\nOrdersize: {self.tradingbot.order_size}')
        log_msg(f'Take profit: {self.tradingbot.profit}%\nStop Loss: {self.tradingbot.profit}%')
        data = self.get_hist_data(self.tradingbot.symbol, self.tradingbot.interval, self.backtest_periods)
        self.init_wealth = self._value_portfolio(data.iloc[0]['Open price'])

        for i in range(self.tradingbot.strategy.get_lookback() + 1, data.shape[0]):
            live_data = data.iloc[:i]
            if log_candles:
                log_msg(live_data.to_string(index=False))
            signal = self.tradingbot.execute_strategy(live_data)
            if signal:
                self.tradingbot.account.trades[-1]['Time'] = live_data.iloc[-1]['Close time']

        log_msg(f'Number of trades: {len(self.tradingbot.account.trades)}', verb=True)
        log_msg(f'{pd.DataFrame(self.tradingbot.account.trades).to_string(index=False)}', verb=True)
        self.final_wealth = self._value_portfolio(data.iloc[-1]['Close price'])
        self.backtest_df = self._backtest_results_dataframe(live_data)
        self.tradingbot.account._value_positions(self.tradingbot.symbol)
        log_msg(f'Return of {str(self.tradingbot.strategy)}: {self.final_wealth - self.init_wealth:.2f} ({(self.final_wealth / self.init_wealth - 1) * 100:.2f}%)', verb=True)
        if plot:
            self._plot_backtest_results()
        return self.final_wealth - self.init_wealth

    def _value_portfolio(self, price: float) -> float:
        """Value current portfolio."""
        cash_position = self.tradingbot.account.cash_position
        coin_position = self.tradingbot.account.position
        commissions = self.tradingbot.account.commissions
        return cash_position + coin_position * price - commissions

    def _backtest_results_dataframe(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create dataframe with price and trade data from backtest."""
        trade_df = pd.DataFrame(self.tradingbot.account.trades)
        trade_df.rename(columns={'Time': 'Close time'}, inplace=True)
        backtest_df = pd.merge(data, trade_df[['Side', 'Close time']], on='Close time', how='left')
        backtest_df['BUY'] = backtest_df.loc[backtest_df['Side'] == 'BUY', 'Close price']
        backtest_df['SELL'] = backtest_df.loc[backtest_df['Side'] == 'SELL', 'Close price']
        return backtest_df

    def _plot_backtest_results(self, save: bool = False) -> None:
        """Plot price chart, entry and exit signals."""
        _, axis = plt.subplots(1, 1, figsize=(10, 8))
        axis.plot(self.backtest_df['Close time'], self.backtest_df['Close price'], zorder=1)
        axis.scatter(self.backtest_df['Close time'], self.backtest_df['BUY'], color='green', label='Buy', marker='^', s=75, zorder=2)
        axis.scatter(self.backtest_df['Close time'], self.backtest_df['SELL'], color='red', label='Sell', marker='v', s=75, zorder=2)
        axis.set_xlabel('Dates', fontsize=20)
        title = f'{self.tradingbot.symbol} Backtest {str(self.tradingbot.strategy)} {self.backtest_periods} periods {self.tradingbot.interval} ticks'
        axis.set_title(title, fontsize=30, y=1.03, loc='center', wrap=True)
        axis.legend(fontsize=15)
        axis.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: format(int(x), ',')))
        if save:
            plt.savefig(title + '.png')
        plt.show()
