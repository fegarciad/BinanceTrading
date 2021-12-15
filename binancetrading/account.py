
"""Account Class"""

import logging
import time
from dataclasses import dataclass

import pandas as pd
from binance.spot import Spot
from binance.lib.utils import config_logging

LOG = False

# Disable binance loggers
logging.getLogger("binance.websocket.binance_socket_manager").disabled = True
logging.getLogger("binance.websocket.binance_client_factory").disabled = True
logging.getLogger("binance.websocket.binance_client_protocol").disabled = True

def enable_logging() -> None:
    """Enable logging, off by default."""
    global LOG
    LOG = True
    config_logging(logging, logging.INFO, log_file=f'{time.strftime("%Y-%m-%d %H-%M", time.localtime())}.log')

def log_msg(msg: str, verb: bool = False) -> None:
    """Log messages to log file and or screen."""
    if LOG:
        logging.info(f'{msg}\n')
    if verb:
        print(f'\n{msg}')


@dataclass
class Account:
    """Account class."""

    api: str
    secret: str
    paper_trade: bool
    paper_position: float = 0.001
    paper_cash_position: float = 1000
    use_real_balance_as_paper: bool = False
    apiurl: str = 'https://api.binance.com'

    def __post_init__(self) -> None:
        self.client = Spot(key=self.api, secret=self.secret, base_url=self.apiurl)
        self.commissions: float = 0.0
        self.init_wealth: float = 0.0
        self.wealth: float = 0.0
        self.trades: list[dict] = []

        self.position: float = 0.0
        self.cash_position: float = 0.0

        log_msg(f'Started at: {time.strftime("%Y-%m-%d %H-%M", time.localtime())}')

    def account_balances(self) -> pd.DataFrame:
        """Get current account balances from binance."""
        acc_df = pd.DataFrame(self.client.account()['balances'])
        acc_df[['free', 'locked']] = acc_df[['free', 'locked']].astype(float)
        acc_df.columns = ['Asset', 'Free', 'Locked']
        acc_df = acc_df.loc[(acc_df['Free'] != 0.0) | (acc_df['Locked'] != 0.0)].reset_index()
        return acc_df[['Asset', 'Free', 'Locked']]

    def get_coin_balance(self, coin: str) -> float:
        """Get balance of specific coin."""
        acc_df = self.account_balances()
        try:
            balance = float(acc_df.loc[acc_df['Asset'] == coin, 'Free'])
        except TypeError:
            balance = 0
        return balance

    def _set_positions(self, coin: str, position: float, cash_position: float) -> None:
        """Initialize local portfolio to track orders and current positions."""
        if self.paper_trade and not self.use_real_balance_as_paper:
            self.position = position
            self.cash_position = cash_position
        else:
            self.position = self.get_coin_balance(coin)
            self.cash_position = self.get_coin_balance('USDT')

    def _refresh_positions(self, side, price, qty, commission) -> None:
        """Given an order, modify positions accordingly."""
        if side == 'BUY':
            self.position += qty
            self.cash_position -= qty * price
            self.commissions += qty * price * commission
        if side == 'SELL':
            self.position -= qty
            self.cash_position += qty * price
            self.commissions += qty * price * commission

    def _value_positions(self, symbol: str, init: bool = False, verbose: bool = True) -> None:
        """Value current positions."""
        price = float(self.client.ticker_price(symbol)['price'])
        self.wealth = self.cash_position + price * self.position - self.commissions
        if init:
            self.init_wealth = self.wealth
        if verbose:
            log_msg(f'{symbol} position: {self.position:,.4f}\nCash position: {self.cash_position:,.2f}\nCommissions: {self.commissions:,.2f}\nTotal: {self.wealth:,.2f}', verb=True)

    def _check_profit_loss(self, symbol: str, profit: float, loss: float) -> tuple[bool, str]:
        """Check profit and loss targets, exit program if they are met."""
        self._value_positions(symbol, verbose=False)
        current_return = (self.wealth / self.init_wealth - 1) * 100
        log_msg(f'Current return: {current_return:.4f}%')
        if current_return > profit:
            log_msg(f'Profit target met at {current_return:.4f}%, exiting program.', verb=True)
            return True, 'Profit'
        if current_return < loss:
            log_msg(f'Stop loss met at {current_return:.4f}%, exiting program.', verb=True)
            return True, 'Loss'
        return False, ''
