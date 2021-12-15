##########################
# Example Trading Script #
##########################

import os
import binancetrading as bt

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')

APIURL = 'https://api.binance.com'
WSURL = 'wss://stream.binance.com:9443/ws'


def main(coin: str, order_size: float, interval: str, duration: int, profit: float, loss: float, paper_trade: bool) -> None:
    """Main trading function."""

    account = bt.Account(API, SECRET, paper_trade, use_real_balance_as_paper=True, apiurl=APIURL)
    exchange = bt.Exchange(wsurl=WSURL)

    strategy = bt.strategies.RandomStrategy(upper=60, lower=40)
    tradebot = bt.TradingBot(account, exchange, strategy, coin, order_size, interval, duration, profit, loss)
    tradebot.run()


if __name__ == '__main__':
    print('\nTrading example\n')
    args = bt.command_line.read_args()
    main(args['Coin'], args['Ordersize'], args['Interval'], args['Duration'], args['Profit'], args['Loss'], args['Papertrade'])
