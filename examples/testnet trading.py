##################################
# Example Testnet Trading Script #
##################################

import os
import binancetrading as bt

API =  os.environ.get('TESTNET_API')
SECRET = os.environ.get('TESTNET_SECRET')

APIURL = 'https://testnet.binance.vision'
WSURL = 'wss://testnet.binance.vision'


def main(coin: str, order_size: float, interval: str, duration: int, profit: float, loss: float, paper_trade: bool) -> None:
    """Main trading function."""

    account = bt.Account(API, SECRET, paper_trade, use_real_balance_as_paper=True, apiurl=APIURL)
    exchange = bt.Exchange(wsurl=WSURL)

    strategy = bt.strategies.RandomStrategy(upper=60, lower=40)
    tradebot = bt.TradingBot(account, exchange, strategy, coin, order_size, interval, duration, profit, loss)
    tradebot.run()


if __name__ == '__main__':
    print('\nTestnet example\n')
    args = bt.command_line.read_args()
    main(args['Coin'], args['Ordersize'], args['Interval'], args['Duration'], args['Profit'], args['Loss'], args['Papertrade'])
