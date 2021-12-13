
"""Trading Bot Class"""

from dataclasses import dataclass

import pandas as pd

from binancetrading.account import Account, log_msg
from binancetrading.exchange import Exchange, _candle_list_to_df, _refresh_candles
from binancetrading.strategies import TradingStrategy


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
        self.candle_list = self.exchange._init_candles(self.symbol, self.interval, self.strategy.get_lookback())
        self.candle_df = _candle_list_to_df(self.candle_list)

    def execute_strategy(self, data: pd.DataFrame) -> str:
        """Check if there is buy/sell signal and execute it."""
        signal = self.strategy.signal(data)
        if signal:
            self.exchange.execute_order(self.account, self.symbol, signal, self.order_size, self.exchange._get_commission(self.account, self.symbol), self.account.paper_trade)
        else:
            log_msg('\nNo order was placed.')
        return signal

    def _ws_handler(self, msg: dict) -> None:
        """Function to handle incoming WebSocket candlestick data and pass it to the strategy."""
        try:
            self.candle_list, changed = _refresh_candles(msg, self.candle_list)
            if changed:
                self.candle_df = _candle_list_to_df(self.candle_list)
                exit_signal, reason = self.account._check_profit_loss(self.symbol, self.profit, self.loss)
                if exit_signal:
                    if reason == 'Loss':
                        self.exchange.exit_positions(self.account, self.symbol, self.account.paper_trade)
                    self.exchange.event.set()  # Terminate trading session
                else:
                    _ = self.execute_strategy(self.candle_df)
        except KeyError:
            if msg == {'result': None, 'id': 1}:
                pass
            else:
                print(msg)
                self.exchange.event.set()  # Terminate trading session

    def run(self) -> None:
        """Initialize portfolio, connecto to WebSocket and run strategy."""
        log_msg(f'\nRunning {self.strategy}', verb=True)
        log_msg(f'\nSymbol: {self.symbol}\nInterval: {self.interval}\nOrdersize: {self.order_size}\nDuration: {self.duration}')
        log_msg(f'\nTake profit: {self.profit}%\nStop loss: {self.loss}%')
        self.account._set_positions(self.coin, self.account.paper_position, self.account.paper_cash_position)
        self.account._value_positions(self.symbol, init=True)
        self.exchange._connect_ws(self.account, self._ws_handler, self.symbol, self.interval, self.duration)
