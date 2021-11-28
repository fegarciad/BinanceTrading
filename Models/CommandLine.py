####################################
# Interpret Command Line Arguments #
####################################

import argparse
import pandas as pd

def read_args() -> dict:
    """Read parameters given in command line."""
    ap = argparse.ArgumentParser(description='Binance Trading Bot')
    intervals = ['1m','15m','1h','4h','1d']

    # Coin
    ap.add_argument("-c", required=False, metavar='Coin', dest='Coin', help="Coin [str] default: BTC",type=str,default='BTC')
    # Interval
    ap.add_argument("-i", required=False, dest='Interval', help="Interval [str] default: 1m",type=str,choices=intervals,default='1m')
    # Order size
    ap.add_argument("-o", required=False, metavar='Ordersize', dest='Ordersize', help="Order size [float] default: 0.0005",type=float,default=0.0005)
    # Duration
    ap.add_argument("-d", required=False, metavar='Duration', dest='Duration', help="Duration (seconds) [int] default: 600",type=int,default=600)
    # Profit target
    ap.add_argument("-t", required=False, metavar='Profit target', dest='Profit', help="Profit target (percent) [float] default: 25",type=float,default=25)
    # Stop loss
    ap.add_argument("-l", required=False, metavar='Stop loss', dest='Loss', help="Stop loss, negative! (percent) [float] default: -5",type=float,default=-5)
    # Paper trade
    ap.add_argument("-p", required=False, dest='Papertrade', help="Paper Trade, if called paper trading is DISABLED, else its enabled.",action="store_false")

    params = vars(ap.parse_args())

    print('Setting params.. -h for help.')
    print('\n'+pd.DataFrame(params,index=[0]).to_string(index=False))
    
    return params

def read_backtest_args() -> dict:
    """Read parameters given in command line for backtesting."""
    ap = argparse.ArgumentParser(description='Binance Trading Bot Backtest')
    intervals = ['1m','15m','1h','4h','1d']

    # Coin
    ap.add_argument("-c", required=False, metavar='Coin', dest='Coin', help="Coin [str] default: BTC",type=str,default='BTC')
    # Interval
    ap.add_argument("-i", required=False, dest='Interval', help="Interval [str] default: 1m",type=str,choices=intervals,default='1m')
    # Order size
    ap.add_argument("-o", required=False, metavar='Ordersize', dest='Ordersize', help="Order size [float] default: 0.0005",type=float,default=0.0005)
    # Backtest period
    ap.add_argument("-b", required=False, metavar='Backtest period', dest='Backtest period', help="Number of data points for backtest [int] default: 500",type=int,default=500)
    
    params = vars(ap.parse_args())

    print('Setting params.. -h for help.')
    print('\n'+pd.DataFrame(params,index=[0]).to_string(index=False))
    
    return params
        