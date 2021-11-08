####################################
# Interpret Command Line Arguments #
####################################

import argparse


class CommandLine():

    def __init__(self) -> None:
        pass

    def read_args(self) -> dict:
        """Read parameters given in command line."""
        ap = argparse.ArgumentParser(description='Binance Trading Bot')
        intervals = ['1m','15m','30m','1h','4h','12h','1d']

        # Coin
        ap.add_argument("-c", "--coin", required=False, help="Coin [str] default: BTC",type=str,default='BTC')
        # Interval
        ap.add_argument("-i", "--interval", required=False, help="Interval [str] default: 1m",type=str,choices=intervals,default='1m')
        # Order size
        ap.add_argument("-o", "--ordersize", required=False, help="Order size [float] default: 0.0005",type=float,default=0.0005)
        # Duration
        ap.add_argument("-d", "--duration", required=False, help="Duration (seconds) [int] default: 600",type=int,default=600)
        # Paper trade
        ap.add_argument("-p", "--papertrade", required=False, help="Paper Trade, if called paper trading is DISABLED, else its enabled.",action="store_false")

        self.params = vars(ap.parse_args())

        print('Setting params.. -h for help.')
        print(self.params)
        
        return self.params

    def read_backtest_args(self) -> dict:
        """Read parameters given in command line for backtesting."""
        ap = argparse.ArgumentParser(description='Binance Trading Bot Backtest')
        intervals = ['1m','15m','30m','1h','4h','12h','1d']

        # Coin
        ap.add_argument("-c", "--coin", required=False, help="Coin [str] default: BTC",type=str,default='BTC')
        # Interval
        ap.add_argument("-i", "--interval", required=False, help="Interval [str] default: 1m",type=str,choices=intervals,default='1m')
        # Order size
        ap.add_argument("-o", "--ordersize", required=False, help="Order size [float] default: 0.0005",type=float,default=0.0005)
        # Backtest period
        ap.add_argument("-b", "--backtestperiod", required=False, help="Number of data points for backtest [int] default: 500",type=int,default=500)
        
        self.params = vars(ap.parse_args())

        print('Setting params.. -h for help.')
        print(self.params)
        
        return self.params
        