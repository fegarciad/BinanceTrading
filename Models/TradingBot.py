######################
# Traiding Bot Class #
######################

import pandas as pd

from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy


class TradingBot():

    def __init__(self, exchange: Exchange, strategy: TradingStrategy, symbol: str, order_size: float, interval: str, duration: int, lookback: int, paper_trade: bool = False):
        self.exchange = exchange
        self.strategy = strategy
        self.symbol = symbol
        self.order_size = order_size
        self.interval = interval
        self.duration = duration
        self.lookback = lookback
        self.paper_trade = paper_trade

        self.exec_order = self.exchange.paper_market_order if self.paper_trade else self.exchange.market_order

        exchange.init_portfolio(symbol,paper_trade)

        self.CandleList = []
        self.CandleDF = None

    def print_data(self) -> None:
        self.exchange.connect_ws(lambda x: print(x),self.symbol,self.interval,self.duration)

    def exec_strategy(self, data: pd.DataFrame) -> None:
        signal = self.strategy.signal(data)
        if signal:
            self.exec_order(self.symbol,signal,self.order_size)
        else:
            print('No order was placed.')

    def ws_handler(self, msg: str) -> None:
        try:
            self.CandleList, changed = self.exchange.refresh_candles(msg,self.CandleList)
            if changed:
                self.CandleDF = self.exchange.candlelist_to_df(self.CandleList)
                self.exec_strategy(self.CandleDF)

        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.close_connection()
                raise
        except Exception as err:
            print(err)
            self.exchange.close_connection()
            raise

    def run(self) -> None:
        print('Running {}, PaperTrade: {}\n'.format(str(self.strategy),self.paper_trade))
        self.CandleList = self.exchange.init_candles(self.symbol,self.interval,self.lookback)
        # value_positions()
        print(self.exchange.candlelist_to_df(self.CandleList))
        self.exchange.connect_ws(self.ws_handler,self.symbol,self.interval,self.duration)
