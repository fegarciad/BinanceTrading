####################################
# Interpret Command Line Arguments #
####################################

import re
import sys


class CommandLine():

    def __init__(self, args: str) -> None:
        self.args = args

    def check_params(self) -> None:
        """Check format of given parameters."""
        intervals = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','3d','1w','1M']
        if self.interval not in intervals:
            print('\nInterval has to be one of {}.'.format(intervals))
            sys.exit()
        try:
            self.lookback = int(self.lookback)
            self.duration = int(self.duration)
        except ValueError:
            print('\nLookback and Duration have to be integers.')
            sys.exit()
        try:
            self.order_size = float(self.order_size)
        except ValueError:
            print('\nOrder Size has to be float.')
            sys.exit()
        if str(self.paper_trade) not in ['True','False']:
            print('\nPaper Trade has to be True or False.')
            sys.exit()
        else:
            self.paper_trade = self.paper_trade == 'True'
        
    def check_backtest_params(self) -> None:
        """Check format of given parameters for backtesting."""
        pass

    def read_args(self) -> dict:
        """Read parameters given in command line."""
        print("Setting params ...")
        # Coin
        try:
            coinArg = re.findall('base:(\w+)',''.join(self.args))
            self.coin = str(coinArg[0])
            print("Coin:",self.coin)
        except:
            self.coin = 'BTC'
            print("Coin:",self.coin)
        # Interval
        try:
            intervArg = re.findall('interval:(\w+)',''.join(self.args))
            self.interval = str(intervArg[0])
            print("Interval:",self.interval)
        except:
            self.interval = '1m'
            print("Interval:",self.interval)
        # Lookback
        try:
            lookArg = re.findall('lookback:(\w+)',''.join(self.args))
            self.lookback = str(lookArg[0])
            print("Lookback:",self.lookback)
        except:
            self.lookback = 20
            print("Lookback:",self.lookback)
        # Order size
        try:
            orderArg = re.findall('order_size:(\w+)',''.join(self.args))
            self.order_size = str(orderArg[0])
            print("Order Size:",self.order_size)
        except:
            self.order_size = 0.01
            print("Order Size:",self.order_size)
        # Duration
        try:
            durArg = re.findall('duration:(\w+)',''.join(self.args))
            self.duration = str(durArg[0])
            print("Duration:",self.duration)
        except:
            self.duration = 600
            print("Duration:",self.duration)
        # Paper Trade
        try:
            paperArg = re.findall('paper_trade:(\w+)',''.join(self.args))
            self.paper_trade = str(paperArg[0])
            print("Paper Trade:",self.paper_trade)
        except:
            self.paper_trade = 'True'
            print("Paper Trade:",self.paper_trade)
        
        self.check_params()

        params = {
            'coin': self.coin,
            'interval': self.interval,
            'lookback': self.lookback,
            'order_size': self.order_size,
            'duration': self.duration,
            'paper_trade': self.paper_trade,
        }
        return params

    def read_backtest_args(self) -> dict:
        """Read parameters given in command line for backtesting."""
        pass
        