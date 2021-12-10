#######################
# Main Trading Script #
#######################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os
import binancetrading as bt

TESTNET = True

API = os.environ.get('BINANCE_API') if not TESTNET else os.environ.get('TESTNET_API')
SECRET = os.environ.get('BINANCE_SECRET') if not TESTNET else os.environ.get('TESTNET_SECRET')

APIURL = 'https://api.binance.com' if not TESTNET else 'https://testnet.binance.vision'
WSURL = 'wss://stream.binance.com:9443/ws' if not TESTNET else 'wss://testnet.binance.vision'


def main(coin: str, order_size: float, interval: str, duration: int, profit: float, loss: float, paper_trade: bool) -> None:
    """Main trading function."""

    account = bt.Account(API, SECRET, paper_trade, use_real_balance_as_paper=True, apiurl=APIURL)
    exchange = bt.Exchange(account, wsurl=WSURL)

    strategy = bt.RandomStrategy(upper=60, lower=40)
    tradebot = bt.TradingBot(account, exchange, strategy, coin, order_size, interval, duration, profit, loss)
    tradebot.run()


if __name__ == '__main__':
    print(f'\nTestnet: {TESTNET}')
    args = bt.read_args()
    main(args['Coin'], args['Ordersize'], args['Interval'], args['Duration'], args['Profit'], args['Loss'], args['Papertrade'])
