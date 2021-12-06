
"""Trading Bot Class"""

from dataclasses import dataclass

import pandas as pd

from Models.account import Account
from Models.exchange import Exchange
from Models.strategies import TradingStrategy


@dataclass
class TradingBot:
    """Trading bot class."""

    account: Account
    exchange: Exchange
    strategy: TradingStrategy
    coin: str
    order_size: float
    interval: str
    duration: int
    profit: float
    loss: float
    verbose: bool = False

    def __post_init__(self) -> None:
        self.symbol = self.coin + 'USDT'
        self.candle_list = self.exchange.init_candles(self.symbol, self.interval, self.strategy.get_lookback())
        self.candle_df = self.exchange.candle_list_to_df(self.candle_list)

        self.account.set_positions(self.coin, self.account.paper_position, self.account.paper_cash_position)
        self.account.value_positions(self.symbol, init=True)

    def exec_strategy(self, data: pd.DataFrame) -> str:
        """Check if there is buy/sell signal and execute it."""
        signal = self.strategy.signal(data)
        if signal:
            self.exchange.execute_order(self.symbol, signal, self.order_size, self.account.paper_trade)
        else:
            self.account.log_to_file('\nNo order was placed.')
        return signal

    def ws_handler(self, msg: str) -> None:
        """Function to handle incoming WebSocket candlestick data and pass it to the strategy."""
        try:
            self.candle_list, changed = self.exchange.refresh_candles(msg, self.candle_list)
            if changed:
                self.candle_df = self.exchange.candle_list_to_df(self.candle_list)
                self.account.log_to_file('\n' + self.candle_df.to_string(index=False))
                exit_signal, reason = self.account.check_profit_loss(self.symbol, self.profit, self.loss)
                if exit_signal:
                    if reason == 'Loss':
                        self.exchange.exit_positions(self.symbol, self.account.paper_trade)
                    self.exchange.event.set()  # Terminate trading session
                else:
                    _ = self.exec_strategy(self.candle_df)
        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.event.set()  # Terminate trading session

    def run(self) -> None:
        """Initialize portfolio, connecto to WebSocket and run strategy."""
        msg = f'\nRunning {self.strategy}'
        print(msg)
        self.account.log_to_file(msg)
        self.account.log_to_file(f'\nSymbol: {self.symbol}\nInterval: {self.interval}\nOrdersize: {self.order_size}\nDuration: {self.duration}')
        self.account.log_to_file(f'\nTake profit: {self.profit}%\nStop Loss: {self.loss}%\n\n{self.exchange.candle_list_to_df(self.candle_list).to_string(index=False)}')
        self.exchange.connect_ws(self.ws_handler, self.symbol, self.interval, self.duration)
