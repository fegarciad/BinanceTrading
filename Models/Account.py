#################
# Account Class #
#################

import os
import time
import pandas as pd
from dataclasses import dataclass

from binance.spot import Spot


@dataclass
class Account:
    
    api: str
    secret: str
    paper_trade: bool
    paper_position: float = 0.001
    paper_cash_position: float = 1000
    use_real_balance_as_paper: bool = False
    apiurl: str = 'https://api.binance.com'
    
    def __post_init__(self) -> None:
        self.Client = Spot(key=self.api, secret=self.secret, base_url=self.apiurl)
        self.commissions = 0
        self.init_wealth = 0
        self.wealth = 0
        self.trades = []

        self.logfile = os.path.join(os.getcwd(),'log_file.txt')
        self.log_to_file('Started at: {}'.format(time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))), init=True)

    def log_to_file(self, msg: str, init: bool = False) -> None:
        """Log messages to log file for later inspection."""
        if init:
            with open(self.logfile,'w') as f:
                f.write(msg)
        else:
            with open(self.logfile,'a+') as f:
                f.write('\n'+msg)

    def set_positions(self, coin: str, position: float, cash_position: float) -> None:
        """Initialize local portfolio to track orders and current positions."""
        if self.paper_trade and not self.use_real_balance_as_paper:
            self.position = position
            self.cash_position = cash_position
        else:
            self.position = self.get_coin_balance(coin)
            self.cash_position = self.get_coin_balance('USDT')

    def account_balance(self) -> pd.DataFrame:
        """Get current account balances from binance."""
        acc_df = pd.DataFrame(self.Client.account()['balances'])
        acc_df[['free','locked']] = acc_df[['free','locked']].astype(float)
        acc_df.columns = ['Asset','Free','Locked']
        acc_df = acc_df.loc[(acc_df['Free'] != 0.0)|(acc_df['Locked'] != 0.0)].reset_index()
        return acc_df[['Asset','Free','Locked']]

    def get_coin_balance(self,coin: str) -> float:
        """Get balance of specific coin."""
        acc_df = self.account_balance()
        return float(acc_df.loc[acc_df['Asset'] == coin,'Free'])

    def refresh_positions(self, side, price, qty, commission) -> None:
        """Given an order, modify positions accordingly."""
        if side == 'BUY':
            self.position += qty
            self.cash_position -= qty * price
            self.commissions += qty * price * commission
        if side == 'SELL':
            self.position -= qty
            self.cash_position += qty * price
            self.commissions += qty * price * commission

    def value_positions(self, symbol: str, init: bool = False, verbose: bool = True) -> None:
        """Value current positions."""
        price = float(self.Client.ticker_price(symbol)['price'])
        self.wealth = self.cash_position + price * self.position - self.commissions
        if init:
            self.init_wealth = self.wealth
        msg = '\n{} position: {:,.4f}\nCash position: {:,.2f}\nCommissions: {:,.2f}\nTotal: {:.2f}'.format(symbol,self.position,self.cash_position,self.commissions,self.wealth)
        if verbose:
            print(msg)
            self.log_to_file(msg)
    
    def check_profit_loss(self, symbol: str, profit: float, loss: float) -> tuple[bool,str]:
        """Check profit and loss targets, exit program if they are met."""
        self.value_positions(symbol,verbose=False)
        current_return = (self.wealth/self.init_wealth - 1) * 100
        print(f'\nCurrent return: {current_return:.4f}%')
        if current_return > profit:
            msg = '\nProfit target met at {:.4f}%, exiting program.'.format(current_return)
            print(msg)
            self.log_to_file(msg)
            return True, 'Profit'
        if current_return < loss:
            msg = '\nStop loss met at {:.4f}%, exiting program.'.format(current_return)
            print(msg)
            self.log_to_file(msg)
            return True, 'Loss'
        return False, ''
