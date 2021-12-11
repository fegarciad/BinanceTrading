########################
# Main Backtest Script #
########################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

import os
import binancetrading as bt

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')


def main(coin: str, order_size: float, interval: str, backtest_period: int) -> None:
    """Main backtest function."""

    account = bt.Account(API, SECRET, paper_trade=True, paper_position=0.1, paper_cash_position=10_000)
    exchange = bt.Exchange(account)

    strategy = bt.strategies.TMAStrategy(period_long=63, period_mid=42, period_short=21)
    tradebot = bt.TradingBot(account, exchange, strategy, coin, order_size, interval, duration=0, profit=0, loss=0)
    backtest = bt.Backtest(account, exchange, tradebot, strategy, backtest_period)
    backtest.run_backtest(plot=True)


if __name__ == '__main__':
    args = bt.command_line.read_backtest_args()
    main(args['Coin'], args['Ordersize'], args['Interval'], args['Backtest window'])
