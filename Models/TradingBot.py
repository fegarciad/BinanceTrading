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
        self.candle_list = self.exchange.init_candles(self.symbol,self.interval,self.strategy.get_lookback())
        self.candle_df = self.exchange.candle_list_to_df(self.candle_list)
        
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
            self.candle_list, changed = self.exchange.refresh_candles(msg,self.candle_list)
            if changed:
                self.candle_df = self.exchange.candle_list_to_df(self.candle_list)
                self.account.log_to_file('\n'+self.candle_df.to_string(index=False))
                exit, signal = self.account.check_profit_loss(self.symbol,self.profit,self.loss)
                if exit:
                    if signal == 'Loss':
                        self.exchange.exit_positions(self.symbol,self.paper_trade)
                    self.exchange.event.set() # Terminate trading session
                else:
                    _ = self.exec_strategy(self.candle_df)
        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.event.set() # Terminate trading session

    def run(self) -> None:
        """Initialize portfolio, connecto to WebSocket and run strategy."""
        msg = '\nRunning {}, PaperTrade: {}'.format(str(self.strategy),self.paper_trade)
        print(msg)
        self.account.log_to_file(msg)
        self.account.log_to_file('\nSymbol: {}\nInterval: {}\nOrdersize: {}\nDuration: {}'.format(self.symbol,self.interval,self.order_size,self.duration))
        self.account.log_to_file('\nTake profit: {}%\nStop Loss: {}%\n\n{}'.format(self.profit,self.loss,self.exchange.candle_list_to_df(self.candle_list).to_string(index=False)))
        self.exchange.connect_ws(self.ws_handler,self.symbol,self.interval,self.duration)
