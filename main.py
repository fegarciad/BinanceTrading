###############################
# Main Binance Trading Script #
###############################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import sys

from config import API_KEY, API_SECRET

from Models.CommandLine import CommandLine
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot


# Main function 
def main(coin: str, order_size: float, interval: str, duration: int, lookback: int, paper_trade: bool) -> None:
    exchange = Exchange(API_KEY,API_SECRET)
    print(exchange.account_balance(),'\n')

    strategy = RandomStrategy()
    tradebot = TradingBot(exchange,strategy,coin,order_size,interval,duration,lookback,paper_trade)
    tradebot.run()


if __name__ == '__main__':
    commandline = CommandLine(sys.argv[1:])
    args = commandline.read_args()
    print(args)
    main(args['coin'],args['order_size'],args['interval'],args['duration'],args['lookback'],args['paper_trade'])

