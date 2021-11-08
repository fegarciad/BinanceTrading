########################
# Main Backtest Script #
########################

"""
IF USING WEBSOCKETS ON WINDOWS FOLLOW INSTRUCTIONS BELOW
https://dev.binance.vision/t/cant-run-any-websocket-example-on-binance-connector-python-on-windows/4957/2
"""

from config import API_KEY, API_SECRET

from Models.Backtest import Backtest
from Models.CommandLine import CommandLine
from Models.Exchange import Exchange
from Models.Strategies import MACDStrategy, RandomStrategy, TMAStrategy
from Models.TradingBot import TradingBot


# Main function 
def main(coin: str, order_size: float, interval: str, backtest_period: int) -> None:
    """Main backtest function."""
    exchange = Exchange(API_KEY,API_SECRET)
    
    paper_cash = 500
    paper_coin = 0.01
    exchange.set_paper_portfolio(coin_balance=paper_coin,cash=paper_cash) # To use actual balance to backtest set: use_real_balance = True and pass coin name 

    strategy = TMAStrategy()
    tradebot = TradingBot(exchange,strategy,coin,order_size,interval,duration=0,paper_trade=True)
    backtest = Backtest(exchange,tradebot,strategy,backtest_period)
    backtest.run_backtest()


if __name__ == '__main__':
    commandline = CommandLine()
    args = commandline.read_backtest_args()
    main(args['coin'],args['ordersize'],args['interval'],args['backtestperiod'])
