#####################
# Trading Bot Class #
#####################

import pandas as pd
from dataclasses import dataclass

from Models.Account import Account
from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy


@dataclass
class TradingBot:

    account: Account
    exchange: Exchange
    strategy: TradingStrategy
    coin: str
    order_size: float
    interval: str
    duration: int
    profit: float
    loss: float
    paper_trade: bool = True
    verbose: bool = False

    def __post_init__(self) -> None:
        self.symbol = self.coin + 'USDT'
        self.CandleList = self.exchange.init_candles(self.symbol,self.interval,self.strategy.get_lookback())
        self.CandleDF = self.exchange.candlelist_to_df(self.CandleList)
        
        self.account.set_positions(self.coin,self.account.paper_position,self.account.paper_cash_position)
        self.account.value_positions(self.symbol,init=True)
        
    def print_data(self) -> None:
        """Print live candlestick data to screen."""
        self.exchange.connect_ws(lambda msg: print(msg),self.symbol,self.interval,self.duration)

    def exec_strategy(self, data: pd.DataFrame) -> str:
        """Check if there is buy/sell signal and execute it."""
        signal = self.strategy.signal(data)
        if signal:
            self.exchange.execute_order(self.symbol,signal,self.order_size,self.paper_trade)
        else:
            self.account.log_to_file('\nNo order was placed.')
        return signal

    def ws_handler(self, msg: str) -> None:
        """Function to handle incoming WebSocket candlestick data and pass it to the strategy."""
        try:
            self.CandleList, changed = self.exchange.refresh_candles(msg,self.CandleList)
            if changed:
                self.CandleDF = self.exchange.candlelist_to_df(self.CandleList)
                self.account.log_to_file('\n'+self.CandleDF.to_string(index=False))
                exit, signal = self.account.check_profit_loss(self.symbol,self.profit,self.loss)
                if exit:
                    if signal == 'Loss':
                        self.exchange.exit_positions()
                    self.exchange.close_connection(self.symbol)
                _ = self.exec_strategy(self.CandleDF)
        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.close_connection(self.symbol)

    def run(self) -> None:
        """Initialize portfolio, connecto to WebSocket and run strategy."""
        msg = '\nRunning {}, PaperTrade: {}'.format(str(self.strategy),self.paper_trade)
        print(msg)
        self.account.log_to_file(msg)
        self.account.log_to_file('\nSymbol: {}\nInterval: {}\nOrdersize: {}\nDuration: {}'.format(self.symbol,self.interval,self.order_size,self.duration))
        self.account.log_to_file('\nTake profit: {}%\nStop Loss: {}%\n\n{}'.format(self.profit,self.loss,self.exchange.candlelist_to_df(self.CandleList).to_string(index=False)))
        self.exchange.connect_ws(self.ws_handler,self.symbol,self.interval,self.duration)
