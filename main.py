###############################
# Main Binance Trading Script #
###############################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os

from Models.CommandLine import read_args
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

def main(coin: str, order_size: float, interval: str, duration: int, profit: float, loss: float, paper_trade: bool) -> None:
    
    exchange = Exchange(API,SECRET)
    
    exchange.set_paper_portfolio(use_real_balance=True, coin=coin)

    strategy = RandomStrategy()
    tradebot = TradingBot(exchange,strategy,coin,order_size,interval,duration,profit,loss,paper_trade)
    tradebot.run()


if __name__ == '__main__':
    args = read_args()
    main(args['Coin'],args['Ordersize'],args['Interval'],args['Duration'],args['Profit'],args['Loss'],args['Papertrade'])
