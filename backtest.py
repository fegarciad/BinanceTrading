########################
# Main Backtest Script #
########################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os

from Models.Backtest import Backtest
from Models.CommandLine import read_backtest_args
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

def main(coin: str, order_size: float, interval: str, backtest_period: int) -> None:
    
    exchange = Exchange(API,SECRET)
    
    paper_cash = 500
    paper_coin = 0.01
    exchange.set_paper_portfolio(coin_balance=paper_coin,cash=paper_cash) # To use actual balance to backtest set: use_real_balance = True and pass coin name 

    strategy = TMAStrategy(period_long=63,period_mid=42,period_short=21)
    tradebot = TradingBot(exchange,strategy,coin,order_size,interval,duration=0,profit=0,loss=0,paper_trade=True)
    backtest = Backtest(exchange,tradebot,strategy,backtest_period)
    backtest.run_backtest()
    backtest.plot_backtest()


if __name__ == '__main__':
    args = read_backtest_args()
    main(args['Coin'],args['Ordersize'],args['Interval'],args['Backtest period'])
