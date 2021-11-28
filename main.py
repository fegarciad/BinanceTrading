#######################
# Main Trading Script #
#######################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os

from Models.Account import Account
from Models.CommandLine import read_args
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot

testnet = True

API = os.environ.get('BINANCE_API') if not testnet else os.environ.get('TESTNET_API')
SECRET = os.environ.get('BINANCE_SECRET') if not testnet else os.environ.get('TESTNET_SECRET')

apiurl = 'https://api.binance.com' if not testnet else 'https://testnet.binance.vision'
wsurl = 'wss://stream.binance.com:9443/ws' if not testnet else 'wss://testnet.binance.vision'

def main(coin: str, order_size: float, interval: str, duration: int, profit: float, loss: float, paper_trade: bool) -> None:
    
    account = Account(API,SECRET,paper_trade,use_real_balance_as_paper=True,apiurl=apiurl)
    exchange = Exchange(account,wsurl=wsurl)

    strategy = RandomStrategy(upper=60,lower=40)
    tradebot = TradingBot(account,exchange,strategy,coin,order_size,interval,duration,profit,loss,paper_trade)
    tradebot.run()


if __name__ == '__main__':
    os.system('cls')
    print(f'Testnet: {testnet}')
    args = read_args()
    main(args['Coin'],args['Ordersize'],args['Interval'],args['Duration'],args['Profit'],args['Loss'],args['Papertrade'])
