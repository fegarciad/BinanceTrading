######################
# Traiding Bot Class #
######################

from Models.Exchange import Exchange
from Models.Strategies import TradingStrategy


class TradingBot():

    def __init__(self,exchange: Exchange,strategy: TradingStrategy,symbol,order_size,interval,duration,lookback,paper_trade=False):
        self.exchange = exchange
        self.strategy = strategy
        self.symbol = symbol
        self.order_size = order_size
        self.interval = interval
        self.duration = duration
        self.lookback = lookback
        self.paper_trade = paper_trade

        self.exec_order = self.exchange.make_paper_order if self.paper_trade else self.exchange.make_market_order

        exchange.init_portfolio(symbol,paper_trade)

        self.CandleList = []
        self.CandleDF = None

    def print_data(self):
        self.exchange.connect_ws(lambda x: print(x),self.symbol,self.interval,self.duration)

    def exec_strategy(self,data):
        signal = self.strategy.signal(data)
        price = data.tail(1).iloc[0]['Close price']
        time = data.tail(1).iloc[0]['Close time']
        
        if signal == 'BUY':
            self.exec_order(self.symbol,'BUY',price,self.order_size,time)
        elif signal == 'SELL':
            self.exec_order(self.symbol,'SELL',price,self.order_size,time)
        else:
            print('No order was placed.')

    def ws_handler(self,msg):
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
        except Exception as e:
            print(e)
            self.exchange.close_connection()
            raise

    def run(self):
        self.CandleList = self.exchange.init_candles(self.symbol,self.interval,self.lookback)
        print(self.exchange.candlelist_to_df(self.CandleList))
        self.exchange.connect_ws(self.ws_handler,self.symbol,self.interval,self.duration)
