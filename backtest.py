########################
# Main Backtest Script #
########################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

from config import API_KEY, API_SECRET

from Models.CommandLine import CommandLine
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot
from Models.Backtest import Backtest


# Main function 
def main(coin: str, order_size: float, interval: str, backtest_period: int, lookback: int) -> None:
    """Main backtest function."""
    exchange = Exchange(API_KEY,API_SECRET)
    
    exchange.set_paper_portfolio(use_real_balance=True, coin=coin)

    strategy = RandomStrategy()
    tradebot = TradingBot(exchange,strategy,coin,order_size,interval,lookback=lookback,paper_trade=True)
    backtest = Backtest(exchange,tradebot,strategy,backtest_period)


if __name__ == '__main__':
    commandline = CommandLine()
    args = commandline.read_backtest_args()
    main(args['coin'],args['ordersize'],args['interval'],args['backtestperiod'],args['lookback'])