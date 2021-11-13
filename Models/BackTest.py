##################
# Backtest Class #
##################

import sys

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd

from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy
from Models.TradingBot import TradingBot


class Backtest():
    
    def __init__(self, exchange: Exchange, tradingbot: TradingBot, strategy: TradingStrategy, periods: int) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.tradingbot = tradingbot
        self.backtest_periods = periods

        if self.tradingbot.paper_trade != True:
            print('\nBacktest can only run in paper trading mode.')
            sys.exit(1)

        if self.backtest_periods < self.strategy.get_lookback():
            print('\nMore periods are required to run {}.'.format(str(self.strategy)))
            sys.exit(1)

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
        self.init_wealth = self.value_portfolio(data.iloc[0]['Open price'])
        self.exchange.log_to_file('Init\n' + data.iloc[:self.strategy.get_lookback()].to_string(index=False))

        for i in range(self.strategy.get_lookback() + 1,data.shape[0]):
            live_data = data.iloc[:i]
            self.exchange.log_to_file(live_data.to_string(index=False))
            sig = self.tradingbot.exec_strategy(live_data)
            if sig:
                self.exchange.Trades[-1]['Time'] = live_data.iloc[-1]['Close time']
        
        print('Number of trades: {}'.format(len(self.exchange.Trades)))
        self.final_wealth = self.value_portfolio(data.iloc[-1]['Close price'])
        self.BacktestDF = self.backtest_dataframe(live_data)
        print('Return of {}: ${:.2f} ({:.2f}%)'.format(str(self.strategy),self.final_wealth-self.init_wealth,(self.final_wealth/self.init_wealth - 1)*100))
        return self.final_wealth - self.init_wealth

    def value_portfolio(self, price: float) -> float:
        """Value current portfolio."""
        cash = self.exchange.CashPosition
        coin = self.exchange.Position
        commissions = self.exchange.Commissions
        wealth = cash + coin*price - commissions
        msg = '\n{} position: {:,.4f}\nCash position: {:,.2f}\nCommissions: {:,.2f}\nTotal: {:.2f}\n'.format(self.exchange.Symbol,coin,cash,commissions,wealth)
        print(msg)
        self.exchange.log_to_file(msg)
        return wealth

    def backtest_dataframe(self,data: pd.DataFrame) -> pd.DataFrame:
        """Create dataframe with price and trade data from backtest."""
        TradeDF = pd.DataFrame(self.exchange.Trades)
        TradeDF.rename(columns={'Time':'Close time'},inplace=True)
        BacktestDF = pd.merge(data,TradeDF[['Side','Close time']],on='Close time',how='left')
        BacktestDF['BUY'] = BacktestDF.loc[BacktestDF['Side'] == 'BUY','Close price']
        BacktestDF['SELL'] = BacktestDF.loc[BacktestDF['Side'] == 'SELL','Close price']
        return BacktestDF

    def plot_backtest(self) -> None:
        """Plot price chart and entry and exit signals."""
        _, ax = plt.subplots(1,1,figsize=(10,8))
        ax.plot(self.BacktestDF['Close time'],self.BacktestDF['Close price'],zorder=1)
        ax.scatter(self.BacktestDF['Close time'],self.BacktestDF['BUY'], color='green', label='Buy', marker='^',s=75,zorder=2)
        ax.scatter(self.BacktestDF['Close time'],self.BacktestDF['SELL'], color='red', label='Sell', marker='v',s=75,zorder=2)
        ax.set_xlabel('Dates',fontsize=20)
        ax.set_title('Backtest {} {} periods'.format(str(self.strategy),self.backtest_periods),fontsize=30,y=1.03,loc='center',wrap=True)
        ax.legend(fontsize=15)
        ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: format(int(x), ',')))
        plt.savefig('Images//Backtest {} {} periods.png'.format(str(self.strategy),self.backtest_periods))
        plt.show()
