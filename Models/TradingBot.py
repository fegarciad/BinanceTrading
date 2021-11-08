######################
# Traiding Bot Class #
######################

import pandas as pd

from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy


class TradingBot():

    def __init__(self, exchange: Exchange, strategy: TradingStrategy, coin: str, order_size: float, interval: str, duration: int, paper_trade: bool = True) -> None:
        self.exchange = exchange
        self.strategy = strategy
        self.symbol = coin + 'USDT'
        self.order_size = order_size
        self.interval = interval
        self.duration = duration
        self.paper_trade = paper_trade

        self.exec_order = self.exchange.paper_market_order if self.paper_trade else self.exchange.market_order

        self.exchange.init_portfolio(coin,paper_trade)

        self.CandleList = []
        self.CandleDF = None

    def print_data(self) -> None:
        """Print live candlestick data to screen."""
        self.exchange.connect_ws(lambda x: print(x),self.symbol,self.interval,self.duration)

    def exec_strategy(self, data: pd.DataFrame) -> None:
        """Check if there is buy/sell signal and execute it."""
        signal = self.strategy.signal(data)
        if signal:
            self.exec_order(self.symbol,signal,self.order_size)
        else:
            msg = 'No order was placed.'
            print(msg)
            self.exchange.log_to_file(msg)

    def ws_handler(self, msg: str) -> None:
        """Function to handle incoming WebSocket candle data and pass it to the strategy."""
        try:
            self.CandleList, changed = self.exchange.refresh_candles(msg,self.CandleList)
            if changed:
                self.CandleDF = self.exchange.candlelist_to_df(self.CandleList)
                self.exchange.log_to_file(self.CandleDF.to_string(index=False))
                self.exec_strategy(self.CandleDF)
        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.close_connection()
                raise

    def run(self) -> None:
        """Initialize portfolio, connecto to WebSocket and run strategy."""
        print('\nRunning {}, PaperTrade: {}\n'.format(str(self.strategy),self.paper_trade))
        self.CandleList = self.exchange.init_candles(self.symbol,self.interval,self.strategy.get_lookback())
        self.exchange.value_positions()
        self.exchange.log_to_file('Init\n'+self.exchange.candlelist_to_df(self.CandleList).to_string(index=False))
        self.exchange.connect_ws(self.ws_handler,self.symbol,self.interval,self.duration)
