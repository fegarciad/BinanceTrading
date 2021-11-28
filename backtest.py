########################
# Main Backtest Script #
########################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os

from Models.Account import Account
from Models.Backtest import Backtest
from Models.CommandLine import read_backtest_args
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

def main(coin: str, order_size: float, interval: str, backtest_period: int) -> None:
    
    account = Account(API,SECRET,paper_trade=True,paper_position=0.01,paper_cash_position=1000)
    exchange = Exchange(account)
    
    strategy = TMAStrategy(period_long=63,period_mid=42,period_short=21)
    tradebot = TradingBot(account,exchange,strategy,coin,order_size,interval,duration=0,profit=0,loss=0)
    backtest = Backtest(account,exchange,tradebot,strategy,backtest_period)
    backtest.run_backtest()
    backtest.plot_backtest()


if __name__ == '__main__':
    os.system('cls')
    args = read_backtest_args()
    main(args['Coin'],args['Ordersize'],args['Interval'],args['Backtest period'])
