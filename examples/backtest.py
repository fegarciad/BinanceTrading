###########################
# Example Backtest Script #
###########################

import os
import binancetrading as bt

API = os.environ.get('BINANCE_API')
SECRET = os.environ.get('BINANCE_SECRET')


def main(coin: str, order_size: float, interval: str, backtest_period: int) -> None:
    """Main backtest function."""

    account = bt.Account(API, SECRET, paper_trade=True, paper_position=0.1, paper_cash_position=10_000)
    exchange = bt.Exchange()

    strategy = bt.strategies.TMAStrategy(period_long=63, period_mid=42, period_short=21)
    tradebot = bt.TradingBot(account, exchange, strategy, coin, order_size, interval, duration=0, profit=0, loss=0)
    backtest = bt.Backtest(tradebot, backtest_period)
    backtest.run_backtest(plot=True)


if __name__ == '__main__':
    print('\nBacktest example\n')
    args = bt.command_line.read_backtest_args()
    main(args['Coin'], args['Ordersize'], args['Interval'], args['Backtest window'])
