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

        if self.tradingbot.paper_trade != True:
            print('\nBacktest can only run in paper trading mode.')
            sys.exit(1)

        if self.backtest_periods < self.strategy.get_lookback():
            print('\nMore than {} periods are required to run {}.'.format(self.strategy.get_lookback(),str(self.strategy)))
            sys.exit(1)

    def get_hist_data(self) -> pd.DataFrame:
        """Get historic price data to backtest strategies."""
        data_list = self.exchange.init_candles(self.tradingbot.symbol,self.tradingbot.interval,self.backtest_periods)
        data = self.exchange.candle_list_to_df(data_list)
        return data

    def run_backtest(self, log_candles: bool = False) -> int:
        """Execute backtest on strategy."""
        self.account.log_to_file('############\n# BACKTEST #\n############',init=True)
        msg = '\nRunning Backest on {}, {} Data Points'.format(str(self.strategy),self.backtest_periods)
        print(msg)
        self.account.log_to_file(msg)
        self.account.log_to_file('\nStarted at: {}'.format(time.strftime('%Y-%m-%d %H:%M', time.localtime())))
        self.account.log_to_file('\nSymbol: {}\nInterval: {}\nOrdersize: {}\nDuration: {}'.format(self.tradingbot.symbol,self.tradingbot.interval,self.tradingbot.order_size,self.tradingbot.duration))
        self.account.log_to_file('\nTake profit: {}%\nStop Loss: {}%'.format(self.tradingbot.profit,self.tradingbot.loss))
        data = self.get_hist_data()
        self.init_wealth = self.value_portfolio(data.iloc[0]['Open price'])

        for i in range(self.strategy.get_lookback() + 1,data.shape[0]):
            live_data = data.iloc[:i]
            if log_candles:
                self.account.log_to_file('\n' + live_data.to_string(index=False))
            sig = self.tradingbot.exec_strategy(live_data)
            if sig:
                self.account.trades[-1]['Time'] = live_data.iloc[-1]['Close time']
        
        msg = '\nNumber of trades: {}'.format(len(self.account.trades))
        print(msg)
        self.account.log_to_file(msg)
        print(pd.DataFrame(self.account.trades))
        self.account.log_to_file(pd.DataFrame(self.account.trades).to_string(index=False))
        self.final_wealth = self.value_portfolio(data.iloc[-1]['Close price'])
        self.BacktestDF = self.backtest_dataframe(live_data)
        self.account.value_positions(self.tradingbot.symbol)
        msg = '\nReturn of {}: {:.2f} ({:.2f}%)'.format(str(self.strategy),self.final_wealth-self.init_wealth,(self.final_wealth/self.init_wealth - 1)*100)
        print(msg)
        self.account.log_to_file(msg)
        return self.final_wealth - self.init_wealth

    def value_portfolio(self, price: float) -> float:
        """Value current portfolio."""
        cash = self.account.cash_position
        coin = self.account.position
        commissions = self.account.commissions
        wealth = cash + coin*price - commissions
        return wealth

    def backtest_dataframe(self,data: pd.DataFrame) -> pd.DataFrame:
        """Create dataframe with price and trade data from backtest."""
        TradeDF = pd.DataFrame(self.account.trades)
        TradeDF.rename(columns={'Time':'Close time'},inplace=True)
        BacktestDF = pd.merge(data,TradeDF[['Side','Close time']],on='Close time',how='left')
        BacktestDF['BUY'] = BacktestDF.loc[BacktestDF['Side'] == 'BUY','Close price']
        BacktestDF['SELL'] = BacktestDF.loc[BacktestDF['Side'] == 'SELL','Close price']
        return BacktestDF

    def plot_backtest(self) -> None:
        """Plot price chart, entry and exit signals."""
        _, ax = plt.subplots(1,1,figsize=(12,10))
        ax.plot(self.BacktestDF['Close time'],self.BacktestDF['Close price'],zorder=1)
        ax.scatter(self.BacktestDF['Close time'],self.BacktestDF['BUY'], color='green', label='Buy', marker='^',s=75,zorder=2)
        ax.scatter(self.BacktestDF['Close time'],self.BacktestDF['SELL'], color='red', label='Sell', marker='v',s=75,zorder=2)
        ax.set_xlabel('Dates',fontsize=20)
        title = 'Backtest {} {} periods {} ticks'.format(str(self.strategy),self.backtest_periods,self.tradingbot.interval)
        ax.set_title(title,fontsize=30,y=1.03,loc='center',wrap=True)
        ax.legend(fontsize=15)
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: format(int(x), ',')))
        plt.savefig('Images//'+title+'.png')
        plt.show()
